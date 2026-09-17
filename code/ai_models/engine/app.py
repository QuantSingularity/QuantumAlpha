"""
AI Engine for QuantumAlpha
This service is responsible for:
1. Model training and evaluation
2. Real-time prediction generation
3. Reinforcement learning environment
4. Model registry management

The HTTP layer lives in ai_models/engine/routes/ (Flask blueprints); this
module wires up the service singletons and registers them.
"""

import logging
import os
import traceback

from ai_models.engine.model_manager import ModelManager
from ai_models.engine.prediction_service import PredictionService
from ai_models.engine.reinforcement_learning import ReinforcementLearningService
from ai_models.engine.routes import (
    create_models_blueprint,
    create_prediction_blueprint,
    create_rl_blueprint,
    create_signal_blueprint,
)
from backend.common import (
    ServiceError,
    get_config_manager,
    get_db_manager,
    setup_logger,
)
from flask import Flask, jsonify
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

app.register_blueprint(create_models_blueprint(model_manager))
app.register_blueprint(create_prediction_blueprint(prediction_service))
app.register_blueprint(create_signal_blueprint(prediction_service))
app.register_blueprint(create_rl_blueprint(rl_service))


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
    return jsonify({"status": "ok", "service": "ai_engine"})


if __name__ == "__main__":
    port = int(
        config_manager.get("services.ai_engine.port")
        or os.getenv("PORT")
        or os.getenv("AI_ENGINE_PORT", "8082")
    )
    app.run(host="0.0.0.0", port=port, debug=True)
