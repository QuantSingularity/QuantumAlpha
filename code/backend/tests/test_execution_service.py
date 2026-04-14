"""
Unit tests for the Execution Service.
"""

import unittest
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

from backend.common import NotFoundError, ServiceError, ValidationError
from backend.execution_service.broker_integration import BrokerIntegration
from backend.execution_service.execution_strategy import ExecutionStrategy
from backend.execution_service.order_manager import OrderManager


class TestOrderManager(unittest.TestCase):
    """Test cases for OrderManager"""

    def setUp(self) -> Any:
        """Set up test environment"""
        self.config_manager = MagicMock()
        self.config_manager.get.return_value = "test_value"
        self.db_manager = MagicMock()
        self.session = MagicMock()
        self.db_manager.get_postgres_session.return_value = self.session
        self.order_manager = OrderManager(self.config_manager, self.db_manager)
        self.order_data = {
            "portfolio_id": "portfolio1",
            "symbol": "AAPL",
            "order_type": "market",
            "side": "buy",
            "quantity": 100,
            "price": None,
            "time_in_force": "day",
            "status": "new",
        }
        self.order = {
            "id": "order1",
            "portfolio_id": "portfolio1",
            "symbol": "AAPL",
            "order_type": "market",
            "side": "buy",
            "quantity": 100,
            "price": None,
            "time_in_force": "day",
            "status": "new",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def test_create_order(self) -> Any:
        """Test order creation"""
        self.session.execute.return_value.fetchone.return_value = ["order1"]
        result = self.order_manager.create_order(self.order_data)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "order1")
        self.assertEqual(result["portfolio_id"], "portfolio1")
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["order_type"], "market")
        self.assertEqual(result["side"], "buy")
        self.assertEqual(result["quantity"], 100)
        self.assertEqual(result["status"], "new")
        self.session.execute.assert_called_once()
        self.session.commit.assert_called_once()

    def test_create_order_missing_fields(self) -> Any:
        """Test order creation with missing fields"""
        order_data = self.order_data.copy()
        del order_data["portfolio_id"]
        with self.assertRaises(ValidationError):
            self.order_manager.create_order(order_data)
        order_data = self.order_data.copy()
        del order_data["symbol"]
        with self.assertRaises(ValidationError):
            self.order_manager.create_order(order_data)
        order_data = self.order_data.copy()
        del order_data["order_type"]
        with self.assertRaises(ValidationError):
            self.order_manager.create_order(order_data)
        order_data = self.order_data.copy()
        del order_data["side"]
        with self.assertRaises(ValidationError):
            self.order_manager.create_order(order_data)
        order_data = self.order_data.copy()
        del order_data["quantity"]
        with self.assertRaises(ValidationError):
            self.order_manager.create_order(order_data)

    def test_create_order_invalid_fields(self) -> Any:
        """Test order creation with invalid fields"""
        order_data = self.order_data.copy()
        order_data["order_type"] = "invalid_type"
        with self.assertRaises(ValidationError):
            self.order_manager.create_order(order_data)
        order_data = self.order_data.copy()
        order_data["side"] = "invalid_side"
        with self.assertRaises(ValidationError):
            self.order_manager.create_order(order_data)
        order_data = self.order_data.copy()
        order_data["time_in_force"] = "invalid_tif"
        with self.assertRaises(ValidationError):
            self.order_manager.create_order(order_data)
        order_data = self.order_data.copy()
        order_data["quantity"] = -100
        with self.assertRaises(ValidationError):
            self.order_manager.create_order(order_data)
        order_data = self.order_data.copy()
        order_data["quantity"] = 0
        with self.assertRaises(ValidationError):
            self.order_manager.create_order(order_data)
        order_data = self.order_data.copy()
        order_data["order_type"] = "limit"
        order_data["price"] = None
        with self.assertRaises(ValidationError):
            self.order_manager.create_order(order_data)

    def test_get_order(self) -> Any:
        """Test getting an order"""
        mock_row = MagicMock()
        mock_row.items.return_value = [
            ("id", "order1"),
            ("portfolio_id", "portfolio1"),
            ("symbol", "AAPL"),
            ("order_type", "market"),
            ("side", "buy"),
            ("quantity", 100),
            ("price", None),
            ("time_in_force", "day"),
            ("status", "new"),
            ("created_at", datetime.now(timezone.utc)),
            ("updated_at", datetime.now(timezone.utc)),
        ]
        self.session.execute.return_value.fetchone.return_value = mock_row
        result = self.order_manager.get_order("order1")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "order1")
        self.assertEqual(result["portfolio_id"], "portfolio1")
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["order_type"], "market")
        self.assertEqual(result["side"], "buy")
        self.assertEqual(result["quantity"], 100)
        self.assertEqual(result["status"], "new")
        self.session.execute.assert_called_once()

    def test_get_order_not_found(self) -> Any:
        """Test getting a non-existent order"""
        self.session.execute.return_value.fetchone.return_value = None
        with self.assertRaises(NotFoundError):
            self.order_manager.get_order("non_existent_order")

    def test_get_orders(self) -> Any:
        """Test getting orders"""
        mock_row1 = MagicMock()
        mock_row1.items.return_value = [
            ("id", "order1"),
            ("portfolio_id", "portfolio1"),
            ("symbol", "AAPL"),
            ("order_type", "market"),
            ("side", "buy"),
            ("quantity", 100),
            ("price", None),
            ("time_in_force", "day"),
            ("status", "new"),
            ("created_at", datetime.now(timezone.utc)),
            ("updated_at", datetime.now(timezone.utc)),
        ]
        mock_row2 = MagicMock()
        mock_row2.items.return_value = [
            ("id", "order2"),
            ("portfolio_id", "portfolio1"),
            ("symbol", "MSFT"),
            ("order_type", "limit"),
            ("side", "sell"),
            ("quantity", 50),
            ("price", 250.0),
            ("time_in_force", "day"),
            ("status", "new"),
            ("created_at", datetime.now(timezone.utc)),
            ("updated_at", datetime.now(timezone.utc)),
        ]
        self.session.execute.return_value.fetchall.return_value = [mock_row1, mock_row2]
        result = self.order_manager.get_orders(portfolio_id="portfolio1")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "order1")
        self.assertEqual(result[0]["symbol"], "AAPL")
        self.assertEqual(result[1]["id"], "order2")
        self.assertEqual(result[1]["symbol"], "MSFT")
        self.session.execute.assert_called_once()

    def test_update_order_status(self) -> Any:
        """Test updating order status"""
        self.session.execute.return_value.rowcount = 1
        result = self.order_manager.update_order_status("order1", "filled")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "order1")
        self.assertEqual(result["status"], "filled")
        self.session.execute.assert_called_once()
        self.session.commit.assert_called_once()

    def test_update_order_status_not_found(self) -> Any:
        """Test updating status of a non-existent order"""
        self.session.execute.return_value.rowcount = 0
        with self.assertRaises(NotFoundError):
            self.order_manager.update_order_status("non_existent_order", "filled")

    def test_update_order_status_invalid_status(self) -> Any:
        """Test updating order status with invalid status"""
        with self.assertRaises(ValidationError):
            self.order_manager.update_order_status("order1", "invalid_status")

    def test_cancel_order(self) -> Any:
        """Test canceling an order"""
        self.session.execute.return_value.rowcount = 1
        result = self.order_manager.cancel_order("order1")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "order1")
        self.assertEqual(result["status"], "canceled")
        self.session.execute.assert_called_once()
        self.session.commit.assert_called_once()

    def test_cancel_order_not_found(self) -> Any:
        """Test canceling a non-existent order"""
        self.session.execute.return_value.rowcount = 0
        with self.assertRaises(NotFoundError):
            self.order_manager.cancel_order("non_existent_order")

    def test_create_trade(self) -> Any:
        """Test trade creation"""
        self.session.execute.return_value.fetchone.return_value = ["trade1"]
        trade_data = {
            "order_id": "order1",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "price": 160.0,
            "commission": 1.0,
        }
        result = self.order_manager.create_trade(trade_data)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "trade1")
        self.assertEqual(result["order_id"], "order1")
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["side"], "buy")
        self.assertEqual(result["quantity"], 100)
        self.assertEqual(result["price"], 160.0)
        self.assertEqual(result["commission"], 1.0)
        self.session.execute.assert_called_once()
        self.session.commit.assert_called_once()

    def test_create_trade_missing_fields(self) -> Any:
        """Test trade creation with missing fields"""
        trade_data = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "price": 160.0,
            "commission": 1.0,
        }
        with self.assertRaises(ValidationError):
            self.order_manager.create_trade(trade_data)
        trade_data = {
            "order_id": "order1",
            "side": "buy",
            "quantity": 100,
            "price": 160.0,
            "commission": 1.0,
        }
        with self.assertRaises(ValidationError):
            self.order_manager.create_trade(trade_data)
        trade_data = {
            "order_id": "order1",
            "symbol": "AAPL",
            "quantity": 100,
            "price": 160.0,
            "commission": 1.0,
        }
        with self.assertRaises(ValidationError):
            self.order_manager.create_trade(trade_data)
        trade_data = {
            "order_id": "order1",
            "symbol": "AAPL",
            "side": "buy",
            "price": 160.0,
            "commission": 1.0,
        }
        with self.assertRaises(ValidationError):
            self.order_manager.create_trade(trade_data)
        trade_data = {
            "order_id": "order1",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "commission": 1.0,
        }
        with self.assertRaises(ValidationError):
            self.order_manager.create_trade(trade_data)

    def test_get_trades(self) -> Any:
        """Test getting trades"""
        mock_row1 = MagicMock()
        mock_row1.items.return_value = [
            ("id", "trade1"),
            ("order_id", "order1"),
            ("symbol", "AAPL"),
            ("side", "buy"),
            ("quantity", 100),
            ("price", 160.0),
            ("commission", 1.0),
            ("timestamp", datetime.now(timezone.utc)),
        ]
        mock_row2 = MagicMock()
        mock_row2.items.return_value = [
            ("id", "trade2"),
            ("order_id", "order2"),
            ("symbol", "MSFT"),
            ("side", "sell"),
            ("quantity", 50),
            ("price", 250.0),
            ("commission", 1.0),
            ("timestamp", datetime.now(timezone.utc)),
        ]
        self.session.execute.return_value.fetchall.return_value = [mock_row1, mock_row2]
        result = self.order_manager.get_trades(portfolio_id="portfolio1")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "trade1")
        self.assertEqual(result[0]["symbol"], "AAPL")
        self.assertEqual(result[1]["id"], "trade2")
        self.assertEqual(result[1]["symbol"], "MSFT")
        self.session.execute.assert_called_once()


