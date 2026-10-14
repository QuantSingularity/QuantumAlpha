import itertools
import random
import time
from typing import Any, Dict, List, Optional

import pandas as pd
from ai_models.core.exceptions import ValidationError
from ai_models.data.preprocessing import prepare_training_data
from ai_models.evaluation.metrics import regression_metrics
from ai_models.models.factory import create_model

DEFAULT_GRIDS: Dict[str, Dict[str, List[Any]]] = {
    "lstm": {
        "units": [32, 64, 128],
        "dropout": [0.1, 0.2, 0.3],
        "learning_rate": [0.001, 0.0005],
        "batch_size": [16, 32],
    },
    "gru": {
        "units": [32, 64, 128],
        "dropout": [0.1, 0.2, 0.3],
        "learning_rate": [0.001, 0.0005],
        "batch_size": [16, 32],
    },
    "cnn": {
        "filters": [32, 64, 128],
        "kernel_size": [2, 3, 5],
        "dropout": [0.1, 0.2, 0.3],
        "learning_rate": [0.001, 0.0005],
    },
    "transformer": {
        "d_model": [32, 64],
        "num_heads": [2, 4],
        "num_blocks": [1, 2],
        "dropout": [0.1, 0.2],
        "learning_rate": [0.001, 0.0005],
    },
    "ridge": {"alpha": [0.01, 0.1, 1.0, 10.0, 100.0]},
    "random_forest": {
        "n_estimators": [100, 200, 300],
        "max_depth": [4, 6, 8, 12],
        "min_samples_leaf": [1, 3, 5],
    },
    "gradient_boosting": {
        "n_estimators": [100, 150, 250],
        "learning_rate": [0.03, 0.05, 0.1],
        "max_depth": [2, 3, 4],
        "subsample": [0.7, 0.8, 1.0],
    },
}


def search(
    ohlcv: pd.DataFrame,
    kind: str,
    features: Optional[List[str]],
    sequence_length: int,
    horizon: int,
    grid: Optional[Dict[str, List[Any]]] = None,
    base_params: Optional[Dict[str, Any]] = None,
    trials: int = 10,
    seed: int = 42,
    time_budget: float = 300.0,
) -> Dict[str, Any]:
    grid = grid or DEFAULT_GRIDS.get(kind)
    if not grid:
        raise ValidationError(f"No search space for model type: {kind}")
    for key, values in grid.items():
        if not isinstance(values, list) or not values:
            raise ValidationError(f"Search space for {key} must be a non-empty list")
    if not 1 <= trials <= 100:
        raise ValidationError("trials must be between 1 and 100")
    data = prepare_training_data(
        ohlcv, features, sequence_length, horizon, test_size=0.2, val_size=0.2
    )
    use_val = len(data.X_val) >= 5
    keys = sorted(grid)
    combos = list(itertools.product(*[grid[k] for k in keys]))
    random.Random(seed).shuffle(combos)
    started = time.monotonic()
    results: List[Dict[str, Any]] = []
    for combo in combos[:trials]:
        if time.monotonic() - started > time_budget and results:
            break
        params = {**(base_params or {}), **dict(zip(keys, combo)), "seed": seed}
        model = create_model(
            kind, params, data.n_features, data.sequence_length, data.horizon
        )
        try:
            model.fit(data)
            X, y = (data.X_val, data.y_val) if use_val else (data.X_test, data.y_test)
            metrics = regression_metrics(y, model.predict(X))
            results.append(
                {
                    "params": dict(zip(keys, combo)),
                    "mse": metrics["mse"],
                    "directional_accuracy": metrics["directional_accuracy"],
                    "skill_vs_naive": metrics["skill_vs_naive"],
                }
            )
        except Exception as exc:
            results.append({"params": dict(zip(keys, combo)), "error": str(exc)})
    scored = [r for r in results if "mse" in r]
    if not scored:
        raise ValidationError("All tuning trials failed", {"trials": results})
    scored.sort(key=lambda r: r["mse"])
    return {
        "best_params": scored[0]["params"],
        "best_score": scored[0]["mse"],
        "metric": "validation_mse" if use_val else "test_mse",
        "trials": results,
        "evaluated": len(results),
    }
