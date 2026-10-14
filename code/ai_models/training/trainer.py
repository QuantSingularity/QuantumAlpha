from datetime import datetime, timezone
from typing import Any, Dict, Optional

import numpy as np
from ai_models.core.exceptions import AIEngineError, ServiceError
from ai_models.core.logging import get_logger
from ai_models.data.client import DataServiceClient
from ai_models.data.preprocessing import prepare_training_data
from ai_models.evaluation.backtest import backtest_signals
from ai_models.evaluation.metrics import regression_metrics, residual_std
from ai_models.models.factory import create_model
from ai_models.registry.bundle import save_bundle
from ai_models.registry.store import ModelRegistry
from ai_models.training.config import TrainingConfig

logger = get_logger("training")


class Trainer:
    def __init__(
        self,
        registry: ModelRegistry,
        data_client: DataServiceClient,
        on_trained: Optional[Any] = None,
    ) -> None:
        self.registry = registry
        self.data_client = data_client
        self.on_trained = on_trained

    def train(self, model_id: str, config: TrainingConfig) -> Dict[str, Any]:
        info = self.registry.begin_training(model_id)
        previous_status = "trained" if info.get("versions") else "created"
        try:
            return self._train(model_id, info, config)
        except AIEngineError:
            self.registry.set_status(
                model_id, previous_status if previous_status == "trained" else "error"
            )
            raise
        except Exception as exc:
            logger.exception("Training failed for %s", model_id)
            self.registry.set_status(
                model_id, previous_status if previous_status == "trained" else "error"
            )
            raise ServiceError(f"Training failed: {exc}") from exc

    def _train(
        self, model_id: str, info: Dict[str, Any], config: TrainingConfig
    ) -> Dict[str, Any]:
        features = info.get("features") or []
        ohlcv = self.data_client.fetch_ohlcv(
            config.symbol, config.timeframe, config.period
        )
        data = prepare_training_data(
            ohlcv,
            features,
            config.sequence_length,
            config.horizon,
            config.test_size,
            config.val_size,
        )
        params = {**(info.get("parameters") or {}), **config.params}
        model = create_model(
            info["type"], params, data.n_features, data.sequence_length, data.horizon
        )
        started = datetime.now(timezone.utc)
        fit_summary = model.fit(data)
        test_pred = model.predict(data.X_test)
        metrics = regression_metrics(data.y_test, test_pred)
        reference = (
            (data.X_val, data.y_val)
            if len(data.X_val) >= 5
            else (data.X_test, data.y_test)
        )
        ref_pred = model.predict(reference[0])
        sigma = residual_std(reference[1], ref_pred)
        trading = backtest_signals(data.close_test, test_pred[:, -1])
        trading.pop("equity_curve", None)
        trading.pop("buy_and_hold", None)
        metrics.update(
            {
                "backtest": trading,
                "fit": fit_summary,
                "train_samples": int(len(data.X_train)),
                "val_samples": int(len(data.X_val)),
                "test_samples": int(len(data.X_test)),
                "training_seconds": (
                    datetime.now(timezone.utc) - started
                ).total_seconds(),
            }
        )
        version = self.registry.next_version(model_id)
        meta = {
            "kind": info["type"],
            "params": model.params,
            "features": features,
            "columns": data.columns,
            "sequence_length": data.sequence_length,
            "horizon": data.horizon,
            "residual_std": sigma.tolist(),
            "symbol": config.symbol,
            "timeframe": config.timeframe,
            "period": config.period,
            "rows": int(len(ohlcv)),
            "target": "forward_return",
            "reference_quantiles": {
                column: np.quantile(
                    data.X_train[:, -1, i], np.linspace(0, 1, 11)
                ).tolist()
                for i, column in enumerate(data.columns)
            },
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "version": version,
        }
        save_bundle(
            self.registry.version_dir(model_id, version), model, data.scaler, meta
        )
        training_data = {
            "symbol": config.symbol,
            "timeframe": config.timeframe,
            "period": config.period,
            "sequence_length": config.sequence_length,
            "horizon": config.horizon,
            "rows": int(len(ohlcv)),
        }
        updated = self.registry.add_version(
            model_id, version, metrics, training_data, model.params, config.activate
        )
        if self.on_trained is not None:
            self.on_trained(model_id)
        logger.info("Trained %s v%s on %s", model_id, version, config.symbol)
        return {
            "id": model_id,
            "name": updated["name"],
            "status": updated["status"],
            "version": version,
            "metrics": metrics,
            "training_data": training_data,
        }
