from typing import Any, Dict, List, Optional, Type

from ai_models.core.exceptions import ValidationError
from ai_models.models.base import ForecastModel
from ai_models.models.classical import (
    GradientBoostingForecaster,
    RandomForestForecaster,
    RidgeForecaster,
)
from ai_models.models.deep import (
    CNNForecaster,
    GRUForecaster,
    LSTMForecaster,
    TransformerForecaster,
)

_MODEL_TYPES: Dict[str, Type[ForecastModel]] = {
    "lstm": LSTMForecaster,
    "gru": GRUForecaster,
    "cnn": CNNForecaster,
    "transformer": TransformerForecaster,
    "ridge": RidgeForecaster,
    "random_forest": RandomForestForecaster,
    "gradient_boosting": GradientBoostingForecaster,
}

DEFAULT_PARAMS: Dict[str, Dict[str, Any]] = {
    "lstm": {
        "units": 64,
        "dropout": 0.2,
        "epochs": 50,
        "batch_size": 32,
        "learning_rate": 0.001,
    },
    "gru": {
        "units": 64,
        "dropout": 0.2,
        "epochs": 50,
        "batch_size": 32,
        "learning_rate": 0.001,
    },
    "cnn": {
        "filters": 64,
        "kernel_size": 3,
        "dropout": 0.2,
        "epochs": 50,
        "batch_size": 32,
        "learning_rate": 0.001,
    },
    "transformer": {
        "d_model": 64,
        "num_heads": 4,
        "num_blocks": 2,
        "ff_dim": 128,
        "dropout": 0.1,
        "epochs": 50,
        "batch_size": 32,
        "learning_rate": 0.001,
    },
    "ridge": {"alpha": 1.0},
    "random_forest": {"n_estimators": 200, "max_depth": 8, "min_samples_leaf": 3},
    "gradient_boosting": {
        "n_estimators": 150,
        "learning_rate": 0.05,
        "max_depth": 3,
        "subsample": 0.8,
    },
}


def supported_types() -> List[str]:
    return sorted(_MODEL_TYPES)


def model_class(kind: str) -> Type[ForecastModel]:
    try:
        return _MODEL_TYPES[kind]
    except KeyError:
        raise ValidationError(
            f"Unsupported model type: {kind}", {"supported": supported_types()}
        )


def create_model(
    kind: str,
    params: Optional[Dict[str, Any]] = None,
    n_features: int = 0,
    sequence_length: int = 0,
    horizon: int = 1,
) -> ForecastModel:
    merged = {**DEFAULT_PARAMS.get(kind, {}), **(params or {})}
    return model_class(kind)(merged, n_features, sequence_length, horizon)


def load_model(
    kind: str,
    directory: str,
    params: Dict[str, Any],
    n_features: int,
    sequence_length: int,
    horizon: int,
) -> ForecastModel:
    return model_class(kind).load(
        directory, params, n_features, sequence_length, horizon
    )
