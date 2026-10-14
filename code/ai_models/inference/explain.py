from typing import Any, Dict

import numpy as np
from ai_models.core.exceptions import DataError
from ai_models.data.preprocessing import build_dataset
from ai_models.registry.bundle import LoadedBundle


def permutation_importance(
    bundle: LoadedBundle,
    ohlcv: Any,
    max_samples: int = 200,
    repeats: int = 3,
    seed: int = 7,
) -> Dict[str, Any]:
    raw = build_dataset(
        ohlcv,
        bundle.meta.get("features"),
        bundle.sequence_length,
        bundle.horizon,
        min_samples=20,
    )
    missing = [c for c in bundle.columns if c not in raw.frame.columns]
    if missing:
        raise DataError(f"Feature columns missing: {missing}")
    order = [list(raw.frame.columns).index(c) for c in bundle.columns]
    windows = raw.windows[-max_samples:][:, :, order]
    targets = raw.targets[-max_samples:]
    shape = windows.shape
    scaled = (
        bundle.scaler.transform(windows.reshape(-1, shape[-1]))
        .reshape(shape)
        .astype(np.float32)
    )
    baseline = float(np.mean((bundle.model.predict(scaled) - targets) ** 2))
    rng = np.random.default_rng(seed)
    scores = []
    for col, name in enumerate(bundle.columns):
        deltas = []
        for _ in range(repeats):
            shuffled = scaled.copy()
            shuffled[:, :, col] = shuffled[rng.permutation(len(shuffled)), :, col]
            deltas.append(
                float(np.mean((bundle.model.predict(shuffled) - targets) ** 2))
                - baseline
            )
        scores.append(
            {
                "feature": name,
                "importance": float(np.mean(deltas)),
                "std": float(np.std(deltas)),
            }
        )
    scores.sort(key=lambda s: s["importance"], reverse=True)
    total = sum(max(s["importance"], 0.0) for s in scores) or 1.0
    for score in scores:
        score["share"] = max(score["importance"], 0.0) / total
    return {"baseline_mse": baseline, "samples": int(len(windows)), "features": scores}
