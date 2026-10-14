import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from ai_models.core.exceptions import (
    AIEngineError,
    NotTrainedError,
    ServiceError,
    ValidationError,
)
from ai_models.core.logging import get_logger
from ai_models.core.settings import Settings
from ai_models.data.client import (
    DataServiceClient,
    normalize_period,
    validate_symbol,
    validate_timeframe,
)
from ai_models.data.features import validate_features
from ai_models.data.preprocessing import FeatureScaler, clean_feature_frame
from ai_models.evaluation.backtest import performance_summary
from ai_models.registry.store import ModelRegistry
from ai_models.rl.agents import ALGORITHMS, CONTINUOUS, Agent, create_agent, load_agent
from ai_models.rl.environment import TradingEnv

logger = get_logger("rl")

RL_FEATURES = (
    "returns",
    "sma_20",
    "rsi_14",
    "macd",
    "bollinger_bands",
    "volatility_20",
    "momentum_10",
)
MAX_HISTORY_POINTS = 500


def _action_mode(algorithm: str) -> str:
    return "continuous" if algorithm in CONTINUOUS else "discrete"


def _scalar(action: Any, mode: str) -> Any:
    if mode == "discrete":
        return int(np.asarray(action).reshape(-1)[0])
    return np.asarray(action, dtype=np.float32).reshape(-1)


def run_episode(agent: Agent, env: TradingEnv) -> Dict[str, Any]:
    obs, _ = env.reset()
    done = False
    while not done:
        action = _scalar(agent.predict(obs), env.action_mode)
        obs, _, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
    values = np.array(
        [env.initial_balance] + [h["portfolio_value"] for h in env.history]
    )
    step_returns = values[1:] / values[:-1] - 1.0
    summary = performance_summary(step_returns)
    summary["final_balance"] = float(values[-1])
    summary["return"] = float(values[-1] / env.initial_balance - 1.0)
    summary["buy_and_hold_return"] = float(env.prices[-1] / env.prices[0] - 1.0)
    summary["trades"] = int(env.trades)
    return summary


