"""
Integration tests for QuantumAlpha backend services.
"""

import unittest
from unittest.mock import MagicMock, patch

import requests
from backend.common.config import ConfigManager
from backend.common.database import DatabaseManager
from sqlalchemy import text as sa_text


class TestServiceIntegration(unittest.TestCase):
    """Integration tests for service communication"""

    @classmethod
    def setUpClass(cls: object) -> None:
        """Set up test environment"""
        cls.config_manager = ConfigManager()
        cls.db_manager = DatabaseManager(cls.config_manager)
        cls.data_service_url = f"http://{cls.config_manager.get('services.data_service.host')}:{cls.config_manager.get('services.data_service.port')}"
        cls.ai_engine_url = f"http://{cls.config_manager.get('services.ai_engine.host')}:{cls.config_manager.get('services.ai_engine.port')}"
        cls.risk_service_url = f"http://{cls.config_manager.get('services.risk_service.host')}:{cls.config_manager.get('services.risk_service.port')}"
        cls.execution_service_url = f"http://{cls.config_manager.get('services.execution_service.host')}:{cls.config_manager.get('services.execution_service.port')}"

    @patch("requests.get")
    def test_data_service_to_ai_engine(self, mock_get: "MagicMock") -> None:
        """Test data flow from Data Service to AI Engine"""
        market_data_response = {
            "symbol": "AAPL",
            "timeframe": "1d",
            "data": [
                {
                    "timestamp": "2023-01-01T00:00:00Z",
                    "open": 100.0,
                    "high": 105.0,
                    "low": 95.0,
                    "close": 102.0,
                    "volume": 1000,
                },
                {
                    "timestamp": "2023-01-02T00:00:00Z",
                    "open": 102.0,
                    "high": 107.0,
                    "low": 100.0,
                    "close": 105.0,
                    "volume": 1200,
                },
            ],
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = market_data_response
        mock_get.return_value = mock_response
        from ai_models.engine.prediction_service import PredictionService

        prediction_service = PredictionService(
            self.config_manager, self.db_manager, MagicMock()
        )
        prediction_service.model_manager.predict.return_value = {
            "symbol": "AAPL",
            "timeframe": "1d",
            "predictions": [
                {"timestamp": "2023-01-03T00:00:00Z", "value": 108.0},
                {"timestamp": "2023-01-04T00:00:00Z", "value": 110.0},
            ],
        }
        result = prediction_service.generate_prediction(
            model_id="model1", symbol="AAPL", timeframe="1d", period="1mo", horizon=2
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["model_id"], "model1")
        self.assertTrue("prediction" in result)
        self.assertTrue("average" in result["prediction"])
        self.assertTrue("direction" in result["prediction"])
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertTrue(args[0].startswith(self.data_service_url))

    @patch("requests.get")
    def test_ai_engine_to_risk_service(self, mock_get: "MagicMock") -> None:
        """Test data flow from AI Engine to Risk Service"""
        prediction_response = {
            "symbol": "AAPL",
            "model_id": "model1",
            "latest_price": 105.0,
            "prediction": {
                "average": 109.0,
                "minimum": 108.0,
                "maximum": 110.0,
                "change": 4.0,
                "change_percent": 3.81,
                "direction": "bullish",
            },
            "predictions": [
                {"timestamp": "2023-01-03T00:00:00Z", "value": 108.0},
                {"timestamp": "2023-01-04T00:00:00Z", "value": 110.0},
            ],
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = prediction_response
        mock_get.return_value = mock_response
        from backend.risk_service.risk_calculator import RiskCalculator

        risk_calculator = RiskCalculator(self.config_manager, self.db_manager)
        portfolio = {
            "id": "portfolio1",
            "name": "Test Portfolio",
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "entry_price": 100.0,
                    "current_price": 105.0,
                }
            ],
            "cash": 10000.0,
        }
        result = risk_calculator.calculate_portfolio_value_with_prediction(
            portfolio=portfolio, model_id="model1"
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], "portfolio1")
        self.assertTrue("current_value" in result)
        self.assertTrue("predicted_value" in result)
        self.assertTrue("change" in result)
        self.assertTrue("change_percent" in result)
        expected_current_value = 100 * 105.0 + 10000.0
        self.assertEqual(result["current_value"], expected_current_value)
        expected_predicted_value = 100 * 109.0 + 10000.0
        self.assertEqual(result["predicted_value"], expected_predicted_value)
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertTrue(args[0].startswith(self.ai_engine_url))

    @patch("requests.get")
    @patch("requests.post")
    def test_risk_service_to_execution_service(
        self, mock_post: object, mock_get: object
    ) -> object:
        """Test data flow from Risk Service to Execution Service"""
        risk_assessment_response = {
            "portfolio_id": "portfolio1",
            "symbol": "AAPL",
            "max_position_size": 200,
            "max_order_value": 20000.0,
            "risk_level": "medium",
        }
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = risk_assessment_response
        mock_get.return_value = mock_get_response
        order_response = {
            "id": "order1",
            "portfolio_id": "portfolio1",
            "symbol": "AAPL",
            "order_type": "market",
            "side": "buy",
            "quantity": 100,
            "price": None,
            "time_in_force": "day",
            "status": "new",
        }
        mock_post_response = MagicMock()
        mock_post_response.status_code = 201
        mock_post_response.json.return_value = order_response
        mock_post.return_value = mock_post_response
        from backend.execution_service.order_manager import OrderManager

        order_manager = OrderManager(self.config_manager, self.db_manager)
        order_data = {
            "portfolio_id": "portfolio1",
            "symbol": "AAPL",
            "order_type": "market",
            "side": "buy",
            "quantity": 100,
            "price": None,
            "time_in_force": "day",
        }
        result = order_manager.create_order_with_risk_check(order_data)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "order1")
        self.assertEqual(result["portfolio_id"], "portfolio1")
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["quantity"], 100)
        self.assertEqual(result["status"], "new")
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertTrue(args[0].startswith(self.risk_service_url))

    @patch("requests.get")
    def test_execution_service_to_data_service(self, mock_get: "MagicMock") -> None:
        """Test data flow from Execution Service to Data Service"""
        market_data_response = {
            "symbol": "AAPL",
            "last_price": 160.0,
            "bid": 159.95,
            "ask": 160.05,
            "volume": 1000000,
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = market_data_response
        mock_get.return_value = mock_response
        from backend.execution_service.broker_integration import BrokerIntegration

        broker_integration = BrokerIntegration(self.config_manager, self.db_manager)
        result = broker_integration.get_market_data("AAPL")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["last_price"], 160.0)
        self.assertEqual(result["bid"], 159.95)
        self.assertEqual(result["ask"], 160.05)
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertTrue(args[0].startswith(self.data_service_url))

    @patch("requests.post")
    def test_end_to_end_trading_flow(self, mock_post: "MagicMock") -> None:
        """Test end-to-end trading flow"""

        def mock_service_response(*args, **kwargs):
            url = args[0]
            if "/market-data/" in url:
                return MagicMock(
                    status_code=200,
                    json=lambda: {
                        "symbol": "AAPL",
                        "data": [
                            {
                                "timestamp": "2023-01-01T00:00:00Z",
                                "open": 100.0,
                                "high": 105.0,
                                "low": 95.0,
                                "close": 102.0,
                                "volume": 1000,
                            }
                        ],
                    },
                )
            elif "/predict/" in url:
                return MagicMock(
                    status_code=200,
                    json=lambda: {
                        "symbol": "AAPL",
                        "prediction": {"direction": "bullish", "change_percent": 3.0},
                    },
                )
            elif "/risk/" in url:
                return MagicMock(
                    status_code=200,
                    json=lambda: {"symbol": "AAPL", "max_position_size": 200},
                )
            elif "/orders/" in url:
                return MagicMock(
                    status_code=201,
                    json=lambda: {
                        "id": "order1",
                        "symbol": "AAPL",
                        "quantity": 100,
                        "status": "new",
                    },
                )
            elif "/broker/" in url:
                return MagicMock(
                    status_code=200,
                    json=lambda: {
                        "broker_order_id": "broker_order1",
                        "status": "filled",
                    },
                )
            else:
                return MagicMock(status_code=404)

        mock_post.side_effect = mock_service_response
        from backend.execution_service.trading_service import TradingService

        trading_service = TradingService(self.config_manager, self.db_manager)
        signal = {
            "symbol": "AAPL",
            "type": "buy",
            "strength": 0.8,
            "price": 160.0,
            "model_id": "model1",
        }
        portfolio_id = "portfolio1"
        result = trading_service.execute_trade_from_signal(signal, portfolio_id)
        self.assertIsInstance(result, dict)
        self.assertTrue("order_id" in result)
        self.assertTrue("status" in result)
        self.assertTrue("execution_details" in result)


