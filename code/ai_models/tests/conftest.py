import numpy as np
import pandas as pd
import pytest
from ai_models.api.app import create_app
from ai_models.api.container import build_services
from ai_models.core.settings import Settings
from ai_models.data.client import DataServiceClient, normalize_period
from ai_models.persistence.prediction_store import PredictionStore


def synthetic_ohlcv(
    rows: int = 600, seed: int = 3, end: str = "2026-09-30"
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    regime = np.sin(np.arange(rows) / 18.0) * 0.004
    returns = regime + rng.normal(0, 0.008, rows)
    close = 100 * np.exp(np.cumsum(returns))
    open_ = close * (1 + rng.normal(0, 0.002, rows))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.003, rows)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.003, rows)))
    volume = rng.integers(1_000_000, 5_000_000, rows).astype(float)
    index = pd.bdate_range(end=end, periods=rows)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=index,
    )


class FakeDataClient(DataServiceClient):
    def __init__(self, frame: pd.DataFrame) -> None:
        super().__init__("http://fake", cache_ttl=0)
        self.frame = frame
        self.calls = 0

    def fetch_ohlcv(self, symbol, timeframe="1d", period="1y"):
        self.calls += 1
        days = int(normalize_period(period)[:-1])
        cutoff = self.frame.index[-1] - pd.Timedelta(days=days)
        return self.frame[self.frame.index >= cutoff].copy()

    def healthy(self) -> bool:
        return True


@pytest.fixture
def frame():
    return synthetic_ohlcv()


@pytest.fixture
def settings(tmp_path):
    return Settings(
        model_dir=str(tmp_path / "models"),
        rl_model_dir=str(tmp_path / "models" / "rl"),
        data_service_url="http://fake",
        database_url=None,
        api_key=None,
        request_timeout=5.0,
        request_retries=0,
        max_workers=2,
        job_history=50,
        cache_ttl=0,
        cache_size=16,
        port=8080,
        min_history_rows=80,
        cors_origins=("*",),
        max_training_epochs=500,
        max_rl_timesteps=200000,
    )


@pytest.fixture
def services(settings, frame):
    return build_services(
        settings, data_client=FakeDataClient(frame), store=PredictionStore(None)
    )


@pytest.fixture
def client(settings, services):
    app = create_app(settings, services)
    app.config["TESTING"] = True
    return app.test_client()