class TestBrokerIntegration(unittest.TestCase):
    """Test cases for BrokerIntegration"""

    def setUp(self) -> Any:
        """Set up test environment"""
        self.config_manager = MagicMock()
        self.config_manager.get.return_value = "test_value"
        self.db_manager = MagicMock()
        self.broker_integration = BrokerIntegration(
            self.config_manager, self.db_manager
        )
        self.order = {
            "id": "order1",
            "portfolio_id": "portfolio1",
            "symbol": "AAPL",
            "order_type": "market",
            "side": "buy",
            "quantity": 100,
            "price": None,
            "time_in_force": "day",
            "status": "new",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    @patch("requests.post")
    def test_submit_order_to_broker(self, mock_post: Any) -> Any:
        """Test submitting order to broker"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "broker_order_id": "broker_order1",
            "status": "submitted",
        }
        mock_post.return_value = mock_response
        result = self.broker_integration.submit_order_to_broker(self.order)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["order_id"], "order1")
        self.assertEqual(result["broker_order_id"], "broker_order1")
        self.assertEqual(result["status"], "submitted")
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_submit_order_to_broker_error(self, mock_post: Any) -> Any:
        """Test submitting order to broker with error"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid order"
        mock_post.return_value = mock_response
        with self.assertRaises(ServiceError):
            self.broker_integration.submit_order_to_broker(self.order)

    @patch("requests.get")
    def test_get_order_status_from_broker(self, mock_get: Any) -> Any:
        """Test getting order status from broker"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "broker_order_id": "broker_order1",
            "status": "filled",
            "filled_quantity": 100,
            "average_price": 160.0,
        }
        mock_get.return_value = mock_response
        result = self.broker_integration.get_order_status_from_broker("broker_order1")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["broker_order_id"], "broker_order1")
        self.assertEqual(result["status"], "filled")
        self.assertEqual(result["filled_quantity"], 100)
        self.assertEqual(result["average_price"], 160.0)
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_get_order_status_from_broker_error(self, mock_get: Any) -> Any:
        """Test getting order status from broker with error"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Order not found"
        mock_get.return_value = mock_response
        with self.assertRaises(ServiceError):
            self.broker_integration.get_order_status_from_broker("broker_order1")

    @patch("requests.delete")
    def test_cancel_order_at_broker(self, mock_delete: Any) -> Any:
        """Test canceling order at broker"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "broker_order_id": "broker_order1",
            "status": "canceled",
        }
        mock_delete.return_value = mock_response
        result = self.broker_integration.cancel_order_at_broker("broker_order1")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["broker_order_id"], "broker_order1")
        self.assertEqual(result["status"], "canceled")
        mock_delete.assert_called_once()

    @patch("requests.delete")
    def test_cancel_order_at_broker_error(self, mock_delete: Any) -> Any:
        """Test canceling order at broker with error"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Cannot cancel order"
        mock_delete.return_value = mock_response
        with self.assertRaises(ServiceError):
            self.broker_integration.cancel_order_at_broker("broker_order1")

    @patch("requests.get")
    def test_get_account_info(self, mock_get: Any) -> Any:
        """Test getting account info"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "account_id": "account1",
            "cash": 10000.0,
            "buying_power": 20000.0,
            "equity": 30000.0,
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "average_price": 150.0,
                    "current_price": 160.0,
                    "market_value": 16000.0,
                    "unrealized_pl": 1000.0,
                }
            ],
        }
        mock_get.return_value = mock_response
        result = self.broker_integration.get_account_info("account1")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["account_id"], "account1")
        self.assertEqual(result["cash"], 10000.0)
        self.assertEqual(result["buying_power"], 20000.0)
        self.assertEqual(result["equity"], 30000.0)
        self.assertEqual(len(result["positions"]), 1)
        self.assertEqual(result["positions"][0]["symbol"], "AAPL")
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_get_account_info_error(self, mock_get: Any) -> Any:
        """Test getting account info with error"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response
        with self.assertRaises(ServiceError):
            self.broker_integration.get_account_info("account1")

    @patch("requests.get")
    def test_get_market_data(self, mock_get: Any) -> Any:
        """Test getting market data"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "symbol": "AAPL",
            "last_price": 160.0,
            "bid": 159.95,
            "ask": 160.05,
            "volume": 1000000,
        }
        mock_get.return_value = mock_response
        result = self.broker_integration.get_market_data("AAPL")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["last_price"], 160.0)
        self.assertEqual(result["bid"], 159.95)
        self.assertEqual(result["ask"], 160.05)
        self.assertEqual(result["volume"], 1000000)
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_get_market_data_error(self, mock_get: Any) -> Any:
        """Test getting market data with error"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Symbol not found"
        mock_get.return_value = mock_response
        with self.assertRaises(ServiceError):
            self.broker_integration.get_market_data("INVALID")


class TestExecutionStrategy(unittest.TestCase):
    """Test cases for ExecutionStrategy"""

    def setUp(self) -> Any:
        """Set up test environment"""
        self.config_manager = MagicMock()
        self.config_manager.get.return_value = "test_value"
        self.db_manager = MagicMock()
        self.execution_strategy = ExecutionStrategy(
            self.config_manager, self.db_manager
        )
        self.order = {
            "id": "order1",
            "portfolio_id": "portfolio1",
            "symbol": "AAPL",
            "order_type": "market",
            "side": "buy",
            "quantity": 100,
            "price": None,
            "time_in_force": "day",
            "status": "new",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.market_data = {
            "symbol": "AAPL",
            "last_price": 160.0,
            "bid": 159.95,
            "ask": 160.05,
            "volume": 1000000,
        }

    def test_select_execution_strategy(self) -> Any:
        """Test selecting execution strategy"""
        strategy = self.execution_strategy.select_execution_strategy(self.order)
        self.assertEqual(strategy, "market")
        order = self.order.copy()
        order["order_type"] = "limit"
        order["price"] = 160.0
        strategy = self.execution_strategy.select_execution_strategy(order)
        self.assertEqual(strategy, "limit")
        order = self.order.copy()
        order["quantity"] = 100000
        strategy = self.execution_strategy.select_execution_strategy(order)
        self.assertEqual(strategy, "vwap")

    def test_execute_market_strategy(self) -> Any:
        """Test executing market strategy"""
        broker_integration = MagicMock()
        broker_integration.submit_order_to_broker.return_value = {
            "order_id": "order1",
            "broker_order_id": "broker_order1",
            "status": "filled",
        }
        broker_integration.get_order_status_from_broker.return_value = {
            "broker_order_id": "broker_order1",
            "status": "filled",
            "filled_quantity": 100,
            "average_price": 160.0,
        }
        result = self.execution_strategy.execute_market_strategy(
            order=self.order, broker_integration=broker_integration
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["order_id"], "order1")
        self.assertEqual(result["broker_order_id"], "broker_order1")
        self.assertEqual(result["status"], "filled")
        self.assertEqual(result["filled_quantity"], 100)
        self.assertEqual(result["average_price"], 160.0)
        broker_integration.submit_order_to_broker.assert_called_once()

    def test_execute_limit_strategy(self) -> Any:
        """Test executing limit strategy"""
        broker_integration = MagicMock()
        broker_integration.submit_order_to_broker.return_value = {
            "order_id": "order1",
            "broker_order_id": "broker_order1",
            "status": "submitted",
        }
        broker_integration.get_order_status_from_broker.return_value = {
            "broker_order_id": "broker_order1",
            "status": "filled",
            "filled_quantity": 100,
            "average_price": 160.0,
        }
        order = self.order.copy()
        order["order_type"] = "limit"
        order["price"] = 160.0
        result = self.execution_strategy.execute_limit_strategy(
            order=order, broker_integration=broker_integration
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["order_id"], "order1")
        self.assertEqual(result["broker_order_id"], "broker_order1")
        self.assertEqual(result["status"], "filled")
        self.assertEqual(result["filled_quantity"], 100)
        self.assertEqual(result["average_price"], 160.0)
        broker_integration.submit_order_to_broker.assert_called_once()

    def test_execute_vwap_strategy(self) -> Any:
        """Test executing VWAP strategy"""
        broker_integration = MagicMock()
        broker_integration.submit_order_to_broker.side_effect = [
            {
                "order_id": f"order1_child_{i}",
                "broker_order_id": f"broker_order1_child_{i}",
                "status": "filled",
            }
            for i in range(5)
        ]
        broker_integration.get_order_status_from_broker.side_effect = [
            {
                "broker_order_id": f"broker_order1_child_{i}",
                "status": "filled",
                "filled_quantity": 20,
                "average_price": 160.0 + i * 0.1,
            }
            for i in range(5)
        ]
        order = self.order.copy()
        order["quantity"] = 100
        result = self.execution_strategy.execute_vwap_strategy(
            order=order,
            broker_integration=broker_integration,
            market_data=self.market_data,
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["order_id"], "order1")
        self.assertEqual(result["status"], "filled")
        self.assertEqual(result["filled_quantity"], 100)
        self.assertTrue("average_price" in result)
        self.assertTrue("child_orders" in result)
        self.assertEqual(len(result["child_orders"]), 5)
        self.assertEqual(broker_integration.submit_order_to_broker.call_count, 5)

    def test_execute_twap_strategy(self) -> Any:
        """Test executing TWAP strategy"""
        broker_integration = MagicMock()
        broker_integration.submit_order_to_broker.side_effect = [
            {
                "order_id": f"order1_child_{i}",
                "broker_order_id": f"broker_order1_child_{i}",
                "status": "filled",
            }
            for i in range(5)
        ]
        broker_integration.get_order_status_from_broker.side_effect = [
            {
                "broker_order_id": f"broker_order1_child_{i}",
                "status": "filled",
                "filled_quantity": 20,
                "average_price": 160.0 + i * 0.1,
            }
            for i in range(5)
        ]
        order = self.order.copy()
        order["quantity"] = 100
        result = self.execution_strategy.execute_twap_strategy(
            order=order,
            broker_integration=broker_integration,
            market_data=self.market_data,
            duration_minutes=5,
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["order_id"], "order1")
        self.assertEqual(result["status"], "filled")
        self.assertEqual(result["filled_quantity"], 100)
        self.assertTrue("average_price" in result)
        self.assertTrue("child_orders" in result)
        self.assertEqual(len(result["child_orders"]), 5)
        self.assertEqual(broker_integration.submit_order_to_broker.call_count, 5)

    def test_execute_iceberg_strategy(self) -> Any:
        """Test executing iceberg strategy"""
        broker_integration = MagicMock()
        broker_integration.submit_order_to_broker.side_effect = [
            {
                "order_id": f"order1_child_{i}",
                "broker_order_id": f"broker_order1_child_{i}",
                "status": "filled",
            }
            for i in range(5)
        ]
        broker_integration.get_order_status_from_broker.side_effect = [
            {
                "broker_order_id": f"broker_order1_child_{i}",
                "status": "filled",
                "filled_quantity": 20,
                "average_price": 160.0,
            }
            for i in range(5)
        ]
        order = self.order.copy()
        order["quantity"] = 100
        result = self.execution_strategy.execute_iceberg_strategy(
            order=order,
            broker_integration=broker_integration,
            market_data=self.market_data,
            display_size=20,
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["order_id"], "order1")
        self.assertEqual(result["status"], "filled")
        self.assertEqual(result["filled_quantity"], 100)
        self.assertTrue("average_price" in result)
        self.assertTrue("child_orders" in result)
        self.assertEqual(len(result["child_orders"]), 5)
        self.assertEqual(broker_integration.submit_order_to_broker.call_count, 5)


if __name__ == "__main__":
    unittest.main()
