"""
HTTP-level tests for the newly-wired ai_models integration routes:
POST /api/portfolio-value-prediction (risk_service) and
POST /api/trade-from-model, POST /api/trade-from-signal (execution_service).

Unlike backend/tests/test_integration.py, which mocks `requests` and calls
it directly (never touching the real Flask apps), these tests drive the
actual `app.py` modules through Flask's test client, so a wiring mistake in
the route itself (wrong method name, missing registration) would fail here.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("MODEL_REGISTRY_PATH", "/tmp/test_ai_integration_routes")


class TestPortfolioValuePredictionRoute(unittest.TestCase):
    """POST /api/portfolio-value-prediction on the real risk_service app"""

    @classmethod
    def setUpClass(cls) -> None:
        import backend.risk_service.app as risk_app

        cls.client = risk_app.app.test_client()

    def test_missing_portfolio(self) -> None:
        resp = self.client.post(
            "/api/portfolio-value-prediction", json={"model_id": "m1"}
        )
        self.assertEqual(resp.status_code, 400)

    def test_missing_model_id(self) -> None:
        resp = self.client.post(
            "/api/portfolio-value-prediction",
            json={"portfolio": {"id": "p1", "positions": [], "cash": 100}},
        )
        self.assertEqual(resp.status_code, 400)

    def test_success(self) -> None:
        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = {
            "symbol": "AAPL",
            "prediction": {"average": 155.0},
        }
        with patch("requests.get", return_value=fake_resp):
            resp = self.client.post(
                "/api/portfolio-value-prediction",
                json={
                    "portfolio": {
                        "id": "p1",
                        "cash": 1000.0,
                        "positions": [
                            {
                                "symbol": "AAPL",
                                "quantity": 10,
                                "current_price": 150.0,
                            }
                        ],
                    },
                    "model_id": "m1",
                },
            )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body["portfolio_id"], "p1")
        self.assertEqual(body["current_value"], 2500.0)
        self.assertEqual(body["predicted_value"], 2550.0)


class TestTradeFromModelRoute(unittest.TestCase):
    """POST /api/trade-from-model and /api/trade-from-signal on the real
    execution_service app"""

    @classmethod
    def setUpClass(cls) -> None:
        import backend.execution_service.app as exec_app

        cls.client = exec_app.app.test_client()

    def test_trade_from_model_missing_fields(self) -> None:
        resp = self.client.post("/api/trade-from-model", json={"symbol": "AAPL"})
        self.assertEqual(resp.status_code, 400)

    def test_trade_from_model_bullish_prediction_executes(self) -> None:
        fake_predict = MagicMock(status_code=200)
        fake_predict.json.return_value = {
            "prediction": {
                "average": 160.0,
                "direction": "bullish",
                "change_percent": 4.5,
            }
        }
        fake_order = MagicMock(status_code=201)
        fake_order.json.return_value = {"id": "order_1"}
        fake_broker = MagicMock(status_code=200)
        fake_broker.json.return_value = {"status": "filled"}

        def fake_post(url, json=None, **kwargs):
            if "predict" in url:
                return fake_predict
            if "orders" in url:
                return fake_order
            return fake_broker

        with patch("requests.post", side_effect=fake_post):
            resp = self.client.post(
                "/api/trade-from-model",
                json={"model_id": "m1", "symbol": "AAPL", "portfolio_id": "p1"},
            )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body["signal"]["type"], "buy")
        self.assertEqual(body["order_id"], "order_1")

    def test_trade_from_model_neutral_prediction_no_action(self) -> None:
        fake_predict = MagicMock(status_code=200)
        fake_predict.json.return_value = {
            "prediction": {
                "average": 150.1,
                "direction": "neutral",
                "change_percent": 0.05,
            }
        }
        with patch("requests.post", return_value=fake_predict):
            resp = self.client.post(
                "/api/trade-from-model",
                json={"model_id": "m1", "symbol": "AAPL", "portfolio_id": "p1"},
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "no_action")

    def test_trade_from_signal_missing_fields(self) -> None:
        resp = self.client.post("/api/trade-from-signal", json={})
        self.assertEqual(resp.status_code, 400)

    def test_trade_from_signal_executes(self) -> None:
        fake_order = MagicMock(status_code=201)
        fake_order.json.return_value = {"id": "order_2"}
        fake_broker = MagicMock(status_code=200)
        fake_broker.json.return_value = {"status": "filled"}

        def fake_post(url, json=None, **kwargs):
            return fake_order if "orders" in url else fake_broker

        with patch("requests.post", side_effect=fake_post):
            resp = self.client.post(
                "/api/trade-from-signal",
                json={
                    "signal": {"symbol": "AAPL", "type": "buy", "strength": 0.8},
                    "portfolio_id": "p1",
                },
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["order_id"], "order_2")


if __name__ == "__main__":
    unittest.main()
