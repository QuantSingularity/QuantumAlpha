import time

import pytest
from ai_models.api.app import create_app
from ai_models.core.settings import Settings


def _create(client, kind="ridge", features=None, **extra):
    body = {
        "name": f"{kind} model",
        "type": kind,
        "features": features or ["sma_20", "rsi_14", "macd"],
        **extra,
    }
    response = client.post("/api/models", json=body)
    assert response.status_code == 201, response.get_json()
    return response.get_json()["id"]


def _train(client, model_id, **extra):
    body = {
        "model_id": model_id,
        "symbol": "AAPL",
        "sequence_length": 20,
        "horizon": 3,
        "period": "2y",
        **extra,
    }
    return client.post("/api/train-model", json=body)


@pytest.fixture
def trained(client):
    model_id = _create(client)
    response = _train(client, model_id)
    assert response.status_code == 200, response.get_json()
    return model_id


def test_health_ready_catalog(client):
    assert client.get("/health").get_json()["status"] == "healthy"
    assert client.get("/ready").status_code == 200
    catalog = client.get("/api/catalog").get_json()
    assert {"lstm", "ridge", "random_forest"} <= {
        m["type"] for m in catalog["model_types"]
    }


def test_model_validation_errors(client):
    assert (
        client.post("/api/models", json={"name": "x", "type": "bogus"}).status_code
        == 400
    )
    assert client.post("/api/models", json={"type": "ridge"}).status_code == 400
    assert (
        client.post(
            "/api/models", json={"name": "x", "type": "ridge", "features": ["bad"]}
        ).status_code
        == 400
    )
    assert client.get("/api/models/missing").status_code == 404
    assert (
        client.post("/api/models", data="nope", content_type="text/plain").status_code
        == 400
    )


def test_train_predict_flow(client, trained):
    detail = client.get(f"/api/models/{trained}").get_json()
    assert detail["status"] == "trained" and detail["active_version"] == 1
    assert detail["metrics"]["samples"] > 0
    assert "backtest" in detail["metrics"]
    result = client.post(
        "/api/predict", json={"model_id": trained, "symbol": "AAPL", "horizon": 3}
    ).get_json()
    assert result["horizon"] == 3 and len(result["predictions"]) == 3
    prediction = result["prediction"]
    assert prediction["direction"] in ("bullish", "bearish", "neutral")
    assert 0.0 <= prediction["probability_up"] <= 1.0
    step = result["predictions"][0]
    assert step["lower"] < step["value"] < step["upper"]
    assert result["predictions"][0]["timestamp"] > result["as_of"]
    get_form = client.get(f"/api/predict/{trained}/AAPL?horizon=2").get_json()
    assert get_form["horizon"] == 2


def test_prediction_default_period_is_accepted_by_data_service_contract(
    client, trained, services
):
    seen = []
    original = services.data_client.fetch_ohlcv

    def spy(symbol, timeframe="1d", period="1y"):
        seen.append(period)
        return original(symbol, timeframe, period)

    services.data_client.fetch_ohlcv = spy
    assert (
        client.post(
            "/api/predict", json={"model_id": trained, "symbol": "AAPL"}
        ).status_code
        == 200
    )
    import re

    assert re.match(r"^\d+d$", seen[0])


def test_predict_requires_trained_model(client):
    model_id = _create(client)
    response = client.post(
        "/api/predict", json={"model_id": model_id, "symbol": "AAPL"}
    )
    assert response.status_code == 409
    assert response.get_json()["code"] == "MODEL_NOT_TRAINED"


def test_insufficient_data_returns_422_and_restores_status(client):
    model_id = _create(client)
    response = _train(client, model_id, period="30d")
    assert response.status_code == 422
    assert client.get(f"/api/models/{model_id}").get_json()["status"] == "error"


def test_batch_ensemble_and_signals(client, trained):
    batch = client.post(
        "/api/predict/batch",
        json={"model_id": trained, "symbols": ["AAPL", "MSFT", "bad symbol"]},
    ).get_json()
    assert batch["count"] == 2 and len(batch["errors"]) == 1
    second = _create(client, "random_forest")
    assert _train(client, second, parameters={"n_estimators": 20}).status_code == 200
    ensemble = client.post(
        "/api/predict/ensemble", json={"model_ids": [trained, second], "symbol": "AAPL"}
    ).get_json()
    assert pytest.approx(sum(ensemble["ensemble"]["weights"])) == 1.0
    assert (
        client.post(
            "/api/predict/ensemble", json={"model_ids": [trained], "symbol": "AAPL"}
        ).status_code
        == 400
    )
    for strategy in ("prediction", "technical", "ensemble"):
        body = {
            "symbols": ["AAPL"],
            "model_id": trained,
            "strategy": strategy,
            "persist": True,
        }
        data = client.post("/api/generate-signals", json=body).get_json()
        assert data["count"] == 1, data
        signal = data["signals"][0]
        assert (
            signal["type"] in ("buy", "sell", "hold")
            and 0.0 <= signal["strength"] <= 1.0
        )
    assert (
        client.post(
            "/api/generate-signals",
            json={"symbols": ["AAPL"], "strategy": "prediction"},
        ).status_code
        == 400
    )
    assert len(client.get("/api/signals?symbol=AAPL").get_json()) == 3


