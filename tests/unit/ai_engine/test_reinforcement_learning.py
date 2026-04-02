"""
Unit tests for the AI Engine's Reinforcement Learning module.
"""

import os
import sys
import unittest
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
try:
    from backend.ai_engine.reinforcement_learning import (
        RLAgent,
        RLEnvironment,
        RLTrainer,
    )
    from backend.common.exceptions import NotFoundError, ServiceError, ValidationError
except ImportError:

    class RLAgent:
        pass

    class RLEnvironment:
        pass

    class RLTrainer:
        pass

    class NotFoundError(Exception):
        pass

    class ValidationError(Exception):
        pass

    class ServiceError(Exception):
        pass


class TestRLEnvironment(unittest.TestCase):
    """Unit tests for RLEnvironment class."""

    def setUp(self) -> Any:
        """Set up test fixtures."""
        self.market_data = pd.DataFrame(
            {
                "timestamp": pd.date_range(start="2023-01-01", periods=100),
                "open": np.random.normal(100, 2, 100),
                "high": np.random.normal(102, 2, 100),
                "low": np.random.normal(98, 2, 100),
                "close": np.random.normal(100, 2, 100),
                "volume": np.random.normal(1000000, 100000, 100),
                "symbol": "AAPL",
            }
        )
        self.env = RLEnvironment(
            data=self.market_data,
            initial_balance=10000.0,
            transaction_fee=0.001,
            window_size=10,
        )

    def test_init(self) -> Any:
        """Test RLEnvironment initialization."""
        env = RLEnvironment(
            data=self.market_data,
            initial_balance=10000.0,
            transaction_fee=0.001,
            window_size=10,
        )
        self.assertEqual(env.initial_balance, 10000.0)
        self.assertEqual(env.balance, 10000.0)
        self.assertEqual(env.transaction_fee, 0.001)
        self.assertEqual(env.window_size, 10)
        self.assertEqual(env.current_step, 0)
        self.assertEqual(env.position, 0)
        self.assertEqual(env.position_price, 0.0)
        self.assertEqual(env.total_reward, 0.0)
        self.assertEqual(env.done, False)

    def test_reset(self) -> Any:
        """Test environment reset."""
        self.env.balance = 9000.0
        self.env.current_step = 50
        self.env.position = 100
        self.env.position_price = 95.0
        self.env.total_reward = 500.0
        self.env.done = True
        state = self.env.reset()
        self.assertEqual(self.env.balance, 10000.0)
        self.assertEqual(self.env.current_step, 0)
        self.assertEqual(self.env.position, 0)
        self.assertEqual(self.env.position_price, 0.0)
        self.assertEqual(self.env.total_reward, 0.0)
        self.assertEqual(self.env.done, False)
        self.assertIsInstance(state, np.ndarray)
        self.assertEqual(state.shape[0], self.env.window_size)

    def test_step_buy(self) -> Any:
        """Test environment step with buy action."""
        self.env.reset()
        initial_balance = self.env.balance
        state, reward, done, info = self.env.step(1)
        self.assertIsInstance(state, np.ndarray)
        self.assertEqual(state.shape[0], self.env.window_size)
        self.assertIsInstance(reward, float)
        self.assertIsInstance(done, bool)
        self.assertIsInstance(info, dict)
        self.assertIn("balance", info)
        self.assertIn("position", info)
        self.assertIn("position_value", info)
        self.assertIn("total_value", info)
        self.assertGreater(self.env.position, 0)
        self.assertGreater(self.env.position_price, 0.0)
        self.assertLess(self.env.balance, initial_balance)

    def test_step_sell(self) -> Any:
        """Test environment step with sell action."""
        self.env.reset()
        self.env.step(1)
        balance_after_buy = self.env.balance
        self.env.position
        state, reward, done, info = self.env.step(2)
        self.assertIsInstance(state, np.ndarray)
        self.assertEqual(state.shape[0], self.env.window_size)
        self.assertIsInstance(reward, float)
        self.assertIsInstance(done, bool)
        self.assertIsInstance(info, dict)
        self.assertIn("balance", info)
        self.assertIn("position", info)
        self.assertIn("position_value", info)
        self.assertIn("total_value", info)
        self.assertEqual(self.env.position, 0)
        self.assertEqual(self.env.position_price, 0.0)
        self.assertGreater(self.env.balance, balance_after_buy)

    def test_step_hold(self) -> Any:
        """Test environment step with hold action."""
        self.env.reset()
        initial_balance = self.env.balance
        initial_step = self.env.current_step
        state, reward, done, info = self.env.step(0)
        self.assertIsInstance(state, np.ndarray)
        self.assertEqual(state.shape[0], self.env.window_size)
        self.assertIsInstance(reward, float)
        self.assertIsInstance(done, bool)
        self.assertIsInstance(info, dict)
        self.assertIn("balance", info)
        self.assertIn("position", info)
        self.assertIn("position_value", info)
        self.assertIn("total_value", info)
        self.assertEqual(self.env.position, 0)
        self.assertEqual(self.env.position_price, 0.0)
        self.assertEqual(self.env.balance, initial_balance)
        self.assertEqual(self.env.current_step, initial_step + 1)

    def test_step_done(self) -> Any:
        """Test environment step until done."""
        self.env.reset()
        done = False
        while not done:
            _, _, done, _ = self.env.step(0)
        self.assertTrue(self.env.done)
        self.assertEqual(self.env.current_step, len(self.env.data) - 1)


