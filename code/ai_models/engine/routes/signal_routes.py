"""
Trading-signal routes for the QuantumAlpha AI Engine.

Wires the Flask HTTP layer to
ai_models.engine.prediction_service.PredictionService.generate_signals.
Previously this route called generate_signals(symbol=..., data=...,
model_id=...) - keyword arguments that don't exist on the real method
(generate_signals(symbols, model_id, timeframe, period, strategy)) - so
every call raised a TypeError. Fixed here to match the real signature.
"""

import logging

from backend.common import ServiceError, ValidationError, setup_logger
from flask import Blueprint, jsonify, request

logger = setup_logger("ai_engine.signal_routes", logging.INFO)


def create_signal_blueprint(prediction_service: object) -> Blueprint:
    """Build the /api/generate-signals route.

    Args:
        prediction_service: A PredictionService instance.
    """
    signals_bp = Blueprint("signals", __name__)

    @signals_bp.route("/api/generate-signals", methods=["POST"])
    def generate_signals() -> object:
        """Generate trading signals.

        Body: symbols (list, required), model_id (required for the default
        "prediction" strategy), timeframe, period, strategy
        ("prediction" | "technical" | "ensemble").
        """
        try:
            data = request.json or {}
            symbols = data.get("symbols")
            if not symbols:
                raise ValidationError("Symbols are required")
            result = prediction_service.generate_signals(
                symbols=symbols,
                model_id=data.get("model_id"),
                timeframe=data.get("timeframe", "1d"),
                period=data.get("period", "1mo"),
                strategy=data.get("strategy", "prediction"),
            )
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    return signals_bp
