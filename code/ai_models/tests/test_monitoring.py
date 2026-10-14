import numpy as np
from ai_models.core.exceptions import DataError
from ai_models.data.preprocessing import prepare_training_data
from ai_models.monitoring.drift import drift_report, population_stability_index
from ai_models.monitoring.metrics import MetricsRegistry
from ai_models.registry.bundle import LoadedBundle
from ai_models.tests.conftest import synthetic_ohlcv


def _bundle(frame, features):
    data = prepare_training_data(frame, features, 20, 3)
    meta = {
        "features": features,
        "columns": data.columns,
        "sequence_length": 20,
        "horizon": 3,
        "reference_quantiles": {
            c: np.quantile(data.X_train[:, -1, i], np.linspace(0, 1, 11)).tolist()
            for i, c in enumerate(data.columns)
        },
    }
    return LoadedBundle(model=None, scaler=data.scaler, meta=meta)


def _shocked(frame, start):
    shocked = frame.copy()
    returns = shocked["close"].pct_change().fillna(0).to_numpy()
    mask = np.arange(len(returns)) > start
    adjusted = returns * np.where(mask, 3.5, 1.0) + np.where(mask, -0.004, 0.0)
    close = 100 * np.cumprod(1 + adjusted)
    ratio = close / shocked["close"].to_numpy()
    for column in ("open", "high", "low", "close"):
        shocked[column] = shocked[column].to_numpy() * ratio
    return shocked


def test_psi_is_near_zero_for_matching_distribution():
    rng = np.random.default_rng(0)
    sample = rng.normal(size=5000)
    quantiles = np.quantile(sample, np.linspace(0, 1, 11)).tolist()
    assert population_stability_index(quantiles, rng.normal(size=500)) < 0.05
    assert population_stability_index(quantiles, rng.normal(3, 1, 500)) > 1.0


def test_drift_stable_in_sample_and_significant_after_shock():
    frame = synthetic_ohlcv(1500)
    bundle = _bundle(frame.iloc[:700], ["sma_20", "rsi_14", "macd"])
    stable = drift_report(bundle, frame.iloc[:1000])
    assert stable["status"] != "significant"
    shocked = drift_report(bundle, _shocked(frame, 1200))
    assert shocked["status"] == "significant"
    assert shocked["mean_psi"] > stable["mean_psi"]
    assert shocked["features"][0]["psi"] >= shocked["features"][-1]["psi"]


def test_drift_requires_reference_and_history():
    frame = synthetic_ohlcv(300)
    bundle = _bundle(frame, ["sma_20"])
    import pytest

    with pytest.raises(DataError):
        drift_report(bundle, frame.iloc[:70])
    bundle.meta.pop("reference_quantiles")
    with pytest.raises(DataError):
        drift_report(bundle, frame)


def test_metrics_registry_render():
    metrics = MetricsRegistry()
    metrics.inc("requests_total", route="/x", status=200)
    metrics.observe("latency_seconds", 0.5, route="/x")
    text = metrics.render()
    assert 'requests_total{route="/x",status="200"} 1.0' in text
    assert 'latency_seconds_count{route="/x"} 1' in text
