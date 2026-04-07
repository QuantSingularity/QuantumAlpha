"""
Stress testing for QuantumAlpha Risk Service.
"""

import logging
import os
import sys
from typing import Any, Dict, List

import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import ServiceError, setup_logger

logger = setup_logger("stress_testing", logging.INFO)


class StressTesting:
    """Stress testing"""

    def __init__(self, config_manager: Any, db_manager: Any) -> None:
        self.config_manager = config_manager
        self.db_manager = db_manager
        logger.info("Stress testing initialized")

    def _portfolio_value(self, portfolio: Dict[str, Any]) -> float:
        positions = portfolio.get("positions", [])
        return sum(
            p["quantity"] * p["current_price"] for p in positions
        ) + portfolio.get("cash", 0.0)

    def run_historical_scenario(
        self,
        portfolio: Dict[str, Any],
        scenario: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """Run a historical stress scenario."""
        try:
            historical_data = self._get_historical_data(scenario, start_date, end_date)
            positions = portfolio.get("positions", [])
            initial_value = self._portfolio_value(portfolio)
            cash = portfolio.get("cash", 0.0)
            position_results = []
            final_positions_value = 0.0

            for pos in positions:
                symbol = pos["symbol"]
                quantity = pos["quantity"]
                initial_price = pos["current_price"]
                if symbol in historical_data:
                    hist_prices = historical_data[symbol]["close"].values
                    final_price = float(hist_prices[-1])
                else:
                    final_price = initial_price

                pos_initial = quantity * initial_price
                pos_final = quantity * final_price
                final_positions_value += pos_final
                position_results.append(
                    {
                        "symbol": symbol,
                        "quantity": quantity,
                        "initial_price": initial_price,
                        "final_price": final_price,
                        "initial_value": pos_initial,
                        "final_value": pos_final,
                        "change": pos_final - pos_initial,
                        "change_percent": (
                            (pos_final - pos_initial) / pos_initial * 100
                            if pos_initial
                            else 0.0
                        ),
                    }
                )

            final_value = final_positions_value + cash
            change = final_value - initial_value
            change_percent = change / initial_value * 100 if initial_value else 0.0
            return {
                "portfolio_id": portfolio.get("id"),
                "scenario": scenario,
                "start_date": start_date,
                "end_date": end_date,
                "initial_value": initial_value,
                "final_value": final_value,
                "change": change,
                "change_percent": change_percent,
                "positions": position_results,
            }
        except Exception as e:
            logger.error(f"Error running historical scenario: {e}")
            raise ServiceError(f"Error running historical scenario: {str(e)}")

    def run_monte_carlo_simulation(
        self,
        portfolio: Dict[str, Any],
        num_simulations: int = 1000,
        time_horizon: int = 252,
        confidence_level: float = 0.95,
    ) -> Dict[str, Any]:
        """Run Monte Carlo simulation."""
        try:
            initial_value = self._portfolio_value(portfolio)
            positions = portfolio.get("positions", [])
            daily_vol = 0.01
            if positions:
                weights = np.array(
                    [p["quantity"] * p["current_price"] for p in positions]
                )
                weights = weights / weights.sum() if weights.sum() > 0 else weights
                daily_vol = float(np.sqrt(np.dot(weights**2, [0.01**2] * len(weights))))

            final_values = []
            for _ in range(num_simulations):
                daily_returns = np.random.normal(0, daily_vol, time_horizon)
                cumulative = initial_value * np.prod(1 + daily_returns)
                final_values.append(float(cumulative))

            final_values_arr = np.array(final_values)
            expected_final = float(np.mean(final_values_arr))
            sorted_vals = np.sort(final_values_arr)
            var_idx = int(num_simulations * (1 - confidence_level))
            var_value = initial_value - float(sorted_vals[max(0, var_idx)])
            expected_return = (expected_final - initial_value) / initial_value * 100
            vol = float(np.std(final_values_arr) / initial_value * 100)

            return {
                "portfolio_id": portfolio.get("id"),
                "num_simulations": num_simulations,
                "time_horizon": time_horizon,
                "confidence_level": confidence_level,
                "initial_value": initial_value,
                "expected_final_value": expected_final,
                "var": var_value,
                "var_percent": (
                    var_value / initial_value * 100 if initial_value else 0.0
                ),
                "expected_return": expected_return,
                "expected_volatility": vol,
                "simulations": final_values,
            }
        except Exception as e:
            logger.error(f"Error running Monte Carlo simulation: {e}")
            raise ServiceError(f"Error running Monte Carlo simulation: {str(e)}")

    def run_sensitivity_analysis(
        self,
        portfolio: Dict[str, Any],
        factors: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Run sensitivity analysis across factor combinations."""
        try:
            initial_value = self._portfolio_value(portfolio)
            positions = portfolio.get("positions", [])
            cash = portfolio.get("cash", 0.0)

            factor_combinations = self._cartesian(factors)
            scenarios = []
            for combo in factor_combinations:
                scenario_value = cash
                for pos in positions:
                    price_change = 0.0
                    for factor_name, factor_value in combo.items():
                        if factor_name == "market_decline":
                            price_change += factor_value / 100.0
                    new_price = pos["current_price"] * (1 + price_change)
                    scenario_value += pos["quantity"] * new_price

                change = scenario_value - initial_value
                change_percent = change / initial_value * 100 if initial_value else 0.0
                scenarios.append(
                    {
                        "factors": combo,
                        "portfolio_value": scenario_value,
                        "change": change,
                        "change_percent": change_percent,
                    }
                )

            return {
                "portfolio_id": portfolio.get("id"),
                "initial_value": initial_value,
                "scenarios": scenarios,
            }
        except Exception as e:
            logger.error(f"Error running sensitivity analysis: {e}")
            raise ServiceError(f"Error running sensitivity analysis: {str(e)}")

    def run_custom_scenario(
        self,
        portfolio: Dict[str, Any],
        scenario_name: str,
        price_changes: Dict[str, float],
    ) -> Dict[str, Any]:
        """Run a custom stress scenario with explicit per-symbol price changes."""
        try:
            positions = portfolio.get("positions", [])
            cash = portfolio.get("cash", 0.0)
            initial_value = self._portfolio_value(portfolio)
            position_results = []
            final_positions_value = 0.0

            for pos in positions:
                symbol = pos["symbol"]
                quantity = pos["quantity"]
                initial_price = pos["current_price"]
                change_pct = price_changes.get(symbol, 0.0)
                final_price = initial_price * (1 + change_pct / 100.0)
                pos_initial = quantity * initial_price
                pos_final = quantity * final_price
                final_positions_value += pos_final
                position_results.append(
                    {
                        "symbol": symbol,
                        "quantity": quantity,
                        "initial_price": initial_price,
                        "final_price": final_price,
                        "initial_value": pos_initial,
                        "final_value": pos_final,
                        "change": pos_final - pos_initial,
                        "change_percent": change_pct,
                    }
                )

            final_value = final_positions_value + cash
            change = final_value - initial_value
            change_percent = change / initial_value * 100 if initial_value else 0.0
            return {
                "portfolio_id": portfolio.get("id"),
                "scenario_name": scenario_name,
                "initial_value": initial_value,
                "final_value": final_value,
                "change": change,
                "change_percent": change_percent,
                "positions": position_results,
            }
        except Exception as e:
            logger.error(f"Error running custom scenario: {e}")
            raise ServiceError(f"Error running custom scenario: {str(e)}")

    def _get_historical_data(
        self, scenario: str, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """Override in tests via mock."""
        return {}

    def _cartesian(self, factors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate Cartesian product of factor values."""
        if not factors:
            return [{}]
        result = [{}]
        for factor in factors:
            name = factor["name"]
            values = factor["values"]
            new_result = []
            for combo in result:
                for val in values:
                    new_combo = dict(combo)
                    new_combo[name] = val
                    new_result.append(new_combo)
            result = new_result
        return result
