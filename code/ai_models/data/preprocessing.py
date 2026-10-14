from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from ai_models.core.exceptions import DataError, ValidationError
from ai_models.data.features import build_features, max_window


class FeatureScaler:
    def __init__(
        self,
        mean: Optional[np.ndarray] = None,
        scale: Optional[np.ndarray] = None,
        clip: float = 6.0,
    ) -> None:
        self.mean = mean
        self.scale = scale
        self.clip = clip

    @property
    def fitted(self) -> bool:
        return self.mean is not None and self.scale is not None

    def fit(self, values: np.ndarray) -> "FeatureScaler":
        values = np.asarray(values, dtype=np.float64)
        if values.ndim != 2 or len(values) < 2:
            raise DataError("Not enough rows to fit the scaler")
        self.mean = values.mean(axis=0)
        std = values.std(axis=0)
        self.scale = np.where(std < 1e-12, 1.0, std)
        return self

    def transform(self, values: np.ndarray) -> np.ndarray:
        if not self.fitted:
            raise ValidationError("Scaler is not fitted")
        scaled = (np.asarray(values, dtype=np.float64) - self.mean) / self.scale
        return np.clip(scaled, -self.clip, self.clip)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mean": self.mean.tolist(),
            "scale": self.scale.tolist(),
            "clip": self.clip,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "FeatureScaler":
        return cls(
            np.asarray(payload["mean"], dtype=np.float64),
            np.asarray(payload["scale"], dtype=np.float64),
            float(payload.get("clip", 6.0)),
        )


@dataclass
class PreparedData:
    X_train: np.ndarray
    y_train: np.ndarray
    X_val: np.ndarray
    y_val: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray
    scaler: FeatureScaler
    columns: List[str]
    sequence_length: int
    horizon: int
    index_test: pd.Index
    close_test: np.ndarray

    @property
    def n_features(self) -> int:
        return len(self.columns)


def required_rows(
    sequence_length: int, horizon: int, features: Optional[List[str]]
) -> int:
    return max_window(features) + sequence_length + horizon


def clean_feature_frame(
    df: pd.DataFrame, features: Optional[List[str]]
) -> pd.DataFrame:
    frame = build_features(df, features)
    frame = frame.dropna(how="any")
    return frame


def forward_returns(close: np.ndarray, horizon: int) -> np.ndarray:
    n = len(close)
    out = np.full((n, horizon), np.nan)
    for step in range(1, horizon + 1):
        out[: n - step, step - 1] = close[step:] / close[: n - step] - 1.0
    return out


def make_windows(values: np.ndarray, sequence_length: int) -> np.ndarray:
    n = len(values) - sequence_length + 1
    if n <= 0:
        return np.empty((0, sequence_length, values.shape[1]))
    shape = (n, sequence_length, values.shape[1])
    strides = (values.strides[0], values.strides[0], values.strides[1])
    return np.lib.stride_tricks.as_strided(values, shape=shape, strides=strides).copy()


@dataclass
class RawDataset:
    windows: np.ndarray
    targets: np.ndarray
    ends: np.ndarray
    frame: pd.DataFrame
    close: np.ndarray
    sequence_length: int
    horizon: int

    def __len__(self) -> int:
        return len(self.windows)


def build_dataset(
    ohlcv: pd.DataFrame,
    features: Optional[List[str]],
    sequence_length: int,
    horizon: int,
    min_samples: int = 30,
) -> RawDataset:
    if sequence_length < 2 or sequence_length > 500:
        raise ValidationError("sequence_length must be between 2 and 500")
    if horizon < 1 or horizon > 60:
        raise ValidationError("horizon must be between 1 and 60")
    frame = clean_feature_frame(ohlcv, features)
    close = ohlcv["close"].reindex(frame.index).to_numpy(dtype=np.float64)
    targets = forward_returns(close, horizon)
    windows = make_windows(frame.to_numpy(dtype=np.float64), sequence_length)
    ends = np.arange(sequence_length - 1, len(frame))
    valid = ~np.isnan(targets[ends]).any(axis=1)
    windows, ends = windows[valid], ends[valid]
    if len(windows) < min_samples:
        raise DataError(
            f"Not enough history: {len(windows)} usable samples, need at least {min_samples}",
            {
                "rows": int(len(ohlcv)),
                "required_rows": required_rows(sequence_length, horizon, features)
                + min_samples,
            },
        )
    return RawDataset(
        windows=windows,
        targets=targets[ends],
        ends=ends,
        frame=frame,
        close=close,
        sequence_length=sequence_length,
        horizon=horizon,
    )


