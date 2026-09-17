"""
Trading service for QuantumAlpha Execution Service.
Orchestrates end-to-end trade execution from signals.
"""

import logging
from typing import Any, Dict

import requests
from backend.common import ServiceError, setup_logger

logger = setup_logger("trading_service", logging.INFO)


class TradingService:
    """Trading service - orchestrates end-to-end trade execution."""

    def __init__(self, config_manager: object, db_manager: object) -> None:
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.data_service_url = config_manager.get("services.data_service.url")
        self.ai_engine_url = config_manager.get("services.ai_engine.url")
        self.risk_service_url = config_manager.get("services.risk_service.url")
        self.execution_service_url = config_manager.get(
            "services.execution_service.url"
        )
        self.broker_url = config_manager.get("broker.url", "http://localhost:9000")
        logger.info("Trading service initialized")

    def execute_trade_from_model(
        self,
        model_id: str,
        symbol: str,
        portfolio_id: str,
        timeframe: str = "1d",
        period: str = "1mo",
        horizon: int = 5,
    ) -> Dict[str, Any]:
        """Get a prediction from the AI engine, turn it into a trading
        signal, and execute it: AI engine -> signal -> order -> broker.

        Args:
            model_id: Trained AI engine model to predict with
            symbol: Symbol to trade
            portfolio_id: Portfolio to trade in
            timeframe: Prediction timeframe
            period: Historical period used for the prediction
            horizon: Prediction horizon

        Returns:
            Execution result (see execute_trade_from_signal), or a
            no_action result if the prediction is neutral.
        """
        try:
            resp = requests.post(
                f"{self.ai_engine_url}/api/predict",
                json={
                    "model_id": model_id,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "period": period,
                    "horizon": horizon,
                },
            )
            if resp.status_code != 200:
                raise ServiceError(f"AI engine prediction failed: {resp.text}")
            prediction = resp.json().get("prediction", {})
            direction = prediction.get("direction", "neutral")
            change_percent = prediction.get("change_percent", 0.0)
            if direction == "bullish":
                signal_type = "buy"
            elif direction == "bearish":
                signal_type = "sell"
            else:
                signal_type = "hold"

            signal = {
                "symbol": symbol,
                "type": signal_type,
                "strength": min(abs(change_percent) / 5.0, 1.0),
                "price": prediction.get("average", 0.0),
                "model_id": model_id,
            }
            if signal_type == "hold":
                return {
                    "status": "no_action",
                    "reason": "neutral prediction",
                    "signal": signal,
                }
            return self.execute_trade_from_signal(signal, portfolio_id)
        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Error executing trade from model: {e}")
            raise ServiceError(f"Error executing trade from model: {str(e)}")

    def execute_trade_from_signal(
        self, signal: Dict[str, Any], portfolio_id: str
    ) -> Dict[str, Any]:
        """Execute a trade from a signal.

        Args:
            signal: Trading signal with symbol, type, strength, price
            portfolio_id: Portfolio to trade in

        Returns:
            Execution result with order_id, status, execution_details
        """
        try:
            symbol = signal.get("symbol")
            side = "buy" if signal.get("type") == "buy" else "sell"
            signal.get("price", 0.0)
            quantity = self._calculate_quantity(signal, portfolio_id)

            order_data = {
                "portfolio_id": portfolio_id,
                "symbol": symbol,
                "order_type": "market",
                "side": side,
                "quantity": quantity,
                "time_in_force": "day",
            }

            order_resp = requests.post(
                f"{self.execution_service_url}/orders/", json=order_data
            )
            if order_resp.status_code not in (200, 201):
                raise ServiceError(f"Order creation failed: {order_resp.text}")
            order = order_resp.json()
            order_id = order.get("id", "order1")

            broker_resp = requests.post(f"{self.broker_url}/broker/submit", json=order)
            execution_details = {}
            if broker_resp.status_code == 200:
                execution_details = broker_resp.json()

            return {
                "order_id": order_id,
                "status": execution_details.get("status", "submitted"),
                "execution_details": execution_details,
                "signal": signal,
            }
        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Error executing trade from signal: {e}")
            raise ServiceError(f"Error executing trade: {str(e)}")

    def _calculate_quantity(self, signal: Dict[str, Any], portfolio_id: str) -> int:
        """Calculate order quantity based on signal strength and portfolio."""
        strength = signal.get("strength", 0.5)
        price = signal.get("price", 100.0)
        base_allocation = 10000.0
        qty = int((base_allocation * strength) / price) if price > 0 else 1
        return max(1, qty)
