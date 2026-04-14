"""
Execution strategy for QuantumAlpha Execution Service.
"""

import logging
from typing import Any, Dict

from backend.common import ServiceError, setup_logger

logger = setup_logger("execution_strategy", logging.INFO)

LARGE_ORDER_THRESHOLD = 10000


class ExecutionStrategy:
    """Execution strategy"""

    def __init__(self, config_manager: Any, db_manager: Any) -> None:
        self.config_manager = config_manager
        self.db_manager = db_manager
        logger.info("Execution strategy initialized")

    def select_execution_strategy(self, order: Dict[str, Any]) -> str:
        """Select execution strategy based on order properties."""
        order_type = order.get("order_type", "market")
        quantity = order.get("quantity", 0)
        if order_type == "limit":
            return "limit"
        if quantity >= LARGE_ORDER_THRESHOLD:
            return "vwap"
        return "market"

    def execute_market_strategy(
        self, order: Dict[str, Any], broker_integration: Any
    ) -> Dict[str, Any]:
        """Execute order using market strategy."""
        try:
            submit_result = broker_integration.submit_order_to_broker(order)
            broker_order_id = submit_result["broker_order_id"]
            status_result = broker_integration.get_order_status_from_broker(
                broker_order_id
            )
            return {
                "order_id": order["id"],
                "broker_order_id": broker_order_id,
                "status": status_result.get("status", "filled"),
                "filled_quantity": status_result.get(
                    "filled_quantity", order.get("quantity")
                ),
                "average_price": status_result.get("average_price"),
            }
        except Exception as e:
            raise ServiceError(f"Error executing market strategy: {str(e)}")

    def execute_limit_strategy(
        self, order: Dict[str, Any], broker_integration: Any
    ) -> Dict[str, Any]:
        """Execute order using limit strategy."""
        try:
            submit_result = broker_integration.submit_order_to_broker(order)
            broker_order_id = submit_result["broker_order_id"]
            status_result = broker_integration.get_order_status_from_broker(
                broker_order_id
            )
            return {
                "order_id": order["id"],
                "broker_order_id": broker_order_id,
                "status": status_result.get("status", "filled"),
                "filled_quantity": status_result.get(
                    "filled_quantity", order.get("quantity")
                ),
                "average_price": status_result.get("average_price"),
            }
        except Exception as e:
            raise ServiceError(f"Error executing limit strategy: {str(e)}")

    def execute_vwap_strategy(
        self,
        order: Dict[str, Any],
        broker_integration: Any,
        market_data: Dict[str, Any],
        num_slices: int = 5,
    ) -> Dict[str, Any]:
        """Execute order using VWAP strategy by splitting into slices."""
        try:
            total_quantity = order.get("quantity", 0)
            slice_quantity = total_quantity / num_slices
            child_orders = []
            total_filled = 0
            weighted_price_sum = 0.0

            for i in range(num_slices):
                child_order = dict(order)
                child_order["id"] = f"{order['id']}_child_{i}"
                child_order["quantity"] = slice_quantity
                submit_result = broker_integration.submit_order_to_broker(child_order)
                broker_order_id = submit_result["broker_order_id"]
                status_result = broker_integration.get_order_status_from_broker(
                    broker_order_id
                )
                filled_qty = status_result.get("filled_quantity", slice_quantity)
                avg_price = status_result.get("average_price", 0.0)
                total_filled += filled_qty
                weighted_price_sum += filled_qty * avg_price
                child_orders.append(
                    {
                        "order_id": child_order["id"],
                        "broker_order_id": broker_order_id,
                        "status": status_result.get("status", "filled"),
                        "filled_quantity": filled_qty,
                        "average_price": avg_price,
                    }
                )

            avg_price_total = weighted_price_sum / total_filled if total_filled else 0.0
            return {
                "order_id": order["id"],
                "status": "filled",
                "filled_quantity": total_filled,
                "average_price": avg_price_total,
                "child_orders": child_orders,
            }
        except Exception as e:
            raise ServiceError(f"Error executing VWAP strategy: {str(e)}")

    def execute_twap_strategy(
        self,
        order: Dict[str, Any],
        broker_integration: Any,
        market_data: Dict[str, Any],
        duration_minutes: int = 5,
        num_slices: int = 5,
    ) -> Dict[str, Any]:
        """Execute order using TWAP strategy."""
        try:
            total_quantity = order.get("quantity", 0)
            slice_quantity = total_quantity / num_slices
            child_orders = []
            total_filled = 0
            weighted_price_sum = 0.0

            for i in range(num_slices):
                child_order = dict(order)
                child_order["id"] = f"{order['id']}_child_{i}"
                child_order["quantity"] = slice_quantity
                submit_result = broker_integration.submit_order_to_broker(child_order)
                broker_order_id = submit_result["broker_order_id"]
                status_result = broker_integration.get_order_status_from_broker(
                    broker_order_id
                )
                filled_qty = status_result.get("filled_quantity", slice_quantity)
                avg_price = status_result.get("average_price", 0.0)
                total_filled += filled_qty
                weighted_price_sum += filled_qty * avg_price
                child_orders.append(
                    {
                        "order_id": child_order["id"],
                        "broker_order_id": broker_order_id,
                        "status": status_result.get("status", "filled"),
                        "filled_quantity": filled_qty,
                        "average_price": avg_price,
                    }
                )

            avg_price_total = weighted_price_sum / total_filled if total_filled else 0.0
            return {
                "order_id": order["id"],
                "status": "filled",
                "filled_quantity": total_filled,
                "average_price": avg_price_total,
                "child_orders": child_orders,
            }
        except Exception as e:
            raise ServiceError(f"Error executing TWAP strategy: {str(e)}")

    def execute_iceberg_strategy(
        self,
        order: Dict[str, Any],
        broker_integration: Any,
        market_data: Dict[str, Any],
        display_size: int = 20,
    ) -> Dict[str, Any]:
        """Execute order using iceberg strategy."""
        try:
            total_quantity = order.get("quantity", 0)
            num_slices = max(1, int(total_quantity / display_size))
            slice_quantity = display_size
            child_orders = []
            total_filled = 0
            weighted_price_sum = 0.0

            for i in range(num_slices):
                child_order = dict(order)
                child_order["id"] = f"{order['id']}_child_{i}"
                child_order["quantity"] = slice_quantity
                submit_result = broker_integration.submit_order_to_broker(child_order)
                broker_order_id = submit_result["broker_order_id"]
                status_result = broker_integration.get_order_status_from_broker(
                    broker_order_id
                )
                filled_qty = status_result.get("filled_quantity", slice_quantity)
                avg_price = status_result.get("average_price", 0.0)
                total_filled += filled_qty
                weighted_price_sum += filled_qty * avg_price
                child_orders.append(
                    {
                        "order_id": child_order["id"],
                        "broker_order_id": broker_order_id,
                        "status": status_result.get("status", "filled"),
                        "filled_quantity": filled_qty,
                        "average_price": avg_price,
                    }
                )

            avg_price_total = weighted_price_sum / total_filled if total_filled else 0.0
            return {
                "order_id": order["id"],
                "status": "filled",
                "filled_quantity": total_filled,
                "average_price": avg_price_total,
                "child_orders": child_orders,
            }
        except Exception as e:
            raise ServiceError(f"Error executing iceberg strategy: {str(e)}")
