from typing import Any

"""
System tests for end-to-end trading workflow.
"""

import os
import sys
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import requests

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
try:
    from backend.ai_engine.model_manager import ModelManager
    from backend.ai_engine.prediction_service import PredictionService
    from backend.common.exceptions import ServiceError, ValidationError
    from backend.data_service.data_processor import DataProcessor
    from backend.execution_service.order_manager import OrderManager
    from backend.risk_service.risk_calculator import RiskCalculator
except ImportError:

    class DataProcessor:
        pass

    class ModelManager:
        pass

    class PredictionService:
        pass

    class RiskCalculator:
        pass

    class OrderManager:
        pass

    class ValidationError(Exception):
        pass

    class ServiceError(Exception):
        pass


class TestEndToEndTradingWorkflow(unittest.TestCase):
    """System tests for end-to-end trading workflow."""

    def setUp(self) -> Any:
        """Set up test fixtures."""
        self.config_manager = MagicMock()
        self.config_manager.get_config.return_value = {
            "data_service": {"cache_dir": "/tmp/cache", "data_dir": "/tmp/data"},
            "ai_engine": {
                "model_dir": "/tmp/models",
                "registry_file": "/tmp/models/registry.json",
            },
            "risk_service": {
                "default_risk_free_rate": 0.02,
                "default_confidence_level": 0.95,
                "max_position_size": 0.1,
                "max_portfolio_var": 0.05,
            },
            "execution_service": {"default_broker": "test_broker", "order_timeout": 60},
            "services": {
                "data_service": {"host": "localhost", "port": 8081},
                "ai_engine": {"host": "localhost", "port": 8082},
                "risk_service": {"host": "localhost", "port": 8083},
                "execution_service": {"host": "localhost", "port": 8084},
            },
        }
        self.db_manager = MagicMock()
        self.broker_integration = MagicMock()
        self.market_data = pd.DataFrame(
            {
                "timestamp": pd.date_range(start="2023-01-01", periods=100),
                "open": np.random.normal(100, 2, 100),
                "high": np.random.normal(102, 2, 100),
                "low": np.random.normal(98, 2, 100),
                "close": np.random.normal(100, 2, 100),
                "volume": np.random.normal(1000000, 100000, 100),
                "symbol": "AAPL",
            }
        )
        self.data_processor = DataProcessor(self.config_manager, self.db_manager)
        self.model_manager = ModelManager(self.config_manager, self.db_manager)
        self.prediction_service = PredictionService(
            self.config_manager, self.db_manager, self.model_manager
        )
        self.risk_calculator = RiskCalculator(self.config_manager, self.db_manager)
        self.order_manager = OrderManager(
            self.config_manager, self.db_manager, self.broker_integration
        )

    @patch("requests.get")
    @patch("requests.post")
    def test_complete_trading_workflow(self, mock_post: Any, mock_get: Any) -> Any:
        """Test complete trading workflow from data to execution."""
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "data": self.market_data.to_dict(orient="records")
        }
        mock_get.return_value = mock_get_response
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "model_id": "model_1234567890",
            "symbol": "AAPL",
            "prediction": {
                "average": 110.0,
                "minimum": 105.0,
                "maximum": 115.0,
                "change": 10.0,
                "change_percent": 10.0,
                "direction": "up",
            },
            "predictions": [
                {
                    "timestamp": "2023-01-11T00:00:00Z",
                    "value": 105.0,
                    "confidence": 0.9,
                },
                {
                    "timestamp": "2023-01-12T00:00:00Z",
                    "value": 107.5,
                    "confidence": 0.85,
                },
                {
                    "timestamp": "2023-01-13T00:00:00Z",
                    "value": 110.0,
                    "confidence": 0.8,
                },
                {
                    "timestamp": "2023-01-14T00:00:00Z",
                    "value": 112.5,
                    "confidence": 0.75,
                },
                {
                    "timestamp": "2023-01-15T00:00:00Z",
                    "value": 115.0,
                    "confidence": 0.7,
                },
            ],
        }
        mock_post.return_value = mock_post_response
        data_service_url = (
            "http://localhost:8081/api/market-data/AAPL?timeframe=1d&period=1mo"
        )
        response = requests.get(data_service_url)
        self.assertEqual(response.status_code, 200)
        market_data = response.json()["data"]
        self.assertIsInstance(market_data, list)
        ai_engine_url = "http://localhost:8082/api/predict"
        response = requests.post(
            ai_engine_url,
            json={
                "model_id": "model_1234567890",
                "symbol": "AAPL",
                "data": market_data,
            },
        )
        self.assertEqual(response.status_code, 200)
        prediction = response.json()
        self.assertEqual(prediction["model_id"], "model_1234567890")
        self.assertEqual(prediction["symbol"], "AAPL")
        self.assertIn("prediction", prediction)
        self.assertIn("predictions", prediction)
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
            mock_create_order.return_value = {
                "id": "order_1234567890",
                "user_id": "user_1234567890",
                "portfolio_id": "portfolio_1234567890",
                "symbol": "AAPL",
                "side": "buy",
                "type": "market",
                "status": "created",
                "quantity": 100,
                "price": None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
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
            self.assertEqual(order["status"], "created")
        with patch.object(self.order_manager, "submit_order") as mock_submit_order:
            mock_submit_order.return_value = {
                "id": "order_1234567890",
                "user_id": "user_1234567890",
                "portfolio_id": "portfolio_1234567890",
                "symbol": "AAPL",
                "side": "buy",
                "type": "market",
                "status": "submitted",
                "quantity": 100,
                "price": None,
                "broker_order_id": "broker_1234567890",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            submitted_order = self.order_manager.submit_order("order_1234567890")
            self.assertEqual(submitted_order["id"], "order_1234567890")
            self.assertEqual(submitted_order["status"], "submitted")
            self.assertEqual(submitted_order["broker_order_id"], "broker_1234567890")
        with patch.object(self.order_manager, "add_execution") as mock_add_execution:
            mock_add_execution.return_value = {
                "id": "execution_1234567890",
                "order_id": "order_1234567890",
                "price": 150.0,
                "quantity": 100,
                "timestamp": datetime.utcnow().isoformat(),
                "broker_execution_id": "broker_execution_1234567890",
            }
            execution = self.order_manager.add_execution(
                order_id="order_1234567890",
                price=150.0,
                quantity=100,
                timestamp=datetime.utcnow(),
                broker_execution_id="broker_execution_1234567890",
            )
            self.assertEqual(execution["id"], "execution_1234567890")
            self.assertEqual(execution["order_id"], "order_1234567890")
            self.assertEqual(execution["price"], 150.0)
            self.assertEqual(execution["quantity"], 100)
        with patch.object(self.risk_calculator, "calculate_position_risk") as mock_risk:
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

    @patch("requests.get")
    @patch("requests.post")
    def test_portfolio_rebalancing_workflow(self, mock_post: Any, mock_get: Any) -> Any:
        """Test portfolio rebalancing workflow."""
        portfolio_positions = [
            {
                "symbol": "AAPL",
                "quantity": 100,
                "entry_price": 150.0,
                "current_price": 155.0,
                "market_value": 15500.0,
                "weight": 0.6,
            },
            {
                "symbol": "MSFT",
                "quantity": 50,
                "entry_price": 250.0,
                "current_price": 260.0,
                "market_value": 13000.0,
                "weight": 0.4,
            },
        ]
        target_allocation = {"AAPL": 0.5, "MSFT": 0.3, "GOOGL": 0.2}
        portfolio_value = 28500.0
        with patch.object(
            self.risk_calculator, "calculate_portfolio_risk"
        ) as mock_portfolio_risk:
            mock_portfolio_risk.return_value = {
                "portfolio_id": "portfolio_1234567890",
                "total_value": 28500.0,
                "var": 0.06,
                "cvar": 0.08,
                "sharpe_ratio": 1.0,
                "sortino_ratio": 1.2,
                "max_drawdown": 0.18,
                "risk_score": 70,
                "risk_level": "high",
                "timestamp": datetime.utcnow().isoformat(),
            }
            current_risk = self.risk_calculator.calculate_portfolio_risk(
                portfolio_id="portfolio_1234567890",
                portfolio=portfolio_positions,
                risk_metrics=[
                    "var",
                    "cvar",
                    "sharpe_ratio",
                    "sortino_ratio",
                    "max_drawdown",
                ],
            )
            self.assertEqual(current_risk["portfolio_id"], "portfolio_1234567890")
            self.assertEqual(current_risk["total_value"], 28500.0)
            self.assertEqual(current_risk["risk_level"], "high")
        rebalancing_orders = []
        for symbol, target_weight in target_allocation.items():
            target_value = portfolio_value * target_weight
            current_position = next(
                (p for p in portfolio_positions if p["symbol"] == symbol), None
            )
            if current_position:
                current_value = current_position["market_value"]
                difference = target_value - current_value
                if abs(difference) > 100:
                    if difference > 0:
                        quantity = int(difference / current_position["current_price"])
                        if quantity > 0:
                            rebalancing_orders.append(
                                {
                                    "symbol": symbol,
                                    "side": "buy",
                                    "quantity": quantity,
                                    "type": "market",
                                }
                            )
                    else:
                        quantity = int(
                            abs(difference) / current_position["current_price"]
                        )
                        if quantity > 0:
                            rebalancing_orders.append(
                                {
                                    "symbol": symbol,
                                    "side": "sell",
                                    "quantity": quantity,
                                    "type": "market",
                                }
                            )
            else:
                current_price = 300.0
                quantity = int(target_value / current_price)
                if quantity > 0:
                    rebalancing_orders.append(
                        {
                            "symbol": symbol,
                            "side": "buy",
                            "quantity": quantity,
                            "type": "market",
                        }
                    )
        self.assertGreater(len(rebalancing_orders), 0)
        executed_orders = []
        for order_data in rebalancing_orders:
            with patch.object(self.order_manager, "create_order") as mock_create_order:
                mock_create_order.return_value = {
                    "id": f"order_{order_data['symbol']}_{order_data['side']}",
                    "user_id": "user_1234567890",
                    "portfolio_id": "portfolio_1234567890",
                    "symbol": order_data["symbol"],
                    "side": order_data["side"],
                    "type": order_data["type"],
                    "status": "created",
                    "quantity": order_data["quantity"],
                    "price": None,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
                order = self.order_manager.create_order(
                    user_id="user_1234567890",
                    portfolio_id="portfolio_1234567890",
                    symbol=order_data["symbol"],
                    side=order_data["side"],
                    order_type=order_data["type"],
                    quantity=order_data["quantity"],
                )
                executed_orders.append(order)
        self.assertEqual(len(executed_orders), len(rebalancing_orders))
        with patch.object(
            self.risk_calculator, "calculate_portfolio_risk"
        ) as mock_new_risk:
            mock_new_risk.return_value = {
                "portfolio_id": "portfolio_1234567890",
                "total_value": 28500.0,
                "var": 0.04,
                "cvar": 0.06,
                "sharpe_ratio": 1.3,
                "sortino_ratio": 1.5,
                "max_drawdown": 0.12,
                "risk_score": 55,
                "risk_level": "medium",
                "timestamp": datetime.utcnow().isoformat(),
            }
            new_risk = self.risk_calculator.calculate_portfolio_risk(
                portfolio_id="portfolio_1234567890",
                portfolio=portfolio_positions,
                risk_metrics=[
                    "var",
                    "cvar",
                    "sharpe_ratio",
                    "sortino_ratio",
                    "max_drawdown",
                ],
            )
            self.assertEqual(new_risk["portfolio_id"], "portfolio_1234567890")
            self.assertEqual(new_risk["risk_level"], "medium")
            self.assertLess(new_risk["var"], current_risk["var"])
            self.assertLess(new_risk["risk_score"], current_risk["risk_score"])

    @patch("requests.get")
    @patch("requests.post")
    def test_stop_loss_workflow(self, mock_post: Any, mock_get: Any) -> Any:
        """Test stop loss workflow."""
        position = {
            "symbol": "AAPL",
            "quantity": 100,
            "entry_price": 150.0,
            "current_price": 140.0,
            "market_value": 14000.0,
            "unrealized_pl": -1000.0,
            "unrealized_pl_percent": -6.67,
        }
        stop_loss_percent = 0.05
        stop_loss_price = position["entry_price"] * (1 - stop_loss_percent)
        self.assertLess(position["current_price"], stop_loss_price)
        with patch.object(self.risk_calculator, "calculate_position_risk") as mock_risk:
            mock_risk.return_value = {
                "symbol": "AAPL",
                "quantity": 100,
                "entry_price": 150.0,
                "current_price": 140.0,
                "var": 0.08,
                "cvar": 0.12,
                "sharpe_ratio": 0.5,
                "sortino_ratio": 0.7,
                "max_drawdown": 0.25,
                "risk_score": 85,
                "risk_level": "high",
                "timestamp": datetime.utcnow().isoformat(),
            }
            risk = self.risk_calculator.calculate_position_risk(
                symbol=position["symbol"],
                quantity=position["quantity"],
                entry_price=position["entry_price"],
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
            self.assertEqual(risk["risk_level"], "high")
            self.assertGreater(risk["risk_score"], 80)
        with patch.object(self.order_manager, "create_order") as mock_create_order:
            mock_create_order.return_value = {
                "id": "order_stop_loss_1234567890",
                "user_id": "user_1234567890",
                "portfolio_id": "portfolio_1234567890",
                "symbol": "AAPL",
                "side": "sell",
                "type": "market",
                "status": "created",
                "quantity": 100,
                "price": None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            stop_loss_order = self.order_manager.create_order(
                user_id="user_1234567890",
                portfolio_id="portfolio_1234567890",
                symbol=position["symbol"],
                side="sell",
                order_type="market",
                quantity=position["quantity"],
            )
            self.assertEqual(stop_loss_order["id"], "order_stop_loss_1234567890")
            self.assertEqual(stop_loss_order["symbol"], "AAPL")
            self.assertEqual(stop_loss_order["side"], "sell")
            self.assertEqual(stop_loss_order["quantity"], 100)
            self.assertEqual(stop_loss_order["status"], "created")
        with patch.object(self.order_manager, "submit_order") as mock_submit_order:
            mock_submit_order.return_value = {
                "id": "order_stop_loss_1234567890",
                "user_id": "user_1234567890",
                "portfolio_id": "portfolio_1234567890",
                "symbol": "AAPL",
                "side": "sell",
                "type": "market",
                "status": "submitted",
                "quantity": 100,
                "price": None,
                "broker_order_id": "broker_stop_loss_1234567890",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            submitted_order = self.order_manager.submit_order(
                "order_stop_loss_1234567890"
            )
            self.assertEqual(submitted_order["id"], "order_stop_loss_1234567890")
            self.assertEqual(submitted_order["status"], "submitted")
            self.assertEqual(
                submitted_order["broker_order_id"], "broker_stop_loss_1234567890"
            )
        with patch.object(self.order_manager, "add_execution") as mock_add_execution:
            mock_add_execution.return_value = {
                "id": "execution_stop_loss_1234567890",
                "order_id": "order_stop_loss_1234567890",
                "price": 140.0,
                "quantity": 100,
                "timestamp": datetime.utcnow().isoformat(),
                "broker_execution_id": "broker_execution_stop_loss_1234567890",
            }
            execution = self.order_manager.add_execution(
                order_id="order_stop_loss_1234567890",
                price=140.0,
                quantity=100,
                timestamp=datetime.utcnow(),
                broker_execution_id="broker_execution_stop_loss_1234567890",
            )
            self.assertEqual(execution["id"], "execution_stop_loss_1234567890")
            self.assertEqual(execution["order_id"], "order_stop_loss_1234567890")
            self.assertEqual(execution["price"], 140.0)
            self.assertEqual(execution["quantity"], 100)
        realized_loss = (position["entry_price"] - execution["price"]) * execution[
            "quantity"
        ]
        self.assertEqual(realized_loss, 1000.0)
        self.assertLessEqual(
            realized_loss,
            position["entry_price"] * position["quantity"] * stop_loss_percent,
        )


if __name__ == "__main__":
    unittest.main()
