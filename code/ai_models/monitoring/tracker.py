from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pandas as pd
from ai_models.core.exceptions import AIEngineError
from ai_models.core.logging import get_logger
from ai_models.data.client import DataServiceClient
from ai_models.monitoring.drift import drift_report
from ai_models.persistence.prediction_store import PredictionStore, parse_timestamp
from ai_models.registry.store import ModelRegistry

logger = get_logger("tracker")

STALE_DAYS = 30


class PerformanceTracker:
    def __init__(
        self,
        registry: ModelRegistry,
        data_client: DataServiceClient,
        store: PredictionStore,
        predictor: Any,
    ) -> None:
        self.registry = registry
        self.data_client = data_client
        self.store = store
        self.predictor = predictor

    def reconcile(self, model_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        self.registry.get(model_id)
        now = datetime.now(timezone.utc)
        pending = self.store.history(
            model_id, symbol, end=now, only_pending=True, limit=5000
        )
        by_symbol: Dict[str, list] = {}
        for record in pending:
            by_symbol.setdefault(record["symbol"], []).append(record)
        updated, skipped, failed = 0, 0, []
        for sym, records in by_symbol.items():
            oldest = min(parse_timestamp(r["timestamp"]) for r in records)
            days = max(10, (now - oldest).days + 10)
            try:
                ohlcv = self.data_client.fetch_ohlcv(sym, "1d", f"{days}d")
            except AIEngineError as exc:
                failed.append({"symbol": sym, "error": exc.message})
                continue
            closes = ohlcv["close"].copy()
            closes.index = pd.DatetimeIndex(closes.index).normalize()
            closes = closes[~closes.index.duplicated(keep="last")]
            for record in records:
                target = (
                    pd.Timestamp(parse_timestamp(record["timestamp"]))
                    .tz_convert(None)
                    .normalize()
                )
                if target in closes.index:
                    self.store.update_actual(record["id"], float(closes.loc[target]))
                    updated += 1
                else:
                    skipped += 1
        return {
            "model_id": model_id,
            "pending": len(pending),
            "updated": updated,
            "skipped": skipped,
            "failed": failed,
        }

    def drift(
        self,
        model_id: str,
        symbol: Optional[str] = None,
        timeframe: str = "1d",
        period: str = "730d",
    ) -> Dict[str, Any]:
        info, version, bundle = self.predictor.load(model_id)
        symbol = symbol or bundle.meta.get("symbol")
        ohlcv = self.data_client.fetch_ohlcv(symbol, timeframe, period)
        report = drift_report(bundle, ohlcv)
        report.update(model_id=model_id, version=version, symbol=symbol)
        return report

    def health(
        self, model_id: str, symbol: Optional[str] = None, check_drift: bool = True
    ) -> Dict[str, Any]:
        info, version, bundle = self.predictor.load(model_id)
        trained_at = parse_timestamp(bundle.meta["trained_at"])
        age_days = (datetime.now(timezone.utc) - trained_at).total_seconds() / 86400.0
        live = self.store.performance(model_id, symbol)
        drift: Optional[Dict[str, Any]] = None
        drift_error: Optional[str] = None
        if check_drift:
            try:
                drift = self.drift(model_id, symbol)
            except AIEngineError as exc:
                drift_error = exc.message
        reasons = []
        if age_days > STALE_DAYS:
            reasons.append(f"model is {int(age_days)} days old")
        if drift and drift["status"] == "significant":
            reasons.append("significant feature drift")
        return {
            "model_id": model_id,
            "version": version,
            "trained_at": bundle.meta["trained_at"],
            "age_days": round(age_days, 2),
            "live_performance": live["metrics"],
            "drift": (
                None
                if drift is None
                else {k: drift[k] for k in ("status", "mean_psi", "max_psi")}
            ),
            "drift_error": drift_error,
            "needs_retraining": bool(reasons),
            "reasons": reasons,
        }
