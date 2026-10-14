import numpy as np
import pandas as pd
import pytest
from ai_models.core.exceptions import DataError, DependencyError, ValidationError
from ai_models.data.client import (
    DataServiceClient,
    normalize_period,
    rows_to_frame,
    validate_symbol,
    validate_timeframe,
)
from ai_models.data.features import (
    DEFAULT_FEATURES,
    build_features,
    supported_features,
    validate_features,
)
from ai_models.data.preprocessing import (
    FeatureScaler,
    future_timestamps,
    latest_window,
    prepare_training_data,
    to_tabular,
)
from ai_models.tests.conftest import synthetic_ohlcv


def test_period_normalization_matches_data_service_contract():
    assert normalize_period("1mo") == "30d"
    assert normalize_period("1wk") == "7d"
    assert normalize_period("1y") == "365d"
    assert normalize_period("2m") == "60d"
    assert normalize_period(None) == "365d"
    with pytest.raises(ValidationError):
        normalize_period("abc")


def test_symbol_and_timeframe_validation():
    assert validate_symbol(" aapl ") == "AAPL"
    with pytest.raises(ValidationError):
        validate_symbol("")
    with pytest.raises(ValidationError):
        validate_symbol("A B")
    with pytest.raises(ValidationError):
        validate_timeframe("2d")


def test_rows_to_frame_cleans_data():
    rows = [
        {
            "timestamp": "2026-01-02T00:00:00Z",
            "open": 10,
            "high": 11,
            "low": 9,
            "close": 10.5,
            "volume": 100,
        },
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "open": 10,
            "high": 11,
            "low": 9,
            "close": 10.2,
            "volume": None,
        },
        {
            "timestamp": "2026-01-02T00:00:00Z",
            "open": 10,
            "high": 11,
            "low": 9,
            "close": 10.6,
            "volume": 90,
        },
        {
            "timestamp": "2026-01-03T00:00:00Z",
            "open": 10,
            "high": 11,
            "low": 9,
            "close": None,
            "volume": 90,
        },
    ]
    frame = rows_to_frame(rows)
    assert len(frame) == 2
    assert frame.index.is_monotonic_increasing
    assert frame["volume"].iloc[0] == 0.0
    assert frame["close"].iloc[-1] == 10.6
    with pytest.raises(DataError):
        rows_to_frame([])
    with pytest.raises(DependencyError):
        rows_to_frame([{"timestamp": "2026-01-01", "close": 1}])


class _Response:
    def __init__(self, status, payload):
        self.status_code = status
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


class _Session:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def get(self, url, params=None, timeout=None):
        self.requests.append((url, params, timeout))
        return self.response


def test_client_unwraps_envelope_and_sends_valid_period():
    rows = [
        {
            "timestamp": f"2026-01-{d:02d}",
            "open": 1,
            "high": 2,
            "low": 1,
            "close": 1.5,
            "volume": 10,
        }
        for d in range(1, 6)
    ]
    session = _Session(_Response(200, {"success": True, "data": {"data": rows}}))
    client = DataServiceClient("http://data:8081/", timeout=7, session=session)
    frame = client.fetch_ohlcv("aapl", "1d", "1mo")
    assert len(frame) == 5
    url, params, timeout = session.requests[0]
    assert url == "http://data:8081/api/market-data/AAPL"
    assert params == {"timeframe": "1d", "period": "30d"}
    assert timeout == 7


def test_client_error_mapping():
    with pytest.raises(DataError):
        DataServiceClient("http://x", session=_Session(_Response(404, {}))).fetch_ohlcv(
            "AAPL"
        )
    with pytest.raises(DependencyError):
        DataServiceClient("http://x", session=_Session(_Response(500, {}))).fetch_ohlcv(
            "AAPL"
        )


def test_features_are_dimensionless_and_complete():
    frame = synthetic_ohlcv(300)
    features = build_features(frame, list(DEFAULT_FEATURES))
    assert not np.isinf(features.to_numpy()).any()
    assert features.dropna().shape[0] > 200
    assert "close" not in features.columns
    assert features["rsi_14"].dropna().between(-1, 1).all()


def test_feature_validation():
    assert validate_features(["sma_5", "rsi", "sma_5"]) == ["sma_5", "rsi"]
    with pytest.raises(ValidationError):
        validate_features(["nonsense"])
    assert "macd" in supported_features()


def test_split_has_no_leakage_and_scaler_uses_train_only():
    frame = synthetic_ohlcv(400)
    data = prepare_training_data(
        frame, ["sma_20", "rsi_14"], 20, 3, test_size=0.2, val_size=0.1
    )
    assert data.X_train.shape[1:] == (20, data.n_features)
    assert data.y_train.shape[1] == 3
    assert len(data.X_test) > 0 and len(data.X_val) > 0
    assert np.abs(data.X_train).max() <= 6.0 + 1e-6
    train_mean = data.X_train[:, -1, :].mean(axis=0)
    assert np.all(np.abs(train_mean) < 1.0)
    assert data.index_test.is_monotonic_increasing
    assert data.index_test[0] > frame.index[int(len(frame) * 0.6)]


def test_insufficient_history_raises():
    with pytest.raises(DataError):
        prepare_training_data(synthetic_ohlcv(60), ["sma_20"], 30, 5)


def test_latest_window_and_tabular():
    frame = synthetic_ohlcv(300)
    data = prepare_training_data(frame, ["sma_20"], 20, 3)
    window, stamp, close = latest_window(
        frame, ["sma_20"], data.columns, data.scaler, 20
    )
    assert window.shape == (1, 20, data.n_features)
    assert close == pytest.approx(frame["close"].iloc[-1])
    assert to_tabular(window).shape == (1, data.n_features * 4)


def test_future_timestamps_skip_weekends():
    stamps = future_timestamps(pd.Timestamp("2026-10-02"), "1d", 3)
    assert [pd.Timestamp(s).weekday() for s in stamps] == [0, 1, 2]


def test_scaler_roundtrip():
    scaler = FeatureScaler().fit(np.random.default_rng(1).normal(5, 2, (100, 3)))
    restored = FeatureScaler.from_dict(scaler.to_dict())
    values = np.ones((4, 3))
    assert np.allclose(scaler.transform(values), restored.transform(values))
