"""
Unit tests for the Risk Service.
"""

import unittest
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
from backend.common import ValidationError
from backend.risk_service.position_sizing import PositionSizing
from backend.risk_service.risk_calculator import RiskCalculator
from backend.risk_service.stress_testing import StressTesting


class TestRiskCalculator(unittest.TestCase):
    """Test cases for RiskCalculator"""

    def setUp(self) -> None:
        """Set up test environment"""
        self.config_manager = MagicMock()
        self.config_manager.get.return_value = "test_value"
        self.db_manager = MagicMock()
        self.risk_calculator = RiskCalculator(self.config_manager, self.db_manager)
        self.portfolio = {
            "id": "portfolio1",
            "name": "Test Portfolio",
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "entry_price": 150.0,
                    "current_price": 160.0,
                },
                {
                    "symbol": "MSFT",
                    "quantity": 50,
                    "entry_price": 250.0,
                    "current_price": 260.0,
                },
                {
                    "symbol": "GOOGL",
                    "quantity": 20,
                    "entry_price": 2800.0,
                    "current_price": 2900.0,
                },
            ],
            "cash": 10000.0,
        }
        self.market_data = {
            "AAPL": pd.DataFrame(
                {
                    "date": pd.date_range(start="2023-01-01", periods=100),
                    "close": np.random.normal(150, 10, 100),
                    "volume": np.random.randint(1000000, 10000000, 100),
                }
            ),
            "MSFT": pd.DataFrame(
                {
                    "date": pd.date_range(start="2023-01-01", periods=100),
                    "close": np.random.normal(250, 15, 100),
                    "volume": np.random.randint(1000000, 10000000, 100),
                }
            ),
            "GOOGL": pd.DataFrame(
                {
                    "date": pd.date_range(start="2023-01-01", periods=100),
                    "close": np.random.normal(2800, 100, 100),
                    "volume": np.random.randint(1000000, 10000000, 100),
                }
            ),
        }

    def test_calculate_portfolio_value(self) -> None:
        """Test portfolio value calculation"""
        result = self.risk_calculator.calculate_portfolio_value(self.portfolio)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], "portfolio1")
        self.assertTrue("total_value" in result)
        self.assertTrue("positions_value" in result)
        self.assertTrue("cash" in result)
        expected_positions_value = 100 * 160.0 + 50 * 260.0 + 20 * 2900.0
        expected_total_value = expected_positions_value + 10000.0
        self.assertEqual(result["positions_value"], expected_positions_value)
        self.assertEqual(result["cash"], 10000.0)
        self.assertEqual(result["total_value"], expected_total_value)

    def test_calculate_portfolio_returns(self) -> None:
        """Test portfolio returns calculation"""
        result = self.risk_calculator.calculate_portfolio_returns(self.portfolio)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], "portfolio1")
        self.assertTrue("total_return" in result)
        self.assertTrue("total_return_percent" in result)
        self.assertTrue("positions_return" in result)
        expected_positions_return = (
            100 * (160.0 - 150.0) + 50 * (260.0 - 250.0) + 20 * (2900.0 - 2800.0)
        )
        expected_positions_cost = 100 * 150.0 + 50 * 250.0 + 20 * 2800.0
        expected_total_return_percent = (
            expected_positions_return / expected_positions_cost * 100
        )
        self.assertEqual(result["positions_return"], expected_positions_return)
        self.assertEqual(result["total_return"], expected_positions_return)
        self.assertAlmostEqual(
            result["total_return_percent"], expected_total_return_percent
        )

    def test_calculate_var(self) -> None:
        """Test Value at Risk calculation"""
        self.risk_calculator._get_market_data = MagicMock(return_value=self.market_data)
        result = self.risk_calculator.calculate_var(
            portfolio=self.portfolio, confidence_level=0.95, time_horizon=1
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], "portfolio1")
        self.assertTrue("var" in result)
        self.assertTrue("var_percent" in result)
        self.assertTrue("confidence_level" in result)
        self.assertTrue("time_horizon" in result)
        self.assertTrue(result["var"] > 0)
        self.assertTrue(0 < result["var_percent"] < 100)
        self.assertEqual(result["confidence_level"], 0.95)
        self.assertEqual(result["time_horizon"], 1)

    def test_calculate_var_invalid_confidence(self) -> None:
        """Test VaR calculation with invalid confidence level"""
        with self.assertRaises(ValidationError):
            self.risk_calculator.calculate_var(
                portfolio=self.portfolio, confidence_level=1.5, time_horizon=1
            )
        with self.assertRaises(ValidationError):
            self.risk_calculator.calculate_var(
                portfolio=self.portfolio, confidence_level=-0.1, time_horizon=1
            )

    def test_calculate_var_invalid_horizon(self) -> None:
        """Test VaR calculation with invalid time horizon"""
        with self.assertRaises(ValidationError):
            self.risk_calculator.calculate_var(
                portfolio=self.portfolio, confidence_level=0.95, time_horizon=0
            )
        with self.assertRaises(ValidationError):
            self.risk_calculator.calculate_var(
                portfolio=self.portfolio, confidence_level=0.95, time_horizon=-1
            )

    def test_calculate_expected_shortfall(self) -> None:
        """Test Expected Shortfall calculation"""
        self.risk_calculator._get_market_data = MagicMock(return_value=self.market_data)
        result = self.risk_calculator.calculate_expected_shortfall(
            portfolio=self.portfolio, confidence_level=0.95, time_horizon=1
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], "portfolio1")
        self.assertTrue("es" in result)
        self.assertTrue("es_percent" in result)
        self.assertTrue("confidence_level" in result)
        self.assertTrue("time_horizon" in result)
        self.assertTrue(result["es"] > 0)
        self.assertTrue(0 < result["es_percent"] < 100)
        self.assertEqual(result["confidence_level"], 0.95)
        self.assertEqual(result["time_horizon"], 1)

    def test_calculate_sharpe_ratio(self) -> None:
        """Test Sharpe Ratio calculation"""
        self.risk_calculator._get_market_data = MagicMock(return_value=self.market_data)
        result = self.risk_calculator.calculate_sharpe_ratio(
            portfolio=self.portfolio, risk_free_rate=0.02, period="1y"
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], "portfolio1")
        self.assertTrue("sharpe_ratio" in result)
        self.assertTrue("annualized_return" in result)
        self.assertTrue("annualized_volatility" in result)
        self.assertTrue("risk_free_rate" in result)
        self.assertTrue(isinstance(result["sharpe_ratio"], float))
        self.assertTrue(isinstance(result["annualized_return"], float))
        self.assertTrue(isinstance(result["annualized_volatility"], float))
        self.assertEqual(result["risk_free_rate"], 0.02)

    def test_calculate_beta(self) -> None:
        """Test Beta calculation"""
        self.risk_calculator._get_market_data = MagicMock(return_value=self.market_data)
        benchmark_data = pd.DataFrame(
            {
                "date": pd.date_range(start="2023-01-01", periods=100),
                "close": np.random.normal(4000, 100, 100),
            }
        )
        self.risk_calculator._get_benchmark_data = MagicMock(
            return_value=benchmark_data
        )
        result = self.risk_calculator.calculate_beta(
            portfolio=self.portfolio, benchmark="SPY", period="1y"
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], "portfolio1")
        self.assertTrue("beta" in result)
        self.assertTrue("benchmark" in result)
        self.assertTrue(isinstance(result["beta"], float))
        self.assertEqual(result["benchmark"], "SPY")


