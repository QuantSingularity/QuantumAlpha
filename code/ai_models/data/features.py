import re
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
from ai_models.core.exceptions import ValidationError

BASE_FEATURES = ("ret_1", "hl_range", "oc_range", "vol_chg")
DEFAULT_FEATURES = (
    "returns",
    "sma_20",
    "ema_20",
    "rsi_14",
    "macd",
    "bollinger_bands",
    "atr_14",
    "volatility_20",
    "momentum_10",
    "obv",
)
WARMUP_ROWS = 35
_PARAMETRIC = re.compile(r"^([a-z_]+?)(?:_(\d+))?$")


def _sma(df: pd.DataFrame, window: int) -> pd.DataFrame:
    avg = df["close"].rolling(window, min_periods=window).mean()
    return pd.DataFrame({f"sma_{window}": df["close"] / avg - 1.0})


def _ema(df: pd.DataFrame, window: int) -> pd.DataFrame:
    avg = df["close"].ewm(span=window, adjust=False, min_periods=window).mean()
    return pd.DataFrame({f"ema_{window}": df["close"] / avg - 1.0})


def _rsi(df: pd.DataFrame, window: int) -> pd.DataFrame:
    delta = df["close"].diff()
    gain = (
        delta.clip(lower=0)
        .ewm(alpha=1.0 / window, adjust=False, min_periods=window)
        .mean()
    )
    loss = (
        (-delta.clip(upper=0))
        .ewm(alpha=1.0 / window, adjust=False, min_periods=window)
        .mean()
    )
    rs = gain / loss.replace(0, np.nan)
    rsi = 100.0 - 100.0 / (1.0 + rs)
    rsi = rsi.where(loss != 0, 100.0)
    return pd.DataFrame({f"rsi_{window}": (rsi - 50.0) / 50.0})


def _macd(df: pd.DataFrame, window: Optional[int] = None) -> pd.DataFrame:
    fast = df["close"].ewm(span=12, adjust=False, min_periods=12).mean()
    slow = df["close"].ewm(span=26, adjust=False, min_periods=26).mean()
    line = (fast - slow) / df["close"]
    signal = line.ewm(span=9, adjust=False, min_periods=9).mean()
    return pd.DataFrame(
        {"macd": line, "macd_signal": signal, "macd_hist": line - signal}
    )


def _bollinger(df: pd.DataFrame, window: Optional[int] = None) -> pd.DataFrame:
    window = window or 20
    mean = df["close"].rolling(window, min_periods=window).mean()
    std = df["close"].rolling(window, min_periods=window).std()
    width = (4.0 * std) / mean
    pct_b = (df["close"] - (mean - 2.0 * std)) / (4.0 * std).replace(0, np.nan)
    return pd.DataFrame({"bb_width": width, "bb_pct_b": pct_b.fillna(0.5)})


def _atr(df: pd.DataFrame, window: int) -> pd.DataFrame:
    prev = df["close"].shift(1)
    tr = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()],
        axis=1,
    ).max(axis=1)
    atr = tr.ewm(alpha=1.0 / window, adjust=False, min_periods=window).mean()
    return pd.DataFrame({f"atr_{window}": atr / df["close"]})


def _obv(df: pd.DataFrame, window: Optional[int] = None) -> pd.DataFrame:
    direction = np.sign(df["close"].diff().fillna(0.0))
    flow = direction * df["volume"]
    scale = df["volume"].rolling(20, min_periods=1).mean().replace(0, np.nan)
    return pd.DataFrame({"obv": (flow / scale).fillna(0.0).clip(-5, 5)})


def _returns(df: pd.DataFrame, window: Optional[int] = None) -> pd.DataFrame:
    return pd.DataFrame({"returns": df["close"].pct_change()})


def _log_returns(df: pd.DataFrame, window: Optional[int] = None) -> pd.DataFrame:
    return pd.DataFrame({"log_returns": np.log(df["close"]).diff()})


def _momentum(df: pd.DataFrame, window: int) -> pd.DataFrame:
    return pd.DataFrame({f"momentum_{window}": df["close"].pct_change(window)})


