import re
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from ai_models.core.cache import TTLCache
from ai_models.core.exceptions import DataError, DependencyError, ValidationError
from ai_models.core.logging import get_logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = get_logger("data.client")

REQUIRED_COLUMNS = ("open", "high", "low", "close", "volume")
TIMEFRAMES = ("1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w")
_PERIOD_ALIASES = {
    "1d": "1d",
    "5d": "5d",
    "1wk": "7d",
    "1w": "7d",
    "1mo": "30d",
    "3mo": "90d",
    "6mo": "180d",
    "1y": "365d",
    "2y": "730d",
    "5y": "1825d",
    "max": "3650d",
}
_PERIOD_PATTERN = re.compile(r"^(\d+)(d|w|wk|m|mo|y)$")
_UNIT_DAYS = {"d": 1, "w": 7, "wk": 7, "m": 30, "mo": 30, "y": 365}


def normalize_period(period: Optional[str]) -> str:
    if not period:
        return "365d"
    period = str(period).strip().lower()
    if period in _PERIOD_ALIASES:
        return _PERIOD_ALIASES[period]
    match = _PERIOD_PATTERN.match(period)
    if not match:
        raise ValidationError(f"Invalid period: {period}")
    return f"{int(match.group(1)) * _UNIT_DAYS[match.group(2)]}d"


def validate_timeframe(timeframe: Optional[str]) -> str:
    timeframe = (timeframe or "1d").strip().lower()
    if timeframe not in TIMEFRAMES:
        raise ValidationError(
            f"Invalid timeframe: {timeframe}", {"allowed": list(TIMEFRAMES)}
        )
    return timeframe


def validate_symbol(symbol: Optional[str]) -> str:
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("Symbol is required")
    symbol = symbol.strip().upper()
    if not re.match(r"^[A-Z0-9][A-Z0-9.\-_^=]{0,19}$", symbol):
        raise ValidationError(f"Invalid symbol: {symbol}")
    return symbol


def _extract_rows(payload: Any) -> List[Dict[str, Any]]:
    node = payload
    for _ in range(3):
        if isinstance(node, dict) and "data" in node:
            node = node["data"]
        else:
            break
    if isinstance(node, dict) and "ohlcv" in node:
        node = node["ohlcv"]
    if not isinstance(node, list):
        raise DependencyError("Unexpected market data payload shape")
    return node


def rows_to_frame(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        raise DataError("No market data returned")
    df = pd.DataFrame(rows)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DependencyError(f"Market data missing columns: {missing}")
    time_col = next((c for c in ("timestamp", "date", "time") if c in df.columns), None)
    for column in REQUIRED_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    if time_col:
        index = pd.to_datetime(df[time_col], utc=True, errors="coerce")
        df = df.drop(columns=[time_col])
        df.index = index.dt.tz_convert(None)
        df = df[df.index.notna()]
    else:
        df.index = pd.RangeIndex(len(df))
    df = df[list(REQUIRED_COLUMNS)]
    df = df[~df.index.duplicated(keep="last")].sort_index()
    df = df.dropna(subset=["close"])
    df = df[df["close"] > 0]
    for column in ("open", "high", "low"):
        df[column] = df[column].where(df[column] > 0, df["close"])
    df["volume"] = df["volume"].fillna(0.0).clip(lower=0.0)
    if df.empty:
        raise DataError("Market data contained no valid rows")
    return df


class DataServiceClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        retries: int = 2,
        cache_ttl: int = 60,
        cache_size: int = 256,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        if session is None:
            retry = Retry(
                total=retries,
                backoff_factor=0.3,
                status_forcelist=(502, 503, 504),
                allowed_methods=frozenset(["GET"]),
                raise_on_status=False,
            )
            adapter = HTTPAdapter(max_retries=retry, pool_maxsize=16)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
        self._cache = TTLCache(cache_size, cache_ttl)

    def fetch_ohlcv(
        self, symbol: str, timeframe: str = "1d", period: Optional[str] = "1y"
    ) -> pd.DataFrame:
        symbol = validate_symbol(symbol)
        timeframe = validate_timeframe(timeframe)
        period = normalize_period(period)
        key = f"ohlcv:{symbol}:{timeframe}:{period}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached.copy()
        try:
            response = self.session.get(
                f"{self.base_url}/api/market-data/{symbol}",
                params={"timeframe": timeframe, "period": period},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            logger.error("Data service unreachable: %s", exc)
            raise DependencyError(f"Data service unreachable: {exc}") from exc
        if response.status_code == 404:
            raise DataError(f"No market data for symbol {symbol}")
        if response.status_code != 200:
            raise DependencyError(
                f"Data service returned {response.status_code}",
                {"body": response.text[:300]},
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise DependencyError("Data service returned invalid JSON") from exc
        frame = rows_to_frame(_extract_rows(payload))
        self._cache.set(key, frame)
        return frame.copy()

    def healthy(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=3)
            return response.status_code == 200
        except requests.RequestException:
            return False