class TestRLAgent(unittest.TestCase):
    """Unit tests for RLAgent class."""

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
        self.agent = RLAgent(
            state_size=10,
            action_size=3,
            model_id="rl_model1",
            config_manager=self.config_manager,
            db_manager=self.db_manager,
        )

    def test_init(self) -> Any:
        """Test RLAgent initialization."""
        agent = RLAgent(
            state_size=10,
            action_size=3,
            model_id="rl_model1",
            config_manager=self.config_manager,
            db_manager=self.db_manager,
        )
        self.assertEqual(agent.state_size, 10)
        self.assertEqual(agent.action_size, 3)
        self.assertEqual(agent.model_id, "rl_model1")
        self.assertEqual(agent.config_manager, self.config_manager)
        self.assertEqual(agent.db_manager, self.db_manager)
        self.assertIsNotNone(agent.model)
        self.assertIsNotNone(agent.target_model)
        self.assertIsNotNone(agent.memory)

    @patch("numpy.random.rand")
    def test_act_explore(self, mock_rand: Any) -> Any:
        """Test agent act method with exploration."""
        mock_rand.return_value = 0.01
        state = np.random.random((1, 10))
        action = self.agent.act(state)
        self.assertIsInstance(action, int)
        self.assertGreaterEqual(action, 0)
        self.assertLess(action, 3)

    @patch("numpy.random.rand")
    def test_act_exploit(self, mock_rand: Any) -> Any:
        """Test agent act method with exploitation."""
        mock_rand.return_value = 0.9
        self.agent.model.predict = MagicMock(return_value=np.array([[0.1, 0.8, 0.1]]))
        state = np.random.random((1, 10))
        action = self.agent.act(state)
        self.assertEqual(action, 1)

    def test_remember(self) -> Any:
        """Test agent remember method."""
        state = np.random.random(10)
        action = 1
        reward = 0.5
        next_state = np.random.random(10)
        done = False
        self.agent.remember(state, action, reward, next_state, done)
        self.assertEqual(len(self.agent.memory), 1)

    @patch("numpy.random.choice")
    def test_replay(self, mock_choice: Any) -> Any:
        """Test agent replay method."""
        batch_size = 32
        experiences = []
        for _ in range(batch_size):
            state = np.random.random(10)
            action = np.random.randint(0, 3)
            reward = np.random.random()
            next_state = np.random.random(10)
            done = np.random.choice([True, False])
            experiences.append((state, action, reward, next_state, done))
        for exp in experiences:
            self.agent.memory.append(exp)
        mock_choice.return_value = np.arange(batch_size)
        self.agent.model.predict = MagicMock(
            return_value=np.random.random((batch_size, 3))
        )
        self.agent.target_model.predict = MagicMock(
            return_value=np.random.random((batch_size, 3))
        )
        self.agent.replay(batch_size)
        self.agent.model.fit.assert_called_once()

    def test_load_model(self) -> Any:
        """Test agent load_model method."""
        with patch("os.path.exists", return_value=True):
            with patch("tensorflow.keras.models.load_model") as mock_load_model:
                self.agent.load_model()
                mock_load_model.assert_called()

    def test_save_model(self) -> Any:
        """Test agent save_model method."""
        with patch("os.path.exists", return_value=True):
            self.agent.model.save = MagicMock()
            self.agent.save_model()
            self.agent.model.save.assert_called_once()


