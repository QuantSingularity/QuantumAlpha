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
            risk_metrics=validated_data["risk_metrics"],
            confidence_level=validated_data["confidence_level"],
            lookback_period=validated_data["lookback_period"],
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
        stress_test_results = stress_testing.run_stress_tests(
            portfolio=validated_data["portfolio"], scenarios=validated_data["scenarios"]
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
    """Calculate optimal position size"""
    try:
        data = request.json
        validated_data = validate_schema(data, PositionSizeRequest)
        position_size = position_sizing.calculate_position_size(
            symbol=validated_data["symbol"],
            signal_strength=validated_data["signal_strength"],
            portfolio_value=validated_data["portfolio_value"],
            risk_tolerance=validated_data["risk_tolerance"],
            volatility=validated_data.get("volatility"),
        )
        return jsonify(position_size)
    except Exception as e:
        logger.error(f"Error calculating position size: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/portfolio-risk", methods=["GET"])
def get_portfolio_risk() -> None:
    """Get risk metrics for a portfolio"""
    try:
        portfolio_id = request.args.get("portfolio_id")
        if not portfolio_id:
            raise ValidationError("Portfolio ID is required")
        portfolio_risk = risk_calculator.get_portfolio_risk(portfolio_id)
        return jsonify(portfolio_risk)
    except Exception as e:
        logger.error(f"Error getting portfolio risk: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/risk-alerts", methods=["GET"])
def get_risk_alerts() -> None:
    """Get risk alerts"""
    try:
        portfolio_id = request.args.get("portfolio_id")
        risk_alerts = risk_calculator.get_risk_alerts(portfolio_id)
        return jsonify({"alerts": risk_alerts})
    except Exception as e:
        logger.error(f"Error getting risk alerts: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
