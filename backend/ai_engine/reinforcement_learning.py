"""
Reinforcement learning service for QuantumAlpha AI Engine.
Handles reinforcement learning models for trading.
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


try:
    import gymnasium as gym
    from gymnasium import spaces

    _GYM_TUPLE_LEN = 5
    _USING_GYMNASIUM = True
except ImportError:
    import gym
    from gym import spaces

    _GYM_TUPLE_LEN = 4
    _USING_GYMNASIUM = False

import numpy as np
import pandas as pd
import requests
from stable_baselines3 import A2C, DQN, PPO, SAC
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.evaluation import evaluate_policy

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import NotFoundError, ServiceError, ValidationError, setup_logger


logger = setup_logger("reinforcement_learning", logging.INFO)

_ALGORITHM_MAP: Dict[str, Any] = {
    "ppo": PPO,
    "a2c": A2C,
    "dqn": DQN,
    "sac": SAC,
}


class TradingEnvironment(gym.Env):
    """
    Custom OpenAI Gym / Gymnasium trading environment.

    Action space  : Discrete(3)  — 0 = hold, 1 = buy, 2 = sell
    Observation   : market features + [balance, position, position_value]
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        df: pd.DataFrame,
        initial_balance: float = 10_000.0,
        transaction_fee: float = 0.001,
    ) -> None:
        super().__init__()
        self.df = df.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.transaction_fee = transaction_fee

        n_features = df.shape[1] + 3
        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(n_features,), dtype=np.float32
        )
        self._reset_state()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _reset_state(self) -> None:
        self.current_step = 0
        self.balance = float(self.initial_balance)
        self.position = 0.0
        self.position_value = 0.0
        self.done = False
        self.history: List[Dict[str, Any]] = []

    def _get_observation(self) -> np.ndarray:
        market_data = self.df.iloc[self.current_step].values.astype(np.float32)
        return np.append(
            market_data,
            [self.balance, self.position, self.position_value],
        ).astype(np.float32)

    def _portfolio_value(self, price: float) -> float:
        return self.balance + self.position * price

    # ------------------------------------------------------------------
    # Gym / Gymnasium API
    # ------------------------------------------------------------------

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Reset the environment to the initial state.

        Returns gymnasium-style (obs, info) tuple when gymnasium is
        installed; plain obs otherwise — stable-baselines3 handles both.
        """
        super().reset(seed=seed)
        self._reset_state()
        obs = self._get_observation()
        if _USING_GYMNASIUM:
            return obs, {}
        return obs

    def step(self, action: int) -> Any:
        """Execute one trading step.

        Returns a 5-tuple (obs, reward, terminated, truncated, info) under
        gymnasium, or a 4-tuple (obs, reward, done, info) under legacy gym.
        stable-baselines3 >= 2.x expects the 5-tuple form.
        """
        current_price = float(self.df.iloc[self.current_step]["close"])

        # --- execute action ---
        if action == 1 and self.balance > 0:  # buy
            fee = self.balance * self.transaction_fee
            self.position = (self.balance - fee) / current_price
            self.position_value = self.position * current_price
            self.balance = 0.0

        elif action == 2 and self.position > 0:  # sell
            gross = self.position * current_price
            fee = gross * self.transaction_fee
            self.balance = gross - fee
            self.position = 0.0
            self.position_value = 0.0

        self.current_step += 1
        terminated = self.current_step >= len(self.df) - 1

        portfolio_value = self._portfolio_value(current_price)
        returns = (portfolio_value - self.initial_balance) / self.initial_balance
        reward = returns * (100.0 if terminated else 10.0)

        self.history.append(
            {
                "step": self.current_step,
                "action": int(action),
                "price": current_price,
                "balance": self.balance,
                "position": self.position,
                "position_value": self.position_value,
                "portfolio_value": portfolio_value,
                "reward": reward,
            }
        )

        obs = self._get_observation()
        info: Dict[str, Any] = {}

        if _USING_GYMNASIUM:
            return obs, reward, terminated, False, info
        return obs, reward, terminated, info

    def render(self, mode: str = "human") -> None:
        if not self.history:
            return
        step = self.history[-1]
        for key, val in step.items():
            logger.info("%s: %s", key, val)
        logger.info("---")


# =============================================================================
# ReinforcementLearningService
# =============================================================================


class ReinforcementLearningService:
    """
    Reinforcement learning service — manages model lifecycle (create, train,
    predict, update, delete) backed by a flat JSON registry on disk.

    The class was previously called ``ReinforcementLearning``; it is now
    ``ReinforcementLearningService`` to match the import in ai_engine/__init__.py:
        from .reinforcement_learning import ReinforcementLearningService
    An alias is kept for any code that still uses the old name.
    """

    def __init__(self, config_manager: Any, db_manager: Any) -> None:
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.data_service_url = (
            f"http://{config_manager.get('services.data_service.host')}"
            f":{config_manager.get('services.data_service.port')}"
        )
        self.model_dir = config_manager.get(
            "ai_engine.rl_model_dir", "backend/rl_models"
        )
        os.makedirs(self.model_dir, exist_ok=True)
        self.registry_file = os.path.join(self.model_dir, "registry.json")
        self.model_registry = self._load_registry()
        logger.info("Reinforcement learning service initialised")

    # ------------------------------------------------------------------
    # Registry helpers
    # ------------------------------------------------------------------

    def _load_registry(self) -> Dict[str, Any]:
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file) as f:
                    return json.load(f)
            except Exception as exc:
                logger.error("Error loading model registry: %s", exc)
        return {"models": {}}

    def _save_registry(self) -> None:
        try:
            with open(self.registry_file, "w") as f:
                json.dump(self.model_registry, f, indent=2)
        except Exception as exc:
            logger.error("Error saving model registry: %s", exc)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def get_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": mid,
                "name": info["name"],
                "description": info["description"],
                "algorithm": info["algorithm"],
                "status": info["status"],
                "created_at": info["created_at"],
                "updated_at": info["updated_at"],
                "metrics": info.get("metrics", {}),
            }
            for mid, info in self.model_registry["models"].items()
        ]

    def get_model(self, model_id: str) -> Dict[str, Any]:
        info = self._require_model(model_id)
        return {
            "id": model_id,
            "name": info["name"],
            "description": info["description"],
            "algorithm": info["algorithm"],
            "status": info["status"],
            "created_at": info["created_at"],
            "updated_at": info["updated_at"],
            "metrics": info.get("metrics", {}),
            "parameters": info.get("parameters", {}),
            "features": info.get("features", []),
        }

    def create_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not data.get("name"):
            raise ValidationError("Model name is required")
        algorithm = data.get("algorithm", "")
        if algorithm not in _ALGORITHM_MAP:
            raise ValidationError(
                f"Invalid algorithm '{algorithm}'. "
                f"Choose from: {sorted(_ALGORITHM_MAP)}"
            )
        model_id = f"rl_model_{uuid.uuid4().hex}"
        now = datetime.utcnow().isoformat()
        info: Dict[str, Any] = {
            "name": data["name"],
            "description": data.get("description", ""),
            "algorithm": algorithm,
            "status": "created",
            "created_at": now,
            "updated_at": now,
            "parameters": data.get("parameters", {}),
            "features": data.get("features", []),
        }
        self.model_registry["models"][model_id] = info
        self._save_registry()
        return {"id": model_id, **info}

    def update_model(self, model_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        info = self._require_model(model_id)
        for field in ("name", "description", "parameters", "features"):
            if field in data:
                info[field] = data[field]
        info["updated_at"] = datetime.utcnow().isoformat()
        self._save_registry()
        return self.get_model(model_id)

    def delete_model(self, model_id: str) -> Dict[str, Any]:
        info = self._require_model(model_id)
        for suffix in (".zip", "_params.json"):
            path = os.path.join(self.model_dir, f"{model_id}{suffix}")
            if os.path.exists(path):
                os.remove(path)
        del self.model_registry["models"][model_id]
        self._save_registry()
        return {"id": model_id, "name": info["name"], "deleted": True}

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train_model(self, model_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        info = self._require_model(model_id)
        for field in ("symbol", "timeframe", "period"):
            if not data.get(field):
                raise ValidationError(f"'{field}' is required for training")

        info["status"] = "training"
        self._save_registry()

        try:
            market_data = self._get_market_data(
                data["symbol"], data["timeframe"], data["period"]
            )
            processed_data = self._process_data(market_data, info.get("features", []))
            metrics = self._train_algorithm(model_id, info, processed_data, data)

            info["status"] = "trained"
            info["updated_at"] = datetime.utcnow().isoformat()
            info["metrics"] = metrics
            info["training_data"] = {
                k: data[k] for k in ("symbol", "timeframe", "period")
            }
            self._save_registry()
            return {
                "id": model_id,
                "name": info["name"],
                "status": "trained",
                "metrics": metrics,
            }

        except (NotFoundError, ValidationError):
            raise
        except Exception as exc:
            info["status"] = "error"
            self._save_registry()
            logger.error("Error training model %s: %s", model_id, exc)
            raise ServiceError(f"Error training model: {exc}") from exc

    def _train_algorithm(
        self,
        model_id: str,
        info: Dict[str, Any],
        data: pd.DataFrame,
        params: Dict[str, Any],
    ) -> Dict[str, float]:
        """Dispatch to the correct SB3 algorithm and return metrics."""
        algorithm = info["algorithm"]
        if algorithm not in _ALGORITHM_MAP:
            raise ValidationError(f"Unsupported algorithm: {algorithm}")

        total_timesteps = int(params.get("total_timesteps", 100_000))
        initial_balance = float(params.get("initial_balance", 10_000))
        transaction_fee = float(params.get("transaction_fee", 0.001))

        clean_data = data.dropna()
        AlgoClass = _ALGORITHM_MAP[algorithm]

        env = DummyVecEnv(
            [lambda: TradingEnvironment(clean_data, initial_balance, transaction_fee)]
        )

        log_dir = os.path.join(self.model_dir, f"{model_id}_logs")
        model = AlgoClass("MlpPolicy", env, verbose=0, tensorboard_log=log_dir)
        model.learn(total_timesteps=total_timesteps)

        model_path = os.path.join(self.model_dir, f"{model_id}.zip")
        model.save(model_path)

        # evaluate_policy handles both gym and gymnasium envs
        mean_reward, std_reward = evaluate_policy(
            model, env, n_eval_episodes=10, warn=False
        )

        params_path = os.path.join(self.model_dir, f"{model_id}_params.json")
        with open(params_path, "w") as f:
            json.dump(
                {
                    "total_timesteps": total_timesteps,
                    "initial_balance": initial_balance,
                    "transaction_fee": transaction_fee,
                },
                f,
                indent=2,
            )

        return {"mean_reward": float(mean_reward), "std_reward": float(std_reward)}

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, model_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        info = self._require_model(model_id)
        if info["status"] != "trained":
            raise ValidationError(f"Model '{model_id}' is not trained yet")
        for field in ("symbol", "timeframe", "period"):
            if not data.get(field):
                raise ValidationError(f"'{field}' is required for prediction")

        try:
            market_data = self._get_market_data(
                data["symbol"], data["timeframe"], data["period"]
            )
            processed_data = self._process_data(
                market_data, info.get("features", [])
            ).dropna()

            params_path = os.path.join(self.model_dir, f"{model_id}_params.json")
            if not os.path.exists(params_path):
                raise NotFoundError(f"Parameters file missing for model {model_id}")
            with open(params_path) as f:
                saved_params = json.load(f)

            model_path = os.path.join(self.model_dir, f"{model_id}.zip")
            if not os.path.exists(model_path):
                raise NotFoundError(f"Model file missing for model {model_id}")

            AlgoClass = _ALGORITHM_MAP.get(info["algorithm"])
            if AlgoClass is None:
                raise ValidationError(f"Unsupported algorithm: {info['algorithm']}")
            model = AlgoClass.load(model_path)

            env = TradingEnvironment(
                processed_data,
                saved_params.get("initial_balance", 10_000),
                saved_params.get("transaction_fee", 0.001),
            )

            # Handle both gymnasium (obs, info) and gym (obs) reset returns
            reset_result = env.reset()
            obs = reset_result[0] if isinstance(reset_result, tuple) else reset_result

            done = False
            actions: List[int] = []
            while not done:
                action, _ = model.predict(obs, deterministic=True)
                step_result = env.step(int(action))
                # gymnasium → 5-tuple; gym → 4-tuple
                if len(step_result) == 5:
                    obs, _, terminated, truncated, _ = step_result
                    done = terminated or truncated
                else:
                    obs, _, done, _ = step_result
                actions.append(int(action))

            history = env.history
            initial_balance = saved_params.get("initial_balance", 10_000)
            final_value = history[-1]["portfolio_value"] if history else initial_balance

            return {
                "symbol": data["symbol"],
                "timeframe": data["timeframe"],
                "initial_balance": initial_balance,
                "final_balance": final_value,
                "return": (final_value - initial_balance) / initial_balance,
                "actions": actions,
                "history": history,
            }

        except (NotFoundError, ValidationError):
            raise
        except Exception as exc:
            logger.error("Error making predictions for model %s: %s", model_id, exc)
            raise ServiceError(f"Error making predictions: {exc}") from exc

    # ------------------------------------------------------------------
    # Data helpers
    # ------------------------------------------------------------------

    def _get_market_data(
        self, symbol: str, timeframe: str, period: str
    ) -> List[Dict[str, Any]]:
        try:
            response = requests.get(
                f"{self.data_service_url}/api/market-data/{symbol}",
                params={"timeframe": timeframe, "period": period},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["data"]
        except Exception as exc:
            logger.error("Error fetching market data for %s: %s", symbol, exc)
            raise ServiceError(f"Error getting market data: {exc}") from exc

    def _process_data(
        self, market_data: List[Dict[str, Any]], features: List[str]
    ) -> pd.DataFrame:
        try:
            from data_service.data_processor import DataProcessor

            processor = DataProcessor(self.config_manager, self.db_manager)
            return processor.process_market_data(market_data, features)
        except Exception as exc:
            logger.error("Error processing market data: %s", exc)
            raise ServiceError(f"Error processing data: {exc}") from exc

    # ------------------------------------------------------------------
    # Internal guard
    # ------------------------------------------------------------------

    def _require_model(self, model_id: str) -> Dict[str, Any]:
        """Return model info dict or raise NotFoundError."""
        if model_id not in self.model_registry["models"]:
            raise NotFoundError(f"Model not found: {model_id}")
        return self.model_registry["models"][model_id]


# Backwards-compat alias — keeps any code using the old class name working
ReinforcementLearning = ReinforcementLearningService
