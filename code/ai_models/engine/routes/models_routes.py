"""
Model registry routes for the QuantumAlpha AI Engine.

Wires the Flask HTTP layer to ai_models.engine.model_manager.ModelManager.
"""

import logging

from backend.common import ServiceError, setup_logger
from flask import Blueprint, jsonify, request

logger = setup_logger("ai_engine.models_routes", logging.INFO)


def create_models_blueprint(model_manager: object) -> Blueprint:
    """Build the /api/models and /api/train-model routes.

    Args:
        model_manager: A ModelManager instance (get_models, get_model,
            create_model, update_model, delete_model, train_model,
            evaluate_model).
    """
    models_bp = Blueprint("models", __name__)

    @models_bp.route("/api/models", methods=["GET"])
    def get_models() -> object:
        """List all models"""
        try:
            models = model_manager.get_models()
            return jsonify({"models": models})
        except Exception as e:
            logger.error(f"Error getting models: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    @models_bp.route("/api/models", methods=["POST"])
    def create_model() -> object:
        """Create a new (untrained) model definition"""
        try:
            data = request.json or {}
            model = model_manager.create_model(data)
            return (jsonify(model), 201)
        except Exception as e:
            logger.error(f"Error creating model: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    @models_bp.route("/api/models/<model_id>", methods=["GET"])
    def get_model(model_id: str) -> object:
        """Get a specific model"""
        try:
            model = model_manager.get_model(model_id)
            return jsonify(model)
        except Exception as e:
            logger.error(f"Error getting model: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    @models_bp.route("/api/models/<model_id>", methods=["PUT"])
    def update_model(model_id: str) -> object:
        """Update a model's metadata (name, description, parameters, features)"""
        try:
            data = request.json or {}
            model = model_manager.update_model(model_id, data)
            return jsonify(model)
        except Exception as e:
            logger.error(f"Error updating model: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    @models_bp.route("/api/models/<model_id>", methods=["DELETE"])
    def delete_model(model_id: str) -> object:
        """Delete a model and its artifacts"""
        try:
            result = model_manager.delete_model(model_id)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error deleting model: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    @models_bp.route("/api/models/<model_id>/evaluate", methods=["POST"])
    def evaluate_model(model_id: str) -> object:
        """Evaluate a trained model against held-out data"""
        try:
            data = request.json or {}
            result = model_manager.evaluate_model(model_id, data)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    @models_bp.route("/api/train-model", methods=["POST"])
    def train_model() -> object:
        """Train a new model or retrain an existing one.

        If `model_id` is present in the body, trains that existing model.
        Otherwise a new model is created first from the body (name, type,
        parameters, features) and then trained in the same call.
        """
        try:
            data = request.json or {}
            model_id = data.get("model_id")
            if not model_id:
                created = model_manager.create_model(data)
                model_id = created["id"]
            model = model_manager.train_model(model_id, data)
            return jsonify(model)
        except Exception as e:
            logger.error(f"Error training model: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    return models_bp
