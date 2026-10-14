from typing import Any, Dict, Optional

import numpy as np

TRADING_DAYS = 252


def _drawdown(equity: np.ndarray) -> float:
    peak = np.maximum.accumulate(equity)
    return float(np.min(equity / peak - 1.0)) if len(equity) else 0.0


def performance_summary(
    returns: np.ndarray, periods_per_year: int = TRADING_DAYS
) -> Dict[str, Any]:
    returns = np.asarray(returns, dtype=np.float64)
    if len(returns) == 0:
        return {"periods": 0}
    equity = np.cumprod(1.0 + returns)
    total = float(equity[-1] - 1.0)
    years = len(returns) / periods_per_year
    annual = (
        float(equity[-1] ** (1.0 / years) - 1.0)
        if years > 0 and equity[-1] > 0
        else 0.0
    )
    vol = float(returns.std(ddof=1)) if len(returns) > 1 else 0.0
    sharpe = float(returns.mean() / vol * np.sqrt(periods_per_year)) if vol > 0 else 0.0
    downside = returns[returns < 0]
    dvol = float(downside.std(ddof=1)) if len(downside) > 1 else 0.0
    sortino = (
        float(returns.mean() / dvol * np.sqrt(periods_per_year)) if dvol > 0 else 0.0
    )
    max_dd = _drawdown(equity)
    calmar = float(annual / abs(max_dd)) if max_dd < 0 else 0.0
    active = returns[returns != 0]
    return {
        "periods": int(len(returns)),
        "total_return": total,
        "annualized_return": annual,
        "annualized_volatility": float(vol * np.sqrt(periods_per_year)),
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": max_dd,
        "calmar": calmar,
        "win_rate": float((active > 0).mean()) if len(active) else 0.0,
    }


def backtest_signals(
    prices: np.ndarray,
    expected_returns: np.ndarray,
    threshold: float = 0.0,
    fee: float = 0.001,
    allow_short: bool = False,
    periods_per_year: int = TRADING_DAYS,
) -> Dict[str, Any]:
    prices = np.asarray(prices, dtype=np.float64)
    expected = np.asarray(expected_returns, dtype=np.float64)
    n = min(len(prices), len(expected))
    if n < 3:
        return {"periods": 0}
    prices, expected = prices[:n], expected[:n]
    position = np.zeros(n)
    position[expected > threshold] = 1.0
    if allow_short:
        position[expected < -threshold] = -1.0
    asset = np.zeros(n)
    asset[1:] = prices[1:] / prices[:-1] - 1.0
    held = np.zeros(n)
    held[1:] = position[:-1]
    turnover = np.abs(np.diff(np.concatenate([[0.0], held])))
    strategy = held * asset - turnover * fee
    summary = performance_summary(strategy[1:], periods_per_year)
    summary["buy_and_hold"] = performance_summary(asset[1:], periods_per_year)
    summary["trades"] = int(np.sum(turnover > 0))
    summary["exposure"] = float(np.mean(held != 0))
    summary["equity_curve"] = np.cumprod(1.0 + strategy[1:]).tolist()
    return summary


def optimal_threshold(
    prices: np.ndarray, expected_returns: np.ndarray, fee: float = 0.001
) -> Optional[float]:
    candidates = np.quantile(np.abs(expected_returns), [0.0, 0.25, 0.5, 0.75])
    best, best_sharpe = None, -np.inf
    for threshold in candidates:
        result = backtest_signals(prices, expected_returns, float(threshold), fee)
        sharpe = result.get("sharpe", -np.inf)
        if sharpe > best_sharpe:
            best, best_sharpe = float(threshold), sharpe
    return best
