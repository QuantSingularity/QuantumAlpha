import logging
import os
from typing import Any, Dict, Optional

import requests
from backend.common import ServiceError, ValidationError, setup_logger

logger = setup_logger("trading_service", logging.INFO)

REQUEST_TIMEOUT = float(os.getenv("SERVICE_REQUEST_TIMEOUT", "30"))
SIGNAL_TYPES = ("buy", "sell")


class TradingService:

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
        self.ai_engine_key = os.getenv("AI_ENGINE_API_KEY") or None
        logger.info("Trading service initialized")

    def _ai_headers(self) -> Dict[str, str]:
        return {"X-Internal-Key": self.ai_engine_key} if self.ai_engine_key else {}

    def execute_trade_from_model(
        self,
        model_id: str,
        symbol: str,
        portfolio_id: str,
        timeframe: str = "1d",
        period: Optional[str] = None,
        horizon: int = 5,
    ) -> Dict[str, Any]:
        try:
            payload: Dict[str, Any] = {
                "model_id": model_id,
                "symbol": symbol,
                "timeframe": timeframe,
                "horizon": horizon,
            }
            if period:
                payload["period"] = period
            resp = requests.post(
                f"{self.ai_engine_url}/api/predict",
                json=payload,
                headers=self._ai_headers(),
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code != 200:
                raise ServiceError(f"AI engine prediction failed: {resp.text}")
            body = resp.json()
            prediction = body.get("prediction", {})
            direction = prediction.get("direction", "neutral")
            change_percent = float(prediction.get("change_percent", 0.0))
            signal_type = {"bullish": "buy", "bearish": "sell"}.get(direction, "hold")
            confidence = prediction.get("confidence")
            strength = (
                float(confidence)
                if confidence is not None
                else min(abs(change_percent) / 5.0, 1.0)
            )
            signal = {
                "symbol": symbol,
                "type": signal_type,
                "strength": max(0.0, min(strength, 1.0)),
                "price": body.get("latest_price") or prediction.get("average", 0.0),
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
        except requests.RequestException as e:
            logger.error(f"AI engine request failed: {e}")
            raise ServiceError(f"AI engine unavailable: {str(e)}")
        except Exception as e:
            logger.error(f"Error executing trade from model: {e}")
            raise ServiceError(f"Error executing trade from model: {str(e)}")

    def execute_trade_from_signal(
        self, signal: Dict[str, Any], portfolio_id: str
    ) -> Dict[str, Any]:
        try:
            symbol = signal.get("symbol")
            side = signal.get("type")
            if not symbol:
                raise ValidationError("Signal symbol is required")
            if side not in SIGNAL_TYPES:
                return {
                    "status": "no_action",
                    "reason": f"signal type '{side}' is not tradable",
                    "signal": signal,
                }
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
                f"{self.execution_service_url}/api/orders",
                json=order_data,
                timeout=REQUEST_TIMEOUT,
            )
            if order_resp.status_code not in (200, 201):
                raise ServiceError(f"Order creation failed: {order_resp.text}")
            order = order_resp.json()
            order_id = order.get("id")
            execution_details: Dict[str, Any] = {}
            try:
                broker_resp = requests.post(
                    f"{self.broker_url}/orders", json=order, timeout=REQUEST_TIMEOUT
                )
                if broker_resp.status_code == 200:
                    execution_details = broker_resp.json()
                else:
                    logger.warning(
                        f"Broker rejected order {order_id}: {broker_resp.text}"
                    )
            except requests.RequestException as e:
                logger.warning(f"Broker unreachable for order {order_id}: {e}")
            return {
                "order_id": order_id,
                "status": execution_details.get(
                    "status", order.get("status", "submitted")
                ),
                "execution_details": execution_details,
                "signal": signal,
            }
        except (ServiceError, ValidationError):
            raise
        except requests.RequestException as e:
            logger.error(f"Order service request failed: {e}")
            raise ServiceError(f"Order service unavailable: {str(e)}")
        except Exception as e:
            logger.error(f"Error executing trade from signal: {e}")
            raise ServiceError(f"Error executing trade: {str(e)}")

    def _calculate_quantity(self, signal: Dict[str, Any], portfolio_id: str) -> int:
        strength = float(signal.get("strength", 0.5) or 0.5)
        price = float(signal.get("price", 0.0) or 0.0)
        base_allocation = 10000.0
        qty = int((base_allocation * strength) / price) if price > 0 else 1
        return max(1, qty)