def assemble(
    raw: RawDataset,
    train: slice,
    val: slice,
    test: slice,
) -> PreparedData:
    train_ends = raw.ends[train]
    if len(train_ends) < 10:
        raise DataError("Not enough samples left for training after the split")
    fit_rows = raw.frame.to_numpy(dtype=np.float64)[: int(train_ends[-1]) + 1]
    scaler = FeatureScaler().fit(fit_rows)

    def scale(block: np.ndarray) -> np.ndarray:
        if block.size == 0:
            return block.astype(np.float32)
        flat = block.reshape(-1, block.shape[-1])
        return scaler.transform(flat).reshape(block.shape).astype(np.float32)

    test_ends = raw.ends[test]
    return PreparedData(
        X_train=scale(raw.windows[train]),
        y_train=raw.targets[train].astype(np.float32),
        X_val=scale(raw.windows[val]),
        y_val=raw.targets[val].astype(np.float32),
        X_test=scale(raw.windows[test]),
        y_test=raw.targets[test].astype(np.float32),
        scaler=scaler,
        columns=list(raw.frame.columns),
        sequence_length=raw.sequence_length,
        horizon=raw.horizon,
        index_test=raw.frame.index[test_ends],
        close_test=raw.close[test_ends],
    )


def holdout_slices(
    n: int, horizon: int, test_size: float, val_size: float
) -> Tuple[slice, slice, slice]:
    if (
        not (0.05 <= test_size < 0.6)
        or not (0.0 <= val_size < 0.4)
        or test_size + val_size > 0.7
    ):
        raise ValidationError("Invalid test_size/val_size")
    n_test = max(1, int(round(n * test_size)))
    n_val = int(round(n * val_size))
    n_train = n - n_test - n_val
    train = slice(0, max(1, n_train - horizon))
    if n_val > horizon:
        val = slice(n_train, n_train + n_val - horizon)
    else:
        val = slice(n_train, n_train)
    test = slice(n_train + n_val, n)
    return train, val, test


def prepare_training_data(
    ohlcv: pd.DataFrame,
    features: Optional[List[str]],
    sequence_length: int,
    horizon: int,
    test_size: float = 0.2,
    val_size: float = 0.1,
    min_samples: int = 30,
) -> PreparedData:
    raw = build_dataset(ohlcv, features, sequence_length, horizon, min_samples)
    train, val, test = holdout_slices(len(raw), horizon, test_size, val_size)
    return assemble(raw, train, val, test)


def latest_window(
    ohlcv: pd.DataFrame,
    features: Optional[List[str]],
    columns: List[str],
    scaler: FeatureScaler,
    sequence_length: int,
) -> Tuple[np.ndarray, pd.Timestamp, float]:
    frame = clean_feature_frame(ohlcv, features)
    missing = [c for c in columns if c not in frame.columns]
    if missing:
        raise ValidationError(f"Feature columns missing at inference: {missing}")
    frame = frame[columns]
    if len(frame) < sequence_length:
        raise DataError(
            f"Not enough history for inference: {len(frame)} usable rows, need {sequence_length}",
            {"rows": int(len(ohlcv))},
        )
    window = scaler.transform(frame.to_numpy(dtype=np.float64)[-sequence_length:])
    last_index = frame.index[-1]
    last_close = (
        float(ohlcv["close"].loc[last_index])
        if last_index in ohlcv.index
        else float(ohlcv["close"].iloc[-1])
    )
    return window[np.newaxis].astype(np.float32), last_index, last_close


def to_tabular(X: np.ndarray) -> np.ndarray:
    if X.ndim == 2:
        return X
    last = X[:, -1, :]
    mean = X.mean(axis=1)
    std = X.std(axis=1)
    trend = X[:, -1, :] - X[:, 0, :]
    return np.concatenate([last, mean, std, trend], axis=1)


_FREQ = {
    "1m": pd.Timedelta(minutes=1),
    "5m": pd.Timedelta(minutes=5),
    "15m": pd.Timedelta(minutes=15),
    "30m": pd.Timedelta(minutes=30),
    "1h": pd.Timedelta(hours=1),
    "4h": pd.Timedelta(hours=4),
    "1w": pd.Timedelta(weeks=1),
}


def future_timestamps(last: Any, timeframe: str, steps: int) -> List[str]:
    if not isinstance(last, pd.Timestamp):
        return [f"t+{i}" for i in range(1, steps + 1)]
    if timeframe == "1d":
        stamps = pd.bdate_range(start=last + pd.Timedelta(days=1), periods=steps)
        return [s.isoformat() for s in stamps]
    delta = _FREQ.get(timeframe, pd.Timedelta(days=1))
    return [(last + delta * i).isoformat() for i in range(1, steps + 1)]