def test_prediction_history_reconcile_and_performance(client, trained, services):
    persisted = client.post(
        "/api/predict", json={"model_id": trained, "symbol": "AAPL", "persist": True}
    ).get_json()
    assert "prediction_id" in persisted
    manual = client.post(
        f"/api/models/{trained}/predictions",
        json={
            "symbol": "AAPL",
            "timestamp": "2026-09-01T00:00:00Z",
            "prediction": 100.0,
        },
    )
    assert manual.status_code == 201
    updated = client.put(
        f"/api/predictions/{manual.get_json()['id']}", json={"actual": 103.0}
    ).get_json()
    assert updated["error"] == pytest.approx(3.0)
    perf = client.get(f"/api/models/{trained}/performance?symbol=AAPL").get_json()
    assert perf["metrics"]["count"] == 1 and perf["metrics"][
        "avg_abs_error"
    ] == pytest.approx(3.0)
    history = client.get(f"/api/models/{trained}/predictions/AAPL").get_json()
    assert len(history) == 2
    assert client.put("/api/predictions/999", json={"actual": 1}).status_code == 404
    assert client.put("/api/predictions/1", json={}).status_code == 400
    services.store.save_prediction(trained, "AAPL", "2026-09-10T00:00:00Z", 101.0)
    result = client.post(
        f"/api/models/{trained}/reconcile", json={"symbol": "AAPL"}
    ).get_json()
    assert result["updated"] >= 1


def test_evaluate_explain_drift_health(client, trained):
    evaluation = client.post(
        f"/api/models/{trained}/evaluate", json={"symbol": "AAPL"}
    ).get_json()
    assert evaluation["metrics"]["evaluated_samples"] > 0
    explain = client.get(f"/api/models/{trained}/explain?symbol=AAPL").get_json()
    assert explain["features"][0]["importance"] >= explain["features"][-1]["importance"]
    drift = client.get(f"/api/models/{trained}/drift").get_json()
    assert drift["status"] in ("stable", "moderate", "significant")
    health = client.get(f"/api/models/{trained}/health").get_json()
    assert health["needs_retraining"] in (True, False)


def test_versions_promote_and_delete(client, trained):
    assert _train(client, trained, activate=False).status_code == 200
    versions = client.get(f"/api/models/{trained}/versions").get_json()
    assert [v["version"] for v in versions] == [1, 2]
    assert client.get(f"/api/models/{trained}").get_json()["active_version"] == 1
    assert (
        client.post(f"/api/models/{trained}/versions/2/promote").get_json()[
            "active_version"
        ]
        == 2
    )
    assert client.delete(f"/api/models/{trained}/versions/2").status_code == 409
    assert client.delete(f"/api/models/{trained}/versions/1").status_code == 200
    assert client.delete(f"/api/models/{trained}").status_code == 200


def test_validate_and_tune_async_jobs(client):
    model_id = _create(client)
    job = client.post(
        f"/api/models/{model_id}/validate",
        json={
            "symbol": "AAPL",
            "sequence_length": 20,
            "horizon": 3,
            "period": "2y",
            "n_splits": 3,
            "async": True,
        },
    )
    assert job.status_code == 202
    job_id = job.get_json()["id"]
    for _ in range(100):
        state = client.get(f"/api/jobs/{job_id}").get_json()
        if state["status"] in ("succeeded", "failed"):
            break
        time.sleep(0.1)
    assert state["status"] == "succeeded", state
    assert len(state["result"]["folds"]) == 3
    tuned = client.post(
        f"/api/models/{model_id}/tune",
        json={
            "symbol": "AAPL",
            "sequence_length": 20,
            "horizon": 3,
            "period": "2y",
            "trials": 3,
            "apply": True,
            "search_space": {"alpha": [0.1, 1.0, 10.0]},
        },
    ).get_json()
    assert tuned["best_params"]["alpha"] in (0.1, 1.0, 10.0)
    assert (
        client.get(f"/api/models/{model_id}").get_json()["parameters"]["alpha"]
        == tuned["best_params"]["alpha"]
    )


def test_async_training_job_and_conflict(client):
    model_id = _create(client, "gradient_boosting")
    response = _train(
        client, model_id, **{"async": True, "parameters": {"n_estimators": 30}}
    )
    assert response.status_code == 202
    job_id = response.get_json()["id"]
    for _ in range(200):
        state = client.get(f"/api/jobs/{job_id}").get_json()
        if state["status"] in ("succeeded", "failed"):
            break
        time.sleep(0.1)
    assert state["status"] == "succeeded", state


def test_error_envelope_and_request_id(client):
    response = client.get("/api/nope")
    assert response.status_code == 404
    assert response.get_json()["status_code"] == 404
    assert response.headers["X-Request-ID"]
    assert client.get("/metrics").status_code == 200
    assert b"ai_engine_requests_total" in client.get("/metrics").data


def test_api_key_enforced(settings, services):
    secured = Settings(**{**settings.__dict__, "api_key": "secret"})
    app = create_app(secured, services)
    http = app.test_client()
    assert http.get("/health").status_code == 200
    assert http.get("/api/models").status_code == 401
    assert (
        http.get("/api/models", headers={"X-Internal-Key": "wrong"}).status_code == 401
    )
    assert (
        http.get("/api/models", headers={"X-Internal-Key": "secret"}).status_code == 200
    )
