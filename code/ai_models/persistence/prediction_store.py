import itertools
import json
import math
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ai_models.core.exceptions import NotFoundError, ServiceError, ValidationError
from ai_models.core.logging import get_logger
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = get_logger("persistence")


def parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        stamp = value
    elif isinstance(value, str) and value:
        try:
            stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise ValidationError(f"Invalid timestamp: {value}")
    else:
        raise ValidationError("Timestamp is required")
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc)


def _float(value: Any) -> Optional[float]:
    return None if value is None else float(value)


def _summarize(
    rows: List[Dict[str, Any]], model_id: str, symbol: Optional[str]
) -> Dict[str, Any]:
    errors = [float(r["error"]) for r in rows if r.get("error") is not None]
    if not errors:
        return {"model_id": model_id, "symbol": symbol, "metrics": None}
    n = len(errors)
    mean = sum(errors) / n
    variance = sum((e - mean) ** 2 for e in errors) / (n - 1) if n > 1 else 0.0
    ape = [
        abs(float(r["error"])) / abs(float(r["actual"]))
        for r in rows
        if r.get("error") is not None and r.get("actual")
    ]
    return {
        "model_id": model_id,
        "symbol": symbol,
        "metrics": {
            "count": n,
            "avg_error": mean,
            "avg_abs_error": sum(abs(e) for e in errors) / n,
            "rmse": math.sqrt(sum(e * e for e in errors) / n),
            "std_error": math.sqrt(variance),
            "min_error": min(errors),
            "max_error": max(errors),
            "mape": (sum(ape) / len(ape)) if ape else None,
        },
    }


