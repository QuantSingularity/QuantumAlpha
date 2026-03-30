from typing import Any

"""
Unit tests for the AI Engine's Prediction Service.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
try:
    from backend.ai_engine.prediction_service import PredictionService
    from backend.common.exceptions import NotFoundError, ServiceError, ValidationError
except ImportError:

    class PredictionService:
        pass

    class NotFoundError(Exception):
        pass

    class ValidationError(Exception):
        pass

    class ServiceError(Exception):
        pass


class TestPredictionService(unittest.TestCase):
    """Unit tests for PredictionService class."""

    def setUp(self) -> Any:
        """Set up test fixtures."""
        self.config_manager = MagicMock()
        self.config_manager.get_config.return_value = {
            "ai_engine": {
                "model_dir": "/tmp/models",
                "registry_file": "/tmp/models/registry.json",
            },
            "services": {"data_service": {"host": "localhost", "port": 8081}},
        }
        self.db_manager = MagicMock()
        self.model_manager = MagicMock()
        self.model_manager.get_model.return_value = {
            "id": "model1",
            "name": "Test Model 1",
            "description": "Model for testing",
            "type": "lstm",
            "status": "active",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "parameters": {
                "layers": [50, 100, 50],
                "dropout": 0.2,
                "activation": "relu",
            },
            "features": ["close", "volume", "rsi_14", "sma_20", "sma_50"],
        }
        self.model_manager.predict.return_value = {
            "symbol": "AAPL",
            "model_id": "model1",
            "latest_price": 100.0,
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
                    "timestamp": "2023-01-02T00:00:00Z",
                    "value": 105.0,
                    "confidence": 0.9,
                },
                {
                    "timestamp": "2023-01-03T00:00:00Z",
                    "value": 107.5,
                    "confidence": 0.85,
                },
                {
                    "timestamp": "2023-01-04T00:00:00Z",
                    "value": 110.0,
                    "confidence": 0.8,
                },
                {
                    "timestamp": "2023-01-05T00:00:00Z",
                    "value": 112.5,
                    "confidence": 0.75,
                },
                {
                    "timestamp": "2023-01-06T00:00:00Z",
                    "value": 115.0,
                    "confidence": 0.7,
                },
            ],
        }
        self.market_data = [
            {
                "timestamp": "2023-01-01T00:00:00Z",
                "open": 99.0,
                "high": 101.0,
                "low": 98.0,
                "close": 100.0,
                "volume": 1000000,
                "symbol": "AAPL",
            }
        ]
        self.prediction_service = PredictionService(
            self.config_manager, self.db_manager, self.model_manager
        )

    def test_init(self) -> Any:
        """Test PredictionService initialization."""
        prediction_service = PredictionService(
            self.config_manager, self.db_manager, self.model_manager
        )
        self.assertEqual(prediction_service.config_manager, self.config_manager)
        self.assertEqual(prediction_service.db_manager, self.db_manager)
        self.assertEqual(prediction_service.model_manager, self.model_manager)

    @patch("requests.get")
    def test_get_market_data(self, mock_get: Any) -> Any:
        """Test getting market data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": self.market_data}
        mock_get.return_value = mock_response
        result = self.prediction_service._get_market_data(
            symbol="AAPL", timeframe="1d", period="1mo"
        )
        self.assertEqual(result, self.market_data)
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_get_market_data_error(self, mock_get: Any) -> Any:
        """Test getting market data with error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}
        mock_get.return_value = mock_response
        with self.assertRaises(ServiceError):
            self.prediction_service._get_market_data(
                symbol="AAPL", timeframe="1d", period="1mo"
            )

    def test_generate_prediction(self) -> Any:
        """Test generating prediction."""
        self.prediction_service._get_market_data = MagicMock(
            return_value=self.market_data
        )
        result = self.prediction_service.generate_prediction(
            model_id="model1", symbol="AAPL", timeframe="1d", period="1mo", horizon=5
        )
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["model_id"], "model1")
        self.assertEqual(result["latest_price"], 100.0)
        self.assertEqual(result["prediction"]["average"], 110.0)
        self.assertEqual(result["prediction"]["minimum"], 105.0)
        self.assertEqual(result["prediction"]["maximum"], 115.0)
        self.assertEqual(result["prediction"]["change"], 10.0)
        self.assertEqual(result["prediction"]["change_percent"], 10.0)
        self.assertEqual(result["prediction"]["direction"], "up")
        self.assertEqual(len(result["predictions"]), 5)
        self.model_manager.predict.assert_called_once()

    def test_generate_prediction_missing_model_id(self) -> Any:
        """Test generating prediction with missing model ID."""
        with self.assertRaises(ValidationError):
            self.prediction_service.generate_prediction(
                model_id="", symbol="AAPL", timeframe="1d", period="1mo", horizon=5
            )

    def test_generate_prediction_missing_symbol(self) -> Any:
        """Test generating prediction with missing symbol."""
        with self.assertRaises(ValidationError):
            self.prediction_service.generate_prediction(
                model_id="model1", symbol="", timeframe="1d", period="1mo", horizon=5
            )

    @patch("requests.get")
    def test_generate_signals(self, mock_get: Any) -> Any:
        """Test generating signals."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": self.market_data}
        mock_get.return_value = mock_response
        result = self.prediction_service.generate_signals(
            symbols=["AAPL", "MSFT"],
            model_id="model1",
            timeframe="1d",
            period="1mo",
            strategy="prediction",
        )
        self.assertEqual(result["strategy"], "prediction")
        self.assertEqual(result["model_id"], "model1")
        self.assertTrue("signals" in result)
        self.assertTrue("count" in result)
        self.assertTrue("generated_at" in result)
        signals = result["signals"]
        self.assertEqual(len(signals), 2)
        self.assertEqual(signals[0]["symbol"], "AAPL")
        self.assertTrue("type" in signals[0])
        self.assertTrue("strength" in signals[0])
        self.assertTrue("price" in signals[0])
        self.assertTrue("prediction" in signals[0])

    def test_generate_signals_missing_symbols(self) -> Any:
        """Test generating signals with missing symbols."""
        with self.assertRaises(ValidationError):
            self.prediction_service.generate_signals(
                symbols=[],
                model_id="model1",
                timeframe="1d",
                period="1mo",
                strategy="prediction",
            )

    def test_generate_signals_missing_model_id(self) -> Any:
        """Test generating signals with missing model ID."""
        with self.assertRaises(ValidationError):
            self.prediction_service.generate_signals(
                symbols=["AAPL", "MSFT"],
                model_id=None,
                timeframe="1d",
                period="1mo",
                strategy="prediction",
            )

    def test_generate_signals_invalid_strategy(self) -> Any:
        """Test generating signals with invalid strategy."""
        with self.assertRaises(ValidationError):
            self.prediction_service.generate_signals(
                symbols=["AAPL", "MSFT"],
                model_id="model1",
                timeframe="1d",
                period="1mo",
                strategy="invalid_strategy",
            )

    def test_calculate_signal_strength(self) -> Any:
        """Test calculating signal strength."""
        strength = self.prediction_service._calculate_signal_strength(
            current_price=100.0, predicted_price=110.0, confidence=0.8
        )
        self.assertIsInstance(strength, float)
        self.assertGreaterEqual(strength, 0.0)
        self.assertLessEqual(strength, 1.0)

    def test_determine_signal_type(self) -> Any:
        """Test determining signal type."""
        signal_type = self.prediction_service._determine_signal_type(
            current_price=100.0, predicted_price=110.0, threshold=0.03
        )
        self.assertEqual(signal_type, "buy")
        signal_type = self.prediction_service._determine_signal_type(
            current_price=100.0, predicted_price=95.0, threshold=0.03
        )
        self.assertEqual(signal_type, "sell")
        signal_type = self.prediction_service._determine_signal_type(
            current_price=100.0, predicted_price=102.0, threshold=0.03
        )
        self.assertEqual(signal_type, "hold")
        signal_type = self.prediction_service._determine_signal_type(
            current_price=100.0, predicted_price=98.0, threshold=0.03
        )
        self.assertEqual(signal_type, "hold")


if __name__ == "__main__":
    unittest.main()
