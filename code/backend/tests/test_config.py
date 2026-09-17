"""
Unit tests for backend.common.config.ConfigManager's service-endpoint
resolution.

Docker Compose sets a single combined `<SERVICE>_URL` env var per service
(e.g. `AI_ENGINE_URL=http://ai-engine:8080`) for inter-container calls, but
ConfigManager used to only read separate `<SERVICE>_HOST`/`<SERVICE>_PORT`
vars - meaning every service was unreachable from every other service in
the actual deployed stack. These tests cover both env var styles and the
default fallback.
"""

import os
import unittest
from unittest.mock import patch

from backend.common.config import ConfigManager


class TestServiceURLResolution(unittest.TestCase):
    """Test cases for ConfigManager's services.* resolution"""

    def _config_with_env(self, env: dict) -> ConfigManager:
        with patch.dict(os.environ, env, clear=False):
            with patch("backend.common.config.load_dotenv"):
                return ConfigManager()

    def test_resolves_combined_url_env_var(self) -> None:
        """The docker-compose style: a single <SERVICE>_URL env var"""
        config = self._config_with_env({"AI_ENGINE_URL": "http://ai-engine:8080"})
        service = config.get("services.ai_engine")
        self.assertEqual(service["host"], "ai-engine")
        self.assertEqual(service["port"], 8080)
        self.assertEqual(service["url"], "http://ai-engine:8080")

    def test_falls_back_to_host_and_port_env_vars(self) -> None:
        """The local-dev style: separate <SERVICE>_HOST/<SERVICE>_PORT vars"""
        config = self._config_with_env(
            {"AI_ENGINE_HOST": "127.0.0.1", "AI_ENGINE_PORT": "9999"}
        )
        service = config.get("services.ai_engine")
        self.assertEqual(service["host"], "127.0.0.1")
        self.assertEqual(service["port"], 9999)
        self.assertEqual(service["url"], "http://127.0.0.1:9999")

    def test_defaults_when_nothing_set(self) -> None:
        env = {
            k: v
            for k, v in os.environ.items()
            if not k.startswith(
                ("AI_ENGINE_", "DATA_SERVICE_", "RISK_SERVICE_", "EXECUTION_SERVICE_")
            )
        }
        with patch.dict(os.environ, env, clear=True):
            with patch("backend.common.config.load_dotenv"):
                config = ConfigManager()
        self.assertEqual(
            config.get("services.ai_engine"),
            {"host": "localhost", "port": 8082, "url": "http://localhost:8082"},
        )
        self.assertEqual(
            config.get("services.data_service"),
            {"host": "localhost", "port": 8081, "url": "http://localhost:8081"},
        )
        self.assertEqual(
            config.get("services.risk_service"),
            {"host": "localhost", "port": 8083, "url": "http://localhost:8083"},
        )
        self.assertEqual(
            config.get("services.execution_service"),
            {"host": "localhost", "port": 8084, "url": "http://localhost:8084"},
        )

    def test_url_env_var_takes_precedence_over_host_port(self) -> None:
        """If both styles are set, the combined URL wins (matches how
        docker-compose actually configures these services)."""
        config = self._config_with_env(
            {
                "AI_ENGINE_URL": "http://ai-engine:8080",
                "AI_ENGINE_HOST": "should-be-ignored",
                "AI_ENGINE_PORT": "1",
            }
        )
        service = config.get("services.ai_engine")
        self.assertEqual(service["host"], "ai-engine")
        self.assertEqual(service["port"], 8080)

    def test_all_four_services_present(self) -> None:
        config = self._config_with_env(
            {
                "DATA_SERVICE_URL": "http://data-service:8080",
                "AI_ENGINE_URL": "http://ai-engine:8080",
                "RISK_SERVICE_URL": "http://risk-service:8080",
                "EXECUTION_SERVICE_URL": "http://execution-service:8080",
            }
        )
        services = config.get("services")
        for name, host in [
            ("data_service", "data-service"),
            ("ai_engine", "ai-engine"),
            ("risk_service", "risk-service"),
            ("execution_service", "execution-service"),
        ]:
            self.assertEqual(services[name]["host"], host)
            self.assertEqual(services[name]["port"], 8080)


if __name__ == "__main__":
    unittest.main()
