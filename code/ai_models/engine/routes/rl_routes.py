"""
Reinforcement-learning routes for the QuantumAlpha AI Engine.

Wires the Flask HTTP layer to
ai_models.engine.reinforcement_learning.ReinforcementLearningService.
Previously `/api/rl/train` and `/api/rl/act` called `train_agent` and
`get_action`, methods that don't exist on that class (the real methods are
`create_model`/`train_model` and `predict`); fixed here, and CRUD routes
are added so the service's model registry is reachable over HTTP at all.
"""

import logging

from backend.common import ServiceError, ValidationError, setup_logger
from flask import Blueprint, jsonify, request

logger = setup_logger("ai_engine.rl_routes", logging.INFO)


def create_rl_blueprint(rl_service: object) -> Blueprint:
    """Build the /api/rl/* routes.

    Args:
        rl_service: A ReinforcementLearningService instance.
    """
    rl_bp = Blueprint("rl", __name__, url_prefix="/api/rl")

    @rl_bp.route("/models", methods=["GET"])
    def get_models() -> object:
        """List all RL models"""
        try:
            return jsonify({"models": rl_service.get_models()})
        except Exception as e:
            logger.error(f"Error getting RL models: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    @rl_bp.route("/models", methods=["POST"])
    def create_model() -> object:
        """Create a new (untrained) RL model definition"""
        try:
            data = request.json or {}
            model = rl_service.create_model(data)
            return (jsonify(model), 201)
        except Exception as e:
            logger.error(f"Error creating RL model: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    @rl_bp.route("/models/<model_id>", methods=["GET"])
    def get_model(model_id: str) -> object:
        """Get a specific RL model"""
        try:
            return jsonify(rl_service.get_model(model_id))
        except Exception as e:
            logger.error(f"Error getting RL model: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    @rl_bp.route("/models/<model_id>", methods=["PUT"])
    def update_model(model_id: str) -> object:
        """Update an RL model's metadata"""
        try:
            data = request.json or {}
            return jsonify(rl_service.update_model(model_id, data))
        except Exception as e:
            logger.error(f"Error updating RL model: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    @rl_bp.route("/models/<model_id>", methods=["DELETE"])
    def delete_model(model_id: str) -> object:
        """Delete an RL model and its artifacts"""
        try:
            return jsonify(rl_service.delete_model(model_id))
        except Exception as e:
            logger.error(f"Error deleting RL model: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    @rl_bp.route("/train", methods=["POST"])
    def train_agent() -> object:
        """Train a reinforcement learning agent.

        If `model_id` is present in the body, trains that existing agent.
        Otherwise a new agent is created first from the body (name,
        algorithm, parameters, features) and then trained in the same call.
        """
        try:
            data = request.json or {}
            model_id = data.get("model_id")
            if not model_id:
                created = rl_service.create_model(data)
                model_id = created["id"]
            agent = rl_service.train_model(model_id, data)
            return jsonify(agent)
        except Exception as e:
            logger.error(f"Error training RL agent: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    @rl_bp.route("/act", methods=["POST"])
    def get_rl_action() -> object:
        """Run a trained agent over a symbol's recent history and return
        its action sequence. Body: model_id, symbol, timeframe, period."""
        try:
            data = request.json or {}
            model_id = data.get("model_id")
            if not model_id:
                raise ValidationError("Model ID is required")
            result = rl_service.predict(model_id, data)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error getting RL action: {e}")
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e))

    return rl_bp
