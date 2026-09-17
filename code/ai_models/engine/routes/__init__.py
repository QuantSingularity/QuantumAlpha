"""
Flask blueprints for the QuantumAlpha AI Engine.

Each module exposes a `create_*_blueprint(...)` factory that takes the
already-constructed service singleton(s) and returns a configured
`flask.Blueprint`, following the same pattern used by
`backend.common.monitoring.create_monitoring_blueprint`.
"""

from ai_models.engine.routes.models_routes import create_models_blueprint
from ai_models.engine.routes.prediction_routes import create_prediction_blueprint
from ai_models.engine.routes.rl_routes import create_rl_blueprint
from ai_models.engine.routes.signal_routes import create_signal_blueprint

__all__ = [
    "create_models_blueprint",
    "create_prediction_blueprint",
    "create_rl_blueprint",
    "create_signal_blueprint",
]
