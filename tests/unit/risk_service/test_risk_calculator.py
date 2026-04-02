"""
Unit tests for the Risk Service's Risk Calculator.
"""

import os
import sys
import unittest
from typing import Any
from unittest.mock import MagicMock

import numpy as np

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
try:
    from backend.common.exceptions import ServiceError, ValidationError
    from backend.risk_service.risk_calculator import RiskCalculator
except ImportError:

    class RiskCalculator:
        pass

    class ValidationError(Exception):
        pass

    class ServiceError(Exception):
        pass


class TestRiskCalculator(unittest.TestCase):
    """Unit tests for RiskCalculator class."""

    def setUp(self) -> Any:
        """Set up test fixtures."""
        self.config_manager = MagicMock()
        self.config_manager.get_config.return_value = {
            "risk_service": {
                "default_risk_free_rate": 0.02,
                "default_confidence_level": 0.95,
                "max_position_size": 0.1,
                "max_portfolio_var": 0.05,
            }
        }
        self.db_manager = MagicMock()
        self.sample_returns = np.array(
            [0.01, -0.02, 0.005, 0.008, -0.01, 0.02, -0.015, 0.012, -0.005, 0.018]
        )
        self.sample_equity_curve = np.array(
            [100000, 101000, 99000, 99500, 100300, 99200, 101000, 99500, 100500, 102000]
        )
        self.sample_portfolio = [
            {
                "symbol": "AAPL",
                "quantity": 100,
                "entry_price": 150.0,
                "current_price": 155.0,
            },
            {
                "symbol": "MSFT",
                "quantity": 50,
                "entry_price": 250.0,
                "current_price": 260.0,
            },
        ]
        self.sample_position_returns = {
            "AAPL": np.array([0.01, -0.015, 0.008, 0.012, -0.005]),
            "MSFT": np.array([0.015, -0.01, 0.005, 0.02, -0.008]),
        }
        self.risk_calculator = RiskCalculator(self.config_manager, self.db_manager)

    def test_init(self) -> Any:
        """Test RiskCalculator initialization."""
        risk_calculator = RiskCalculator(self.config_manager, self.db_manager)
        self.assertEqual(risk_calculator.config_manager, self.config_manager)
        self.assertEqual(risk_calculator.db_manager, self.db_manager)
        self.assertEqual(risk_calculator.default_risk_free_rate, 0.02)
        self.assertEqual(risk_calculator.default_confidence_level, 0.95)
        self.assertEqual(risk_calculator.max_position_size, 0.1)
        self.assertEqual(risk_calculator.max_portfolio_var, 0.05)

    def test_calculate_portfolio_risk(self) -> Any:
        """Test portfolio risk calculation."""
        self.risk_calculator._get_historical_data = MagicMock(
            return_value=self.sample_returns
        )
        risk = self.risk_calculator.calculate_portfolio_risk(
            portfolio_id="portfolio_1234567890",
            risk_metrics=[
                "var",
                "cvar",
                "sharpe_ratio",
                "sortino_ratio",
                "max_drawdown",
            ],
        )
        self.assertIsInstance(risk, dict)
        self.assertEqual(risk["portfolio_id"], "portfolio_1234567890")
        self.assertIn("var", risk)
        self.assertIn("cvar", risk)
        self.assertIn("sharpe_ratio", risk)
        self.assertIn("sortino_ratio", risk)
        self.assertIn("max_drawdown", risk)
        self.assertIn("timestamp", risk)

    def test_calculate_portfolio_risk_invalid_metrics(self) -> Any:
        """Test portfolio risk calculation with invalid metrics."""
        with self.assertRaises(ValidationError):
            self.risk_calculator.calculate_portfolio_risk(
                portfolio_id="portfolio_1234567890", risk_metrics=["invalid_metric"]
            )

    def test_calculate_position_risk(self) -> Any:
        """Test position risk calculation."""
        self.risk_calculator._get_historical_data = MagicMock(
            return_value=self.sample_returns
        )
        risk = self.risk_calculator.calculate_position_risk(
            symbol="AAPL",
            quantity=100,
            entry_price=150.0,
            current_price=155.0,
            risk_metrics=[
                "var",
                "cvar",
                "sharpe_ratio",
                "sortino_ratio",
                "max_drawdown",
            ],
        )
        self.assertIsInstance(risk, dict)
        self.assertEqual(risk["symbol"], "AAPL")
        self.assertEqual(risk["quantity"], 100)
        self.assertEqual(risk["entry_price"], 150.0)
        self.assertEqual(risk["current_price"], 155.0)
        self.assertIn("var", risk)
        self.assertIn("cvar", risk)
        self.assertIn("sharpe_ratio", risk)
        self.assertIn("sortino_ratio", risk)
        self.assertIn("max_drawdown", risk)
        self.assertIn("timestamp", risk)

    def test_calculate_position_risk_invalid_metrics(self) -> Any:
        """Test position risk calculation with invalid metrics."""
        with self.assertRaises(ValidationError):
            self.risk_calculator.calculate_position_risk(
                symbol="AAPL",
                quantity=100,
                entry_price=150.0,
                current_price=155.0,
                risk_metrics=["invalid_metric"],
            )

    def test_calculate_position_size(self) -> Any:
        """Test position size calculation."""
        size = self.risk_calculator.calculate_position_size(
            symbol="AAPL",
            portfolio_value=100000.0,
            risk_per_trade=0.01,
            stop_loss_percent=0.05,
        )
        self.assertIsInstance(size, dict)
        self.assertEqual(size["symbol"], "AAPL")
        self.assertIn("size", size)
        self.assertIn("value", size)
        self.assertIn("max_loss", size)

    def test_calculate_position_size_invalid_risk(self) -> Any:
        """Test position size calculation with invalid risk."""
        with self.assertRaises(ValidationError):
            self.risk_calculator.calculate_position_size(
                symbol="AAPL",
                portfolio_value=100000.0,
                risk_per_trade=0.5,
                stop_loss_percent=0.05,
            )

    def test_calculate_position_size_invalid_stop_loss(self) -> Any:
        """Test position size calculation with invalid stop loss."""
        with self.assertRaises(ValidationError):
            self.risk_calculator.calculate_position_size(
                symbol="AAPL",
                portfolio_value=100000.0,
                risk_per_trade=0.01,
                stop_loss_percent=0.0,
            )

    def test_calculate_var(self) -> Any:
        """Test Value at Risk calculation."""
        var_95 = self.risk_calculator._calculate_var(
            self.sample_returns, confidence_level=0.95
        )
        var_99 = self.risk_calculator._calculate_var(
            self.sample_returns, confidence_level=0.99
        )
        self.assertIsInstance(var_95, float)
        self.assertIsInstance(var_99, float)
        self.assertGreater(var_95, 0)
        self.assertGreater(var_99, 0)
        self.assertGreaterEqual(var_99, var_95)

    def test_calculate_cvar(self) -> Any:
        """Test Conditional Value at Risk calculation."""
        cvar_95 = self.risk_calculator._calculate_cvar(
            self.sample_returns, confidence_level=0.95
        )
        self.assertIsInstance(cvar_95, float)
        self.assertGreater(cvar_95, 0)
        var_95 = self.risk_calculator._calculate_var(
            self.sample_returns, confidence_level=0.95
        )
        self.assertGreaterEqual(cvar_95, var_95)

    def test_calculate_sharpe_ratio(self) -> Any:
        """Test Sharpe ratio calculation."""
        sharpe = self.risk_calculator._calculate_sharpe_ratio(
            self.sample_returns, risk_free_rate=0.0
        )
        sharpe_custom = self.risk_calculator._calculate_sharpe_ratio(
            self.sample_returns, risk_free_rate=0.02
        )
        self.assertIsInstance(sharpe, float)
        self.assertIsInstance(sharpe_custom, float)

    def test_calculate_sortino_ratio(self) -> Any:
        """Test Sortino ratio calculation."""
        sortino = self.risk_calculator._calculate_sortino_ratio(
            self.sample_returns, risk_free_rate=0.0
        )
        sortino_custom = self.risk_calculator._calculate_sortino_ratio(
            self.sample_returns, risk_free_rate=0.02
        )
        self.assertIsInstance(sortino, float)
        self.assertIsInstance(sortino_custom, float)

    def test_calculate_max_drawdown(self) -> Any:
        """Test maximum drawdown calculation."""
        max_dd = self.risk_calculator._calculate_max_drawdown(self.sample_returns)
        self.assertIsInstance(max_dd, float)
        self.assertGreaterEqual(max_dd, 0)
        self.assertLessEqual(max_dd, 1.0)

    def test_calculate_portfolio_returns(self) -> Any:
        """Test portfolio returns calculation."""
        returns = self.risk_calculator._calculate_portfolio_returns(
            portfolio=self.sample_portfolio,
            position_returns=self.sample_position_returns,
        )
        self.assertIsInstance(returns, np.ndarray)
        self.assertEqual(len(returns), 5)

    def test_calculate_returns(self) -> Any:
        """Test returns calculation."""
        data = [
            {"close": 100.0},
            {"close": 102.0},
            {"close": 101.0},
            {"close": 103.0},
            {"close": 105.0},
        ]
        returns = self.risk_calculator._calculate_returns(data)
        self.assertIsInstance(returns, np.ndarray)
        self.assertEqual(len(returns), 4)
        np.testing.assert_almost_equal(
            returns, np.array([0.02, -0.0098, 0.0198, 0.0194]), decimal=4
        )

    def test_get_historical_data(self) -> Any:
        """Test historical data retrieval."""
        mock_session = MagicMock()
        self.db_manager.get_postgres_session.return_value = mock_session
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            {"timestamp": "2023-01-01T00:00:00Z", "close": 100.0, "volume": 1000000},
            {"timestamp": "2023-01-02T00:00:00Z", "close": 102.0, "volume": 1100000},
            {"timestamp": "2023-01-03T00:00:00Z", "close": 101.0, "volume": 900000},
            {"timestamp": "2023-01-04T00:00:00Z", "close": 103.0, "volume": 1200000},
            {"timestamp": "2023-01-05T00:00:00Z", "close": 105.0, "volume": 1300000},
        ]
        mock_session.execute.return_value = mock_result
        data = self.risk_calculator._get_historical_data(symbol="AAPL", days=30)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 5)
        self.assertEqual(data[0]["close"], 100.0)
        self.assertEqual(data[4]["close"], 105.0)

    def test_get_historical_data_empty(self) -> Any:
        """Test historical data retrieval with empty result."""
        mock_session = MagicMock()
        self.db_manager.get_postgres_session.return_value = mock_session
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result
        with self.assertRaises(ValidationError):
            self.risk_calculator._get_historical_data(symbol="AAPL", days=30)

    def test_generate_synthetic_data(self) -> Any:
        """Test synthetic data generation."""
        data = self.risk_calculator._generate_synthetic_data(symbol="AAPL", days=30)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 30)
        self.assertEqual(data[0]["symbol"], "AAPL")
        self.assertIn("timestamp", data[0])
        self.assertIn("open", data[0])
        self.assertIn("high", data[0])
        self.assertIn("low", data[0])
        self.assertIn("close", data[0])
        self.assertIn("volume", data[0])


if __name__ == "__main__":
    unittest.main()