class TestPositionSizing(unittest.TestCase):
    """Test cases for PositionSizing"""

    def setUp(self) -> None:
        """Set up test environment"""
        self.config_manager = MagicMock()
        self.config_manager.get.return_value = "test_value"
        self.db_manager = MagicMock()
        self.position_sizing = PositionSizing(self.config_manager, self.db_manager)
        self.portfolio = {
            "id": "portfolio1",
            "name": "Test Portfolio",
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "entry_price": 150.0,
                    "current_price": 160.0,
                },
                {
                    "symbol": "MSFT",
                    "quantity": 50,
                    "entry_price": 250.0,
                    "current_price": 260.0,
                },
            ],
            "cash": 10000.0,
        }

    def test_calculate_position_size_fixed(self) -> None:
        """Test fixed position size calculation"""
        result = self.position_sizing.calculate_position_size(
            portfolio=self.portfolio,
            symbol="GOOGL",
            price=2800.0,
            method="fixed",
            params={"amount": 5000.0},
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], "GOOGL")
        self.assertEqual(result["price"], 2800.0)
        self.assertEqual(result["method"], "fixed")
        self.assertTrue("quantity" in result)
        self.assertTrue("value" in result)
        expected_quantity = 5000.0 / 2800.0
        expected_value = expected_quantity * 2800.0
        self.assertAlmostEqual(result["quantity"], expected_quantity)
        self.assertAlmostEqual(result["value"], expected_value)

    def test_calculate_position_size_percent(self) -> None:
        """Test percentage position size calculation"""
        result = self.position_sizing.calculate_position_size(
            portfolio=self.portfolio,
            symbol="GOOGL",
            price=2800.0,
            method="percent",
            params={"percent": 10.0},
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], "GOOGL")
        self.assertEqual(result["price"], 2800.0)
        self.assertEqual(result["method"], "percent")
        self.assertTrue("quantity" in result)
        self.assertTrue("value" in result)
        portfolio_value = 100 * 160.0 + 50 * 260.0 + 10000.0
        expected_value = portfolio_value * 0.1
        expected_quantity = expected_value / 2800.0
        self.assertAlmostEqual(result["quantity"], expected_quantity)
        self.assertAlmostEqual(result["value"], expected_value)

    def test_calculate_position_size_risk(self) -> None:
        """Test risk-based position size calculation"""
        result = self.position_sizing.calculate_position_size(
            portfolio=self.portfolio,
            symbol="GOOGL",
            price=2800.0,
            method="risk",
            params={"risk_percent": 1.0, "stop_loss_percent": 5.0},
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], "GOOGL")
        self.assertEqual(result["price"], 2800.0)
        self.assertEqual(result["method"], "risk")
        self.assertTrue("quantity" in result)
        self.assertTrue("value" in result)
        self.assertTrue("stop_loss" in result)
        portfolio_value = 100 * 160.0 + 50 * 260.0 + 10000.0
        risk_amount = portfolio_value * 0.01
        stop_loss = 2800.0 * 0.95
        expected_quantity = risk_amount / (2800.0 - stop_loss)
        expected_value = expected_quantity * 2800.0
        self.assertAlmostEqual(result["quantity"], expected_quantity)
        self.assertAlmostEqual(result["value"], expected_value)
        self.assertEqual(result["stop_loss"], stop_loss)

    def test_calculate_position_size_kelly(self) -> None:
        """Test Kelly Criterion position size calculation"""
        result = self.position_sizing.calculate_position_size(
            portfolio=self.portfolio,
            symbol="GOOGL",
            price=2800.0,
            method="kelly",
            params={"win_rate": 0.6, "win_loss_ratio": 2.0},
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], "GOOGL")
        self.assertEqual(result["price"], 2800.0)
        self.assertEqual(result["method"], "kelly")
        self.assertTrue("quantity" in result)
        self.assertTrue("value" in result)
        self.assertTrue("kelly_percent" in result)
        portfolio_value = 100 * 160.0 + 50 * 260.0 + 10000.0
        kelly_percent = 0.6 - (1 - 0.6) / 2.0
        expected_value = portfolio_value * kelly_percent
        expected_quantity = expected_value / 2800.0
        self.assertAlmostEqual(result["quantity"], expected_quantity)
        self.assertAlmostEqual(result["value"], expected_value)
        self.assertEqual(result["kelly_percent"], kelly_percent)

    def test_calculate_position_size_invalid_method(self) -> None:
        """Test position size calculation with invalid method"""
        with self.assertRaises(ValidationError):
            self.position_sizing.calculate_position_size(
                portfolio=self.portfolio,
                symbol="GOOGL",
                price=2800.0,
                method="invalid_method",
                params={},
            )

    def test_calculate_position_size_missing_params(self) -> None:
        """Test position size calculation with missing parameters"""
        with self.assertRaises(ValidationError):
            self.position_sizing.calculate_position_size(
                portfolio=self.portfolio,
                symbol="GOOGL",
                price=2800.0,
                method="fixed",
                params={},
            )
        with self.assertRaises(ValidationError):
            self.position_sizing.calculate_position_size(
                portfolio=self.portfolio,
                symbol="GOOGL",
                price=2800.0,
                method="percent",
                params={},
            )
        with self.assertRaises(ValidationError):
            self.position_sizing.calculate_position_size(
                portfolio=self.portfolio,
                symbol="GOOGL",
                price=2800.0,
                method="risk",
                params={"risk_percent": 1.0},
            )
        with self.assertRaises(ValidationError):
            self.position_sizing.calculate_position_size(
                portfolio=self.portfolio,
                symbol="GOOGL",
                price=2800.0,
                method="kelly",
                params={"win_rate": 0.6},
            )

    def test_calculate_position_size_invalid_params(self) -> None:
        """Test position size calculation with invalid parameters"""
        with self.assertRaises(ValidationError):
            self.position_sizing.calculate_position_size(
                portfolio=self.portfolio,
                symbol="GOOGL",
                price=2800.0,
                method="percent",
                params={"percent": 101.0},
            )
        with self.assertRaises(ValidationError):
            self.position_sizing.calculate_position_size(
                portfolio=self.portfolio,
                symbol="GOOGL",
                price=2800.0,
                method="risk",
                params={"risk_percent": 10.0, "stop_loss_percent": 0.0},
            )
        with self.assertRaises(ValidationError):
            self.position_sizing.calculate_position_size(
                portfolio=self.portfolio,
                symbol="GOOGL",
                price=2800.0,
                method="kelly",
                params={"win_rate": 1.1, "win_loss_ratio": 2.0},
            )


