"""
Mock objects for QuantumAlpha tests.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

import numpy as np


class MockConfigManager:
    """Mock ConfigManager for testing."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize MockConfigManager.

        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or {
            "database": {
                "postgres": {
                    "host": "localhost",
                    "port": 5432,
                    "user": "test_user",
                    "password": "test_password",
                    "database": "test_db",
                },
                "redis": {"host": "localhost", "port": 6379, "db": 0},
            },
            "services": {
                "data_service": {"host": "localhost", "port": 8081},
                "ai_engine": {"host": "localhost", "port": 8082},
                "risk_service": {"host": "localhost", "port": 8083},
                "execution_service": {"host": "localhost", "port": 8084},
            },
            "logging": {
                "level": "DEBUG",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "security": {"jwt_secret": "test_secret", "jwt_expiration": 3600},
        }

    def get_config(self) -> Dict[str, Any]:
        """
        Get the full configuration.

        Returns:
            Configuration dictionary
        """
        return self.config

    def get_database_config(self) -> Dict[str, Any]:
        """
        Get database configuration.

        Returns:
            Database configuration dictionary
        """
        return self.config["database"]

    def get_service_config(self) -> Dict[str, Any]:
        """
        Get service configuration.

        Returns:
            Service configuration dictionary
        """
        return self.config["services"]

    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration.

        Returns:
            Logging configuration dictionary
        """
        return self.config["logging"]

    def get_security_config(self) -> Dict[str, Any]:
        """
        Get security configuration.

        Returns:
            Security configuration dictionary
        """
        return self.config["security"]


class MockDatabaseManager:
    """Mock DatabaseManager for testing."""

    def __init__(self) -> None:
        """Initialize MockDatabaseManager."""
        self.postgres_session = MagicMock()
        self.redis_connection = MagicMock()

    def get_postgres_session(self) -> Any:
        """
        Get PostgreSQL session.

        Returns:
            Mock PostgreSQL session
        """
        return self.postgres_session

    def get_redis_connection(self) -> Any:
        """
        Get Redis connection.

        Returns:
            Mock Redis connection
        """
        return self.redis_connection


class MockMarketDataAPI:
    """Mock Market Data API for testing."""

    def __init__(self, data: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Initialize MockMarketDataAPI.

        Args:
            data: Market data (optional)
        """
        self.data = data or []

    def get_market_data(
        self,
        symbol: str,
        timeframe: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get market data.

        Args:
            symbol: Symbol
            timeframe: Timeframe
            start_date: Start date
            end_date: End date
            limit: Limit

        Returns:
            Market data
        """
        if not self.data:
            from ..helpers.test_helpers import generate_market_data

            self.data = generate_market_data(
                symbol=symbol,
                start_date=start_date or "2023-01-01",
                end_date=end_date,
                periods=limit or 30,
            )
        return self.data


class MockModelManager:
    """Mock Model Manager for testing."""

    def __init__(self) -> None:
        """Initialize MockModelManager."""
        self.models = {
            "model1": {
                "id": "model1",
                "name": "Test Model 1",
                "type": "lstm",
                "status": "active",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            },
            "model2": {
                "id": "model2",
                "name": "Test Model 2",
                "type": "transformer",
                "status": "training",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            },
        }

    def get_model(self, model_id: str) -> Dict[str, Any]:
        """
        Get model by ID.

        Args:
            model_id: Model ID

        Returns:
            Model data

        Raises:
            KeyError: If model is not found
        """
        if model_id not in self.models:
            raise KeyError(f"Model not found: {model_id}")
        return self.models[model_id]

    def list_models(self) -> List[Dict[str, Any]]:
        """
        List all models.

        Returns:
            List of models
        """
        return list(self.models.values())

    def predict(
        self, model_id: str, data: Dict[str, Any], horizon: int = 5
    ) -> Dict[str, Any]:
        """
        Generate predictions.

        Args:
            model_id: Model ID
            data: Input data
            horizon: Prediction horizon

        Returns:
            Predictions

        Raises:
            KeyError: If model is not found
        """
        if model_id not in self.models:
            raise KeyError(f"Model not found: {model_id}")
        symbol = data.get("symbol", "AAPL")
        latest_price = data.get("latest_price", 100.0)
        predictions = []
        current_price = latest_price
        for i in range(horizon):
            current_price = current_price * (1 + np.random.normal(0, 0.01))
            predictions.append(
                {
                    "timestamp": (datetime.utcnow() + timedelta(days=i + 1)).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "value": round(current_price, 2),
                    "confidence": round(0.9 - i * 0.05, 2),
                }
            )
        return {
            "symbol": symbol,
            "model_id": model_id,
            "latest_price": latest_price,
            "prediction": {
                "average": round(
                    sum((p["value"] for p in predictions)) / len(predictions), 2
                ),
                "minimum": round(min((p["value"] for p in predictions)), 2),
                "maximum": round(max((p["value"] for p in predictions)), 2),
                "change": round(predictions[-1]["value"] - latest_price, 2),
                "change_percent": round(
                    (predictions[-1]["value"] - latest_price) / latest_price * 100, 2
                ),
                "direction": (
                    "up" if predictions[-1]["value"] > latest_price else "down"
                ),
            },
            "predictions": predictions,
        }


class MockBrokerAPI:
    """Mock Broker API for testing."""

    def __init__(self) -> None:
        """Initialize MockBrokerAPI."""
        self.orders = {}
        self.executions = {}
        self.positions = {}

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str,
        price: Optional[float] = None,
        time_in_force: str = "day",
    ) -> Dict[str, Any]:
        """
        Place an order.

        Args:
            symbol: Symbol
            side: Side (buy or sell)
            quantity: Quantity
            order_type: Order type (market or limit)
            price: Price (required for limit orders)
            time_in_force: Time in force

        Returns:
            Order data
        """
        order_id = f"broker_order_{len(self.orders) + 1}"
        order = {
            "id": order_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "type": order_type,
            "price": price,
            "time_in_force": time_in_force,
            "status": "filled",
            "filled_quantity": quantity,
            "average_fill_price": price or 100.0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self.orders[order_id] = order
        execution_id = f"broker_execution_{len(self.executions) + 1}"
        execution = {
            "id": execution_id,
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price or 100.0,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.executions[execution_id] = execution
        if symbol not in self.positions:
            self.positions[symbol] = {
                "symbol": symbol,
                "quantity": 0,
                "average_price": 0.0,
            }
        position = self.positions[symbol]
        if side == "buy":
            position["quantity"] += quantity
            position["average_price"] = (
                position["average_price"] * (position["quantity"] - quantity)
                + (price or 100.0) * quantity
            ) / position["quantity"]
        else:
            position["quantity"] -= quantity
        return order

    def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        Get order by ID.

        Args:
            order_id: Order ID

        Returns:
            Order data

        Raises:
            KeyError: If order is not found
        """
        if order_id not in self.orders:
            raise KeyError(f"Order not found: {order_id}")
        return self.orders[order_id]

    def get_executions(self, order_id: str) -> List[Dict[str, Any]]:
        """
        Get executions for an order.

        Args:
            order_id: Order ID

        Returns:
            List of executions
        """
        return [e for e in self.executions.values() if e["order_id"] == order_id]

    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get all positions.

        Returns:
            List of positions
        """
        return list(self.positions.values())
