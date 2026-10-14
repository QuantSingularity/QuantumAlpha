from typing import Any, Dict, List, Optional

import numpy as np
from ai_models.core.exceptions import ValidationError
from ai_models.inference.predictor import Forecast, PredictionService, summarize


class EnsembleService:
    def __init__(self, predictor: PredictionService) -> None:
        self.predictor = predictor

    def _weights(
        self, model_ids: List[str], weights: Optional[List[float]], mode: str
    ) -> np.ndarray:
        if weights is not None:
            if (
                len(weights) != len(model_ids)
                or any(w < 0 for w in weights)
                or sum(weights) <= 0
            ):
                raise ValidationError(
                    "weights must be non-negative, match model_ids, and sum above zero"
                )
            raw = np.asarray(weights, dtype=float)
        elif mode == "skill":
            raw = []
            for model_id in model_ids:
                metrics = self.predictor.registry.get(model_id).get("metrics") or {}
                raw.append(max(float(metrics.get("skill_vs_naive", 0.0)), 0.0) + 0.05)
            raw = np.asarray(raw, dtype=float)
        elif mode == "equal":
            raw = np.ones(len(model_ids))
        else:
            raise ValidationError("mode must be 'equal' or 'skill'")
        return raw / raw.sum()

    def predict(
        self,
        model_ids: List[str],
        symbol: str,
        timeframe: str = "1d",
        period: Optional[str] = None,
        horizon: Optional[int] = None,
        weights: Optional[List[float]] = None,
        mode: str = "skill",
    ) -> Dict[str, Any]:
        if not isinstance(model_ids, list) or len(model_ids) < 2:
            raise ValidationError("At least two model_ids are required")
        if len(set(model_ids)) != len(model_ids) or len(model_ids) > 10:
            raise ValidationError("model_ids must be unique and at most 10")
        w = self._weights(model_ids, weights, mode)
        forecasts: List[Forecast] = [
            self.predictor.forecast(model_id, symbol, timeframe, period, horizon)
            for model_id in model_ids
        ]
        steps = min(f.horizon for f in forecasts)
        returns = np.stack([f.returns[:steps] for f in forecasts])
        sigmas = np.stack([f.sigma[:steps] for f in forecasts])
        mean = (w[:, None] * returns).sum(axis=0)
        variance = (w[:, None] * (sigmas**2 + (returns - mean) ** 2)).sum(axis=0)
        base = forecasts[0]
        combined = Forecast(
            model_id="ensemble",
            version=0,
            info={},
            symbol=base.symbol,
            timeframe=base.timeframe,
            returns=mean,
            sigma=np.sqrt(variance),
            last_close=base.last_close,
            last_timestamp=base.last_timestamp,
            horizon=steps,
            trained_symbol=None,
        )
        return summarize(
            combined,
            {
                "model_id": None,
                "ensemble": {
                    "model_ids": model_ids,
                    "weights": w.tolist(),
                    "mode": "custom" if weights else mode,
                    "dispersion": float(np.std(returns[:, -1])),
                },
            },
        )
