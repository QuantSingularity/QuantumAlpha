"""
HTTP-level tests for backend/risk_service/app.py.

Previously /api/risk-metrics, /api/stress-test, and /api/calculate-position
validated requests with schemas whose fields (portfolio_id, risk_metrics,
confidence_level, lookback_period, signal_strength, portfolio_value,
risk_tolerance, scenarios) didn't match what the route handlers actually
read off the validated data, and some of those handlers called
RiskCalculator/StressTesting methods that didn't exist at all
(calculate_risk_metrics, get_portfolio_risk, get_risk_alerts,
run_stress_tests). These tests drive the real Flask app end-to-end so a
schema/handler/method mismatch fails here instead of only at request time
in production.
"""

import unittest
from unittest.mock import MagicMock, patch

import numpy as np


class TestRiskServiceRoutes(unittest.TestCase):
    """HTTP-level tests for the real risk_service Flask app"""

    @classmethod
    def setUpClass(cls) -> None:
        import backend.risk_service.app as risk_app

        cls.risk_app = risk_app
        cls.client = risk_app.app.test_client()

    def setUp(self) -> None:
        self.portfolio = {
            "id": "p1",
            "cash": 10000.0,
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "current_price": 160.0,
                    "entry_price": 150.0,
                },
                {
                    "symbol": "MSFT",
                    "quantity": 50,
                    "current_price": 260.0,
                    "entry_price": 250.0,
                },
            ],
        }
        self.fake_returns = np.random.normal(0.0005, 0.02, 252)

    def _patched_calculator(self):
        return patch.multiple(
            self.risk_app.risk_calculator,
            _get_market_data=MagicMock(return_value={}),
            _compute_portfolio_returns=MagicMock(return_value=self.fake_returns),
        )

    def test_risk_metrics_success(self) -> None:
        with self._patched_calculator():
            resp = self.client.post(
                "/api/risk-metrics",
                json={"portfolio": self.portfolio, "confidence_levels": [0.95, 0.99]},
            )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body["portfolio_id"], "p1")
        self.assertIn("0.95", body["var"])
        self.assertIn("0.99", body["var"])

    def test_risk_metrics_missing_portfolio(self) -> None:
        resp = self.client.post("/api/risk-metrics", json={})
        self.assertEqual(resp.status_code, 400)

    def test_risk_metrics_invalid_position(self) -> None:
        """A position missing a required field (current_price) should be
        rejected by the nested PortfolioStateSchema, not reach the
        calculator and fail with a confusing KeyError."""
        resp = self.client.post(
            "/api/risk-metrics",
            json={
                "portfolio": {
                    "id": "p1",
                    "cash": 100,
                    "positions": [{"symbol": "AAPL", "quantity": 1}],
                }
            },
        )
        self.assertEqual(resp.status_code, 400)

    def test_portfolio_risk_success(self) -> None:
        with self._patched_calculator():
            resp = self.client.post(
                "/api/portfolio-risk", json={"portfolio": self.portfolio}
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["portfolio_id"], "p1")

    def test_portfolio_risk_missing_portfolio(self) -> None:
        resp = self.client.post("/api/portfolio-risk", json={})
        self.assertEqual(resp.status_code, 400)

    def test_risk_alerts_success(self) -> None:
        with self._patched_calculator():
            resp = self.client.post(
                "/api/risk-alerts",
                json={
                    "portfolio": self.portfolio,
                    "concentration_threshold_percent": 10.0,
                },
            )
        self.assertEqual(resp.status_code, 200)
        alerts = resp.get_json()["alerts"]
        self.assertTrue(any(a["type"] == "concentration" for a in alerts))

    def test_stress_test_historical(self) -> None:
        with patch.object(
            self.risk_app.stress_testing, "_get_historical_data", return_value={}
        ):
            resp = self.client.post(
                "/api/stress-test",
                json={"portfolio": self.portfolio, "scenario_name": "covid_crash_2020"},
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["scenario"], "covid_crash_2020")

    def test_stress_test_custom(self) -> None:
        resp = self.client.post(
            "/api/stress-test",
            json={
                "portfolio": self.portfolio,
                "scenario_name": "custom",
                "shocks": {"AAPL": -0.2},
            },
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        aapl = next(p for p in body["positions"] if p["symbol"] == "AAPL")
        self.assertAlmostEqual(aapl["change_percent"], -20.0)

    def test_stress_test_custom_requires_shocks(self) -> None:
        resp = self.client.post(
            "/api/stress-test",
            json={"portfolio": self.portfolio, "scenario_name": "custom"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_stress_test_invalid_scenario_name(self) -> None:
        resp = self.client.post(
            "/api/stress-test",
            json={"portfolio": self.portfolio, "scenario_name": "not_a_real_scenario"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_calculate_position_risk_percent(self) -> None:
        resp = self.client.post(
            "/api/calculate-position",
            json={
                "portfolio": self.portfolio,
                "symbol": "GOOGL",
                "entry_price": 2800.0,
                "stop_price": 2700.0,
                "risk_percent": 0.01,
                "side": "buy",
            },
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body["method"], "risk")
        self.assertEqual(body["symbol"], "GOOGL")
        self.assertEqual(body["stop_price"], 2700.0)

    def test_calculate_position_risk_amount(self) -> None:
        resp = self.client.post(
            "/api/calculate-position",
            json={
                "portfolio": self.portfolio,
                "symbol": "GOOGL",
                "entry_price": 2800.0,
                "stop_price": 2700.0,
                "risk_amount": 260.0,
                "side": "buy",
            },
        )
        self.assertEqual(resp.status_code, 200)

    def test_calculate_position_invalid_stop_for_buy(self) -> None:
        """Schema business-rule validation: stop_price must be below
        entry_price for a buy order."""
        resp = self.client.post(
            "/api/calculate-position",
            json={
                "portfolio": self.portfolio,
                "symbol": "GOOGL",
                "entry_price": 2700.0,
                "stop_price": 2800.0,
                "risk_percent": 0.01,
                "side": "buy",
            },
        )
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
