from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
from ai_models.core.exceptions import AIEngineError, ValidationError
from ai_models.core.logging import get_logger
from ai_models.data.client import DataServiceClient, validate_symbol, validate_timeframe
from ai_models.data.features import build_features
from ai_models.inference.predictor import PredictionService
from ai_models.persistence.prediction_store import PredictionStore

logger = get_logger("signals")

STRATEGIES = ("prediction", "technical", "ensemble")
ACTION_THRESHOLD = 0.25


def _action(score: float) -> str:
    if score > ACTION_THRESHOLD:
        return "buy"
    if score < -ACTION_THRESHOLD:
        return "sell"
    return "hold"


def technical_score(ohlcv: Any) -> Dict[str, Any]:
    frame = build_features(
        ohlcv, ["sma_5", "sma_20", "rsi_14", "macd", "bollinger_bands"]
    ).dropna()
    if frame.empty:
        raise ValidationError("Not enough history for technical signals")
    last = frame.iloc[-1]
    trend = float(np.tanh((last["sma_5"] - last["sma_20"]) * 20.0))
    rsi = (last["rsi_14"] * 50.0) + 50.0
    reversion = (
        float(np.clip((50.0 - rsi) / 25.0, -1.0, 1.0))
        if (rsi < 30 or rsi > 70)
        else 0.0
    )
    momentum = float(np.tanh(last["macd_hist"] * 400.0))
    band = (
        float(np.clip((0.5 - last["bb_pct_b"]) * 2.0, -1.0, 1.0))
        if (last["bb_pct_b"] < 0.05 or last["bb_pct_b"] > 0.95)
        else 0.0
    )
    components = {
        "trend": trend,
        "momentum": momentum,
        "rsi_reversion": reversion,
        "band_reversion": band,
    }
    score = 0.4 * trend + 0.3 * momentum + 0.2 * reversion + 0.1 * band
    return {
        "score": float(np.clip(score, -1.0, 1.0)),
        "components": components,
        "rsi": float(rsi),
    }


class SignalGenerator:
    def __init__(
        self,
        predictor: PredictionService,
        data_client: DataServiceClient,
        store: PredictionStore,
    ) -> None:
        self.predictor = predictor
        self.data_client = data_client
        self.store = store

    def _prediction_signal(
        self, model_id: str, symbol: str, timeframe: str, period: Optional[str]
    ) -> Dict[str, Any]:
        result = self.predictor.predict(model_id, symbol, timeframe, period)
        pred = result["prediction"]
        sigma = max(
            (result["predictions"][-1]["upper"] - result["predictions"][-1]["lower"])
            / (2 * 1.959964 * result["latest_price"]),
            1e-6,
        )
        score = float(np.tanh(pred["expected_return"] / sigma))
        return {
            "score": score,
            "price": result["latest_price"],
            "prediction": pred,
            "model_version": result["model_version"],
        }

    def _technical_signal(
        self, symbol: str, timeframe: str, period: Optional[str]
    ) -> Dict[str, Any]:
        ohlcv = self.data_client.fetch_ohlcv(symbol, timeframe, period or "180d")
        result = technical_score(ohlcv)
        result["price"] = float(ohlcv["close"].iloc[-1])
        return result

    def generate_one(
        self,
        symbol: str,
        strategy: str,
        model_id: Optional[str],
        timeframe: str,
        period: Optional[str],
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        base: Dict[str, Any] = {
            "symbol": symbol,
            "strategy": strategy,
            "model_id": model_id,
        }
        if strategy == "prediction":
            part = self._prediction_signal(model_id, symbol, timeframe, period)
            score, price = part["score"], part["price"]
            base.update(
                prediction=part["prediction"], model_version=part["model_version"]
            )
        elif strategy == "technical":
            part = self._technical_signal(symbol, timeframe, period)
            score, price = part["score"], part["price"]
            base.update(components=part["components"])
        else:
            weights = weights or {"prediction": 0.6, "technical": 0.4}
            total = float(weights.get("prediction", 0.6)) + float(
                weights.get("technical", 0.4)
            )
            if total <= 0:
                raise ValidationError("Ensemble weights must sum above zero")
            wp, wt = (
                float(weights.get("prediction", 0.6)) / total,
                float(weights.get("technical", 0.4)) / total,
            )
            pred = self._prediction_signal(model_id, symbol, timeframe, period)
            tech = self._technical_signal(symbol, timeframe, period)
            score = wp * pred["score"] + wt * tech["score"]
            if (
                np.sign(pred["score"]) != np.sign(tech["score"])
                and min(abs(pred["score"]), abs(tech["score"])) > ACTION_THRESHOLD
            ):
                score *= 0.5
            price = pred["price"]
            base.update(
                prediction=pred["prediction"],
                components={
                    "prediction_score": pred["score"],
                    "technical_score": tech["score"],
                    **tech["components"],
                },
                model_version=pred["model_version"],
            )
        signal_type = _action(score)
        base.update(
            type=signal_type,
            strength=round(abs(score), 2) if signal_type != "hold" else 0.0,
            score=round(score, 4),
            price=price,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
        return base

    def generate(
        self,
        symbols: List[str],
        model_id: Optional[str] = None,
        timeframe: str = "1d",
        period: Optional[str] = None,
        strategy: str = "prediction",
        weights: Optional[Dict[str, float]] = None,
        persist: bool = False,
    ) -> Dict[str, Any]:
        if not symbols or not isinstance(symbols, list):
            raise ValidationError("Symbols are required")
        if len(symbols) > 50:
            raise ValidationError("At most 50 symbols per request")
        if strategy not in STRATEGIES:
            raise ValidationError(
                f"Unsupported strategy: {strategy}", {"supported": list(STRATEGIES)}
            )
        if strategy in ("prediction", "ensemble") and not model_id:
            raise ValidationError(f"Model ID is required for {strategy} signals")
        timeframe = validate_timeframe(timeframe)
        signals: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        info = None
        if persist and model_id:
            try:
                info = self.predictor._model_info(self.predictor.registry.get(model_id))
            except AIEngineError:
                info = None
        for symbol in dict.fromkeys(validate_symbol(s) for s in symbols):
            try:
                signal = self.generate_one(
                    symbol, strategy, model_id, timeframe, period, weights
                )
                signals.append(signal)
                if persist:
                    self.store.save_signal(signal, info)
            except AIEngineError as exc:
                errors.append(
                    {"symbol": symbol, "error": exc.message, "code": exc.code}
                )
                logger.warning("Signal failed for %s: %s", symbol, exc.message)
        return {
            "signals": signals,
            "errors": errors,
            "count": len(signals),
            "strategy": strategy,
            "model_id": model_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
