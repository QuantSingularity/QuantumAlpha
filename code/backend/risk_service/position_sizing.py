"""
Position sizing for QuantumAlpha Risk Service.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from backend.common import ServiceError, ValidationError, setup_logger

logger = setup_logger("position_sizing", logging.INFO)

VALID_METHODS = ["fixed", "percent", "risk", "kelly"]


class PositionSizing:
    """Position sizing"""

    def __init__(self, config_manager: Any, db_manager: Any) -> None:
        self.config_manager = config_manager
        self.db_manager = db_manager
        logger.info("Position sizing initialized")

    def _get_portfolio_value(self, portfolio: Dict[str, Any]) -> float:
        positions_value = sum(
            p["quantity"] * p["current_price"] for p in portfolio.get("positions", [])
        )
        return positions_value + portfolio.get("cash", 0.0)

    def calculate_position_size(
        self,
        portfolio: Dict[str, Any],
        symbol: str,
        price: float,
        method: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate position size.

        Args:
            portfolio: Portfolio dict with positions and cash
            symbol: Ticker symbol
            price: Current price of the asset
            method: Sizing method: 'fixed', 'percent', 'risk', 'kelly'
            params: Method-specific parameters

        Returns:
            Dict with quantity, value, method, symbol, price and extras
        """
        try:
            if method not in VALID_METHODS:
                raise ValidationError(
                    f"Invalid method: {method}. Must be one of {VALID_METHODS}"
                )

            portfolio_value = self._get_portfolio_value(portfolio)

            if method == "fixed":
                if "amount" not in params:
                    raise ValidationError("'amount' is required for fixed method")
                amount = params["amount"]
                quantity = amount / price
                value = quantity * price
                return {
                    "symbol": symbol,
                    "price": price,
                    "method": method,
                    "quantity": quantity,
                    "value": value,
                }

            elif method == "percent":
                if "percent" not in params:
                    raise ValidationError("'percent' is required for percent method")
                percent = params["percent"]
                if percent < 0 or percent > 100:
                    raise ValidationError("'percent' must be between 0 and 100")
                value = portfolio_value * (percent / 100.0)
                quantity = value / price
                return {
                    "symbol": symbol,
                    "price": price,
                    "method": method,
                    "quantity": quantity,
                    "value": value,
                }

            elif method == "risk":
                if "risk_percent" not in params:
                    raise ValidationError("'risk_percent' is required for risk method")
                if "stop_loss_percent" not in params:
                    raise ValidationError(
                        "'stop_loss_percent' is required for risk method"
                    )
                stop_loss_percent = params["stop_loss_percent"]
                if stop_loss_percent <= 0:
                    raise ValidationError("'stop_loss_percent' must be positive")
                risk_amount = portfolio_value * (params["risk_percent"] / 100.0)
                stop_loss = price * (1 - stop_loss_percent / 100.0)
                risk_per_share = price - stop_loss
                quantity = risk_amount / risk_per_share
                value = quantity * price
                return {
                    "symbol": symbol,
                    "price": price,
                    "method": method,
                    "quantity": quantity,
                    "value": value,
                    "stop_loss": stop_loss,
                }

            elif method == "kelly":
                if "win_rate" not in params:
                    raise ValidationError("'win_rate' is required for kelly method")
                if "win_loss_ratio" not in params:
                    raise ValidationError(
                        "'win_loss_ratio' is required for kelly method"
                    )
                win_rate = params["win_rate"]
                win_loss_ratio = params["win_loss_ratio"]
                if win_rate < 0 or win_rate > 1:
                    raise ValidationError("'win_rate' must be between 0 and 1")
                kelly_percent = win_rate - (1 - win_rate) / win_loss_ratio
                value = portfolio_value * kelly_percent
                quantity = value / price
                return {
                    "symbol": symbol,
                    "price": price,
                    "method": method,
                    "quantity": quantity,
                    "value": value,
                    "kelly_percent": kelly_percent,
                }

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            raise ServiceError(f"Error calculating position size: {str(e)}")

    def optimize_portfolio(
        self,
        portfolio: List[Dict[str, Any]],
        signals: List[Dict[str, Any]],
        risk_tolerance: float,
    ) -> Dict[str, Any]:
        try:
            if not portfolio:
                raise ValidationError("Portfolio is required")
            if not signals:
                raise ValidationError("Signals are required")
            if risk_tolerance < 0 or risk_tolerance > 1:
                raise ValidationError("Risk tolerance must be between 0 and 1")
            portfolio_value = sum(
                p["quantity"] * p.get("entry_price", p.get("current_price", 0))
                for p in portfolio
            )
            return {
                "portfolio_value": portfolio_value,
                "position_sizes": [],
                "calculated_at": datetime.now(timezone.utc).isoformat(),
            }
        except ValidationError:
            raise
        except Exception as e:
            raise ServiceError(f"Error optimizing portfolio: {str(e)}")
