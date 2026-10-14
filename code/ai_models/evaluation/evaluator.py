from typing import Any, Dict

import numpy as np
from ai_models.core.exceptions import DataError
from ai_models.data.preprocessing import build_dataset
from ai_models.evaluation.backtest import backtest_signals
from ai_models.evaluation.metrics import regression_metrics
from ai_models.registry.bundle import LoadedBundle


def evaluate_bundle(
    bundle: LoadedBundle, ohlcv: Any, last_n: int = 120
) -> Dict[str, Any]:
    raw = build_dataset(
        ohlcv,
        bundle.meta.get("features"),
        bundle.sequence_length,
        bundle.horizon,
        min_samples=10,
    )
    missing = [c for c in bundle.columns if c not in raw.frame.columns]
    if missing:
        raise DataError(f"Feature columns missing: {missing}")
    order = [list(raw.frame.columns).index(c) for c in bundle.columns]
    windows = raw.windows[-last_n:][:, :, order]
    targets = raw.targets[-last_n:]
    prices = raw.close[raw.ends[-last_n:]]
    shape = windows.shape
    scaled = (
        bundle.scaler.transform(windows.reshape(-1, shape[-1]))
        .reshape(shape)
        .astype(np.float32)
    )
    predictions = bundle.model.predict(scaled)
    metrics = regression_metrics(targets, predictions)
    trading = backtest_signals(prices, predictions[:, -1])
    trading.pop("equity_curve", None)
    metrics["backtest"] = trading
    metrics["evaluated_samples"] = int(len(windows))
    return metrics