class TestRLTrainer(unittest.TestCase):
    """Unit tests for RLTrainer class."""

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
        self.market_data = pd.DataFrame(
            {
                "timestamp": pd.date_range(start="2023-01-01", periods=100),
                "open": np.random.normal(100, 2, 100),
                "high": np.random.normal(102, 2, 100),
                "low": np.random.normal(98, 2, 100),
                "close": np.random.normal(100, 2, 100),
                "volume": np.random.normal(1000000, 100000, 100),
                "symbol": "AAPL",
            }
        )
        self.trainer = RLTrainer(
            config_manager=self.config_manager, db_manager=self.db_manager
        )

    def test_init(self) -> Any:
        """Test RLTrainer initialization."""
        trainer = RLTrainer(
            config_manager=self.config_manager, db_manager=self.db_manager
        )
        self.assertEqual(trainer.config_manager, self.config_manager)
        self.assertEqual(trainer.db_manager, self.db_manager)

    @patch("backend.ai_engine.reinforcement_learning.RLEnvironment")
    @patch("backend.ai_engine.reinforcement_learning.RLAgent")
    def test_train(self, mock_agent_class: Any, mock_env_class: Any) -> Any:
        """Test trainer train method."""
        mock_env = MagicMock()
        mock_env.reset.return_value = np.random.random(10)
        mock_env.step.return_value = (np.random.random(10), 0.5, False, {})
        mock_env_class.return_value = mock_env
        mock_agent = MagicMock()
        mock_agent.act.return_value = 1
        mock_agent_class.return_value = mock_agent
        result = self.trainer.train(
            model_id="rl_model1",
            data=self.market_data,
            episodes=2,
            batch_size=32,
            window_size=10,
            initial_balance=10000.0,
            transaction_fee=0.001,
        )
        self.assertIsInstance(result, dict)
        self.assertIn("model_id", result)
        self.assertIn("episodes", result)
        self.assertIn("final_reward", result)
        self.assertIn("training_time", result)
        mock_agent.act.assert_called()
        mock_agent.remember.assert_called()
        mock_agent.replay.assert_called()
        mock_agent.save_model.assert_called_once()

    @patch("backend.ai_engine.reinforcement_learning.RLEnvironment")
    @patch("backend.ai_engine.reinforcement_learning.RLAgent")
    def test_evaluate(self, mock_agent_class: Any, mock_env_class: Any) -> Any:
        """Test trainer evaluate method."""
        mock_env = MagicMock()
        mock_env.reset.return_value = np.random.random(10)
        mock_env.step.return_value = (
            np.random.random(10),
            0.5,
            False,
            {
                "balance": 10000.0,
                "position": 0,
                "position_value": 0.0,
                "total_value": 10000.0,
            },
        )
        mock_env_class.return_value = mock_env
        mock_agent = MagicMock()
        mock_agent.act.return_value = 1
        mock_agent_class.return_value = mock_agent
        result = self.trainer.evaluate(
            model_id="rl_model1",
            data=self.market_data,
            window_size=10,
            initial_balance=10000.0,
            transaction_fee=0.001,
        )
        self.assertIsInstance(result, dict)
        self.assertIn("model_id", result)
        self.assertIn("initial_balance", result)
        self.assertIn("final_balance", result)
        self.assertIn("total_reward", result)
        self.assertIn("profit", result)
        self.assertIn("profit_percent", result)
        self.assertIn("trades", result)
        mock_agent.act.assert_called()
        mock_agent.load_model.assert_called_once()


if __name__ == "__main__":
    unittest.main()
