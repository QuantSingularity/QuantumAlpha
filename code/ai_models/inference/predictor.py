import math
import threading
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from ai_models.core.exceptions import AIEngineError, NotTrainedError, ValidationError
from ai_models.core.logging import get_logger
from ai_models.core.settings import Settings
from ai_models.data.client import DataServiceClient, validate_symbol, validate_timeframe
from ai_models.data.features import max_window
from ai_models.data.preprocessing import future_timestamps, latest_window
from ai_models.persistence.prediction_store import PredictionStore
from ai_models.registry.bundle import LoadedBundle, load_bundle
from ai_models.registry.store import ModelRegistry

logger = get_logger("inference")

_BARS_PER_DAY = {
    "1d": 0.7,
    "1w": 0.15,
    "4h": 2.0,
    "1h": 7.0,
    "30m": 13.0,
    "15m": 26.0,
    "5m": 78.0,
    "1m": 390.0,
}
Z_95 = 1.959964


def default_period(
    timeframe: str, sequence_length: int, features: Optional[List[str]]
) -> str:
    rows = sequence_length + max_window(features) + 20
    days = math.ceil(rows / _BARS_PER_DAY.get(timeframe, 0.7) * 1.15) + 5
    return f"{min(days, 3650)}d"


def normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


@dataclass
class Forecast:
    model_id: str
    version: int
    info: Dict[str, Any]
    symbol: str
    timeframe: str
    returns: np.ndarray
    sigma: np.ndarray
    last_close: float
    last_timestamp: Any
    horizon: int
    trained_symbol: Optional[str]


