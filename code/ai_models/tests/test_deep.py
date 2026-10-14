import pytest

pytest.importorskip("tensorflow")

from ai_models.data.preprocessing import prepare_training_data
from ai_models.models.factory import create_model, load_model
from ai_models.tests.conftest import synthetic_ohlcv

pytestmark = pytest.mark.deep


@pytest.mark.parametrize("kind", ["lstm", "gru", "cnn", "transformer"])
def test_deep_model_fit_predict_save_load(kind, tmp_path):
    data = prepare_training_data(synthetic_ohlcv(300), ["sma_20", "rsi_14"], 16, 3)
    model = create_model(
        kind,
        {
            "epochs": 2,
            "units": 8,
            "filters": 8,
            "d_model": 16,
            "num_heads": 2,
            "ff_dim": 16,
            "batch_size": 16,
        },
        data.n_features,
        16,
        3,
    )
    summary = model.fit(data)
    assert summary["epochs_run"] >= 1
    predictions = model.predict(data.X_test)
    assert predictions.shape == (len(data.X_test), 3)
    model.save(str(tmp_path))
    restored = load_model(kind, str(tmp_path), model.params, data.n_features, 16, 3)
    assert abs(restored.predict(data.X_test) - predictions).max() < 1e-4


def test_deep_model_end_to_end_via_api(client):
    created = client.post(
        "/api/models",
        json={"name": "lstm", "type": "lstm", "features": ["sma_20", "rsi_14"]},
    )
    model_id = created.get_json()["id"]
    trained = client.post(
        "/api/train-model",
        json={
            "model_id": model_id,
            "symbol": "AAPL",
            "period": "2y",
            "sequence_length": 16,
            "horizon": 3,
            "epochs": 2,
            "units": 8,
        },
    )
    assert trained.status_code == 200, trained.get_json()
    result = client.post("/api/predict", json={"model_id": model_id, "symbol": "AAPL"})
    assert result.status_code == 200
    assert len(result.get_json()["predictions"]) == 3
