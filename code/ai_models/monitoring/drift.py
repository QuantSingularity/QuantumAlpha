from typing import Any, Dict, List

import numpy as np
from ai_models.core.exceptions import DataError
from ai_models.data.preprocessing import clean_feature_frame
from ai_models.registry.bundle import LoadedBundle

PSI_MODERATE = 0.25
PSI_SIGNIFICANT = 0.5
DEFAULT_WINDOW = 250
MIN_WINDOW = 60


def population_stability_index(
    reference_quantiles: List[float], values: np.ndarray
) -> float:
    edges = np.unique(np.asarray(reference_quantiles, dtype=float))
    if len(edges) < 3 or len(values) == 0:
        return 0.0
    interior = edges[1:-1]
    bins = np.searchsorted(interior, values, side="right")
    actual = np.bincount(bins, minlength=len(interior) + 1).astype(float)
    count = actual.sum()
    actual = np.clip(actual / count, 1e-4, None)
    expected = np.full(len(actual), 1.0 / len(actual))
    raw = float(np.sum((actual - expected) * np.log(actual / expected)))
    return max(0.0, raw - (len(actual) - 1) / count)


def status_for(psi: float) -> str:
    if psi >= PSI_SIGNIFICANT:
        return "significant"
    if psi >= PSI_MODERATE:
        return "moderate"
    return "stable"


def drift_report(
    bundle: LoadedBundle, ohlcv: Any, recent: int = DEFAULT_WINDOW
) -> Dict[str, Any]:
    reference = bundle.meta.get("reference_quantiles")
    if not reference:
        raise DataError(
            "Model has no reference distribution; retrain to enable drift monitoring"
        )
    frame = clean_feature_frame(ohlcv, bundle.meta.get("features"))
    missing = [c for c in bundle.columns if c not in frame.columns]
    if missing:
        raise DataError(f"Feature columns missing: {missing}")
    frame = frame[bundle.columns].tail(recent)
    if len(frame) < MIN_WINDOW:
        raise DataError(
            f"Not enough recent rows to assess drift: {len(frame)} usable, need {MIN_WINDOW}"
        )
    scaled = bundle.scaler.transform(frame.to_numpy(dtype=float))
    features: List[Dict[str, Any]] = []
    for i, column in enumerate(bundle.columns):
        psi = population_stability_index(reference[column], scaled[:, i])
        features.append({"feature": column, "psi": psi, "status": status_for(psi)})
    features.sort(key=lambda f: f["psi"], reverse=True)
    values = np.array([f["psi"] for f in features])
    overall = float(values.mean())
    worst = float(values.max())
    if worst >= PSI_SIGNIFICANT and (values >= PSI_SIGNIFICANT).sum() >= max(
        2, len(values) // 5
    ):
        status = "significant"
    elif overall >= PSI_MODERATE or worst >= PSI_SIGNIFICANT:
        status = "moderate"
    else:
        status = "stable"
    return {
        "status": status,
        "mean_psi": overall,
        "max_psi": worst,
        "window": int(len(frame)),
        "features": features,
    }