class TestDatabaseIntegration(unittest.TestCase):
    """Integration tests for database operations"""

    @classmethod
    def setUpClass(cls: object) -> None:
        """Set up test environment"""
        cls.config_manager = ConfigManager()
        cls.db_manager = DatabaseManager(cls.config_manager)

    def test_postgres_connection(self) -> None:
        """Test PostgreSQL connection"""
        session = self.db_manager.get_postgres_session()
        self.assertIsNotNone(session)
        result = session.execute(sa_text("SELECT 1 as test"))
        row = result.fetchone()
        self.assertEqual(row[0], 1)
        session.close()

    def test_timescale_connection(self) -> None:
        """Test TimescaleDB connection"""
        session = self.db_manager.get_timescale_session()
        self.assertIsNotNone(session)
        result = session.execute(sa_text("SELECT 1 as test"))
        row = result.fetchone()
        self.assertEqual(row[0], 1)
        session.close()

    def test_redis_connection(self) -> None:
        """Test Redis connection"""
        redis_client = self.db_manager.get_redis_client()
        self.assertIsNotNone(redis_client)
        redis_client.set("test_key", "test_value")
        value = redis_client.get("test_key")
        self.assertEqual(value.decode("utf-8"), "test_value")
        redis_client.delete("test_key")

    def test_kafka_connection(self) -> None:
        """Test Kafka connection"""
        producer = self.db_manager.get_kafka_producer()
        self.assertIsNotNone(producer)
        consumer = self.db_manager.get_kafka_consumer(["test_topic"])
        self.assertIsNotNone(consumer)


