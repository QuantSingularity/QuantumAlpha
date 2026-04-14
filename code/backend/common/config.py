"""
Configuration utilities for QuantumAlpha services.
Loads configuration from environment variables and configuration files.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ConfigManager:
    """Manager for configuration settings"""

    def __init__(
        self, env_file: Optional[str] = None, config_file: Optional[str] = None
    ) -> None:
        """Initialize configuration manager

        Args:
            env_file: Path to .env file
            config_file: Path to config file (YAML or JSON)
        """
        self.config = {}
        if env_file and os.path.exists(env_file):
            load_dotenv(env_file)
            logger.info(f"Loaded environment variables from {env_file}")
        else:
            load_dotenv()
            logger.info("Loaded environment variables from default locations")
        if config_file and os.path.exists(config_file):
            self._load_config_file(config_file)
            logger.info(f"Loaded configuration from {config_file}")
        self._load_from_env()
        logger.info("Configuration manager initialized")

    def _load_config_file(self, config_file: str) -> None:
        """Load configuration from file

        Args:
            config_file: Path to config file (YAML or JSON)
        """
        _, ext = os.path.splitext(config_file)
        try:
            with open(config_file, "r") as f:
                if ext.lower() in [".yaml", ".yml"]:
                    self.config.update(yaml.safe_load(f))
                elif ext.lower() == ".json":
                    self.config.update(json.load(f))
                else:
                    logger.warning(f"Unsupported config file format: {ext}")
        except Exception as e:
            logger.error(f"Error loading config file: {e}")

    def _load_from_env(self) -> None:
        """Load configuration from environment variables"""
        self.config["postgres"] = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "username": os.getenv("DB_USERNAME", "postgres"),
            "password": os.getenv("DB_PASSWORD", "postgres"),
            "database": os.getenv("DB_NAME", "quantumalpha"),
        }
        self.config["redis"] = {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "password": os.getenv("REDIS_PASSWORD", None),
            "db": int(os.getenv("REDIS_DB", "0")),
        }
        self.config["influxdb"] = {
            "url": os.getenv("INFLUXDB_URL", "http://localhost:8086"),
            "token": os.getenv("INFLUXDB_TOKEN", ""),
            "org": os.getenv("INFLUXDB_ORG", "quantumalpha"),
            "bucket": os.getenv("INFLUXDB_BUCKET", "market_data"),
        }
        self.config["mongodb"] = {
            "host": os.getenv("MONGODB_HOST", "localhost"),
            "port": int(os.getenv("MONGODB_PORT", "27017")),
            "username": os.getenv("MONGODB_USERNAME", ""),
            "password": os.getenv("MONGODB_PASSWORD", ""),
            "database": os.getenv("MONGODB_DATABASE", "quantumalpha"),
        }
        self.config["api_keys"] = {
            "alpha_vantage": os.getenv("ALPHA_VANTAGE_API_KEY", ""),
            "polygon": os.getenv("POLYGON_API_KEY", ""),
            "news_api": os.getenv("NEWS_API_KEY", ""),
        }
        self.config["brokers"] = {
            "alpaca": {
                "api_key": os.getenv("ALPACA_API_KEY", ""),
                "secret_key": os.getenv("ALPACA_SECRET_KEY", ""),
                "endpoint": os.getenv(
                    "ALPACA_ENDPOINT", "https://paper-api.alpaca.markets"
                ),
            }
        }
        self.config["ml"] = {
            "model_registry_path": os.getenv(
                "MODEL_REGISTRY_PATH", "/path/to/model/registry"
            )
        }
        self.config["services"] = {
            "data_service": {
                "host": os.getenv("DATA_SERVICE_HOST", "localhost"),
                "port": int(os.getenv("DATA_SERVICE_PORT", "8081")),
            },
            "ai_engine": {
                "host": os.getenv("AI_ENGINE_HOST", "localhost"),
                "port": int(os.getenv("AI_ENGINE_PORT", "8082")),
            },
            "risk_service": {
                "host": os.getenv("RISK_SERVICE_HOST", "localhost"),
                "port": int(os.getenv("RISK_SERVICE_PORT", "8083")),
            },
            "execution_service": {
                "host": os.getenv("EXECUTION_SERVICE_HOST", "localhost"),
                "port": int(os.getenv("EXECUTION_SERVICE_PORT", "8084")),
            },
        }
        self.config["kafka"] = {
            "bootstrap_servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            "topics": {
                "market_data": os.getenv("KAFKA_TOPIC_MARKET_DATA", "market_data"),
                "signals": os.getenv("KAFKA_TOPIC_SIGNALS", "signals"),
                "orders": os.getenv("KAFKA_TOPIC_ORDERS", "orders"),
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value

        Args:
            key: Configuration key (dot notation supported)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values

        Returns:
            Dictionary with all configuration values
        """
        return self.config


_config_manager: Optional[ConfigManager] = None


def get_config_manager(
    env_file: Optional[str] = None, config_file: Optional[str] = None
) -> ConfigManager:
    """Get the configuration manager singleton

    Args:
        env_file: Path to .env file
        config_file: Path to config file (YAML or JSON)

    Returns:
        Configuration manager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(env_file, config_file)
    return _config_manager
