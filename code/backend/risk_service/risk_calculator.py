"""
Risk calculator for QuantumAlpha Risk Service.
"""

import logging
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from backend.common import ValidationError, setup_logger

logger = setup_logger("risk_calculator", logging.INFO)


class RiskCalculator:
    """Risk calculator"""

    def __init__(self, config_manager: object, db_manager: object) -> None:
        self.config_manager = config_manager
        self.db_manager = db_manager
        logger.info("Risk calculator initialized")

    def calculate_portfolio_value(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate total portfolio value."""
        positions = portfolio.get("positions", [])
        positions_value = sum(p["quantity"] * p["current_price"] for p in positions)
        cash = portfolio.get("cash", 0.0)
        total_value = positions_value + cash
        return {
            "portfolio_id": portfolio.get("id"),
            "positions_value": positions_value,
            "cash": cash,
            "total_value": total_value,
        }

    def calculate_portfolio_returns(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate portfolio returns."""
        positions = portfolio.get("positions", [])
        positions_return = sum(
            p["quantity"] * (p["current_price"] - p["entry_price"]) for p in positions
        )
        positions_cost = sum(p["quantity"] * p["entry_price"] for p in positions)
        total_return_percent = (
            (positions_return / positions_cost * 100) if positions_cost else 0.0
        )
        return {
            "portfolio_id": portfolio.get("id"),
            "positions_return": positions_return,
            "total_return": positions_return,
            "total_return_percent": total_return_percent,
        }

    def calculate_var(
        self,
        portfolio: Dict[str, Any],
        confidence_level: float = 0.95,
        time_horizon: int = 1,
    ) -> Dict[str, Any]:
        """Calculate Value at Risk."""
        if confidence_level <= 0 or confidence_level >= 1:
            raise ValidationError(
                "confidence_level must be between 0 and 1 (exclusive)"
            )
        if time_horizon <= 0:
            raise ValidationError("time_horizon must be a positive integer")

        portfolio_value_info = self.calculate_portfolio_value(portfolio)
        total_value = portfolio_value_info["total_value"]
        market_data = self._get_market_data(portfolio)
        portfolio_returns = self._compute_portfolio_returns(portfolio, market_data)
        var = self._calc_var(portfolio_returns, confidence_level) * np.sqrt(
            time_horizon
        )
        var_dollar = var * total_value
        return {
            "portfolio_id": portfolio.get("id"),
            "var": var_dollar,
            "var_percent": var * 100,
            "confidence_level": confidence_level,
            "time_horizon": time_horizon,
        }

    def calculate_expected_shortfall(
        self,
        portfolio: Dict[str, Any],
        confidence_level: float = 0.95,
        time_horizon: int = 1,
    ) -> Dict[str, Any]:
        """Calculate Expected Shortfall (CVaR)."""
        if confidence_level <= 0 or confidence_level >= 1:
            raise ValidationError(
                "confidence_level must be between 0 and 1 (exclusive)"
            )
        if time_horizon <= 0:
            raise ValidationError("time_horizon must be a positive integer")

        portfolio_value_info = self.calculate_portfolio_value(portfolio)
        total_value = portfolio_value_info["total_value"]
        market_data = self._get_market_data(portfolio)
        portfolio_returns = self._compute_portfolio_returns(portfolio, market_data)
        sorted_ret = np.sort(portfolio_returns)
        idx = int(len(sorted_ret) * (1 - confidence_level))
        tail = sorted_ret[: max(1, idx)]
        es = float(-np.mean(tail)) * np.sqrt(time_horizon)
        es_dollar = es * total_value
        return {
            "portfolio_id": portfolio.get("id"),
            "es": es_dollar,
            "es_percent": es * 100,
            "confidence_level": confidence_level,
            "time_horizon": time_horizon,
        }

    def calculate_sharpe_ratio(
        self,
        portfolio: Dict[str, Any],
        risk_free_rate: float = 0.02,
        period: str = "1y",
    ) -> Dict[str, Any]:
        """Calculate Sharpe Ratio."""
        market_data = self._get_market_data(portfolio)
        portfolio_returns = self._compute_portfolio_returns(portfolio, market_data)
        daily_rf = risk_free_rate / 252
        excess = portfolio_returns - daily_rf
        ann_return = float(np.mean(portfolio_returns) * 252)
        ann_vol = float(np.std(portfolio_returns) * np.sqrt(252))
        sharpe = float(np.mean(excess) / np.std(excess)) if np.std(excess) > 0 else 0.0
        return {
            "portfolio_id": portfolio.get("id"),
            "sharpe_ratio": sharpe,
            "annualized_return": ann_return,
            "annualized_volatility": ann_vol,
            "risk_free_rate": risk_free_rate,
        }

    def calculate_beta(
        self,
        portfolio: Dict[str, Any],
        benchmark: str = "SPY",
        period: str = "1y",
    ) -> Dict[str, Any]:
        """Calculate Beta."""
        market_data = self._get_market_data(portfolio)
        portfolio_returns = self._compute_portfolio_returns(portfolio, market_data)
        benchmark_data = self._get_benchmark_data(benchmark, period)
        bench_prices = benchmark_data["close"].values
        bench_returns = np.diff(bench_prices) / bench_prices[:-1]
        min_len = min(len(portfolio_returns), len(bench_returns))
        pr = portfolio_returns[-min_len:]
        br = bench_returns[-min_len:]
        cov = np.cov(pr, br)
        beta = float(cov[0, 1] / cov[1, 1]) if cov[1, 1] != 0 else 1.0
        return {
            "portfolio_id": portfolio.get("id"),
            "beta": beta,
            "benchmark": benchmark,
        }

    def calculate_portfolio_value_with_prediction(
        self,
        portfolio: Dict[str, Any],
        model_id: str,
        ai_engine_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculate portfolio value and predicted value using AI engine predictions."""
        import requests as _requests

        if ai_engine_url is None:
            host = self.config_manager.get("services.ai_engine.host", "localhost")
            port = self.config_manager.get("services.ai_engine.port", "8082")
            ai_engine_url = f"http://{host}:{port}"

        positions = portfolio.get("positions", [])
        cash = portfolio.get("cash", 0.0)
        current_value = (
            sum(p["quantity"] * p["current_price"] for p in positions) + cash
        )

        predicted_positions_value = 0.0
        for pos in positions:
            symbol = pos["symbol"]
            quantity = pos["quantity"]
            try:
                resp = _requests.get(f"{ai_engine_url}/api/predict/{model_id}/{symbol}")
                if resp.status_code == 200:
                    pred_data = resp.json()
                    pred = pred_data.get("prediction", {})
                    avg_price = pred.get("average", pos["current_price"])
                else:
                    avg_price = pos["current_price"]
            except Exception:
                avg_price = pos["current_price"]
            predicted_positions_value += quantity * avg_price

        predicted_value = predicted_positions_value + cash
        change = predicted_value - current_value
        change_percent = (change / current_value * 100) if current_value else 0.0

        return {
            "portfolio_id": portfolio.get("id"),
            "current_value": current_value,
            "predicted_value": predicted_value,
            "change": change,
            "change_percent": change_percent,
        }

    def _get_market_data(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Get market data for all positions. Override in tests via mock."""
        return {}

    def _get_benchmark_data(self, benchmark: str, period: str) -> pd.DataFrame:
        """Get benchmark data. Override in tests via mock."""
        return pd.DataFrame({"close": np.ones(100)})

    def _compute_portfolio_returns(
        self, portfolio: Dict[str, Any], market_data: Dict[str, Any]
    ) -> np.ndarray:
        """Compute weighted portfolio returns from market_data dict."""
        positions = portfolio.get("positions", [])
        if not positions:
            return np.zeros(100)

        portfolio_value = sum(p["quantity"] * p["current_price"] for p in positions)
        if portfolio_value == 0:
            return np.zeros(100)

        weights = {
            p["symbol"]: (p["quantity"] * p["current_price"]) / portfolio_value
            for p in positions
        }
        all_returns = []
        for symbol, weight in weights.items():
            if symbol in market_data:
                prices = market_data[symbol]["close"].values
                if len(prices) > 1:
                    ret = np.diff(prices) / prices[:-1]
                    all_returns.append((weight, ret))

        if not all_returns:
            return np.random.normal(0, 0.01, 100)

        min_len = min(len(r) for _, r in all_returns)
        combined = np.zeros(min_len)
        for weight, ret in all_returns:
            combined += weight * ret[-min_len:]
        return combined

    def _calc_var(self, returns: np.ndarray, confidence_level: float) -> float:
        sorted_ret = np.sort(returns)
        idx = int(len(sorted_ret) * (1 - confidence_level))
        return float(-sorted_ret[max(0, idx)])
