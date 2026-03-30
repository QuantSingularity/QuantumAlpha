"""
Test configuration utilities.

This module provides utilities for test configuration.
"""

import json
import os
import tempfile
from typing import Any, Dict, Optional
import pytest
import yaml


class TestConfig:
    """Test configuration manager."""

    def __init__(self, config_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the test configuration manager.

        Args:
            config_data: Configuration data
        """
        self.config_data = config_data or self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration.

        Returns:
            Default configuration
        """
        return {
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
            "data_sources": {
                "alpha_vantage": {
                    "api_key": "demo",
                    "base_url": "https://www.alphavantage.co/query",
                },
                "yahoo_finance": {
                    "base_url": "https://query1.finance.yahoo.com/v8/finance/chart"
                },
            },
            "database": {
                "postgres": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "quantumalpha_test",
                    "user": "postgres",
                    "password": "postgres",
                },
                "timescale": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "timescaledb_test",
                    "user": "postgres",
                    "password": "postgres",
                },
                "sqlite": {"path": ":memory:"},
            },
            "services": {
                "data_service": {"host": "localhost", "port": 8081},
                "ai_engine": {"host": "localhost", "port": 8082},
                "risk_service": {"host": "localhost", "port": 8083},
                "execution_service": {"host": "localhost", "port": 8084},
            },
            "security": {
                "jwt_secret": "test_secret",
                "jwt_expiration": 3600,
                "refresh_token_expiration": 86400,
            },
            "logging": {
                "level": "DEBUG",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "/tmp/quantumalpha_test.log",
            },
            "test": {"mock_external_apis": True, "use_in_memory_db": True},
        }

    def get_config(self) -> Dict[str, Any]:
        """
        Get the configuration.

        Returns:
            Configuration data
        """
        return self.config_data

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a configuration section.

        Args:
            section: Section name

        Returns:
            Section data
        """
        return self.config_data.get(section, {})

    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Key path (dot-separated)
            default: Default value

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config_data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set_value(self, key: str, value: Any) -> Any:
        """
        Set a configuration value.

        Args:
            key: Key path (dot-separated)
            value: Value to set
        """
        keys = key.split(".")
        config = self.config_data
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def save_to_file(self, file_path: str, format: str = "json") -> Any:
        """
        Save configuration to a file.

        Args:
            file_path: File path
            format: File format (json or yaml)
        """
        with open(file_path, "w") as f:
            if format == "json":
                json.dump(self.config_data, f, indent=2)
            elif format == "yaml":
                yaml.dump(self.config_data, f, default_flow_style=False)
            else:
                raise ValueError(f"Unsupported format: {format}")

    @classmethod
    def load_from_file(cls: Any, file_path: str, format: str = None) -> Any:
        """
        Load configuration from a file.

        Args:
            file_path: File path
            format: File format (json or yaml, auto-detected if None)

        Returns:
            TestConfig instance
        """
        if format is None:
            _, ext = os.path.splitext(file_path)
            if ext.lower() in [".yml", ".yaml"]:
                format = "yaml"
            else:
                format = "json"
        with open(file_path, "r") as f:
            if format == "json":
                config_data = json.load(f)
            elif format == "yaml":
                config_data = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported format: {format}")
        return cls(config_data)


class MockConfigManager:
    """Mock configuration manager for testing."""

    def __init__(self, test_config: TestConfig) -> None:
        """
        Initialize the mock configuration manager.

        Args:
            test_config: Test configuration
        """
        self.test_config = test_config

    def get_config(self) -> Dict[str, Any]:
        """
        Get the configuration.

        Returns:
            Configuration data
        """
        return self.test_config.get_config()

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a configuration section.

        Args:
            section: Section name

        Returns:
            Section data
        """
        return self.test_config.get_section(section)

    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Key path (dot-separated)
            default: Default value

        Returns:
            Configuration value
        """
        return self.test_config.get_value(key, default)

    def get_security_config(self) -> Dict[str, Any]:
        """
        Get security configuration.

        Returns:
            Security configuration
        """
        return self.test_config.get_section("security")

    def get_database_config(self) -> Dict[str, Any]:
        """
        Get database configuration.

        Returns:
            Database configuration
        """
        return self.test_config.get_section("database")

    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """
        Get service configuration.

        Args:
            service_name: Service name

        Returns:
            Service configuration
        """
        services = self.test_config.get_section("services")
        return services.get(service_name, {})

    def get_data_source_config(self, source_name: str) -> Dict[str, Any]:
        """
        Get data source configuration.

        Args:
            source_name: Data source name

        Returns:
            Data source configuration
        """
        data_sources = self.test_config.get_section("data_sources")
        return data_sources.get(source_name, {})


@pytest.fixture
def test_config() -> Any:
    """Pytest fixture for test configuration."""
    return TestConfig()


@pytest.fixture
def mock_config_manager(test_config: Any) -> Any:
    """Pytest fixture for mock configuration manager."""
    return MockConfigManager(test_config)


class TestEnvironment:
    """Test environment manager."""

    def __init__(self) -> None:
        """Initialize the test environment manager."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_dir = self.temp_dir.name
        self.data_dir = os.path.join(self.root_dir, "data")
        self.cache_dir = os.path.join(self.root_dir, "cache")
        self.model_dir = os.path.join(self.root_dir, "models")
        self.log_dir = os.path.join(self.root_dir, "logs")
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.model_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        self.config = TestConfig()
        self.config.set_value("data_service.data_dir", self.data_dir)
        self.config.set_value("data_service.cache_dir", self.cache_dir)
        self.config.set_value("ai_engine.model_dir", self.model_dir)
        self.config.set_value(
            "ai_engine.registry_file", os.path.join(self.model_dir, "registry.json")
        )
        self.config.set_value("logging.file", os.path.join(self.log_dir, "test.log"))

    def cleanup(self) -> Any:
        """Clean up the test environment."""
        self.temp_dir.cleanup()

    def get_config(self) -> TestConfig:
        """
        Get the test configuration.

        Returns:
            Test configuration
        """
        return self.config

    def get_config_manager(self) -> MockConfigManager:
        """
        Get the mock configuration manager.

        Returns:
            Mock configuration manager
        """
        return MockConfigManager(self.config)

    def get_root_dir(self) -> str:
        """
        Get the root directory.

        Returns:
            Root directory path
        """
        return self.root_dir

    def get_data_dir(self) -> str:
        """
        Get the data directory.

        Returns:
            Data directory path
        """
        return self.data_dir

    def get_cache_dir(self) -> str:
        """
        Get the cache directory.

        Returns:
            Cache directory path
        """
        return self.cache_dir

    def get_model_dir(self) -> str:
        """
        Get the model directory.

        Returns:
            Model directory path
        """
        return self.model_dir

    def get_log_dir(self) -> str:
        """
        Get the log directory.

        Returns:
            Log directory path
        """
        return self.log_dir


@pytest.fixture
def test_env() -> Any:
    """Pytest fixture for test environment."""
    env = TestEnvironment()
    yield env
    env.cleanup()
