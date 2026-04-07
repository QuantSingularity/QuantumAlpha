"""
Trading service for QuantumAlpha Execution Service.
Orchestrates end-to-end trade execution from signals.
"""

import logging
import os
import sys
from typing import Any, Dict

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import ServiceError, setup_logger

logger = setup_logger("trading_service", logging.INFO)


class TradingService:
    """Trading service - orchestrates end-to-end trade execution."""

    def __init__(self, config_manager: Any, db_manager: Any) -> None:
        self.config_manager = config_manager
        self.db_manager = db_manager

        def _url(service: str, default_port: str) -> str:
            host = config_manager.get(f"services.{service}.host", "localhost")
            port = config_manager.get(f"services.{service}.port", default_port)
            return f"http://{host}:{port}"

        self.data_service_url = _url("data_service", "8081")
        self.ai_engine_url = _url("ai_engine", "8082")
        self.risk_service_url = _url("risk_service", "8083")
        self.execution_service_url = _url("execution_service", "8084")
        self.broker_url = config_manager.get("broker.url", "http://localhost:9000")
        logger.info("Trading service initialized")

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
