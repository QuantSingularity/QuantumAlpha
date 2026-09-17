"""
Prediction routes for the QuantumAlpha AI Engine.

Wires the Flask HTTP layer to
ai_models.engine.prediction_service.PredictionService. Previously the
`/api/predict` route called a `PredictionService.predict(...)` method that
did not exist (the real method is `generate_prediction`); this module fixes
that mismatch and adds the previously-unreachable history/performance
endpoints backed by already-implemented, tested service methods.
"""

import logging

from backend.common import ServiceError, ValidationError, setup_logger
from flask import Blueprint, jsonify, request

logger = setup_logger("ai_engine.prediction_routes", logging.INFO)


def create_prediction_blueprint(prediction_service: object) -> Blueprint:
    """Build the prediction/history/performance routes.

    Args:
        prediction_service: A PredictionService instance.
    """
    predictions_bp = Blueprint("predictions", __name__)

    def _generate(model_id, symbol, timeframe, period, horizon):
        if not model_id:
            raise ValidationError("Model ID is required")
        if not symbol:
            raise ValidationError("Symbol is required")
        return prediction_service.generate_prediction(
            model_id=model_id,
            symbol=symbol,
            timeframe=timeframe,
            period=period,
            horizon=horizon,
        )

    @predictions_bp.route("/api/predict", methods=["POST"])
    def predict() -> object:
        """Generate a prediction. Body: model_id, symbol, timeframe?, period?, horizon?"""
        try:
            data = request.json or {}
            prediction = _generate(
                model_id=data.get("model_id"),
                symbol=data.get("symbol"),
                timeframe=data.get("timeframe", "1d"),
                period=data.get("period", "1mo"),
                horizon=int(data.get("horizon", 5)),
            )
            return jsonify(prediction)
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    @predictions_bp.route("/api/predict/<model_id>/<symbol>", methods=["GET"])
    def predict_get(model_id: str, symbol: str) -> object:
        """Convenience GET form of /api/predict, e.g. for simple polling clients."""
        try:
            prediction = _generate(
                model_id=model_id,
                symbol=symbol,
                timeframe=request.args.get("timeframe", "1d"),
                period=request.args.get("period", "1mo"),
                horizon=int(request.args.get("horizon", 5)),
            )
            return jsonify(prediction)
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    @predictions_bp.route(
        "/api/models/<model_id>/predictions/<symbol>", methods=["GET"]
    )
    def prediction_history(model_id: str, symbol: str) -> object:
        """Get saved prediction history for a model/symbol pair"""
        try:
            history = prediction_service.get_prediction_history(
                model_id=model_id,
                symbol=symbol,
                start_date=request.args.get("start_date"),
                end_date=request.args.get("end_date"),
            )
            return jsonify(history)
        except Exception as e:
            logger.error(f"Error getting prediction history: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    @predictions_bp.route("/api/models/<model_id>/predictions", methods=["POST"])
    def save_prediction(model_id: str) -> object:
        """Persist a prediction (and optionally its realised actual value)"""
        try:
            data = request.json or {}
            result = prediction_service.save_prediction(
                model_id=model_id,
                symbol=data.get("symbol"),
                timestamp=data.get("timestamp"),
                prediction=data.get("prediction"),
                actual=data.get("actual"),
            )
            return (jsonify(result), 201)
        except Exception as e:
            logger.error(f"Error saving prediction: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    @predictions_bp.route("/api/predictions/<prediction_id>", methods=["PUT"])
    def update_prediction(prediction_id: str) -> object:
        """Attach a realised actual value to a previously saved prediction"""
        try:
            data = request.json or {}
            result = prediction_service.update_prediction(
                prediction_id=prediction_id, actual=data.get("actual")
            )
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error updating prediction: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    @predictions_bp.route("/api/models/<model_id>/performance", methods=["GET"])
    def model_performance(model_id: str) -> object:
        """Get accuracy/error metrics for a model, optionally scoped to a symbol"""
        try:
            performance = prediction_service.get_model_performance(
                model_id=model_id,
                symbol=request.args.get("symbol"),
                start_date=request.args.get("start_date"),
                end_date=request.args.get("end_date"),
            )
            return jsonify(performance)
        except Exception as e:
            logger.error(f"Error getting model performance: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    return predictions_bp
