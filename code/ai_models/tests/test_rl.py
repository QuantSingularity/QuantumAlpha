import numpy as np
import pytest
from ai_models.core.exceptions import ValidationError
from ai_models.rl.agents import QLearningAgent, create_agent
from ai_models.rl.environment import TradingEnv


def _env(n=200, mode="discrete", fee=0.001):
    rng = np.random.default_rng(0)
    prices = 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.01, n)))
    return TradingEnv(rng.normal(size=(n, 4)), prices, 10000.0, fee, mode)


def test_env_discrete_accounting_and_no_lookahead():
    env = _env()
    obs, _ = env.reset(seed=1)
    assert obs.shape == (6,)
    obs, reward, done, _, info = env.step(1)
    expected = (env.prices[1] / env.prices[0] - 1.0) - env.transaction_fee
    assert info["portfolio_value"] == pytest.approx(10000.0 * (1 + expected))
    assert env.exposure == 1.0
    env.step(0)
    assert env.exposure == 1.0
    env.step(2)
    assert env.exposure == 0.0


def test_env_runs_to_termination_and_continuous_mode():
    env = _env(mode="continuous")
    env.reset()
    done = False
    steps = 0
    while not done:
        _, _, done, _, _ = env.step(np.array([0.5], dtype=np.float32))
        steps += 1
    assert steps == len(env.prices) - 1


def test_env_rejects_bad_inputs():
    with pytest.raises(ValueError):
        TradingEnv(np.zeros((5, 2)), np.ones(4))
    with pytest.raises(ValueError):
        TradingEnv(np.zeros((5, 2)), np.ones(5), action_mode="x")


def test_q_learning_learns_and_roundtrips(tmp_path):
    columns = ["ret_1", "rsi_14", "macd", "sma_20"]
    rng = np.random.default_rng(5)
    n = 400
    signal = rng.normal(size=n)
    prices = 100 * np.exp(np.cumsum(np.concatenate([[0], signal[:-1] * 0.01])))
    features = np.column_stack(
        [signal, rng.normal(size=n), rng.normal(size=n), rng.normal(size=n)]
    )

    def factory():
        return TradingEnv(features, prices, 10000.0, 0.0, "discrete")

    agent = create_agent("q_learning", {}, columns)
    summary = agent.learn(factory, 20000, seed=3)
    assert summary["visited_states"] > 0
    env = factory()
    obs, _ = env.reset()
    done = False
    while not done:
        obs, _, done, _, _ = env.step(agent.predict(obs))
    assert env.value > 10000.0
    agent.save(str(tmp_path))
    restored = QLearningAgent.load(str(tmp_path), {}, columns)
    assert np.array_equal(agent.q, restored.q)


def test_invalid_algorithm():
    with pytest.raises(ValidationError):
        create_agent("nope", {}, ["a"])


def test_rl_api_flow(client):
    created = client.post(
        "/api/rl/models", json={"name": "rl", "algorithm": "q_learning"}
    )
    assert created.status_code == 201
    model_id = created.get_json()["id"]
    assert created.get_json()["algorithm"] == "q_learning"
    assert (
        client.post(
            "/api/rl/models", json={"name": "x", "algorithm": "bogus"}
        ).status_code
        == 400
    )
    trained = client.post(
        "/api/rl/train",
        json={
            "model_id": model_id,
            "symbol": "AAPL",
            "period": "3y",
            "total_timesteps": 3000,
        },
    )
    assert trained.status_code == 200, trained.get_json()
    body = trained.get_json()
    assert (
        "test" in body["metrics"] and "buy_and_hold_return" in body["metrics"]["test"]
    )
    act = client.post(
        "/api/rl/act", json={"model_id": model_id, "symbol": "AAPL", "period": "1y"}
    ).get_json()
    assert act["recommendation"]["action"] in ("buy", "sell", "hold")
    assert act["final_balance"] > 0 and len(act["history"]) > 0
    assert client.get("/api/rl/models").get_json()[0]["id"] == model_id
    assert client.delete(f"/api/rl/models/{model_id}").status_code == 200
    assert (
        client.post(
            "/api/rl/act", json={"model_id": "missing", "symbol": "AAPL"}
        ).status_code
        == 404
    )