class RLService:
    def __init__(
        self,
        registry: ModelRegistry,
        data_client: DataServiceClient,
        settings: Settings,
    ) -> None:
        self.registry = registry
        self.data_client = data_client
        self.settings = settings

    @staticmethod
    def public(info: Dict[str, Any], detail: bool = False) -> Dict[str, Any]:
        out = ModelRegistry.detail(info) if detail else ModelRegistry.summary(info)
        out["algorithm"] = info.get("type")
        return out

    def list(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        return [self.public(i) for i in self.registry.list(status)]

    def get(self, model_id: str) -> Dict[str, Any]:
        return self.public(self.registry.get(model_id), detail=True)

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        algorithm = data.get("algorithm", "q_learning")
        if algorithm not in ALGORITHMS:
            raise ValidationError(
                f"Invalid algorithm '{algorithm}'", {"supported": list(ALGORITHMS)}
            )
        features = validate_features(data.get("features")) or list(RL_FEATURES)
        info = self.registry.create(
            data.get("name"),
            algorithm,
            data.get("description", ""),
            data.get("parameters") or {},
            features,
            data.get("tags"),
        )
        return self.public(info, detail=True)

    def update(self, model_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        changes = {
            k: data[k]
            for k in ("name", "description", "parameters", "tags")
            if k in data
        }
        if "features" in data:
            changes["features"] = validate_features(data["features"])
        return self.public(self.registry.update(model_id, changes), detail=True)

    def delete(self, model_id: str) -> Dict[str, Any]:
        return self.registry.delete(model_id)

    def _frame(
        self,
        ohlcv: pd.DataFrame,
        features: List[str],
        columns: Optional[List[str]] = None,
    ):
        frame = clean_feature_frame(ohlcv, features)
        if columns is not None:
            missing = [c for c in columns if c not in frame.columns]
            if missing:
                raise ValidationError(f"Feature columns missing: {missing}")
            frame = frame[columns]
        prices = ohlcv["close"].reindex(frame.index).to_numpy(dtype=np.float64)
        return frame, prices

    def train(self, model_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        symbol = validate_symbol(data.get("symbol"))
        timeframe = validate_timeframe(data.get("timeframe", "1d"))
        period = normalize_period(data.get("period", "1095d"))
        try:
            steps = int(data.get("total_timesteps", 20000))
            holdout = float(data.get("test_size", 0.2))
            balance = float(data.get("initial_balance", 10000))
            fee = float(data.get("transaction_fee", 0.001))
            seed = int(data.get("seed", 42))
        except (TypeError, ValueError):
            raise ValidationError("Numeric training parameters are invalid")
        if not 100 <= steps <= self.settings.max_rl_timesteps:
            raise ValidationError(
                f"total_timesteps must be between 100 and {self.settings.max_rl_timesteps}"
            )
        if not 0.1 <= holdout <= 0.5 or balance <= 0 or not 0 <= fee < 0.1:
            raise ValidationError(
                "Invalid test_size, initial_balance or transaction_fee"
            )
        info = self.registry.begin_training(model_id)
        previous = "trained" if info.get("versions") else "error"
        try:
            result = self._train(
                model_id,
                info,
                symbol,
                timeframe,
                period,
                steps,
                holdout,
                balance,
                fee,
                seed,
            )
            return result
        except AIEngineError:
            self.registry.set_status(model_id, previous)
            raise
        except Exception as exc:
            logger.exception("RL training failed for %s", model_id)
            self.registry.set_status(model_id, previous)
            raise ServiceError(f"RL training failed: {exc}") from exc

    def _train(
        self,
        model_id,
        info,
        symbol,
        timeframe,
        period,
        steps,
        holdout,
        balance,
        fee,
        seed,
    ) -> Dict[str, Any]:
        algorithm = info["type"]
        mode = _action_mode(algorithm)
        ohlcv = self.data_client.fetch_ohlcv(symbol, timeframe, period)
        frame, prices = self._frame(ohlcv, info.get("features") or list(RL_FEATURES))
        n = len(frame)
        split = int(n * (1.0 - holdout))
        if split < 60 or n - split < 20:
            raise ValidationError(
                "Not enough history for RL training", {"rows": int(n)}
            )
        columns = list(frame.columns)
        values = frame.to_numpy(dtype=np.float64)
        scaler = FeatureScaler().fit(values[:split])
        scaled = scaler.transform(values).astype(np.float32)
        params = info.get("parameters") or {}

        def make_train_env() -> TradingEnv:
            return TradingEnv(scaled[:split], prices[:split], balance, fee, mode)

        agent = create_agent(algorithm, params, columns)
        started = datetime.now(timezone.utc)
        fit = agent.learn(make_train_env, steps, seed)
        train_perf = run_episode(agent, make_train_env())
        test_perf = run_episode(
            agent, TradingEnv(scaled[split:], prices[split:], balance, fee, mode)
        )
        metrics = {
            "train": train_perf,
            "test": test_perf,
            "fit": fit,
            "total_timesteps": steps,
            "training_seconds": (datetime.now(timezone.utc) - started).total_seconds(),
        }
        version = self.registry.next_version(model_id)
        directory = self.registry.version_dir(model_id, version)
        agent.save(directory)
        with open(os.path.join(directory, "scaler.json"), "w") as handle:
            json.dump(scaler.to_dict(), handle)
        meta = {
            "algorithm": algorithm,
            "columns": columns,
            "features": info.get("features"),
            "action_mode": mode,
            "initial_balance": balance,
            "transaction_fee": fee,
            "symbol": symbol,
            "timeframe": timeframe,
            "params": params,
            "trained_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(os.path.join(directory, "meta.json"), "w") as handle:
            json.dump(meta, handle, default=float)
        training_data = {
            "symbol": symbol,
            "timeframe": timeframe,
            "period": period,
            "rows": int(n),
        }
        updated = self.registry.add_version(
            model_id, version, metrics, training_data, params
        )
        return {
            "id": model_id,
            "name": updated["name"],
            "algorithm": algorithm,
            "status": updated["status"],
            "version": version,
            "metrics": metrics,
            "training_data": training_data,
        }

    def predict(self, model_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        symbol = validate_symbol(data.get("symbol"))
        timeframe = validate_timeframe(data.get("timeframe", "1d"))
        period = normalize_period(data.get("period", "365d"))
        info, version, path = self.registry.active_path(model_id)
        if version is None:
            raise NotTrainedError(f"Model is not trained: {model_id}")
        with open(os.path.join(path, "meta.json")) as handle:
            meta = json.load(handle)
        with open(os.path.join(path, "scaler.json")) as handle:
            scaler = FeatureScaler.from_dict(json.load(handle))
        balance = float(data.get("initial_balance", meta["initial_balance"]))
        agent = load_agent(
            meta["algorithm"], path, meta.get("params", {}), meta["columns"]
        )
        ohlcv = self.data_client.fetch_ohlcv(symbol, timeframe, period)
        frame, prices = self._frame(
            ohlcv, meta.get("features") or list(RL_FEATURES), meta["columns"]
        )
        if len(frame) < 5:
            raise ValidationError(
                "Not enough history for RL prediction", {"rows": int(len(frame))}
            )
        scaled = scaler.transform(frame.to_numpy(dtype=np.float64)).astype(np.float32)
        env = TradingEnv(
            scaled, prices, balance, meta["transaction_fee"], meta["action_mode"]
        )
        summary = run_episode(agent, env)
        final_action = _scalar(agent.predict(env._observation()), meta["action_mode"])
        if meta["action_mode"] == "discrete":
            recommendation = ("hold", "buy", "sell")[int(final_action)]
            target = None
        else:
            target = float(final_action[0])
            recommendation = (
                "buy" if target > 0.6 else "sell" if target < 0.2 else "hold"
            )
        history = env.history
        stride = max(1, len(history) // MAX_HISTORY_POINTS)
        stamps = frame.index
        sampled = []
        for item in history[::stride]:
            row = dict(item)
            stamp = stamps[min(item["step"], len(stamps) - 1)]
            row["timestamp"] = (
                stamp.isoformat() if hasattr(stamp, "isoformat") else str(stamp)
            )
            sampled.append(row)
        return {
            "model_id": model_id,
            "model_version": version,
            "algorithm": meta["algorithm"],
            "symbol": symbol,
            "timeframe": timeframe,
            "initial_balance": balance,
            "final_balance": summary["final_balance"],
            "return": summary["return"],
            "performance": summary,
            "recommendation": {
                "action": recommendation,
                "target_exposure": target,
                "price": float(prices[-1]),
            },
            "actions": [h["action"] for h in sampled],
            "history": sampled,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