def _volatility(df: pd.DataFrame, window: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            f"volatility_{window}": df["close"]
            .pct_change()
            .rolling(window, min_periods=window)
            .std()
        }
    )


def _stochastic(df: pd.DataFrame, window: int) -> pd.DataFrame:
    low = df["low"].rolling(window, min_periods=window).min()
    high = df["high"].rolling(window, min_periods=window).max()
    pct = (df["close"] - low) / (high - low).replace(0, np.nan)
    return pd.DataFrame({f"stochastic_{window}": pct.fillna(0.5)})


def _roc(df: pd.DataFrame, window: int) -> pd.DataFrame:
    return pd.DataFrame({f"roc_{window}": df["close"].pct_change(window)})


def _zscore(df: pd.DataFrame, window: int) -> pd.DataFrame:
    mean = df["close"].rolling(window, min_periods=window).mean()
    std = df["close"].rolling(window, min_periods=window).std().replace(0, np.nan)
    return pd.DataFrame({f"zscore_{window}": ((df["close"] - mean) / std).fillna(0.0)})


_REGISTRY: Dict[str, Tuple[Callable[..., pd.DataFrame], Optional[int]]] = {
    "sma": (_sma, 20),
    "ema": (_ema, 20),
    "rsi": (_rsi, 14),
    "macd": (_macd, None),
    "bollinger_bands": (_bollinger, None),
    "atr": (_atr, 14),
    "obv": (_obv, None),
    "returns": (_returns, None),
    "log_returns": (_log_returns, None),
    "momentum": (_momentum, 10),
    "volatility": (_volatility, 20),
    "stochastic": (_stochastic, 14),
    "roc": (_roc, 10),
    "zscore": (_zscore, 20),
}
_ALIASES = {
    "bollinger": "bollinger_bands",
    "bbands": "bollinger_bands",
    "bollinger_percent_b": "bollinger_bands",
}


def supported_features() -> List[str]:
    return sorted(_REGISTRY)


def _resolve(name: str) -> Tuple[str, Optional[int]]:
    key = _ALIASES.get(name.strip().lower(), name.strip().lower())
    if key in _REGISTRY:
        return key, _REGISTRY[key][1]
    match = _PARAMETRIC.match(key)
    if match and match.group(1) in _REGISTRY and match.group(2):
        window = int(match.group(2))
        if window < 2 or window > 400:
            raise ValidationError(f"Invalid window in feature: {name}")
        return match.group(1), window
    raise ValidationError(
        f"Unsupported feature: {name}", {"supported": supported_features()}
    )


def validate_features(features: Optional[Iterable[str]]) -> List[str]:
    if features is None:
        return []
    if isinstance(features, str):
        features = [features]
    seen: List[str] = []
    for feature in features:
        if not isinstance(feature, str):
            raise ValidationError("Features must be strings")
        _resolve(feature)
        if feature not in seen:
            seen.append(feature)
    return seen


def _base_features(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    out["ret_1"] = df["close"].pct_change()
    out["hl_range"] = (df["high"] - df["low"]) / df["close"]
    out["oc_range"] = (df["close"] - df["open"]) / df["open"]
    out["vol_chg"] = np.log1p(df["volume"]).diff()
    return out


def build_features(
    df: pd.DataFrame, features: Optional[Iterable[str]] = None
) -> pd.DataFrame:
    requested = validate_features(features)
    parts = [_base_features(df)]
    for feature in requested:
        name, window = _resolve(feature)
        func = _REGISTRY[name][0]
        parts.append(func(df, window) if window else func(df))
    out = pd.concat(parts, axis=1)
    out = out.loc[:, ~out.columns.duplicated()]
    out = out.replace([np.inf, -np.inf], np.nan)
    return out


def max_window(features: Optional[Iterable[str]]) -> int:
    largest = WARMUP_ROWS
    for feature in validate_features(features):
        _, window = _resolve(feature)
        if window:
            largest = max(largest, window + 5)
    return largest
