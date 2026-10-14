import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("MODEL_REGISTRY_PATH", "/tmp/test_ai_integration_routes")


class TestPortfolioValuePredictionRoute(unittest.TestCase):

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
            if url.endswith("/api/orders"):
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
            return fake_order if url.endswith("/api/orders") else fake_broker

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


class TestTradingServiceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import backend.execution_service.app as exec_app

        cls.client = exec_app.app.test_client()

    def test_hold_signal_does_not_trade(self) -> None:
        with patch("requests.post") as mock_post:
            resp = self.client.post(
                "/api/trade-from-signal",
                json={
                    "signal": {"symbol": "AAPL", "type": "hold", "price": 10.0},
                    "portfolio_id": "p1",
                },
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "no_action")
        mock_post.assert_not_called()

    def test_order_and_broker_urls_and_timeouts(self) -> None:
        fake_order = MagicMock(status_code=201)
        fake_order.json.return_value = {"id": "o1"}
        fake_broker = MagicMock(status_code=200)
        fake_broker.json.return_value = {"status": "filled"}
        calls = []

        def fake_post(url, json=None, **kwargs):
            calls.append((url, kwargs))
            return fake_order if url.endswith("/api/orders") else fake_broker

        with patch("requests.post", side_effect=fake_post):
            resp = self.client.post(
                "/api/trade-from-signal",
                json={
                    "signal": {
                        "symbol": "AAPL",
                        "type": "sell",
                        "price": 100.0,
                        "strength": 0.5,
                    },
                    "portfolio_id": "p1",
                },
            )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(calls[0][0].endswith("/api/orders"))
        self.assertTrue(calls[1][0].endswith("/orders"))
        self.assertTrue(all("timeout" in kw for _, kw in calls))
        self.assertEqual(resp.get_json()["status"], "filled")

    def test_ai_prediction_request_has_timeout_and_no_legacy_period(self) -> None:
        fake_predict = MagicMock(status_code=200)
        fake_predict.json.return_value = {
            "latest_price": 100.0,
            "prediction": {"direction": "neutral", "change_percent": 0.1},
        }
        with patch("requests.post", return_value=fake_predict) as mock_post:
            self.client.post(
                "/api/trade-from-model",
                json={"model_id": "m1", "symbol": "AAPL", "portfolio_id": "p1"},
            )
        _, kwargs = mock_post.call_args
        self.assertIn("timeout", kwargs)
        self.assertNotIn("period", kwargs["json"])
