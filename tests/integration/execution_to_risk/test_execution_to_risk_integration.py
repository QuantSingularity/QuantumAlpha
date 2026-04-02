"""
Integration tests for execution service to risk service integration.
"""

import os
import sys
import unittest
from typing import Any
from datetime import datetime
from unittest.mock import MagicMock, patch

import requests

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
try:
    from backend.common.exceptions import ServiceError, ValidationError
    from backend.execution_service.order_manager import OrderManager
    from backend.risk_service.position_manager import PositionManager
    from backend.risk_service.risk_calculator import RiskCalculator
except ImportError:

    class OrderManager:
        pass

    class RiskCalculator:
        pass

    class PositionManager:
        pass

    class ValidationError(Exception):
        pass

    class ServiceError(Exception):
        pass


class TestExecutionToRiskIntegration(unittest.TestCase):
    """Integration tests for execution service to risk service integration."""

    def setUp(self) -> Any:
        """Set up test fixtures."""
        self.config_manager = MagicMock()
        self.config_manager.get_config.return_value = {
            "execution_service": {"default_broker": "test_broker", "order_timeout": 60},
            "risk_service": {
                "default_risk_free_rate": 0.02,
                "default_confidence_level": 0.95,
                "max_position_size": 0.1,
                "max_portfolio_var": 0.05,
            },
            "services": {
                "execution_service": {"host": "localhost", "port": 8084},
                "risk_service": {"host": "localhost", "port": 8083},
            },
        }
        self.db_manager = MagicMock()
        self.broker_integration = MagicMock()
        self.sample_order = {
            "id": "order_1234567890",
            "user_id": "user_1234567890",
            "portfolio_id": "portfolio_1234567890",
            "symbol": "AAPL",
            "side": "buy",
            "type": "market",
            "status": "filled",
            "quantity": 100,
            "price": None,
            "filled_quantity": 100,
            "average_fill_price": 150.0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self.sample_execution = {
            "id": "execution_1234567890",
            "order_id": "order_1234567890",
            "price": 150.0,
            "quantity": 100,
            "timestamp": datetime.utcnow().isoformat(),
            "broker_execution_id": "broker_execution_1234567890",
        }
        self.sample_position = {
            "id": "position_1234567890",
            "user_id": "user_1234567890",
            "portfolio_id": "portfolio_1234567890",
            "symbol": "AAPL",
            "quantity": 100,
            "average_entry_price": 150.0,
            "current_price": 155.0,
            "market_value": 15500.0,
            "unrealized_pl": 500.0,
            "unrealized_pl_percent": 3.33,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self.order_manager = OrderManager(
            self.config_manager, self.db_manager, self.broker_integration
        )
        self.risk_calculator = RiskCalculator(self.config_manager, self.db_manager)
        self.position_manager = PositionManager(self.config_manager, self.db_manager)

    def test_order_execution_to_position_creation(self) -> Any:
        """Test order execution to position creation flow."""
        with patch.object(self.order_manager, "get_order") as mock_get_order:
            mock_get_order.return_value = self.sample_order
            order = self.order_manager.get_order("order_1234567890")
            self.assertEqual(order["id"], "order_1234567890")
            self.assertEqual(order["symbol"], "AAPL")
            self.assertEqual(order["side"], "buy")
            self.assertEqual(order["status"], "filled")
            self.assertEqual(order["quantity"], 100)
            self.assertEqual(order["filled_quantity"], 100)
            self.assertEqual(order["average_fill_price"], 150.0)
            with patch.object(
                self.position_manager, "create_or_update_position"
            ) as mock_create_position:
                mock_create_position.return_value = self.sample_position
                position = self.position_manager.create_or_update_position(
                    user_id=order["user_id"],
                    portfolio_id=order["portfolio_id"],
                    symbol=order["symbol"],
                    quantity=(
                        order["filled_quantity"]
                        if order["side"] == "buy"
                        else -order["filled_quantity"]
                    ),
                    price=order["average_fill_price"],
                )
                self.assertEqual(position["id"], "position_1234567890")
                self.assertEqual(position["user_id"], "user_1234567890")
                self.assertEqual(position["portfolio_id"], "portfolio_1234567890")
                self.assertEqual(position["symbol"], "AAPL")
                self.assertEqual(position["quantity"], 100)
                self.assertEqual(position["average_entry_price"], 150.0)
                mock_create_position.assert_called_once()
                args, kwargs = mock_create_position.call_args
                self.assertEqual(kwargs["user_id"], "user_1234567890")
                self.assertEqual(kwargs["portfolio_id"], "portfolio_1234567890")
                self.assertEqual(kwargs["symbol"], "AAPL")
                self.assertEqual(kwargs["quantity"], 100)
                self.assertEqual(kwargs["price"], 150.0)

    @patch("requests.post")
    def test_position_creation_to_risk_calculation(self, mock_post: Any) -> Any:
        """Test position creation to risk calculation flow."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "symbol": "AAPL",
            "quantity": 100,
            "entry_price": 150.0,
            "current_price": 155.0,
            "var": 0.05,
            "cvar": 0.07,
            "sharpe_ratio": 1.2,
            "sortino_ratio": 1.5,
            "max_drawdown": 0.15,
            "risk_score": 65,
            "risk_level": "medium",
            "timestamp": datetime.utcnow().isoformat(),
        }
        mock_post.return_value = mock_response
        with patch.object(self.position_manager, "get_position") as mock_get_position:
            mock_get_position.return_value = self.sample_position
            position = self.position_manager.get_position("position_1234567890")
            self.assertEqual(position["id"], "position_1234567890")
            self.assertEqual(position["symbol"], "AAPL")
            self.assertEqual(position["quantity"], 100)
            self.assertEqual(position["average_entry_price"], 150.0)
            self.assertEqual(position["current_price"], 155.0)
            with patch.object(
                self.risk_calculator, "calculate_position_risk"
            ) as mock_risk:
                mock_risk.return_value = {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "entry_price": 150.0,
                    "current_price": 155.0,
                    "var": 0.05,
                    "cvar": 0.07,
                    "sharpe_ratio": 1.2,
                    "sortino_ratio": 1.5,
                    "max_drawdown": 0.15,
                    "risk_score": 65,
                    "risk_level": "medium",
                    "timestamp": datetime.utcnow().isoformat(),
                }
                risk = self.risk_calculator.calculate_position_risk(
                    symbol=position["symbol"],
                    quantity=position["quantity"],
                    entry_price=position["average_entry_price"],
                    current_price=position["current_price"],
                    risk_metrics=[
                        "var",
                        "cvar",
                        "sharpe_ratio",
                        "sortino_ratio",
                        "max_drawdown",
                    ],
                )
                self.assertEqual(risk["symbol"], "AAPL")
                self.assertEqual(risk["quantity"], 100)
                self.assertEqual(risk["entry_price"], 150.0)
                self.assertEqual(risk["current_price"], 155.0)
                self.assertIn("var", risk)
                self.assertIn("cvar", risk)
                self.assertIn("sharpe_ratio", risk)
                self.assertIn("sortino_ratio", risk)
                self.assertIn("max_drawdown", risk)
                self.assertIn("risk_score", risk)
                self.assertIn("risk_level", risk)
                mock_risk.assert_called_once()
                args, kwargs = mock_risk.call_args
                self.assertEqual(kwargs["symbol"], "AAPL")
                self.assertEqual(kwargs["quantity"], 100)
                self.assertEqual(kwargs["entry_price"], 150.0)
                self.assertEqual(kwargs["current_price"], 155.0)

    @patch("requests.get")
    @patch("requests.post")
    def test_execution_service_to_risk_service_api_integration(
        self, mock_post: Any, mock_get: Any
    ) -> Any:
        """Test execution service to risk service API integration."""
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = self.sample_order
        mock_get.return_value = mock_get_response
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "symbol": "AAPL",
            "quantity": 100,
            "entry_price": 150.0,
            "current_price": 155.0,
            "var": 0.05,
            "cvar": 0.07,
            "sharpe_ratio": 1.2,
            "sortino_ratio": 1.5,
            "max_drawdown": 0.15,
            "risk_score": 65,
            "risk_level": "medium",
            "timestamp": datetime.utcnow().isoformat(),
        }
        mock_post.return_value = mock_post_response
        execution_service_url = "http://localhost:8084/api/orders/order_1234567890"
        response = requests.get(execution_service_url)
        self.assertEqual(response.status_code, 200)
        order = response.json()
        self.assertEqual(order["id"], "order_1234567890")
        self.assertEqual(order["symbol"], "AAPL")
        self.assertEqual(order["side"], "buy")
        self.assertEqual(order["status"], "filled")
        risk_service_url = "http://localhost:8083/api/risk/position"
        response = requests.post(
            risk_service_url,
            json={
                "symbol": order["symbol"],
                "quantity": (
                    order["filled_quantity"]
                    if order["side"] == "buy"
                    else -order["filled_quantity"]
                ),
                "entry_price": order["average_fill_price"],
                "current_price": 155.0,
                "risk_metrics": [
                    "var",
                    "cvar",
                    "sharpe_ratio",
                    "sortino_ratio",
                    "max_drawdown",
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        risk = response.json()
        self.assertEqual(risk["symbol"], "AAPL")
        self.assertEqual(risk["quantity"], 100)
        self.assertEqual(risk["entry_price"], 150.0)
        self.assertEqual(risk["current_price"], 155.0)
        self.assertIn("var", risk)
        self.assertIn("cvar", risk)
        self.assertIn("sharpe_ratio", risk)
        self.assertIn("sortino_ratio", risk)
        self.assertIn("max_drawdown", risk)
        self.assertIn("risk_score", risk)
        self.assertIn("risk_level", risk)

    def test_order_execution_to_portfolio_risk_update(self) -> Any:
        """Test order execution to portfolio risk update flow."""
        with patch.object(self.order_manager, "get_order") as mock_get_order:
            mock_get_order.return_value = self.sample_order
            order = self.order_manager.get_order("order_1234567890")
            with patch.object(
                self.position_manager, "create_or_update_position"
            ) as mock_create_position:
                mock_create_position.return_value = self.sample_position
                position = self.position_manager.create_or_update_position(
                    user_id=order["user_id"],
                    portfolio_id=order["portfolio_id"],
                    symbol=order["symbol"],
                    quantity=(
                        order["filled_quantity"]
                        if order["side"] == "buy"
                        else -order["filled_quantity"]
                    ),
                    price=order["average_fill_price"],
                )
                with patch.object(
                    self.position_manager, "get_portfolio_positions"
                ) as mock_get_positions:
                    mock_get_positions.return_value = [
                        self.sample_position,
                        {
                            "id": "position_9876543210",
                            "user_id": "user_1234567890",
                            "portfolio_id": "portfolio_1234567890",
                            "symbol": "MSFT",
                            "quantity": 50,
                            "average_entry_price": 250.0,
                            "current_price": 260.0,
                            "market_value": 13000.0,
                            "unrealized_pl": 500.0,
                            "unrealized_pl_percent": 4.0,
                            "created_at": datetime.utcnow().isoformat(),
                            "updated_at": datetime.utcnow().isoformat(),
                        },
                    ]
                    positions = self.position_manager.get_portfolio_positions(
                        "portfolio_1234567890"
                    )
                    self.assertEqual(len(positions), 2)
                    self.assertEqual(positions[0]["symbol"], "AAPL")
                    self.assertEqual(positions[1]["symbol"], "MSFT")
                    with patch.object(
                        self.risk_calculator, "calculate_portfolio_risk"
                    ) as mock_risk:
                        mock_risk.return_value = {
                            "portfolio_id": "portfolio_1234567890",
                            "total_value": 28500.0,
                            "var": 0.04,
                            "cvar": 0.06,
                            "sharpe_ratio": 1.1,
                            "sortino_ratio": 1.3,
                            "max_drawdown": 0.12,
                            "risk_score": 60,
                            "risk_level": "medium",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                        risk = self.risk_calculator.calculate_portfolio_risk(
                            portfolio_id="portfolio_1234567890",
                            portfolio=positions,
                            risk_metrics=[
                                "var",
                                "cvar",
                                "sharpe_ratio",
                                "sortino_ratio",
                                "max_drawdown",
                            ],
                        )
                        self.assertEqual(risk["portfolio_id"], "portfolio_1234567890")
                        self.assertEqual(risk["total_value"], 28500.0)
                        self.assertIn("var", risk)
                        self.assertIn("cvar", risk)
                        self.assertIn("sharpe_ratio", risk)
                        self.assertIn("sortino_ratio", risk)
                        self.assertIn("max_drawdown", risk)
                        self.assertIn("risk_score", risk)
                        self.assertIn("risk_level", risk)
                        mock_risk.assert_called_once()
                        args, kwargs = mock_risk.call_args
                        self.assertEqual(kwargs["portfolio_id"], "portfolio_1234567890")
                        self.assertEqual(len(kwargs["portfolio"]), 2)

    def test_position_sizing_before_order_creation(self) -> Any:
        """Test position sizing before order creation flow."""
        with patch.object(self.risk_calculator, "calculate_position_size") as mock_size:
            mock_size.return_value = {
                "symbol": "AAPL",
                "size": 100,
                "value": 15000.0,
                "max_loss": 750.0,
            }
            size = self.risk_calculator.calculate_position_size(
                symbol="AAPL",
                portfolio_value=100000.0,
                risk_per_trade=0.01,
                stop_loss_percent=0.05,
            )
            self.assertEqual(size["symbol"], "AAPL")
            self.assertEqual(size["size"], 100)
            self.assertEqual(size["value"], 15000.0)
            self.assertEqual(size["max_loss"], 750.0)
            with patch.object(self.order_manager, "create_order") as mock_create_order:
                mock_create_order.return_value = self.sample_order
                order = self.order_manager.create_order(
                    user_id="user_1234567890",
                    portfolio_id="portfolio_1234567890",
                    symbol=size["symbol"],
                    side="buy",
                    order_type="market",
                    quantity=size["size"],
                )
                self.assertEqual(order["id"], "order_1234567890")
                self.assertEqual(order["symbol"], "AAPL")
                self.assertEqual(order["side"], "buy")
                self.assertEqual(order["quantity"], 100)
                mock_create_order.assert_called_once()
                args, kwargs = mock_create_order.call_args
                self.assertEqual(kwargs["user_id"], "user_1234567890")
                self.assertEqual(kwargs["portfolio_id"], "portfolio_1234567890")
                self.assertEqual(kwargs["symbol"], "AAPL")
                self.assertEqual(kwargs["side"], "buy")
                self.assertEqual(kwargs["quantity"], 100)


if __name__ == "__main__":
    unittest.main()