def summarize(
    forecast: Forecast, extra: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    h = forecast.horizon
    returns = forecast.returns[:h]
    sigma = forecast.sigma[:h]
    price = forecast.last_close
    values = price * (1.0 + returns)
    lower = price * (1.0 + returns - Z_95 * sigma)
    upper = price * (1.0 + returns + Z_95 * sigma)
    stamps = future_timestamps(forecast.last_timestamp, forecast.timeframe, h)
    final_return = float(returns[-1])
    final_sigma = float(max(sigma[-1], 1e-6))
    probability_up = normal_cdf(final_return / final_sigma)
    threshold = max(0.005, 0.5 * final_sigma)
    if final_return > threshold:
        direction = "bullish"
    elif final_return < -threshold:
        direction = "bearish"
    else:
        direction = "neutral"
    average = float(values.mean())
    change = average - price
    response = {
        "symbol": forecast.symbol,
        "model_id": forecast.model_id,
        "model_version": forecast.version,
        "latest_price": price,
        "as_of": (
            forecast.last_timestamp.isoformat()
            if hasattr(forecast.last_timestamp, "isoformat")
            else str(forecast.last_timestamp)
        ),
        "prediction": {
            "average": average,
            "minimum": float(values.min()),
            "maximum": float(values.max()),
            "change": change,
            "change_percent": change / price * 100.0,
            "expected_return": final_return,
            "direction": direction,
            "probability_up": probability_up,
            "confidence": abs(probability_up - 0.5) * 2.0,
        },
        "horizon": h,
        "timeframe": forecast.timeframe,
        "predictions": [
            {
                "step": i + 1,
                "timestamp": stamps[i],
                "value": float(values[i]),
                "lower": float(lower[i]),
                "upper": float(upper[i]),
                "expected_return": float(returns[i]),
            }
            for i in range(h)
        ],
        "trained_on": forecast.trained_symbol,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        response.update(extra)
    return response


class PredictionService:
    def __init__(
        self,
        registry: ModelRegistry,
        data_client: DataServiceClient,
        store: PredictionStore,
        settings: Settings,
        bundle_cache_size: int = 8,
    ) -> None:
        self.registry = registry
        self.data_client = data_client
        self.store = store
        self.settings = settings
        self._bundles: "OrderedDict[Tuple[str, int], LoadedBundle]" = OrderedDict()
        self._bundle_lock = threading.Lock()
        self._bundle_cache_size = bundle_cache_size

    def invalidate(self, model_id: Optional[str] = None) -> None:
        with self._bundle_lock:
            if model_id is None:
                self._bundles.clear()
                return
            for key in [k for k in self._bundles if k[0] == model_id]:
                del self._bundles[key]

    def load(
        self, model_id: str, version: Optional[int] = None
    ) -> Tuple[Dict[str, Any], int, LoadedBundle]:
        info, resolved, path = self.registry.active_path(model_id, version)
        if resolved is None or path is None:
            raise NotTrainedError(f"Model is not trained: {model_id}")
        key = (model_id, resolved)
        with self._bundle_lock:
            bundle = self._bundles.get(key)
            if bundle is not None:
                self._bundles.move_to_end(key)
                return info, resolved, bundle
        bundle = load_bundle(path, info["type"])
        with self._bundle_lock:
            self._bundles[key] = bundle
            while len(self._bundles) > self._bundle_cache_size:
                self._bundles.popitem(last=False)
        return info, resolved, bundle

    def forecast(
        self,
        model_id: str,
        symbol: str,
        timeframe: str = "1d",
        period: Optional[str] = None,
        horizon: Optional[int] = None,
        version: Optional[int] = None,
    ) -> Forecast:
        symbol = validate_symbol(symbol)
        timeframe = validate_timeframe(timeframe)
        info, resolved, bundle = self.load(model_id, version)
        if horizon is not None:
            try:
                horizon = int(horizon)
            except (TypeError, ValueError):
                raise ValidationError("horizon must be an integer")
            if horizon < 1:
                raise ValidationError("horizon must be at least 1")
        used = min(horizon or bundle.horizon, bundle.horizon)
        period = period or default_period(
            timeframe, bundle.sequence_length, bundle.meta.get("features")
        )
        ohlcv = self.data_client.fetch_ohlcv(symbol, timeframe, period)
        window, last_ts, last_close = latest_window(
            ohlcv,
            bundle.meta.get("features"),
            bundle.columns,
            bundle.scaler,
            bundle.sequence_length,
        )
        returns = bundle.model.predict(window)[0]
        sigma = np.asarray(
            bundle.meta.get("residual_std") or [0.02] * bundle.horizon, dtype=float
        )
        if len(sigma) < bundle.horizon:
            sigma = np.pad(sigma, (0, bundle.horizon - len(sigma)), mode="edge")
        return Forecast(
            model_id=model_id,
            version=resolved,
            info=info,
            symbol=symbol,
            timeframe=timeframe,
            returns=np.asarray(returns, dtype=float),
            sigma=sigma,
            last_close=last_close,
            last_timestamp=last_ts,
            horizon=used,
            trained_symbol=bundle.meta.get("symbol"),
        )

    def predict(
        self,
        model_id: str,
        symbol: str,
        timeframe: str = "1d",
        period: Optional[str] = None,
        horizon: Optional[int] = None,
        version: Optional[int] = None,
        persist: bool = False,
    ) -> Dict[str, Any]:
        if not model_id:
            raise ValidationError("Model ID is required")
        forecast = self.forecast(model_id, symbol, timeframe, period, horizon, version)
        response = summarize(forecast)
        if persist:
            self._persist(forecast, response)
        return response

    def _persist(self, forecast: Forecast, response: Dict[str, Any]) -> None:
        try:
            step = response["predictions"][0]
            saved = self.store.save_prediction(
                forecast.model_id,
                forecast.symbol,
                step["timestamp"],
                step["value"],
                model_info=self._model_info(forecast.info),
            )
            response["prediction_id"] = saved["id"]
        except AIEngineError as exc:
            logger.warning("Prediction not persisted: %s", exc.message)

    @staticmethod
    def _model_info(info: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": info["id"],
            "name": info.get("name"),
            "description": info.get("description"),
            "type": info.get("type"),
            "status": info.get("status"),
            "parameters": info.get("parameters"),
            "metrics": info.get("metrics"),
        }

    def predict_many(
        self,
        model_id: str,
        symbols: List[str],
        timeframe: str = "1d",
        period: Optional[str] = None,
        horizon: Optional[int] = None,
        persist: bool = False,
    ) -> Dict[str, Any]:
        if not symbols or not isinstance(symbols, list):
            raise ValidationError("Symbols are required")
        if len(symbols) > 50:
            raise ValidationError("At most 50 symbols per request")
        results: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        for symbol in dict.fromkeys(symbols):
            try:
                results.append(
                    self.predict(
                        model_id, symbol, timeframe, period, horizon, persist=persist
                    )
                )
            except AIEngineError as exc:
                errors.append(
                    {"symbol": symbol, "error": exc.message, "code": exc.code}
                )
        return {
            "model_id": model_id,
            "results": results,
            "errors": errors,
            "count": len(results),
        }
