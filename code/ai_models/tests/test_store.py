import pytest
from ai_models.core.exceptions import NotFoundError, ValidationError
from ai_models.persistence.prediction_store import PredictionStore
from sqlalchemy import create_engine, event, text


def _sqlite_engine():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def attach(connection, _):
        connection.execute("ATTACH DATABASE ':memory:' AS ai_models")
        connection.execute("ATTACH DATABASE ':memory:' AS market_data")

    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE market_data.symbols (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT UNIQUE NOT NULL)"
            )
        )
        conn.execute(
            text(
                "CREATE TABLE ai_models.models (id TEXT PRIMARY KEY, name TEXT, description TEXT, type TEXT, status TEXT, parameters TEXT, metrics TEXT, updated_at TEXT)"
            )
        )
        conn.execute(
            text(
                "CREATE TABLE ai_models.prediction_history (id INTEGER PRIMARY KEY AUTOINCREMENT, model_id TEXT, symbol TEXT, "
                "timestamp TIMESTAMP, prediction REAL, actual REAL, error REAL)"
            )
        )
        conn.execute(
            text(
                "CREATE TABLE ai_models.signals (id INTEGER PRIMARY KEY AUTOINCREMENT, model_id TEXT, symbol TEXT, timestamp TIMESTAMP, "
                "signal_type TEXT, strength REAL, price REAL, parameters TEXT)"
            )
        )
    return engine


@pytest.fixture(params=["memory", "sql"])
def store(request):
    if request.param == "memory":
        return PredictionStore(None)
    return PredictionStore(engine=_sqlite_engine())


INFO = {
    "id": "m1",
    "name": "n",
    "description": "",
    "type": "ridge",
    "status": "trained",
    "parameters": {},
    "metrics": {},
}


def test_save_update_history_performance(store):
    first = store.save_prediction(
        "m1", "AAPL", "2026-09-01T00:00:00Z", 100.0, model_info=INFO
    )
    store.save_prediction(
        "m1", "AAPL", "2026-09-02T00:00:00Z", 110.0, actual=108.0, model_info=INFO
    )
    store.update_actual(first["id"], 103.0)
    history = store.history("m1", "AAPL")
    assert [h["prediction"] for h in history] == [100.0, 110.0]
    assert store.history("m1", "AAPL", only_pending=True) == []
    perf = store.performance("m1", "AAPL")["metrics"]
    assert perf["count"] == 2
    assert perf["avg_error"] == pytest.approx(0.5)
    assert perf["rmse"] == pytest.approx(((9 + 4) / 2) ** 0.5)
    assert store.performance("other")["metrics"] is None


def test_validation_and_missing(store):
    with pytest.raises(ValidationError):
        store.save_prediction("", "AAPL", "2026-09-01", 1.0)
    with pytest.raises(ValidationError):
        store.save_prediction("m1", "AAPL", "not a date", 1.0)
    with pytest.raises(ValidationError):
        store.save_prediction("m1", "AAPL", "2026-09-01", float("nan"))
    with pytest.raises(NotFoundError):
        store.get_prediction(12345)
    with pytest.raises(ValidationError):
        store.update_actual("abc", 1)


def test_signals_roundtrip(store):
    signal = {
        "model_id": "m1",
        "symbol": "AAPL",
        "type": "buy",
        "strength": 0.61,
        "price": 101.5,
        "generated_at": "2026-09-03T00:00:00+00:00",
        "strategy": "prediction",
    }
    store.save_signal(signal, INFO)
    recent = store.recent_signals("AAPL")
    assert recent[0]["type"] == "buy" and recent[0]["strength"] == pytest.approx(0.61)
    assert store.healthy()
