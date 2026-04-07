"""
AI Engine for QuantumAlpha
"""


def _lazy_load():
    from .model_manager import ModelManager
    from .prediction_service import PredictionService

    return ModelManager, PredictionService


__all__ = ["ModelManager", "PredictionService"]

try:
    from .model_manager import ModelManager
    from .prediction_service import PredictionService
except Exception:
    pass

try:
    __all__.append("ReinforcementLearningService")
except Exception:
    pass
