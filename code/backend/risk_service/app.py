"""
Risk Service for QuantumAlpha
This service is responsible for:
1. Portfolio risk calculation
2. Stress testing and scenario analysis
3. Position sizing optimization
4. Risk monitoring and alerts
"""

import logging
import os
import traceback

from backend.common import (
    ServiceError,
    ValidationError,
    get_config_manager,
    get_db_manager,
    setup_logger,
    validate_schema,
)
from backend.common.validation import (
    PositionSizeRequest,
    RiskMetricsRequest,
    StressTestRequest,
)
from backend.risk_service.position_sizing import PositionSizing
from backend.risk_service.risk_calculator import RiskCalculator
from backend.risk_service.stress_testing import StressTesting
from flask import Flask, jsonify, request
from flask_cors import CORS

logger = setup_logger("risk_service", logging.INFO)
app = Flask(__name__)
CORS(app)
config_manager = get_config_manager(
    env_file=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", ".env"
    )
)
db_manager = get_db_manager(config_manager.get_all())
risk_calculator = RiskCalculator(config_manager, db_manager)
stress_testing = StressTesting(config_manager, db_manager)
position_sizing = PositionSizing(config_manager, db_manager)


@app.errorhandler(Exception)
def handle_error(error: Exception) -> None:
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
def health_check() -> object:
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "risk_service"})


@app.route("/api/risk-metrics", methods=["POST"])
def calculate_risk_metrics() -> None:
    """Calculate risk metrics for a portfolio"""
    try:
        data = request.json
        validated_data = validate_schema(data, RiskMetricsRequest)
        risk_metrics = risk_calculator.calculate_risk_metrics(
            portfolio=validated_data["portfolio"],
            confidence_levels=validated_data["confidence_levels"],
            timeframe=validated_data["timeframe"],
            include_positions=validated_data["include_positions"],
        )
        return jsonify(risk_metrics)
    except Exception as e:
        logger.error(f"Error calculating risk metrics: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/stress-test", methods=["POST"])
def run_stress_test() -> None:
    """Run stress tests on a portfolio"""
    try:
        data = request.json
        validated_data = validate_schema(data, StressTestRequest)
        stress_test_results = stress_testing.run_stress_test(
            portfolio=validated_data["portfolio"],
            scenario_name=validated_data["scenario_name"],
            parameters=validated_data.get("parameters"),
            shocks=validated_data.get("shocks"),
        )
        return jsonify(stress_test_results)
    except Exception as e:
        logger.error(f"Error running stress tests: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/calculate-position", methods=["POST"])
def calculate_position_size() -> None:
    """Calculate optimal position size, sized so a stop-out at stop_price
    loses no more than the requested risk_amount/risk_percent."""
    try:
        data = request.json
        validated_data = validate_schema(data, PositionSizeRequest)
        portfolio = validated_data["portfolio"]
        entry_price = float(validated_data["entry_price"])
        stop_price = float(validated_data["stop_price"])
        side = validated_data["side"]
        risk_percent = validated_data.get("risk_percent")
        if risk_percent is not None:
            # Schema stores this as a 0-1 fraction; the sizing method wants
            # a percentage.
            risk_percent = float(risk_percent) * 100
        else:
            portfolio_value = risk_calculator.calculate_portfolio_value(portfolio)[
                "total_value"
            ]
            if portfolio_value <= 0:
                raise ValidationError(
                    "Portfolio has no value to size a risk_amount against"
                )
            risk_percent = float(validated_data["risk_amount"]) / portfolio_value * 100
        stop_loss_percent = abs(entry_price - stop_price) / entry_price * 100
        position_size = position_sizing.calculate_position_size(
            portfolio=portfolio,
            symbol=validated_data["symbol"],
            price=entry_price,
            method="risk",
            params={
                "risk_percent": risk_percent,
                "stop_loss_percent": stop_loss_percent,
            },
        )
        position_size["side"] = side
        position_size["entry_price"] = entry_price
        position_size["stop_price"] = stop_price
        return jsonify(position_size)
    except Exception as e:
        logger.error(f"Error calculating position size: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/portfolio-risk", methods=["POST"])
def get_portfolio_risk() -> None:
    """Get a risk-metrics snapshot for a portfolio.

    POST (not GET) because risk_service has no way to look up a portfolio
    by ID on its own - the caller must supply the portfolio's current
    state (positions + cash) in the request body.
    """
    try:
        data = request.json or {}
        portfolio = data.get("portfolio")
        if not portfolio:
            raise ValidationError("Portfolio is required")
        portfolio_risk = risk_calculator.get_portfolio_risk(portfolio)
        return jsonify(portfolio_risk)
    except Exception as e:
        logger.error(f"Error getting portfolio risk: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/risk-alerts", methods=["POST"])
def get_risk_alerts() -> None:
    """Get threshold-based risk alerts for a portfolio (see POST
    /api/portfolio-risk for why this takes a body instead of a GET query)."""
    try:
        data = request.json or {}
        portfolio = data.get("portfolio")
        if not portfolio:
            raise ValidationError("Portfolio is required")
        risk_alerts = risk_calculator.get_risk_alerts(
            portfolio,
            var_threshold_percent=float(data.get("var_threshold_percent", 5.0)),
            concentration_threshold_percent=float(
                data.get("concentration_threshold_percent", 25.0)
            ),
        )
        return jsonify({"alerts": risk_alerts})
    except Exception as e:
        logger.error(f"Error getting risk alerts: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/portfolio-value-prediction", methods=["POST"])
def get_portfolio_value_prediction() -> None:
    """Calculate a portfolio's current value alongside its AI-model-predicted
    value, using the ai_engine service (ai_models/engine)."""
    try:
        data = request.json or {}
        portfolio = data.get("portfolio")
        model_id = data.get("model_id")
        if not portfolio:
            raise ValidationError("Portfolio is required")
        if not model_id:
            raise ValidationError("Model ID is required")
        result = risk_calculator.calculate_portfolio_value_with_prediction(
            portfolio=portfolio, model_id=model_id
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error calculating portfolio value prediction: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


if __name__ == "__main__":
    port = int(
        config_manager.get("services.risk_service.port")
        or os.getenv("PORT")
        or os.getenv("RISK_SERVICE_PORT", "8083")
    )
    app.run(host="0.0.0.0", port=port, debug=True)