class TestAPIEndpoints(unittest.TestCase):
    """Integration tests for API endpoints"""

    @classmethod
    def setUpClass(cls: object) -> None:
        """Set up test environment"""
        cls.config_manager = ConfigManager()
        cls.data_service_url = f"http://{cls.config_manager.get('services.data_service.host')}:{cls.config_manager.get('services.data_service.port')}"
        cls.ai_engine_url = f"http://{cls.config_manager.get('services.ai_engine.host')}:{cls.config_manager.get('services.ai_engine.port')}"
        cls.risk_service_url = f"http://{cls.config_manager.get('services.risk_service.host')}:{cls.config_manager.get('services.risk_service.port')}"
        cls.execution_service_url = f"http://{cls.config_manager.get('services.execution_service.host')}:{cls.config_manager.get('services.execution_service.port')}"

    @patch("requests.get")
    def test_data_service_market_data_endpoint(self, mock_get: "MagicMock") -> None:
        """Test Data Service market data endpoint"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "symbol": "AAPL",
            "timeframe": "1d",
            "data": [
                {
                    "timestamp": "2023-01-01T00:00:00Z",
                    "open": 100.0,
                    "high": 105.0,
                    "low": 95.0,
                    "close": 102.0,
                    "volume": 1000,
                }
            ],
        }
        mock_get.return_value = mock_response
        response = requests.get(
            f"{self.data_service_url}/api/market-data/AAPL?timeframe=1d&period=1mo"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["symbol"], "AAPL")
        self.assertTrue("data" in data)
        self.assertTrue(len(data["data"]) > 0)

    @patch("requests.post")
    def test_ai_engine_predict_endpoint(self, mock_post: "MagicMock") -> None:
        """Test AI Engine predict endpoint"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "symbol": "AAPL",
            "model_id": "model1",
            "prediction": {"direction": "bullish", "change_percent": 3.0},
        }
        mock_post.return_value = mock_response
        response = requests.post(
            f"{self.ai_engine_url}/api/predict",
            json={"model_id": "model1", "symbol": "AAPL", "timeframe": "1d"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["symbol"], "AAPL")
        self.assertTrue("prediction" in data)
        self.assertEqual(data["prediction"]["direction"], "bullish")

    @patch("requests.get")
    def test_risk_service_portfolio_risk_endpoint(self, mock_get: "MagicMock") -> None:
        """Test Risk Service portfolio risk endpoint"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "portfolio_id": "portfolio1",
            "var": 5000.0,
            "var_percent": 5.0,
            "sharpe_ratio": 1.2,
        }
        mock_get.return_value = mock_response
        response = requests.get(
            f"{self.risk_service_url}/api/risk/portfolio/portfolio1"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["portfolio_id"], "portfolio1")
        self.assertTrue("var" in data)
        self.assertTrue("sharpe_ratio" in data)

    @patch("requests.post")
    def test_execution_service_orders_endpoint(self, mock_post: "MagicMock") -> None:
        """Test Execution Service orders endpoint"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "order1",
            "portfolio_id": "portfolio1",
            "symbol": "AAPL",
            "order_type": "market",
            "side": "buy",
            "quantity": 100,
            "status": "new",
        }
        mock_post.return_value = mock_response
        response = requests.post(
            f"{self.execution_service_url}/api/orders",
            json={
                "portfolio_id": "portfolio1",
                "symbol": "AAPL",
                "order_type": "market",
                "side": "buy",
                "quantity": 100,
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["symbol"], "AAPL")
        self.assertEqual(data["quantity"], 100)
        self.assertEqual(data["status"], "new")


if __name__ == "__main__":
    unittest.main()
