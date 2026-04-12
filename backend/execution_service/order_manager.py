"""
Order manager for QuantumAlpha Execution Service.
Handles order management and execution.
"""

import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import NotFoundError, ServiceError, ValidationError, setup_logger

logger = setup_logger("order_manager", logging.INFO)

VALID_ORDER_TYPES = ["market", "limit", "stop", "stop_limit"]
VALID_SIDES = ["buy", "sell"]
VALID_TIME_IN_FORCE = ["day", "gtc", "ioc", "fok", "opg", "cls"]
VALID_STATUSES = [
    "new",
    "open",
    "pending",
    "submitted",
    "partially_filled",
    "filled",
    "canceled",
    "cancelled",
    "rejected",
    "expired",
    "error",
]


class OrderManager:
    """Order manager"""

    def __init__(self, config_manager: Any, db_manager: Any) -> None:
        self.config_manager = config_manager
        self.db_manager = db_manager
        logger.info("Order manager initialized")

    def create_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info("Creating order")
            for field in ["portfolio_id", "symbol", "order_type", "side", "quantity"]:
                if field not in data:
                    raise ValidationError(f"{field} is required")

            if data["order_type"] not in VALID_ORDER_TYPES:
                raise ValidationError(f"Invalid order type: {data['order_type']}")
            if data["side"] not in VALID_SIDES:
                raise ValidationError(f"Invalid side: {data['side']}")

            tif = data.get("time_in_force", "day")
            if tif not in VALID_TIME_IN_FORCE:
                raise ValidationError(f"Invalid time_in_force: {tif}")

            quantity = data["quantity"]
            if not isinstance(quantity, (int, float)) or quantity <= 0:
                raise ValidationError("Quantity must be a positive number")

            if data["order_type"] in ["limit", "stop_limit"]:
                if data.get("price") is None:
                    raise ValidationError("Price is required for limit orders")

            session = self.db_manager.get_postgres_session()
            order_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()

            from sqlalchemy import text

            result = session.execute(
                text(
                    "INSERT INTO orders (id, portfolio_id, symbol, order_type, side, quantity,"
                    " price, time_in_force, status, created_at, updated_at)"
                    " VALUES (:id,:portfolio_id,:symbol,:order_type,:side,:quantity,"
                    ":price,:tif,:status,:now,:now) RETURNING id"
                ),
                {
                    "id": order_id,
                    "portfolio_id": data["portfolio_id"],
                    "symbol": data["symbol"],
                    "order_type": data["order_type"],
                    "side": data["side"],
                    "quantity": quantity,
                    "price": data.get("price"),
                    "tif": tif,
                    "status": data.get("status", "new"),
                    "now": now,
                },
            )
            returned = result.fetchone()
            actual_id = returned[0] if returned else order_id
            session.commit()

            return {
                "id": actual_id,
                "portfolio_id": data["portfolio_id"],
                "symbol": data["symbol"],
                "order_type": data["order_type"],
                "side": data["side"],
                "quantity": quantity,
                "price": data.get("price"),
                "time_in_force": tif,
                "status": data.get("status", "new"),
                "created_at": now,
                "updated_at": now,
            }
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise ServiceError(f"Error creating order: {str(e)}")

    def get_order(self, order_id: str) -> Dict[str, Any]:
        try:
            logger.info(f"Getting order {order_id}")
            session = self.db_manager.get_postgres_session()
            from sqlalchemy import text

            result = session.execute(
                text("SELECT * FROM orders WHERE id = :id"), {"id": order_id}
            )
            row = result.fetchone()
            if not row:
                raise NotFoundError(f"Order not found: {order_id}")
            order_dict = {}
            for key, value in row.items():
                if isinstance(value, datetime):
                    value = value.isoformat()
                order_dict[key] = value
            return order_dict
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting order: {e}")
            raise ServiceError(f"Error getting order: {str(e)}")

    def get_orders(
        self,
        portfolio_id: Optional[str] = None,
        status: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        try:
            logger.info("Getting orders")
            session = self.db_manager.get_postgres_session()
            from sqlalchemy import text

            query = "SELECT * FROM orders WHERE 1=1"
            params: Dict[str, Any] = {}
            if portfolio_id:
                query += " AND portfolio_id = :portfolio_id"
                params["portfolio_id"] = portfolio_id
            if status:
                query += " AND status = :status"
                params["status"] = status
            if symbol:
                query += " AND symbol = :symbol"
                params["symbol"] = symbol
            result = session.execute(text(query), params)
            rows = result.fetchall()
            orders = []
            for row in rows:
                d = {}
                for key, value in row.items():
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    d[key] = value
                orders.append(d)
            return orders
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            raise ServiceError(f"Error getting orders: {str(e)}")

    def update_order_status(
        self,
        order_id: str,
        status: str,
        broker_order_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            logger.info(f"Updating order status: {order_id} -> {status}")
            if status not in VALID_STATUSES:
                raise ValidationError(f"Invalid status: {status}")
            session = self.db_manager.get_postgres_session()
            from sqlalchemy import text

            now = datetime.now(timezone.utc).isoformat()
            result = session.execute(
                text("UPDATE orders SET status=:status, updated_at=:now WHERE id=:id"),
                {"id": order_id, "status": status, "now": now},
            )
            if result.rowcount == 0:
                raise NotFoundError(f"Order not found: {order_id}")
            session.commit()
            return {"id": order_id, "status": status, "updated_at": now}
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            raise ServiceError(f"Error updating order status: {str(e)}")

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        try:
            logger.info(f"Canceling order {order_id}")
            session = self.db_manager.get_postgres_session()
            from sqlalchemy import text

            now = datetime.now(timezone.utc).isoformat()
            result = session.execute(
                text(
                    "UPDATE orders SET status='canceled', updated_at=:now WHERE id=:id"
                ),
                {"id": order_id, "now": now},
            )
            if result.rowcount == 0:
                raise NotFoundError(f"Order not found: {order_id}")
            session.commit()
            return {"id": order_id, "status": "canceled", "updated_at": now}
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            raise ServiceError(f"Error canceling order: {str(e)}")

    def create_trade(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info("Creating trade")
            for field in ["order_id", "symbol", "side", "quantity", "price"]:
                if field not in data:
                    raise ValidationError(f"{field} is required")

            session = self.db_manager.get_postgres_session()
            trade_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            from sqlalchemy import text

            result = session.execute(
                text(
                    "INSERT INTO trades (id, order_id, symbol, side, quantity, price,"
                    " commission, timestamp) VALUES (:id,:order_id,:symbol,:side,"
                    ":quantity,:price,:commission,:now) RETURNING id"
                ),
                {
                    "id": trade_id,
                    "order_id": data["order_id"],
                    "symbol": data["symbol"],
                    "side": data["side"],
                    "quantity": data["quantity"],
                    "price": data["price"],
                    "commission": data.get("commission", 0.0),
                    "now": now,
                },
            )
            returned = result.fetchone()
            actual_id = returned[0] if returned else trade_id
            session.commit()
            return {
                "id": actual_id,
                "order_id": data["order_id"],
                "symbol": data["symbol"],
                "side": data["side"],
                "quantity": data["quantity"],
                "price": data["price"],
                "commission": data.get("commission", 0.0),
                "timestamp": now,
            }
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating trade: {e}")
            raise ServiceError(f"Error creating trade: {str(e)}")

    def create_order_with_risk_check(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an order after performing a risk check via Risk Service."""
        import requests as _requests

        host = self.config_manager.get("services.risk_service.host", "localhost")
        port = self.config_manager.get("services.risk_service.port", "8083")
        risk_service_url = f"http://{host}:{port}"

        portfolio_id = data.get("portfolio_id")
        symbol = data.get("symbol")
        try:
            resp = _requests.get(
                f"{risk_service_url}/api/risk/position-size",
                params={"portfolio_id": portfolio_id, "symbol": symbol},
            )
            if resp.status_code == 200:
                risk_data = resp.json()
                max_qty = risk_data.get("max_position_size")
                if max_qty is not None and data.get("quantity", 0) > max_qty:
                    raise ValidationError(
                        f"Order quantity exceeds max position size: {max_qty}"
                    )
        except ValidationError:
            raise
        except Exception:
            pass

        host2 = self.config_manager.get("services.execution_service.host", "localhost")
        port2 = self.config_manager.get("services.execution_service.port", "8084")
        exec_url = f"http://{host2}:{port2}"
        resp2 = _requests.post(f"{exec_url}/api/orders", json=data)
        if resp2.status_code in (200, 201):
            return resp2.json()
        raise ServiceError(f"Error creating order: {resp2.text}")

    def get_trades(
        self,
        portfolio_id: Optional[str] = None,
        order_id: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        try:
            logger.info("Getting trades")
            session = self.db_manager.get_postgres_session()
            from sqlalchemy import text

            if portfolio_id:
                query = (
                    "SELECT t.* FROM trades t JOIN orders o ON t.order_id=o.id"
                    " WHERE o.portfolio_id=:portfolio_id"
                )
                params: Dict[str, Any] = {"portfolio_id": portfolio_id}
            elif order_id:
                query = "SELECT * FROM trades WHERE order_id=:order_id"
                params = {"order_id": order_id}
            elif symbol:
                query = "SELECT * FROM trades WHERE symbol=:symbol"
                params = {"symbol": symbol}
            else:
                query = "SELECT * FROM trades"
                params = {}
            result = session.execute(text(query), params)
            rows = result.fetchall()
            trades = []
            for row in rows:
                d = {}
                for key, value in row.items():
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    d[key] = value
                trades.append(d)
            return trades
        except Exception as e:
            logger.error(f"Error getting trades: {e}")
            raise ServiceError(f"Error getting trades: {str(e)}")
