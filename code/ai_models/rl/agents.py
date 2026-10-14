import json
import os
from typing import Any, Callable, Dict, List

import numpy as np
from ai_models.core.exceptions import DependencyError, ValidationError

ALGORITHMS = ("q_learning", "ppo", "a2c", "dqn", "sac")
CONTINUOUS = {"sac"}
PREFERRED_STATE_COLUMNS = (
    "rsi_14",
    "macd",
    "sma_20",
    "momentum_10",
    "bb_pct_b",
    "ret_1",
    "volatility_20",
)


class Agent:
    algorithm = ""

    def learn(
        self, env_factory: Callable[[], Any], total_timesteps: int, seed: int = 42
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def predict(self, observation: np.ndarray) -> Any:
        raise NotImplementedError

    def save(self, directory: str) -> None:
        raise NotImplementedError

    @classmethod
    def load(
        cls, directory: str, params: Dict[str, Any], columns: List[str]
    ) -> "Agent":
        raise NotImplementedError


class QLearningAgent(Agent):
    algorithm = "q_learning"
    BINS = 5
    LIMIT = 2.5

    def __init__(self, params: Dict[str, Any], columns: List[str]) -> None:
        self.params = dict(params)
        self.columns = list(columns)
        preferred = [c for c in PREFERRED_STATE_COLUMNS if c in columns]
        chosen = (preferred + [c for c in columns if c not in preferred])[
            : int(params.get("state_features", 4))
        ]
        self.state_indices = [columns.index(c) for c in chosen]
        self.state_columns = chosen
        n_states = self.BINS ** len(self.state_indices) * 2
        self.q = np.zeros((n_states, 3), dtype=np.float64)

    def _state(self, observation: np.ndarray) -> int:
        edges = np.linspace(-self.LIMIT, self.LIMIT, self.BINS - 1)
        index = 0
        for i in self.state_indices:
            index = index * self.BINS + int(np.searchsorted(edges, observation[i]))
        in_position = 1 if observation[len(self.columns)] > 0.5 else 0
        return index * 2 + in_position

    def learn(
        self, env_factory: Callable[[], Any], total_timesteps: int, seed: int = 42
    ) -> Dict[str, Any]:
        rng = np.random.default_rng(seed)
        alpha = float(self.params.get("alpha", 0.1))
        gamma = float(self.params.get("gamma", 0.95))
        eps_start = float(self.params.get("epsilon_start", 1.0))
        eps_end = float(self.params.get("epsilon_end", 0.05))
        env = env_factory()
        steps_done = 0
        rewards: List[float] = []
        episode = 0
        while steps_done < total_timesteps:
            obs, _ = env.reset(seed=seed + episode)
            state = self._state(obs)
            done = False
            total = 0.0
            while not done and steps_done < total_timesteps:
                progress = steps_done / max(1, total_timesteps)
                epsilon = eps_start + (eps_end - eps_start) * progress
                action = (
                    int(rng.integers(3))
                    if rng.random() < epsilon
                    else int(np.argmax(self.q[state]))
                )
                obs, reward, terminated, truncated, _ = env.step(action)
                next_state = self._state(obs)
                target = reward + (
                    0.0 if terminated else gamma * float(np.max(self.q[next_state]))
                )
                self.q[state, action] += alpha * (target - self.q[state, action])
                state = next_state
                total += reward
                steps_done += 1
                done = terminated or truncated
            rewards.append(total)
            episode += 1
        tail = rewards[-10:] if rewards else [0.0]
        return {
            "episodes": episode,
            "mean_episode_reward": float(np.mean(tail)),
            "visited_states": int(np.count_nonzero(np.abs(self.q).sum(axis=1))),
        }

    def predict(self, observation: np.ndarray) -> int:
        return int(np.argmax(self.q[self._state(observation)]))

    def save(self, directory: str) -> None:
        os.makedirs(directory, exist_ok=True)
        np.save(os.path.join(directory, "q_table.npy"), self.q)
        with open(os.path.join(directory, "agent.json"), "w") as handle:
            json.dump(
                {"state_columns": self.state_columns, "params": self.params}, handle
            )

    @classmethod
    def load(
        cls, directory: str, params: Dict[str, Any], columns: List[str]
    ) -> "QLearningAgent":
        path = os.path.join(directory, "q_table.npy")
        if not os.path.exists(path):
            raise ValidationError(f"Agent artifact missing: {path}")
        with open(os.path.join(directory, "agent.json")) as handle:
            saved = json.load(handle)
        agent = cls({**saved.get("params", {}), **params}, columns)
        agent.state_columns = saved["state_columns"]
        agent.state_indices = [columns.index(c) for c in agent.state_columns]
        agent.q = np.load(path)
        return agent


class SB3Agent(Agent):
    def __init__(self, algorithm: str, params: Dict[str, Any]) -> None:
        self.algorithm = algorithm
        self.params = dict(params)
        self.model: Any = None

    @staticmethod
    def _classes() -> Dict[str, Any]:
        try:
            from stable_baselines3 import A2C, DQN, PPO, SAC
        except ImportError as exc:
            raise DependencyError(
                "stable-baselines3 is required for this algorithm",
                {"install": "stable-baselines3 torch"},
            ) from exc
        return {"ppo": PPO, "a2c": A2C, "dqn": DQN, "sac": SAC}

    def learn(
        self, env_factory: Callable[[], Any], total_timesteps: int, seed: int = 42
    ) -> Dict[str, Any]:
        from stable_baselines3.common.vec_env import DummyVecEnv

        cls = self._classes()[self.algorithm]
        env = DummyVecEnv([env_factory])
        kwargs = {
            k: v
            for k, v in self.params.items()
            if k in ("learning_rate", "gamma", "batch_size", "n_steps", "ent_coef")
        }
        self.model = cls("MlpPolicy", env, verbose=0, seed=seed, **kwargs)
        self.model.learn(total_timesteps=total_timesteps)
        return {"timesteps": int(total_timesteps)}

    def predict(self, observation: np.ndarray) -> Any:
        action, _ = self.model.predict(observation, deterministic=True)
        return action

    def save(self, directory: str) -> None:
        os.makedirs(directory, exist_ok=True)
        self.model.save(os.path.join(directory, "agent"))

    @classmethod
    def load_for(
        cls, algorithm: str, directory: str, params: Dict[str, Any]
    ) -> "SB3Agent":
        path = os.path.join(directory, "agent.zip")
        if not os.path.exists(path):
            raise ValidationError(f"Agent artifact missing: {path}")
        agent = cls(algorithm, params)
        agent.model = cls._classes()[algorithm].load(path)
        return agent


def create_agent(algorithm: str, params: Dict[str, Any], columns: List[str]) -> Agent:
    if algorithm not in ALGORITHMS:
        raise ValidationError(
            f"Invalid algorithm '{algorithm}'", {"supported": list(ALGORITHMS)}
        )
    if algorithm == "q_learning":
        return QLearningAgent(params, columns)
    return SB3Agent(algorithm, params)


def load_agent(
    algorithm: str, directory: str, params: Dict[str, Any], columns: List[str]
) -> Agent:
    if algorithm == "q_learning":
        return QLearningAgent.load(directory, params, columns)
    return SB3Agent.load_for(algorithm, directory, params)
