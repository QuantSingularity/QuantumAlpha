"""
HTTP-level tests for the AI Engine's Flask blueprints.

Previously ai_models/engine/app.py had zero route-level test coverage -
only the underlying service classes were tested directly - which is how
routes calling nonexistent methods (prediction_service.predict,
model_manager.train_model(data) with the wrong arity, generate_signals
with wrong kwargs, rl_service.train_agent/get_action) went undetected.
These tests build each blueprint against a mocked service and exercise it
through Flask's test client, so a route/method mismatch fails a test.
"""

import unittest
from unittest.mock import MagicMock

from backend.common import ServiceError
from flask import Flask, jsonify


def _build_app(blueprint) -> Flask:
    """Build a minimal Flask app with one blueprint plus the same
    ServiceError -> status_code error handling ai_models/engine/app.py
    registers for its blueprints, so validation errors raised by a route
    (e.g. a missing required field) surface with the right HTTP status
    instead of a generic 500 from Flask's default handler."""
    app = Flask(__name__)
    app.register_blueprint(blueprint)

    @app.errorhandler(Exception)
    def handle_error(error: Exception):
        if isinstance(error, ServiceError):
            return (jsonify(error.to_dict()), error.status_code)
        return (jsonify({"error": "Internal server error"}), 500)

    return app


