from typing import Any, Dict

import numpy as np


def _safe(value: float) -> float:
    return float(value) if np.isfinite(value) else 0.0


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    if y_true.ndim == 1:
        y_true = y_true.reshape(-1, 1)
        y_pred = y_pred.reshape(-1, 1)
    if len(y_true) == 0:
        return {"samples": 0}
    err = y_pred - y_true
    mse = float(np.mean(err**2))
    mae = float(np.mean(np.abs(err)))
    denom = float(np.sum((y_true - y_true.mean(axis=0)) ** 2))
    r2 = 1.0 - float(np.sum(err**2)) / denom if denom > 0 else 0.0
    naive_mse = float(np.mean(y_true**2))
    skill = 1.0 - mse / naive_mse if naive_mse > 0 else 0.0
    hits = np.sign(y_pred) == np.sign(y_true)
    nonzero = y_true != 0
    directional = float(hits[nonzero].mean()) if nonzero.any() else 0.0
    per_step = [
        _safe(np.mean(hits[:, k][nonzero[:, k]])) if nonzero[:, k].any() else 0.0
        for k in range(y_true.shape[1])
    ]
    flat_true, flat_pred = y_true.ravel(), y_pred.ravel()
    if len(flat_true) > 2 and flat_true.std() > 0 and flat_pred.std() > 0:
        ic = float(np.corrcoef(flat_true, flat_pred)[0, 1])
    else:
        ic = 0.0
    return {
        "samples": int(len(y_true)),
        "mse": _safe(mse),
        "rmse": _safe(np.sqrt(mse)),
        "mae": _safe(mae),
        "r2": _safe(r2),
        "naive_mse": _safe(naive_mse),
        "skill_vs_naive": _safe(skill),
        "directional_accuracy": _safe(directional),
        "directional_accuracy_by_step": per_step,
        "information_coefficient": _safe(ic),
    }


def residual_std(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    err = np.asarray(y_pred, dtype=np.float64) - np.asarray(y_true, dtype=np.float64)
    if err.ndim == 1:
        err = err.reshape(-1, 1)
    if len(err) < 2:
        return np.full(err.shape[1], 0.02)
    return np.maximum(err.std(axis=0, ddof=1), 1e-4)