class PredictionStore:
    def __init__(
        self,
        database_url: Optional[str] = None,
        engine: Optional[Engine] = None,
        schema: str = "ai_models",
    ) -> None:
        self.engine = engine
        self.schema = schema
        if self.engine is None and database_url:
            try:
                self.engine = create_engine(
                    database_url, pool_pre_ping=True, pool_size=5, max_overflow=5
                )
            except Exception as exc:
                logger.error("Database engine creation failed: %s", exc)
                self.engine = None
        self._lock = threading.Lock()
        self._ids = itertools.count(1)
        self._memory: Dict[int, Dict[str, Any]] = {}
        self._signals: List[Dict[str, Any]] = []
        self._max_memory = 5000

    @property
    def backend(self) -> str:
        return "database" if self.engine is not None else "memory"

    def _t(self, name: str) -> str:
        return f"{self.schema}.{name}" if self.schema else name

    def _json(self, param: str) -> str:
        if self.engine is not None and self.engine.dialect.name == "postgresql":
            return f"CAST(:{param} AS JSONB)"
        return f":{param}"

    def healthy(self) -> bool:
        if self.engine is None:
            return True
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def ensure_model(self, info: Dict[str, Any]) -> None:
        if self.engine is None:
            return
        sql = text(
            f"INSERT INTO {self._t('models')} (id, name, description, type, status, parameters, metrics) "
            f"VALUES (:id, :name, :description, :type, :status, {self._json('parameters')}, {self._json('metrics')}) "
            "ON CONFLICT (id) DO UPDATE SET name = :name, description = :description, type = :type, "
            f"status = :status, parameters = {self._json('parameters')}, metrics = {self._json('metrics')}, updated_at = CURRENT_TIMESTAMP"
        )
        params = {
            "id": info["id"],
            "name": info.get("name"),
            "description": info.get("description") or "",
            "type": info.get("type"),
            "status": info.get("status"),
            "parameters": json.dumps(info.get("parameters") or {}, default=str),
            "metrics": json.dumps(info.get("metrics") or {}, default=str),
        }
        try:
            with self.engine.begin() as conn:
                conn.execute(sql, params)
        except Exception as exc:
            logger.error("ensure_model failed: %s", exc)
            raise ServiceError(f"Database error: {exc}")

    def _ensure_symbol(self, conn: Any, symbol: str) -> None:
        conn.execute(
            text(
                f"INSERT INTO {self._t_market('symbols')} (symbol) VALUES (:symbol) ON CONFLICT (symbol) DO NOTHING"
            ),
            {"symbol": symbol},
        )

    def _t_market(self, name: str) -> str:
        return f"market_data.{name}" if self.schema else name

    def save_prediction(
        self,
        model_id: str,
        symbol: str,
        timestamp: Any,
        prediction: float,
        actual: Optional[float] = None,
        model_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not model_id:
            raise ValidationError("Model ID is required")
        if not symbol:
            raise ValidationError("Symbol is required")
        stamp = parse_timestamp(timestamp)
        try:
            prediction = float(prediction)
            actual = None if actual is None else float(actual)
        except (TypeError, ValueError):
            raise ValidationError("prediction and actual must be numbers")
        if not math.isfinite(prediction) or (
            actual is not None and not math.isfinite(actual)
        ):
            raise ValidationError("prediction and actual must be finite")
        error = None if actual is None else actual - prediction
        if self.engine is None:
            with self._lock:
                record_id = next(self._ids)
                record = {
                    "id": record_id,
                    "model_id": model_id,
                    "symbol": symbol,
                    "timestamp": stamp.isoformat(),
                    "prediction": prediction,
                    "actual": actual,
                    "error": error,
                }
                self._memory[record_id] = record
                while len(self._memory) > self._max_memory:
                    self._memory.pop(next(iter(self._memory)))
            return dict(record)
        try:
            if model_info:
                self.ensure_model(model_info)
            with self.engine.begin() as conn:
                self._ensure_symbol(conn, symbol)
                row = conn.execute(
                    text(
                        f"INSERT INTO {self._t('prediction_history')} (model_id, symbol, timestamp, prediction, actual, error) "
                        "VALUES (:model_id, :symbol, :timestamp, :prediction, :actual, :error) RETURNING id"
                    ),
                    {
                        "model_id": model_id,
                        "symbol": symbol,
                        "timestamp": stamp,
                        "prediction": prediction,
                        "actual": actual,
                        "error": error,
                    },
                ).fetchone()
            return {
                "id": int(row[0]),
                "model_id": model_id,
                "symbol": symbol,
                "timestamp": stamp.isoformat(),
                "prediction": prediction,
                "actual": actual,
                "error": error,
            }
        except (ValidationError, ServiceError):
            raise
        except Exception as exc:
            logger.error("save_prediction failed: %s", exc)
            raise ServiceError(f"Database error: {exc}")

    @staticmethod
    def _row(mapping: Any) -> Dict[str, Any]:
        stamp = mapping["timestamp"]
        if isinstance(stamp, str):
            stamp = parse_timestamp(stamp)
        return {
            "id": int(mapping["id"]),
            "model_id": mapping["model_id"],
            "symbol": mapping["symbol"],
            "timestamp": stamp.isoformat(),
            "prediction": _float(mapping["prediction"]),
            "actual": _float(mapping["actual"]),
            "error": _float(mapping["error"]),
        }

    def get_prediction(self, prediction_id: Any) -> Dict[str, Any]:
        try:
            prediction_id = int(prediction_id)
        except (TypeError, ValueError):
            raise ValidationError("Prediction ID must be an integer")
        if self.engine is None:
            record = self._memory.get(prediction_id)
            if record is None:
                raise NotFoundError(f"Prediction not found: {prediction_id}")
            return dict(record)
        with self.engine.connect() as conn:
            row = (
                conn.execute(
                    text(
                        f"SELECT * FROM {self._t('prediction_history')} WHERE id = :id"
                    ),
                    {"id": prediction_id},
                )
                .mappings()
                .first()
            )
        if row is None:
            raise NotFoundError(f"Prediction not found: {prediction_id}")
        return self._row(row)

    def update_actual(self, prediction_id: Any, actual: Any) -> Dict[str, Any]:
        record = self.get_prediction(prediction_id)
        try:
            actual = float(actual)
        except (TypeError, ValueError):
            raise ValidationError("actual must be a number")
        if not math.isfinite(actual):
            raise ValidationError("actual must be finite")
        error = actual - record["prediction"]
        if self.engine is None:
            with self._lock:
                self._memory[record["id"]].update(actual=actual, error=error)
                return dict(self._memory[record["id"]])
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    f"UPDATE {self._t('prediction_history')} SET actual = :actual, error = :error WHERE id = :id"
                ),
                {"actual": actual, "error": error, "id": record["id"]},
            )
        record.update(actual=actual, error=error)
        return record

    def history(
        self,
        model_id: str,
        symbol: Optional[str] = None,
        start: Any = None,
        end: Any = None,
        limit: int = 1000,
        only_pending: bool = False,
    ) -> List[Dict[str, Any]]:
        start_ts = parse_timestamp(start) if start else None
        end_ts = parse_timestamp(end) if end else None
        limit = max(1, min(int(limit), 10000))
        if self.engine is None:
            with self._lock:
                rows = [
                    dict(r) for r in self._memory.values() if r["model_id"] == model_id
                ]
            out = []
            for r in rows:
                stamp = parse_timestamp(r["timestamp"])
                if symbol and r["symbol"] != symbol:
                    continue
                if start_ts and stamp < start_ts:
                    continue
                if end_ts and stamp > end_ts:
                    continue
                if only_pending and r["actual"] is not None:
                    continue
                out.append(r)
            out.sort(key=lambda r: r["timestamp"])
            return out[:limit]
        clauses = ["model_id = :model_id"]
        params: Dict[str, Any] = {"model_id": model_id, "limit": limit}
        if symbol:
            clauses.append("symbol = :symbol")
            params["symbol"] = symbol
        if start_ts:
            clauses.append("timestamp >= :start")
            params["start"] = start_ts
        if end_ts:
            clauses.append("timestamp <= :end")
            params["end"] = end_ts
        if only_pending:
            clauses.append("actual IS NULL")
        sql = text(
            f"SELECT * FROM {self._t('prediction_history')} WHERE {' AND '.join(clauses)} ORDER BY timestamp ASC LIMIT :limit"
        )
        with self.engine.connect() as conn:
            return [self._row(r) for r in conn.execute(sql, params).mappings()]

    def performance(
        self,
        model_id: str,
        symbol: Optional[str] = None,
        start: Any = None,
        end: Any = None,
    ) -> Dict[str, Any]:
        rows = [
            r
            for r in self.history(model_id, symbol, start, end, limit=10000)
            if r["actual"] is not None
        ]
        return _summarize(rows, model_id, symbol)

    def save_signal(
        self, signal: Dict[str, Any], model_info: Optional[Dict[str, Any]] = None
    ) -> None:
        if self.engine is None:
            with self._lock:
                self._signals.append(dict(signal))
                del self._signals[: max(0, len(self._signals) - self._max_memory)]
            return
        try:
            if model_info:
                self.ensure_model(model_info)
            with self.engine.begin() as conn:
                self._ensure_symbol(conn, signal["symbol"])
                conn.execute(
                    text(
                        f"INSERT INTO {self._t('signals')} (model_id, symbol, timestamp, signal_type, strength, price, parameters) "
                        f"VALUES (:model_id, :symbol, :timestamp, :signal_type, :strength, :price, {self._json('parameters')})"
                    ),
                    {
                        "model_id": signal.get("model_id"),
                        "symbol": signal["symbol"],
                        "timestamp": parse_timestamp(
                            signal.get("generated_at") or datetime.now(timezone.utc)
                        ),
                        "signal_type": signal["type"],
                        "strength": round(float(signal.get("strength", 0.0)), 2),
                        "price": signal.get("price"),
                        "parameters": json.dumps(
                            {
                                k: signal.get(k)
                                for k in (
                                    "strategy",
                                    "prediction",
                                    "components",
                                    "reason",
                                )
                            },
                            default=str,
                        ),
                    },
                )
        except Exception as exc:
            logger.error("save_signal failed: %s", exc)

    def recent_signals(
        self, symbol: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        limit = max(1, min(int(limit), 500))
        if self.engine is None:
            with self._lock:
                rows = [dict(s) for s in self._signals if symbol in (None, s["symbol"])]
            return list(reversed(rows))[:limit]
        clause = "WHERE symbol = :symbol" if symbol else ""
        sql = text(
            f"SELECT model_id, symbol, timestamp, signal_type, strength, price FROM {self._t('signals')} {clause} "
            "ORDER BY timestamp DESC LIMIT :limit"
        )
        params: Dict[str, Any] = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        with self.engine.connect() as conn:
            rows = conn.execute(sql, params).mappings().all()
        return [
            {
                "model_id": r["model_id"],
                "symbol": r["symbol"],
                "type": r["signal_type"],
                "strength": _float(r["strength"]),
                "price": _float(r["price"]),
                "generated_at": (
                    r["timestamp"].isoformat()
                    if hasattr(r["timestamp"], "isoformat")
                    else str(r["timestamp"])
                ),
            }
            for r in rows
        ]