class TestModelsBlueprint(unittest.TestCase):
    """HTTP-level tests for routes/models_routes.py"""

    def setUp(self) -> None:
        from ai_models.engine.routes.models_routes import create_models_blueprint

        self.model_manager = MagicMock()
        app = _build_app(create_models_blueprint(self.model_manager))
        self.client = app.test_client()

    def test_get_models(self) -> None:
        self.model_manager.get_models.return_value = [{"id": "m1", "name": "Model 1"}]
        resp = self.client.get("/api/models")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {"models": [{"id": "m1", "name": "Model 1"}]})

    def test_create_model(self) -> None:
        self.model_manager.create_model.return_value = {"id": "m1", "name": "Model 1"}
        resp = self.client.post("/api/models", json={"name": "Model 1", "type": "lstm"})
        self.assertEqual(resp.status_code, 201)
        self.model_manager.create_model.assert_called_once_with(
            {"name": "Model 1", "type": "lstm"}
        )

    def test_get_model(self) -> None:
        self.model_manager.get_model.return_value = {"id": "m1"}
        resp = self.client.get("/api/models/m1")
        self.assertEqual(resp.status_code, 200)
        self.model_manager.get_model.assert_called_once_with("m1")

    def test_update_model(self) -> None:
        self.model_manager.update_model.return_value = {"id": "m1", "name": "New name"}
        resp = self.client.put("/api/models/m1", json={"name": "New name"})
        self.assertEqual(resp.status_code, 200)
        self.model_manager.update_model.assert_called_once_with(
            "m1", {"name": "New name"}
        )

    def test_delete_model(self) -> None:
        self.model_manager.delete_model.return_value = {"id": "m1", "deleted": True}
        resp = self.client.delete("/api/models/m1")
        self.assertEqual(resp.status_code, 200)
        self.model_manager.delete_model.assert_called_once_with("m1")

    def test_evaluate_model(self) -> None:
        self.model_manager.evaluate_model.return_value = {"mse": 1.2}
        resp = self.client.post(
            "/api/models/m1/evaluate",
            json={"symbol": "AAPL", "timeframe": "1d", "period": "1mo"},
        )
        self.assertEqual(resp.status_code, 200)
        self.model_manager.evaluate_model.assert_called_once_with(
            "m1", {"symbol": "AAPL", "timeframe": "1d", "period": "1mo"}
        )

    def test_train_existing_model(self) -> None:
        """train-model with an explicit model_id trains that model directly,
        not train_model(data) with the whole body as a single positional
        argument (the original, broken arity)."""
        self.model_manager.train_model.return_value = {"id": "m1", "status": "trained"}
        resp = self.client.post(
            "/api/train-model",
            json={
                "model_id": "m1",
                "symbol": "AAPL",
                "timeframe": "1d",
                "period": "1mo",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.model_manager.create_model.assert_not_called()
        self.model_manager.train_model.assert_called_once_with(
            "m1",
            {"model_id": "m1", "symbol": "AAPL", "timeframe": "1d", "period": "1mo"},
        )

    def test_train_model_without_id_creates_first(self) -> None:
        """train-model without a model_id creates a model first, then trains it."""
        self.model_manager.create_model.return_value = {"id": "new_m1"}
        self.model_manager.train_model.return_value = {
            "id": "new_m1",
            "status": "trained",
        }
        resp = self.client.post(
            "/api/train-model",
            json={"name": "Model 1", "type": "lstm", "symbol": "AAPL"},
        )
        self.assertEqual(resp.status_code, 200)
        self.model_manager.create_model.assert_called_once()
        self.model_manager.train_model.assert_called_once()
        self.assertEqual(self.model_manager.train_model.call_args[0][0], "new_m1")


class TestPredictionBlueprint(unittest.TestCase):
    """HTTP-level tests for routes/prediction_routes.py"""

    def setUp(self) -> None:
        from ai_models.engine.routes.prediction_routes import (
            create_prediction_blueprint,
        )

        self.prediction_service = MagicMock()
        app = _build_app(create_prediction_blueprint(self.prediction_service))
        self.client = app.test_client()

    def test_predict_post_calls_generate_prediction(self) -> None:
        """The fixed contract: POST /api/predict calls generate_prediction,
        not the nonexistent PredictionService.predict()."""
        self.prediction_service.generate_prediction.return_value = {
            "symbol": "AAPL",
            "prediction": {"average": 150.0},
        }
        resp = self.client.post(
            "/api/predict",
            json={
                "model_id": "m1",
                "symbol": "AAPL",
                "timeframe": "1d",
                "period": "1mo",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.prediction_service.generate_prediction.assert_called_once_with(
            model_id="m1", symbol="AAPL", timeframe="1d", period="1mo", horizon=5
        )

    def test_predict_get_convenience_route(self) -> None:
        """GET /api/predict/<model_id>/<symbol> - matches the URL pattern
        risk_service/risk_calculator.py's calculate_portfolio_value_with_prediction
        already calls."""
        self.prediction_service.generate_prediction.return_value = {
            "symbol": "AAPL",
            "prediction": {"average": 150.0},
        }
        resp = self.client.get("/api/predict/m1/AAPL?timeframe=1d&period=1mo&horizon=3")
        self.assertEqual(resp.status_code, 200)
        self.prediction_service.generate_prediction.assert_called_once_with(
            model_id="m1", symbol="AAPL", timeframe="1d", period="1mo", horizon=3
        )

    def test_predict_missing_symbol(self) -> None:
        resp = self.client.post("/api/predict", json={"model_id": "m1"})
        self.assertEqual(resp.status_code, 400)

    def test_prediction_history(self) -> None:
        self.prediction_service.get_prediction_history.return_value = {
            "predictions": []
        }
        resp = self.client.get("/api/models/m1/predictions/AAPL")
        self.assertEqual(resp.status_code, 200)
        self.prediction_service.get_prediction_history.assert_called_once_with(
            model_id="m1", symbol="AAPL", start_date=None, end_date=None
        )

    def test_save_prediction(self) -> None:
        self.prediction_service.save_prediction.return_value = {"id": "pred1"}
        resp = self.client.post(
            "/api/models/m1/predictions",
            json={"symbol": "AAPL", "timestamp": "2024-01-01", "prediction": 150.0},
        )
        self.assertEqual(resp.status_code, 201)

    def test_update_prediction(self) -> None:
        self.prediction_service.update_prediction.return_value = {"id": "pred1"}
        resp = self.client.put("/api/predictions/pred1", json={"actual": 151.0})
        self.assertEqual(resp.status_code, 200)
        self.prediction_service.update_prediction.assert_called_once_with(
            prediction_id="pred1", actual=151.0
        )

    def test_model_performance(self) -> None:
        self.prediction_service.get_model_performance.return_value = {"mae": 1.1}
        resp = self.client.get("/api/models/m1/performance?symbol=AAPL")
        self.assertEqual(resp.status_code, 200)
        self.prediction_service.get_model_performance.assert_called_once_with(
            model_id="m1", symbol="AAPL", start_date=None, end_date=None
        )


class TestSignalBlueprint(unittest.TestCase):
    """HTTP-level tests for routes/signal_routes.py"""

    def setUp(self) -> None:
        from ai_models.engine.routes.signal_routes import create_signal_blueprint

        self.prediction_service = MagicMock()
        app = _build_app(create_signal_blueprint(self.prediction_service))
        self.client = app.test_client()

    def test_generate_signals_uses_correct_kwargs(self) -> None:
        """The fixed contract: generate_signals(symbols=..., model_id=...,
        timeframe=..., period=..., strategy=...), not the original
        symbol=/data= kwargs that don't exist on the real method."""
        self.prediction_service.generate_signals.return_value = {
            "signals": [],
            "count": 0,
        }
        resp = self.client.post(
            "/api/generate-signals",
            json={
                "symbols": ["AAPL", "MSFT"],
                "model_id": "m1",
                "strategy": "prediction",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.prediction_service.generate_signals.assert_called_once_with(
            symbols=["AAPL", "MSFT"],
            model_id="m1",
            timeframe="1d",
            period="1mo",
            strategy="prediction",
        )

    def test_generate_signals_missing_symbols(self) -> None:
        resp = self.client.post("/api/generate-signals", json={"model_id": "m1"})
        self.assertEqual(resp.status_code, 400)


class TestRLBlueprint(unittest.TestCase):
    """HTTP-level tests for routes/rl_routes.py"""

    def setUp(self) -> None:
        from ai_models.engine.routes.rl_routes import create_rl_blueprint

        self.rl_service = MagicMock()
        app = _build_app(create_rl_blueprint(self.rl_service))
        self.client = app.test_client()

    def test_get_models(self) -> None:
        self.rl_service.get_models.return_value = [{"id": "rl1"}]
        resp = self.client.get("/api/rl/models")
        self.assertEqual(resp.status_code, 200)

    def test_train_existing_agent(self) -> None:
        """The fixed contract: train_model(model_id, data), not the
        nonexistent train_agent(data)."""
        self.rl_service.train_model.return_value = {"id": "rl1", "status": "trained"}
        resp = self.client.post(
            "/api/rl/train",
            json={
                "model_id": "rl1",
                "symbol": "AAPL",
                "timeframe": "1d",
                "period": "6mo",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.rl_service.create_model.assert_not_called()
        self.rl_service.train_model.assert_called_once_with(
            "rl1",
            {"model_id": "rl1", "symbol": "AAPL", "timeframe": "1d", "period": "6mo"},
        )

    def test_train_new_agent_creates_first(self) -> None:
        self.rl_service.create_model.return_value = {"id": "new_rl1"}
        self.rl_service.train_model.return_value = {
            "id": "new_rl1",
            "status": "trained",
        }
        resp = self.client.post(
            "/api/rl/train",
            json={"name": "Agent 1", "algorithm": "ppo", "symbol": "AAPL"},
        )
        self.assertEqual(resp.status_code, 200)
        self.rl_service.create_model.assert_called_once()
        self.assertEqual(self.rl_service.train_model.call_args[0][0], "new_rl1")

    def test_act_calls_predict(self) -> None:
        """The fixed contract: predict(model_id, data), not the nonexistent
        get_action(agent_id=..., state=...)."""
        self.rl_service.predict.return_value = {"action": "buy"}
        resp = self.client.post(
            "/api/rl/act",
            json={
                "model_id": "rl1",
                "symbol": "AAPL",
                "timeframe": "1d",
                "period": "1mo",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.rl_service.predict.assert_called_once_with(
            "rl1",
            {"model_id": "rl1", "symbol": "AAPL", "timeframe": "1d", "period": "1mo"},
        )

    def test_act_missing_model_id(self) -> None:
        resp = self.client.post("/api/rl/act", json={"symbol": "AAPL"})
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
