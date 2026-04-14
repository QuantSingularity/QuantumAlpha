"""
AI Engine for QuantumAlpha
This service is responsible for:
1. Model training and evaluation
2. Real-time prediction generation
3. Reinforcement learning environment
4. Model registry management
"""

import logging
import os
import traceback
from typing import Any

from ai_models.engine.model_manager import ModelManager
from ai_models.engine.prediction_service import PredictionService
from ai_models.engine.reinforcement_learning import ReinforcementLearningService
from backend.common import (
    ServiceError,
    ValidationError,
    get_config_manager,
    get_db_manager,
    setup_logger,
)
from flask import Flask, jsonify, request
from flask_cors import CORS

logger = setup_logger("ai_engine", logging.INFO)
app = Flask(__name__)
CORS(app)
config_manager = get_config_manager(
    env_file=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", ".env"
    )
)
db_manager = get_db_manager(config_manager.get_all())
model_manager = ModelManager(config_manager, db_manager)
prediction_service = PredictionService(config_manager, db_manager, model_manager)
rl_service = ReinforcementLearningService(config_manager, db_manager)


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
    return jsonify({"status": "ok", "service": "ai_engine"})


@app.route("/api/models", methods=["GET"])
def get_models() -> Any:
    """Get all models"""
    try:
        models = model_manager.get_models()
        return jsonify({"models": models})
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/models/<model_id>", methods=["GET"])
def get_model(model_id: Any) -> Any:
    """Get a specific model"""
    try:
        model = model_manager.get_model(model_id)
        return jsonify(model)
    except Exception as e:
        logger.error(f"Error getting model: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/train-model", methods=["POST"])
def train_model() -> Any:
    """Train a new model or retrain an existing one"""
    try:
        data = request.json
        model = model_manager.train_model(data)
        return jsonify(model)
    except Exception as e:
        logger.error(f"Error training model: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/generate-signals", methods=["POST"])
def generate_signals() -> Any:
    """Generate trading signals using a model"""
    try:
        data = request.json
        if "symbol" not in data:
            raise ValidationError("Symbol is required")
        if "data" not in data:
            raise ValidationError("Data is required")
        model_id = data.get("model_id")
        signals = prediction_service.generate_signals(
            symbol=data["symbol"], data=data["data"], model_id=model_id
        )
        return jsonify({"symbol": data["symbol"], "signals": signals})
    except Exception as e:
        logger.error(f"Error generating signals: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/predict", methods=["POST"])
def predict() -> Any:
    """Generate predictions using a model"""
    try:
        data = request.json
        if "model_id" not in data:
            raise ValidationError("Model ID is required")
        if "data" not in data:
            raise ValidationError("Data is required")
        predictions = prediction_service.predict(
            model_id=data["model_id"], data=data["data"]
        )
        return jsonify({"model_id": data["model_id"], "predictions": predictions})
    except Exception as e:
        logger.error(f"Error generating predictions: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/rl/train", methods=["POST"])
def train_rl_agent() -> Any:
    """Train a reinforcement learning agent"""
    try:
        data = request.json
        agent = rl_service.train_agent(data)
        return jsonify(agent)
    except Exception as e:
        logger.error(f"Error training RL agent: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/rl/act", methods=["POST"])
def get_rl_action() -> Any:
    """Get action from a reinforcement learning agent"""
    try:
        data = request.json
        if "agent_id" not in data:
            raise ValidationError("Agent ID is required")
        if "state" not in data:
            raise ValidationError("State is required")
        action = rl_service.get_action(agent_id=data["agent_id"], state=data["state"])
        return jsonify({"agent_id": data["agent_id"], "action": action})
    except Exception as e:
        logger.error(f"Error getting RL action: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