class TestStressTesting(unittest.TestCase):
    """Test cases for StressTesting"""

    def setUp(self) -> None:
        """Set up test environment"""
        self.config_manager = MagicMock()
        self.config_manager.get.return_value = "test_value"
        self.db_manager = MagicMock()
        self.stress_testing = StressTesting(self.config_manager, self.db_manager)
        self.portfolio = {
            "id": "portfolio1",
            "name": "Test Portfolio",
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "entry_price": 150.0,
                    "current_price": 160.0,
                },
                {
                    "symbol": "MSFT",
                    "quantity": 50,
                    "entry_price": 250.0,
                    "current_price": 260.0,
                },
                {
                    "symbol": "GOOGL",
                    "quantity": 20,
                    "entry_price": 2800.0,
                    "current_price": 2900.0,
                },
            ],
            "cash": 10000.0,
        }

    def test_run_historical_scenario(self) -> None:
        """Test historical scenario stress test"""
        historical_data = {
            "AAPL": pd.DataFrame(
                {
                    "date": pd.date_range(start="2008-09-01", periods=100),
                    "close": np.linspace(150, 100, 100),
                }
            ),
            "MSFT": pd.DataFrame(
                {
                    "date": pd.date_range(start="2008-09-01", periods=100),
                    "close": np.linspace(250, 200, 100),
                }
            ),
            "GOOGL": pd.DataFrame(
                {
                    "date": pd.date_range(start="2008-09-01", periods=100),
                    "close": np.linspace(2800, 2300, 100),
                }
            ),
        }
        self.stress_testing._get_historical_data = MagicMock(
            return_value=historical_data
        )
        result = self.stress_testing.run_historical_scenario(
            portfolio=self.portfolio,
            scenario="financial_crisis_2008",
            start_date="2008-09-01",
            end_date="2008-12-31",
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], "portfolio1")
        self.assertEqual(result["scenario"], "financial_crisis_2008")
        self.assertTrue("initial_value" in result)
        self.assertTrue("final_value" in result)
        self.assertTrue("change" in result)
        self.assertTrue("change_percent" in result)
        self.assertTrue("positions" in result)
        initial_value = 100 * 160.0 + 50 * 260.0 + 20 * 2900.0 + 10000.0
        final_value = 100 * 100.0 + 50 * 200.0 + 20 * 2300.0 + 10000.0
        change = final_value - initial_value
        change_percent = change / initial_value * 100
        self.assertEqual(result["initial_value"], initial_value)
        self.assertEqual(result["final_value"], final_value)
        self.assertEqual(result["change"], change)
        self.assertEqual(result["change_percent"], change_percent)

    def test_run_monte_carlo_simulation(self) -> None:
        """Test Monte Carlo simulation stress test"""
        result = self.stress_testing.run_monte_carlo_simulation(
            portfolio=self.portfolio,
            num_simulations=100,
            time_horizon=252,
            confidence_level=0.95,
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], "portfolio1")
        self.assertEqual(result["num_simulations"], 100)
        self.assertEqual(result["time_horizon"], 252)
        self.assertEqual(result["confidence_level"], 0.95)
        self.assertTrue("initial_value" in result)
        self.assertTrue("expected_final_value" in result)
        self.assertTrue("var" in result)
        self.assertTrue("var_percent" in result)
        self.assertTrue("expected_return" in result)
        self.assertTrue("expected_volatility" in result)
        self.assertTrue("simulations" in result)
        initial_value = 100 * 160.0 + 50 * 260.0 + 20 * 2900.0 + 10000.0
        self.assertEqual(result["initial_value"], initial_value)
        self.assertTrue(len(result["simulations"]) == 100)

    def test_run_sensitivity_analysis(self) -> None:
        """Test sensitivity analysis stress test"""
        result = self.stress_testing.run_sensitivity_analysis(
            portfolio=self.portfolio,
            factors=[
                {"name": "market_decline", "values": [-10, -20, -30]},
                {"name": "interest_rate", "values": [0.03, 0.04, 0.05]},
            ],
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], "portfolio1")
        self.assertTrue("initial_value" in result)
        self.assertTrue("scenarios" in result)
        initial_value = 100 * 160.0 + 50 * 260.0 + 20 * 2900.0 + 10000.0
        self.assertEqual(result["initial_value"], initial_value)
        self.assertEqual(len(result["scenarios"]), 9)

    def test_run_custom_scenario(self) -> None:
        """Test custom scenario stress test"""
        result = self.stress_testing.run_custom_scenario(
            portfolio=self.portfolio,
            scenario_name="Custom Scenario",
            price_changes={"AAPL": -15.0, "MSFT": -10.0, "GOOGL": -20.0},
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], "portfolio1")
        self.assertEqual(result["scenario_name"], "Custom Scenario")
        self.assertTrue("initial_value" in result)
        self.assertTrue("final_value" in result)
        self.assertTrue("change" in result)
        self.assertTrue("change_percent" in result)
        self.assertTrue("positions" in result)
        initial_value = 100 * 160.0 + 50 * 260.0 + 20 * 2900.0 + 10000.0
        final_value = (
            100 * (160.0 * (1 - 0.15))
            + 50 * (260.0 * (1 - 0.1))
            + 20 * (2900.0 * (1 - 0.2))
            + 10000.0
        )
        change = final_value - initial_value
        change_percent = change / initial_value * 100
        self.assertEqual(result["initial_value"], initial_value)
        self.assertEqual(result["final_value"], final_value)
        self.assertEqual(result["change"], change)
        self.assertEqual(result["change_percent"], change_percent)


if __name__ == "__main__":
    unittest.main()
