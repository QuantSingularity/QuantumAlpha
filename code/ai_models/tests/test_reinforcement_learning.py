"""
Unit tests for the AI Engine's reinforcement-learning service.

Previously ReinforcementLearningService had no test coverage at all, which
is how ai_models/engine/app.py's /api/rl/train and /api/rl/act routes were
able to call train_agent()/get_action() - methods that don't exist on this
class - without anything catching it. These tests exercise the real,
existing methods (create_model, get_models, get_model, update_model,
delete_model, train_model, predict).
"""

import unittest
from unittest.mock import MagicMock, patch

from backend.common import NotFoundError, ValidationError


class TestReinforcementLearningService(unittest.TestCase):
    """Test cases for ReinforcementLearningService"""

    def setUp(self) -> None:
        """Set up test environment"""
        import shutil
        import tempfile

        from ai_models.engine.reinforcement_learning import ReinforcementLearningService

        self.tmp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)
        self.config_manager = MagicMock()
        self.config_manager.get.return_value = self.tmp_dir
        self.db_manager = MagicMock()
        self.rl_service = ReinforcementLearningService(
            self.config_manager, self.db_manager
        )
        self.rl_service.model_registry = {"models": {}}
        self.rl_service._save_registry = MagicMock()

    def test_create_model(self) -> None:
        """Test RL model creation"""
        result = self.rl_service.create_model(
            {
                "name": "PPO Trader",
                "algorithm": "ppo",
                "description": "Test PPO agent",
                "parameters": {"total_timesteps": 1000},
                "features": ["close", "volume"],
            }
        )
        self.assertIsInstance(result, dict)
        self.assertIn("id", result)
        self.assertEqual(result["name"], "PPO Trader")
        self.assertEqual(result["algorithm"], "ppo")
        self.assertEqual(result["status"], "created")
        self.assertIn(result["id"], self.rl_service.model_registry["models"])

    def test_create_model_missing_name(self) -> None:
        """Test RL model creation with missing name"""
        with self.assertRaises(ValidationError):
            self.rl_service.create_model({"algorithm": "ppo"})

    def test_create_model_invalid_algorithm(self) -> None:
        """Test RL model creation with an unsupported algorithm"""
        with self.assertRaises(ValidationError):
            self.rl_service.create_model({"name": "Bad Agent", "algorithm": "not_real"})

    def test_get_models_empty(self) -> None:
        """Test getting all models when none exist"""
        self.assertEqual(self.rl_service.get_models(), [])

    def test_get_models(self) -> None:
        """Test getting all models"""
        created = self.rl_service.create_model({"name": "Agent 1", "algorithm": "dqn"})
        models = self.rl_service.get_models()
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0]["id"], created["id"])
        self.assertEqual(models[0]["algorithm"], "dqn")

    def test_get_model(self) -> None:
        """Test getting a specific model"""
        created = self.rl_service.create_model({"name": "Agent 1", "algorithm": "a2c"})
        model = self.rl_service.get_model(created["id"])
        self.assertEqual(model["name"], "Agent 1")
        self.assertEqual(model["algorithm"], "a2c")

    def test_get_model_not_found(self) -> None:
        """Test getting a model that doesn't exist"""
        with self.assertRaises(NotFoundError):
            self.rl_service.get_model("does_not_exist")

    def test_update_model(self) -> None:
        """Test updating a model's metadata"""
        created = self.rl_service.create_model({"name": "Agent 1", "algorithm": "sac"})
        updated = self.rl_service.update_model(created["id"], {"name": "Renamed Agent"})
        self.assertEqual(updated["name"], "Renamed Agent")
        self.assertEqual(updated["algorithm"], "sac")

    def test_delete_model(self) -> None:
        """Test deleting a model"""
        created = self.rl_service.create_model({"name": "Agent 1", "algorithm": "ppo"})
        with patch("os.path.exists", return_value=False):
            result = self.rl_service.delete_model(created["id"])
        self.assertTrue(result["deleted"])
        self.assertNotIn(created["id"], self.rl_service.model_registry["models"])

    def test_delete_model_not_found(self) -> None:
        """Test deleting a model that doesn't exist"""
        with self.assertRaises(NotFoundError):
            self.rl_service.delete_model("does_not_exist")

    def test_train_model_not_found(self) -> None:
        """Test training a model that doesn't exist"""
        with self.assertRaises(NotFoundError):
            self.rl_service.train_model("does_not_exist", {"symbol": "AAPL"})

    def test_train_model_missing_symbol(self) -> None:
        """Test training without a symbol"""
        created = self.rl_service.create_model({"name": "Agent 1", "algorithm": "ppo"})
        with self.assertRaises(ValidationError):
            self.rl_service.train_model(created["id"], {})

    def test_train_model_trains_and_saves(self) -> None:
        """Test that train_model drives the algorithm's learn/save calls and
        updates the registry, without actually running real RL training."""
        import pandas as pd

        created = self.rl_service.create_model({"name": "Agent 1", "algorithm": "ppo"})
        fake_agent = MagicMock()
        fake_df = pd.DataFrame({"close": [100.0, 101.0, 102.0, 103.0, 104.0]})
        with patch.object(
            self.rl_service, "_get_market_data", return_value=[]
        ), patch.object(self.rl_service, "_process_data", return_value=fake_df), patch(
            "ai_models.engine.reinforcement_learning._ALGORITHM_MAP",
            {"ppo": MagicMock(return_value=fake_agent)},
        ), patch(
            "ai_models.engine.reinforcement_learning.DummyVecEnv",
            return_value=MagicMock(),
        ), patch(
            "ai_models.engine.reinforcement_learning.evaluate_policy",
            return_value=(12.5, 1.2),
        ):
            result = self.rl_service.train_model(
                created["id"],
                {"symbol": "AAPL", "timeframe": "1d", "period": "6mo"},
            )
        fake_agent.learn.assert_called_once()
        fake_agent.save.assert_called_once()
        self.assertEqual(result["status"], "trained")
        self.assertEqual(result["metrics"], {"mean_reward": 12.5, "std_reward": 1.2})
        self.assertEqual(
            self.rl_service.model_registry["models"][created["id"]]["status"],
            "trained",
        )

    def test_predict_untrained_model(self) -> None:
        """Test that predicting with an untrained model raises ValidationError"""
        created = self.rl_service.create_model({"name": "Agent 1", "algorithm": "ppo"})
        with self.assertRaises(ValidationError):
            self.rl_service.predict(
                created["id"], {"symbol": "AAPL", "timeframe": "1d", "period": "1mo"}
            )


if __name__ == "__main__":
    unittest.main()
