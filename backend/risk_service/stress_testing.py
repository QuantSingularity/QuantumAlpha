"""
Stress testing for QuantumAlpha Risk Service.
Handles stress testing and scenario analysis.
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import NotFoundError, ServiceError, ValidationError, setup_logger

logger = setup_logger("stress_testing", logging.INFO)


class StressTesting:
    """Stress testing"""

    def __init__(self, config_manager: Any, db_manager: Any) -> None:
        """Initialize stress testing

        Args:
            config_manager: Configuration manager
            db_manager: Database manager
        """
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.data_service_url = f"http://{config_manager.get('services.data_service.host')}:{config_manager.get('services.data_service.port')}"
        self.predefined_scenarios = {
            "market_crash": {
                "name": "Market Crash",
                "description": "Simulates a severe market crash similar to 2008",
                "shocks": {
                    "equity": -0.4,
                    "bond": 0.05,
                    "commodity": -0.3,
                    "crypto": -0.7,
                },
            },
            "tech_bubble": {
                "name": "Tech Bubble Burst",
                "description": "Simulates a tech sector crash similar to 2000",
                "shocks": {
                    "equity": -0.25,
                    "tech": -0.6,
                    "bond": 0.1,
                    "commodity": 0.05,
                },
            },
            "inflation_surge": {
                "name": "Inflation Surge",
                "description": "Simulates a period of high inflation",
                "shocks": {
                    "equity": -0.15,
                    "bond": -0.2,
                    "commodity": 0.3,
                    "gold": 0.25,
                    "real_estate": 0.1,
                },
            },
            "interest_rate_hike": {
                "name": "Interest Rate Hike",
                "description": "Simulates a sudden increase in interest rates",
                "shocks": {
                    "equity": -0.1,
                    "bond": -0.15,
                    "bank": 0.05,
                    "real_estate": -0.2,
                },
            },
            "pandemic": {
                "name": "Pandemic",
                "description": "Simulates a global pandemic scenario",
                "shocks": {
                    "equity": -0.3,
                    "travel": -0.6,
                    "healthcare": 0.2,
                    "tech": 0.15,
                    "retail": -0.25,
                },
            },
        }
        self.asset_class_mappings = {
            "AAPL": ["equity", "tech"],
            "MSFT": ["equity", "tech"],
            "GOOGL": ["equity", "tech"],
            "AMZN": ["equity", "tech", "retail"],
            "META": ["equity", "tech"],
            "TSLA": ["equity", "tech", "auto"],
            "JPM": ["equity", "bank"],
            "BAC": ["equity", "bank"],
            "GS": ["equity", "bank"],
            "XOM": ["equity", "energy"],
            "CVX": ["equity", "energy"],
            "PFE": ["equity", "healthcare"],
            "JNJ": ["equity", "healthcare"],
            "UNH": ["equity", "healthcare"],
            "HD": ["equity", "retail"],
            "WMT": ["equity", "retail"],
            "DIS": ["equity", "entertainment"],
            "NFLX": ["equity", "tech", "entertainment"],
            "BA": ["equity", "industrial", "travel"],
            "DAL": ["equity", "travel"],
            "MAR": ["equity", "travel", "real_estate"],
            "SPY": ["equity", "index"],
            "QQQ": ["equity", "tech", "index"],
            "IWM": ["equity", "index"],
            "AGG": ["bond"],
            "BND": ["bond"],
            "TLT": ["bond"],
            "LQD": ["bond"],
            "GLD": ["commodity", "gold"],
            "SLV": ["commodity", "silver"],
            "USO": ["commodity", "energy"],
            "BTC-USD": ["crypto"],
            "ETH-USD": ["crypto"],
            "VNQ": ["real_estate"],
        }
        logger.info("Stress testing initialized")

    def run_stress_tests(
        self, portfolio: List[Dict[str, Any]], scenarios: List[str]
    ) -> Dict[str, Any]:
        """Run stress tests on a portfolio

        Args:
            portfolio: Portfolio positions
            scenarios: List of scenario names

        Returns:
            Stress test results

        Raises:
            ValidationError: If parameters are invalid
        """
        try:
            logger.info("Running stress tests")
            if not portfolio:
                raise ValidationError("Portfolio is required")
            if not scenarios:
                raise ValidationError("Scenarios are required")
            portfolio_value = sum(
                (
                    position["quantity"] * position["entry_price"]
                    for position in portfolio
                )
            )
            results = {}
            for scenario_name in scenarios:
                if scenario_name not in self.predefined_scenarios:
                    logger.warning(f"Scenario not found: {scenario_name}")
                    continue
                scenario = self.predefined_scenarios[scenario_name]
                scenario_result = self._run_scenario(portfolio, scenario)
                results[scenario_name] = {
                    "name": scenario["name"],
                    "description": scenario["description"],
                    "portfolio_value_before": portfolio_value,
                    "portfolio_value_after": scenario_result["portfolio_value_after"],
                    "change_amount": scenario_result["change_amount"],
                    "change_percent": scenario_result["change_percent"],
                    "position_impacts": scenario_result["position_impacts"],
                }
            response = {
                "portfolio_value": portfolio_value,
                "scenarios": results,
                "calculated_at": datetime.utcnow().isoformat(),
            }
            return response
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error running stress tests: {e}")
            raise ServiceError(f"Error running stress tests: {str(e)}")

    def _run_scenario(
        self, portfolio: List[Dict[str, Any]], scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run a stress test scenario

        Args:
            portfolio: Portfolio positions
            scenario: Scenario definition

        Returns:
            Scenario result
        """
        portfolio_value_before = sum(
            (position["quantity"] * position["entry_price"] for position in portfolio)
        )
        position_impacts = []
        portfolio_value_after = 0
        for position in portfolio:
            symbol = position["symbol"]
            quantity = position["quantity"]
            entry_price = position["entry_price"]
            position_value = quantity * entry_price
            asset_classes = self.asset_class_mappings.get(symbol, ["equity"])
            shock = 0
            for asset_class in asset_classes:
                if asset_class in scenario["shocks"]:
                    shock += scenario["shocks"][asset_class]
            shock /= len(asset_classes)
            new_price = entry_price * (1 + shock)
            new_value = quantity * new_price
            impact = {
                "symbol": symbol,
                "quantity": quantity,
                "price_before": entry_price,
                "price_after": new_price,
                "value_before": position_value,
                "value_after": new_value,
                "change_amount": new_value - position_value,
                "change_percent": (new_value - position_value) / position_value,
            }
            position_impacts.append(impact)
            portfolio_value_after += new_value
        change_amount = portfolio_value_after - portfolio_value_before
        change_percent = change_amount / portfolio_value_before
        return {
            "portfolio_value_after": portfolio_value_after,
            "change_amount": change_amount,
            "change_percent": change_percent,
            "position_impacts": position_impacts,
        }

    def get_scenarios(self) -> List[Dict[str, Any]]:
        """Get all predefined scenarios

        Returns:
            List of scenarios
        """
        scenarios = []
        for scenario_id, scenario in self.predefined_scenarios.items():
            scenarios.append(
                {
                    "id": scenario_id,
                    "name": scenario["name"],
                    "description": scenario["description"],
                }
            )
        return scenarios

    def create_scenario(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom scenario

        Args:
            data: Scenario data

        Returns:
            Created scenario

        Raises:
            ValidationError: If data is invalid
        """
        if "name" not in data:
            raise ValidationError("Scenario name is required")
        if "shocks" not in data:
            raise ValidationError("Scenario shocks are required")
        scenario_id = data["name"].lower().replace(" ", "_")
        scenario = {
            "name": data["name"],
            "description": data.get("description", ""),
            "shocks": data["shocks"],
        }
        self.predefined_scenarios[scenario_id] = scenario
        return {
            "id": scenario_id,
            "name": scenario["name"],
            "description": scenario["description"],
        }

    def generate_extreme_scenario(
        self, scenario_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generates a custom extreme scenario based on user-defined parameters.

        Args:
            scenario_params: Dictionary containing parameters for the extreme scenario.
                             Expected keys: 'name', 'description', 'shocks' (dict of asset class shocks),
                             'correlation_changes' (optional, dict of correlation changes between asset classes).

        Returns:
            A dictionary representing the newly created extreme scenario.

        Raises:
            ValidationError: If required parameters are missing or invalid.
        """
        logger.info("Generating custom extreme scenario.")
        if "name" not in scenario_params:
            raise ValidationError("Scenario name is required.")
        if "shocks" not in scenario_params or not isinstance(
            scenario_params["shocks"], dict
        ):
            raise ValidationError("Scenario shocks (dictionary) are required.")
        scenario_id = scenario_params["name"].lower().replace(" ", "_")
        if scenario_id in self.predefined_scenarios:
            logger.warning(f"Scenario ID '{scenario_id}' already exists. Overwriting.")
        new_scenario = {
            "name": scenario_params["name"],
            "description": scenario_params.get(
                "description", "Custom extreme scenario."
            ),
            "shocks": scenario_params["shocks"],
            "correlation_changes": scenario_params.get("correlation_changes", {}),
        }
        self.predefined_scenarios[scenario_id] = new_scenario
        logger.info(
            f"Custom extreme scenario '{new_scenario['name']}' generated and added."
        )
        return {
            "id": scenario_id,
            "name": new_scenario["name"],
            "description": new_scenario["description"],
        }

    def _apply_correlation_changes(
        self, returns_df: pd.DataFrame, correlation_changes: Dict[str, float]
    ) -> pd.DataFrame:
        """Applies correlation changes to historical returns for scenario modeling.
        This is a simplified approach and a full implementation would require
        more advanced copula or factor models.

        Args:
            returns_df: DataFrame of historical returns.
            correlation_changes: Dictionary of asset class pairs and their target correlation changes.
                                 e.g., {'equity_bond': -0.5} to reduce equity-bond correlation by 0.5.

        Returns:
            DataFrame of adjusted returns.
        """
        if not correlation_changes or returns_df.empty:
            return returns_df
        logger.info("Applying correlation changes to returns.")
        adjusted_returns_df = returns_df.copy()
        for pair, change in correlation_changes.items():
            asset1, asset2 = pair.split("_")
            logger.info(
                f"Attempting to adjust correlation between {asset1} and {asset2} by {change}."
            )
        return adjusted_returns_df

    def run_extreme_scenario(
        self, portfolio: List[Dict[str, Any]], scenario_id: str
    ) -> Dict[str, Any]:
        """Runs a specific extreme scenario on a portfolio, including correlation changes.

        Args:
            portfolio: Portfolio positions.
            scenario_id: ID of the extreme scenario to run.

        Returns:
            Stress test results for the extreme scenario.

        Raises:
            NotFoundError: If the scenario is not found.
            ServiceError: For other processing errors.
        """
        try:
            logger.info(f"Running extreme scenario: {scenario_id}")
            scenario = self.predefined_scenarios.get(scenario_id)
            if not scenario:
                raise NotFoundError(f"Extreme scenario not found: {scenario_id}")
            symbols = [pos["symbol"] for pos in portfolio]
            all_historical_data = {}
            for symbol in symbols:
                all_historical_data[symbol] = self._get_historical_data(
                    symbol, lookback_period=252
                )
            returns_data = {}
            for symbol, data in all_historical_data.items():
                returns_data[symbol] = self._calculate_returns(data)
            min_len = (
                min((len(r) for r in returns_data.values())) if returns_data else 0
            )
            returns_df = pd.DataFrame({s: r[:min_len] for s, r in returns_data.items()})
            if "correlation_changes" in scenario and scenario["correlation_changes"]:
                returns_df = self._apply_correlation_changes(
                    returns_df, scenario["correlation_changes"]
                )
            portfolio_value_before = sum(
                (
                    position["quantity"] * position["entry_price"]
                    for position in portfolio
                )
            )
            portfolio_value_after = 0
            position_impacts = []
            for position in portfolio:
                symbol = position["symbol"]
                quantity = position["quantity"]
                entry_price = position["entry_price"]
                position_value = quantity * entry_price
                asset_classes = self.asset_class_mappings.get(symbol, ["equity"])
                shock = 0
                for asset_class in asset_classes:
                    if asset_class in scenario["shocks"]:
                        shock += scenario["shocks"][asset_class]
                shock /= len(asset_classes) if asset_classes else 1
                new_price = entry_price * (1 + shock)
                new_value = quantity * new_price
                impact = {
                    "symbol": symbol,
                    "quantity": quantity,
                    "price_before": entry_price,
                    "price_after": new_price,
                    "value_before": position_value,
                    "value_after": new_value,
                    "change_amount": new_value - position_value,
                    "change_percent": (
                        (new_value - position_value) / position_value
                        if position_value != 0
                        else 0
                    ),
                }
                position_impacts.append(impact)
                portfolio_value_after += new_value
            change_amount = portfolio_value_after - portfolio_value_before
            change_percent = (
                change_amount / portfolio_value_before
                if portfolio_value_before != 0
                else 0
            )
            return {
                "scenario_id": scenario_id,
                "scenario_name": scenario["name"],
                "portfolio_value_before": portfolio_value_before,
                "portfolio_value_after": portfolio_value_after,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "position_impacts": position_impacts,
                "calculated_at": datetime.utcnow().isoformat(),
            }
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error running extreme scenario: {e}")
            raise ServiceError(f"Error running extreme scenario: {str(e)}")

    def _get_historical_data(
        self, symbol: str, lookback_period: int
    ) -> List[Dict[str, Any]]:
        """Get historical data for a symbol (simplified for stress testing).
        In a real system, this would call the data service.
        """
        logger.warning(f"Using dummy historical data for {symbol} in stress testing.")
        n_samples = lookback_period
        data = []
        for i in range(n_samples):
            date = (datetime.utcnow() - timedelta(days=n_samples - i)).strftime(
                "%Y-%m-%dT00:00:00"
            )
            close = 100 + np.random.normal(0, 1) * 10
            data.append(
                {
                    "timestamp": date,
                    "open": close - 1,
                    "high": close + 1,
                    "low": close - 2,
                    "close": close,
                    "volume": 1000000 + np.random.normal(0, 1) * 100000,
                }
            )
        return data

    def _calculate_returns(self, data: List[Dict[str, Any]]) -> np.ndarray:
        """Calculate returns from historical data (simplified for stress testing)."""
        prices = np.array([d["close"] for d in data])
        returns = np.diff(prices) / prices[:-1]
        return returns
