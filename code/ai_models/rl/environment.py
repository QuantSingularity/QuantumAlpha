from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces

    GYMNASIUM = True
except ImportError:
    GYMNASIUM = False

    class _Discrete:
        def __init__(self, n: int) -> None:
            self.n = n

        def sample(self) -> int:
            return int(np.random.randint(self.n))

    class _Box:
        def __init__(
            self,
            low: Any,
            high: Any,
            shape: Tuple[int, ...] = (),
            dtype: Any = np.float32,
        ) -> None:
            self.low, self.high, self.shape, self.dtype = low, high, shape, dtype

        def sample(self) -> np.ndarray:
            return np.random.uniform(self.low, self.high, self.shape).astype(self.dtype)

    class spaces:
        Discrete = _Discrete
        Box = _Box

    class _Env:
        def reset(
            self,
            *,
            seed: Optional[int] = None,
            options: Optional[Dict[str, Any]] = None,
        ) -> None:
            if seed is not None:
                np.random.seed(seed)

    class gym:
        Env = _Env


ACTIONS = ("hold", "buy", "sell")


class TradingEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(
        self,
        features: np.ndarray,
        prices: np.ndarray,
        initial_balance: float = 10_000.0,
        transaction_fee: float = 0.001,
        action_mode: str = "discrete",
        reward_scale: float = 100.0,
        drawdown_penalty: float = 0.0,
    ) -> None:
        super().__init__()
        features = np.asarray(features, dtype=np.float32)
        prices = np.asarray(prices, dtype=np.float64)
        if len(features) != len(prices) or len(prices) < 3:
            raise ValueError(
                "features and prices must align and contain at least 3 rows"
            )
        if action_mode not in ("discrete", "continuous"):
            raise ValueError("action_mode must be 'discrete' or 'continuous'")
        self.features = features
        self.prices = prices
        self.initial_balance = float(initial_balance)
        self.transaction_fee = float(transaction_fee)
        self.action_mode = action_mode
        self.reward_scale = float(reward_scale)
        self.drawdown_penalty = float(drawdown_penalty)
        self.n_features = features.shape[1]
        self.action_space = (
            spaces.Discrete(3)
            if action_mode == "discrete"
            else spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)
        )
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(self.n_features + 2,), dtype=np.float32
        )
        self._init_state()

    def _init_state(self) -> None:
        self.t = 0
        self.exposure = 0.0
        self.value = self.initial_balance
        self.peak = self.initial_balance
        self.entry_price = 0.0
        self.trades = 0
        self.history: List[Dict[str, Any]] = []

    def _observation(self) -> np.ndarray:
        open_pnl = 0.0
        if self.exposure > 0 and self.entry_price > 0:
            open_pnl = self.prices[self.t] / self.entry_price - 1.0
        tail = np.array([self.exposure, open_pnl], dtype=np.float32)
        return np.concatenate([self.features[self.t], tail]).astype(np.float32)

    def reset(
        self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        if GYMNASIUM:
            super().reset(seed=seed)
        elif seed is not None:
            np.random.seed(seed)
        self._init_state()
        return self._observation(), {}

    def _target_exposure(self, action: Any) -> float:
        if self.action_mode == "discrete":
            action = int(action)
            if action == 1:
                return 1.0
            if action == 2:
                return 0.0
            return self.exposure
        value = float(np.asarray(action).reshape(-1)[0])
        return float(np.clip(value, 0.0, 1.0))

    def step(self, action: Any) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        target = self._target_exposure(action)
        turnover = abs(target - self.exposure)
        if target > 0 and self.exposure == 0:
            self.entry_price = self.prices[self.t]
        if turnover > 1e-9:
            self.trades += 1
        asset_return = self.prices[self.t + 1] / self.prices[self.t] - 1.0
        step_return = target * asset_return - turnover * self.transaction_fee
        self.value *= 1.0 + step_return
        self.peak = max(self.peak, self.value)
        drawdown = self.value / self.peak - 1.0
        reward = float(
            np.log1p(max(step_return, -0.99)) * self.reward_scale
            + self.drawdown_penalty * drawdown
        )
        self.exposure = target
        if target == 0:
            self.entry_price = 0.0
        self.t += 1
        terminated = self.t >= len(self.prices) - 1
        self.history.append(
            {
                "step": self.t,
                "action": (
                    ACTIONS[int(action)]
                    if self.action_mode == "discrete"
                    else float(target)
                ),
                "price": float(self.prices[self.t]),
                "exposure": float(self.exposure),
                "portfolio_value": float(self.value),
                "reward": reward,
            }
        )
        return (
            self._observation(),
            reward,
            terminated,
            False,
            {"portfolio_value": self.value, "drawdown": drawdown},
        )
