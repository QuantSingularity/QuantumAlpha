"""
Execution Service for QuantumAlpha
This service is responsible for:
1. Order management
2. Broker integration
3. Execution strategy
4. Trade reconciliation
"""

import logging
import os
import traceback
from typing import Any

from backend.common import (
    ServiceError,
    ValidationError,
    get_config_manager,
    get_db_manager,
    setup_logger,
    validate_schema,
)
from backend.common.validation import CancelOrderRequest, OrderRequest
from backend.execution_service.broker_integration import BrokerIntegration
from backend.execution_service.execution_strategy import ExecutionStrategy
from backend.execution_service.order_manager import OrderManager
from flask import Flask, jsonify, request
from flask_cors import CORS

logger = setup_logger("execution_service", logging.INFO)
app = Flask(__name__)
CORS(app)
config_manager = get_config_manager(
    env_file=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", ".env"
    )
)
db_manager = get_db_manager(config_manager.get_all())
broker_integration = BrokerIntegration(config_manager, db_manager)
execution_strategy = ExecutionStrategy(config_manager, db_manager)
order_manager = OrderManager(
    config_manager, db_manager, broker_integration, execution_strategy
)


@app.errorhandler(Exception)
def handle_error(error: Any) -> Any:
    """Handle errors"""
    if isinstance(error, ServiceError):
        return (jsonify(error.to_dict()), error.status_code)
    logger.error(f"Unhandled error: {error}")
    logger.error(traceback.format_exc())
    return (
        jsonify(
            {
                "error": "Internal server error",
                "status_code": 500,
                "details": str(error),
            }
        ),
        500,
    )


@app.route("/health", methods=["GET"])
def health_check() -> Any:
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "execution_service"})


@app.route("/api/orders", methods=["GET"])
def get_orders() -> Any:
    """Get all orders"""
    try:
        portfolio_id = request.args.get("portfolio_id")
        status = request.args.get("status")
        symbol = request.args.get("symbol")
        orders = order_manager.get_orders(
            portfolio_id=portfolio_id, status=status, symbol=symbol
        )
        return jsonify({"orders": orders})
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/orders/<order_id>", methods=["GET"])
def get_order(order_id: Any) -> Any:
    """Get a specific order"""
    try:
        order = order_manager.get_order(order_id)
        return jsonify(order)
    except Exception as e:
        logger.error(f"Error getting order: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/orders", methods=["POST"])
def create_order() -> Any:
    """Create a new order"""
    try:
        data = request.json
        validated_data = validate_schema(data, OrderRequest)
        order = order_manager.create_order(validated_data)
        return jsonify(order)
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id: Any) -> Any:
    """Cancel an order"""
    try:
        data = request.json or {}
        data["order_id"] = order_id
        validated_data = validate_schema(data, CancelOrderRequest)
        result = order_manager.cancel_order(validated_data["order_id"])
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error canceling order: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/execution-strategies", methods=["GET"])
def get_execution_strategies() -> Any:
    """Get all execution strategies"""
    try:
        strategies = execution_strategy.get_strategies()
        return jsonify({"strategies": strategies})
    except Exception as e:
        logger.error(f"Error getting execution strategies: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/execution-strategies/<strategy_id>", methods=["GET"])
def get_execution_strategy(strategy_id: Any) -> Any:
    """Get a specific execution strategy"""
    try:
        strategy = execution_strategy.get_strategy(strategy_id)
        return jsonify(strategy)
    except Exception as e:
        logger.error(f"Error getting execution strategy: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/brokers", methods=["GET"])
def get_brokers() -> Any:
    """Get all brokers"""
    try:
        brokers = broker_integration.get_brokers()
        return jsonify({"brokers": brokers})
    except Exception as e:
        logger.error(f"Error getting brokers: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/brokers/<broker_id>", methods=["GET"])
def get_broker(broker_id: Any) -> Any:
    """Get a specific broker"""
    try:
        broker = broker_integration.get_broker(broker_id)
        return jsonify(broker)
    except Exception as e:
        logger.error(f"Error getting broker: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/brokers/<broker_id>/accounts", methods=["GET"])
def get_broker_accounts(broker_id: Any) -> Any:
    """Get accounts for a broker"""
    try:
        accounts = broker_integration.get_accounts(broker_id)
        return jsonify({"accounts": accounts})
    except Exception as e:
        logger.error(f"Error getting broker accounts: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/brokers/<broker_id>/positions", methods=["GET"])
def get_broker_positions(broker_id: Any) -> Any:
    """Get positions for a broker"""
    try:
        account_id = request.args.get("account_id")
        if not account_id:
            raise ValidationError("Account ID is required")
        positions = broker_integration.get_positions(broker_id, account_id)
        return jsonify({"positions": positions})
    except Exception as e:
        logger.error(f"Error getting broker positions: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
