from typing import Any

"""
Unit tests for the AI Engine's Model Manager.
"""

import json
import os
import pickle
import sys
import unittest
from unittest.mock import MagicMock, mock_open, patch

import numpy as np

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
try:
    from backend.ai_engine.model_manager import ModelManager
    from backend.common.exceptions import NotFoundError, ServiceError, ValidationError
except ImportError:

    class ModelManager:
        pass

    class NotFoundError(Exception):
        pass

    class ValidationError(Exception):
        pass

    class ServiceError(Exception):
        pass


class TestModelManager(unittest.TestCase):
    """Unit tests for ModelManager class."""

    def setUp(self) -> Any:
        """Set up test fixtures."""
        self.config_manager = MagicMock()
        self.config_manager.get_config.return_value = {
            "ai_engine": {
                "model_dir": "/tmp/models",
                "registry_file": "/tmp/models/registry.json",
            }
        }
        self.db_manager = MagicMock()
        self.model_registry = {
            "version": "1.0",
            "updated_at": "2023-01-01T00:00:00Z",
            "models": {
                "model1": {
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
                },
                "model2": {
                    "id": "model2",
                    "name": "Test Model 2",
                    "description": "Another model for testing",
                    "type": "transformer",
                    "status": "training",
                    "created_at": "2023-01-02T00:00:00Z",
                    "updated_at": "2023-01-02T00:00:00Z",
                    "parameters": {
                        "layers": [64, 128, 64],
                        "dropout": 0.3,
                        "activation": "tanh",
                    },
                    "features": ["close", "volume", "macd", "signal_line"],
                },
            },
        }
        self.mock_open_registry = mock_open(read_data=json.dumps(self.model_registry))
        with patch("builtins.open", self.mock_open_registry):
            self.model_manager = ModelManager(self.config_manager, self.db_manager)

    def test_init(self) -> Any:
        """Test ModelManager initialization."""
        with patch("builtins.open", self.mock_open_registry):
            model_manager = ModelManager(self.config_manager, self.db_manager)
            self.assertEqual(model_manager.model_dir, "/tmp/models")
            self.assertEqual(model_manager.registry_file, "/tmp/models/registry.json")
            self.assertEqual(model_manager.model_registry, self.model_registry)

    def test_list_models(self) -> Any:
        """Test listing models."""
        models = self.model_manager.list_models()
        self.assertEqual(len(models), 2)
        self.assertEqual(models[0]["id"], "model1")
        self.assertEqual(models[0]["name"], "Test Model 1")
        self.assertEqual(models[0]["type"], "lstm")
        self.assertEqual(models[0]["status"], "active")
        self.assertEqual(models[1]["id"], "model2")
        self.assertEqual(models[1]["name"], "Test Model 2")
        self.assertEqual(models[1]["type"], "transformer")
        self.assertEqual(models[1]["status"], "training")

    def test_get_model_existing(self) -> Any:
        """Test getting an existing model."""
        model = self.model_manager.get_model("model1")
        self.assertEqual(model["id"], "model1")
        self.assertEqual(model["name"], "Test Model 1")
        self.assertEqual(model["type"], "lstm")
        self.assertEqual(model["status"], "active")
        self.assertEqual(model["parameters"]["layers"], [50, 100, 50])
        self.assertEqual(model["parameters"]["dropout"], 0.2)
        self.assertEqual(model["parameters"]["activation"], "relu")
        self.assertEqual(
            model["features"], ["close", "volume", "rsi_14", "sma_20", "sma_50"]
        )

    def test_get_model_not_found(self) -> Any:
        """Test getting a non-existent model."""
        with self.assertRaises(NotFoundError):
            self.model_manager.get_model("non_existent_model")

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_create_model(
        self, mock_json_dump: Any, mock_file_open: Any, mock_exists: Any
    ) -> Any:
        """Test creating a new model."""
        mock_exists.return_value = False
        model_data = {
            "name": "New Test Model",
            "description": "A new model for testing",
            "type": "cnn",
            "parameters": {
                "layers": [32, 64, 32],
                "dropout": 0.1,
                "activation": "sigmoid",
            },
            "features": ["close", "volume", "bollinger_upper", "bollinger_lower"],
        }
        with patch.object(self.model_manager, "_save_registry") as mock_save_registry:
            result = self.model_manager.create_model(model_data)
            self.assertIsNotNone(result["id"])
            self.assertEqual(result["name"], "New Test Model")
            self.assertEqual(result["description"], "A new model for testing")
            self.assertEqual(result["type"], "cnn")
            self.assertEqual(result["status"], "created")
            self.assertEqual(result["parameters"]["layers"], [32, 64, 32])
            self.assertEqual(result["parameters"]["dropout"], 0.1)
            self.assertEqual(result["parameters"]["activation"], "sigmoid")
            self.assertEqual(
                result["features"],
                ["close", "volume", "bollinger_upper", "bollinger_lower"],
            )
            mock_save_registry.assert_called_once()

    def test_create_model_missing_name(self) -> Any:
        """Test creating a model with missing name."""
        model_data = {
            "description": "A new model for testing",
            "type": "cnn",
            "parameters": {
                "layers": [32, 64, 32],
                "dropout": 0.1,
                "activation": "sigmoid",
            },
            "features": ["close", "volume", "bollinger_upper", "bollinger_lower"],
        }
        with self.assertRaises(ValidationError):
            self.model_manager.create_model(model_data)

    def test_create_model_missing_type(self) -> Any:
        """Test creating a model with missing type."""
        model_data = {
            "name": "New Test Model",
            "description": "A new model for testing",
            "parameters": {
                "layers": [32, 64, 32],
                "dropout": 0.1,
                "activation": "sigmoid",
            },
            "features": ["close", "volume", "bollinger_upper", "bollinger_lower"],
        }
        with self.assertRaises(ValidationError):
            self.model_manager.create_model(model_data)

    def test_update_model_existing(self) -> Any:
        """Test updating an existing model."""
        update_data = {
            "name": "Updated Test Model",
            "description": "Updated description",
            "parameters": {
                "layers": [100, 200, 100],
                "dropout": 0.3,
                "activation": "tanh",
            },
            "features": ["close", "volume", "rsi_14", "macd"],
        }
        with patch.object(self.model_manager, "_save_registry") as mock_save_registry:
            result = self.model_manager.update_model("model1", update_data)
            self.assertEqual(result["id"], "model1")
            self.assertEqual(result["name"], "Updated Test Model")
            self.assertEqual(result["description"], "Updated description")
            self.assertEqual(result["parameters"]["layers"], [100, 200, 100])
            self.assertEqual(result["parameters"]["dropout"], 0.3)
            self.assertEqual(result["parameters"]["activation"], "tanh")
            self.assertEqual(result["features"], ["close", "volume", "rsi_14", "macd"])
            mock_save_registry.assert_called_once()

    def test_update_model_not_found(self) -> Any:
        """Test updating a non-existent model."""
        update_data = {
            "name": "Updated Test Model",
            "description": "Updated description",
        }
        with self.assertRaises(NotFoundError):
            self.model_manager.update_model("non_existent_model", update_data)

    def test_delete_model_existing(self) -> Any:
        """Test deleting an existing model."""
        with patch.object(self.model_manager, "_save_registry") as mock_save_registry:
            result = self.model_manager.delete_model("model1")
            self.assertTrue(result)
            self.assertNotIn("model1", self.model_manager.model_registry["models"])
            mock_save_registry.assert_called_once()

    def test_delete_model_not_found(self) -> Any:
        """Test deleting a non-existent model."""
        with self.assertRaises(NotFoundError):
            self.model_manager.delete_model("non_existent_model")

    @patch("os.path.exists")
    @patch("tensorflow.keras.models.load_model")
    def test_predict(self, mock_load_model: Any, mock_exists: Any) -> Any:
        """Test model prediction."""
        mock_exists.return_value = True
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array(
            [[105.0], [110.0], [115.0], [120.0], [125.0]]
        )
        mock_load_model.return_value = mock_model
        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = np.array([[0.1, 0.2, 0.3, 0.4, 0.5]])
        mock_scaler.inverse_transform.return_value = np.array(
            [[105.0], [110.0], [115.0], [120.0], [125.0]]
        )
        data = {
            "symbol": "AAPL",
            "timeframe": "1d",
            "latest_price": 100.0,
            "data": [
                {
                    "timestamp": "2023-01-01T00:00:00Z",
                    "open": 99.0,
                    "high": 101.0,
                    "low": 98.0,
                    "close": 100.0,
                    "volume": 1000000,
                }
            ],
        }
        mock_open_scaler = mock_open(read_data=pickle.dumps(mock_scaler))
        mock_open_params = mock_open(
            read_data=json.dumps(
                {"target_column": "close", "sequence_length": 10, "target_shift": 1}
            )
        )
        with patch("builtins.open") as mock_file:
            mock_file.side_effect = [mock_open_scaler(), mock_open_params()]
            with patch("pickle.load", return_value=mock_scaler):
                with patch.object(
                    self.model_manager,
                    "_preprocess_data",
                    return_value=np.array([[0.1, 0.2, 0.3, 0.4, 0.5]]),
                ):
                    result = self.model_manager.predict("model1", data, horizon=5)
                    self.assertEqual(result["symbol"], "AAPL")
                    self.assertEqual(result["model_id"], "model1")
                    self.assertEqual(result["latest_price"], 100.0)
                    self.assertEqual(result["prediction"]["average"], 115.0)
                    self.assertEqual(result["prediction"]["minimum"], 105.0)
                    self.assertEqual(result["prediction"]["maximum"], 125.0)
                    self.assertEqual(result["prediction"]["change"], 25.0)
                    self.assertEqual(result["prediction"]["change_percent"], 25.0)
                    self.assertEqual(result["prediction"]["direction"], "up")
                    self.assertEqual(len(result["predictions"]), 5)

    def test_predict_model_not_found(self) -> Any:
        """Test prediction with non-existent model."""
        data = {
            "symbol": "AAPL",
            "timeframe": "1d",
            "latest_price": 100.0,
            "data": [
                {
                    "timestamp": "2023-01-01T00:00:00Z",
                    "open": 99.0,
                    "high": 101.0,
                    "low": 98.0,
                    "close": 100.0,
                    "volume": 1000000,
                }
            ],
        }
        with self.assertRaises(NotFoundError):
            self.model_manager.predict("non_existent_model", data)

    def test_predict_missing_data(self) -> Any:
        """Test prediction with missing data."""
        data = {"symbol": "AAPL", "timeframe": "1d", "latest_price": 100.0}
        with self.assertRaises(ValidationError):
            self.model_manager.predict("model1", data)

    def test_predict_missing_symbol(self) -> Any:
        """Test prediction with missing symbol."""
        data = {
            "timeframe": "1d",
            "latest_price": 100.0,
            "data": [
                {
                    "timestamp": "2023-01-01T00:00:00Z",
                    "open": 99.0,
                    "high": 101.0,
                    "low": 98.0,
                    "close": 100.0,
                    "volume": 1000000,
                }
            ],
        }
        with self.assertRaises(ValidationError):
            self.model_manager.predict("model1", data)


if __name__ == "__main__":
    unittest.main()
