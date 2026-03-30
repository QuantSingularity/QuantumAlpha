from typing import Any

"""
Shared pytest fixtures for QuantumAlpha tests.
"""

import os
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock
import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    pass
except ImportError:
    pass


@pytest.fixture
def config_manager() -> Any:
    """Fixture for ConfigManager with test configuration."""
    config = {
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
    cm = MagicMock()
    cm.get_config.return_value = config
    cm.get_database_config.return_value = config["database"]
    cm.get_service_config.return_value = config["services"]
    cm.get_logging_config.return_value = config["logging"]
    cm.get_security_config.return_value = config["security"]
    return cm


@pytest.fixture
def db_manager(config_manager: Any) -> Any:
    """Fixture for DatabaseManager with mocked connections."""
    db_manager = MagicMock()
    postgres_session = MagicMock()
    db_manager.get_postgres_session.return_value = postgres_session
    redis_conn = MagicMock()
    db_manager.get_redis_connection.return_value = redis_conn
    return db_manager


@pytest.fixture
def sample_market_data() -> Any:
    """Fixture for sample market data."""
    dates = pd.date_range(start="2023-01-01", periods=30)
    data = []
    price = 100.0
    for date in dates:
        price = price * (1 + np.random.normal(0, 0.01))
        volume = int(1000000 + np.random.normal(0, 100000))
        data.append(
            {
                "timestamp": date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": round(price * (1 - 0.005), 2),
                "high": round(price * (1 + 0.01), 2),
                "low": round(price * (1 - 0.01), 2),
                "close": round(price, 2),
                "volume": volume,
                "symbol": "AAPL",
            }
        )
    return data


@pytest.fixture
def sample_user() -> Any:
    """Fixture for sample user data."""
    return {
        "id": "user_1234567890",
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "role": "user",
        "created_at": datetime.utcnow().isoformat(),
        "last_login": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_portfolio() -> Any:
    """Fixture for sample portfolio data."""
    return {
        "id": "portfolio_1234567890",
        "user_id": "user_1234567890",
        "name": "Test Portfolio",
        "description": "Portfolio for testing",
        "initial_balance": 100000.0,
        "current_balance": 105000.0,
        "currency": "USD",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "positions": [
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
        ],
    }


@pytest.fixture
def sample_strategy() -> Any:
    """Fixture for sample strategy data."""
    return {
        "id": "strategy_1234567890",
        "user_id": "user_1234567890",
        "name": "Test Strategy",
        "description": "Strategy for testing",
        "type": "trend_following",
        "status": "active",
        "config": {
            "timeframe": "1d",
            "symbols": ["AAPL", "MSFT", "GOOGL"],
            "parameters": {
                "sma_fast": 20,
                "sma_slow": 50,
                "rsi_period": 14,
                "rsi_overbought": 70,
                "rsi_oversold": 30,
            },
        },
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_model() -> Any:
    """Fixture for sample model data."""
    return {
        "id": "model_1234567890",
        "strategy_id": "strategy_1234567890",
        "name": "Test Model",
        "type": "lstm",
        "status": "active",
        "config": {
            "layers": [50, 100, 50],
            "dropout": 0.2,
            "activation": "relu",
            "optimizer": "adam",
            "loss": "mse",
            "epochs": 100,
            "batch_size": 32,
        },
        "performance": {"mse": 0.0025, "rmse": 0.05, "mae": 0.04, "r2": 0.85},
        "registry_path": "/models/model_1234567890",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "last_trained": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_signal() -> Any:
    """Fixture for sample signal data."""
    return {
        "id": "signal_1234567890",
        "strategy_id": "strategy_1234567890",
        "model_id": "model_1234567890",
        "symbol": "AAPL",
        "direction": "buy",
        "strength": 0.8,
        "confidence": 0.75,
        "target_price": 160.0,
        "stop_loss": 145.0,
        "timestamp": datetime.utcnow().isoformat(),
        "expiration": (datetime.utcnow() + timedelta(days=1)).isoformat(),
    }


@pytest.fixture
def sample_order() -> Any:
    """Fixture for sample order data."""
    return {
        "id": "order_1234567890",
        "user_id": "user_1234567890",
        "portfolio_id": "portfolio_1234567890",
        "strategy_id": "strategy_1234567890",
        "signal_id": "signal_1234567890",
        "symbol": "AAPL",
        "side": "buy",
        "type": "market",
        "status": "filled",
        "quantity": 100,
        "price": 150.0,
        "filled_quantity": 100,
        "average_fill_price": 150.0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "broker_order_id": "broker_1234567890",
    }


@pytest.fixture
def sample_execution() -> Any:
    """Fixture for sample execution data."""
    return {
        "id": "execution_1234567890",
        "order_id": "order_1234567890",
        "price": 150.0,
        "quantity": 100,
        "timestamp": datetime.utcnow().isoformat(),
        "broker_execution_id": "broker_exec_1234567890",
    }


@pytest.fixture
def sample_returns() -> Any:
    """Fixture for sample returns data."""
    return np.array(
        [0.01, -0.02, 0.005, 0.008, -0.01, 0.02, -0.015, 0.012, -0.005, 0.018]
    )


@pytest.fixture
def sample_equity_curve() -> Any:
    """Fixture for sample equity curve data."""
    return np.array(
        [100000, 101000, 99000, 99500, 100300, 99200, 101000, 99500, 100500, 102000]
    )
