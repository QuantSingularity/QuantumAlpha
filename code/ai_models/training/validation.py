from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from ai_models.core.exceptions import DataError
from ai_models.data.preprocessing import assemble, build_dataset
from ai_models.evaluation.backtest import backtest_signals
from ai_models.evaluation.metrics import regression_metrics
from ai_models.models.factory import create_model


def walk_forward(
    ohlcv: pd.DataFrame,
    kind: str,
    params: Optional[Dict[str, Any]],
    features: Optional[List[str]],
    sequence_length: int,
    horizon: int,
    n_splits: int = 4,
    min_train_fraction: float = 0.5,
) -> Dict[str, Any]:
    raw = build_dataset(ohlcv, features, sequence_length, horizon, min_samples=60)
    n = len(raw)
    first = int(n * min_train_fraction)
    fold_size = (n - first) // n_splits
    if fold_size < 5:
        raise DataError("Not enough history for the requested number of splits")
    folds: List[Dict[str, Any]] = []
    for k in range(n_splits):
        train_end = first + k * fold_size
        test_end = n if k == n_splits - 1 else train_end + fold_size
        train = slice(0, train_end - horizon)
        val = slice(train_end, train_end)
        test = slice(train_end, test_end)
        data = assemble(raw, train, val, test)
        model = create_model(
            kind, params, data.n_features, data.sequence_length, data.horizon
        )
        model.fit(data)
        prediction = model.predict(data.X_test)
        metrics = regression_metrics(data.y_test, prediction)
        trading = backtest_signals(data.close_test, prediction[:, -1])
        folds.append(
            {
                "fold": k + 1,
                "train_samples": int(len(data.X_train)),
                "test_samples": int(len(data.X_test)),
                "mse": metrics["mse"],
                "directional_accuracy": metrics["directional_accuracy"],
                "skill_vs_naive": metrics["skill_vs_naive"],
                "information_coefficient": metrics["information_coefficient"],
                "sharpe": trading.get("sharpe", 0.0),
                "total_return": trading.get("total_return", 0.0),
            }
        )
    summary: Dict[str, Any] = {}
    for key in (
        "mse",
        "directional_accuracy",
        "skill_vs_naive",
        "information_coefficient",
        "sharpe",
        "total_return",
    ):
        values = np.array([f[key] for f in folds], dtype=float)
        summary[key] = {"mean": float(values.mean()), "std": float(values.std())}
    return {"folds": folds, "summary": summary, "n_splits": n_splits}
