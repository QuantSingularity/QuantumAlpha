from dataclasses import dataclass, field
from typing import Any, Dict

from ai_models.core.exceptions import ValidationError
from ai_models.core.settings import Settings
from ai_models.data.client import normalize_period, validate_symbol, validate_timeframe

PARAM_KEYS = (
    "epochs",
    "batch_size",
    "learning_rate",
    "units",
    "dropout",
    "filters",
    "kernel_size",
    "d_model",
    "num_heads",
    "num_blocks",
    "ff_dim",
    "patience",
    "alpha",
    "n_estimators",
    "max_depth",
    "min_samples_leaf",
    "subsample",
    "seed",
)


@dataclass
class TrainingConfig:
    symbol: str
    timeframe: str = "1d"
    period: str = "730d"
    sequence_length: int = 30
    horizon: int = 5
    test_size: float = 0.2
    val_size: float = 0.1
    params: Dict[str, Any] = field(default_factory=dict)
    activate: bool = True


def _number(
    data: Dict[str, Any], key: str, default: Any, cast: Any, low: float, high: float
) -> Any:
    value = data.get(key, default)
    try:
        value = cast(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{key} must be a number")
    if value < low or value > high:
        raise ValidationError(f"{key} must be between {low} and {high}")
    return value


def parse_training_config(data: Dict[str, Any], settings: Settings) -> TrainingConfig:
    params: Dict[str, Any] = {}
    if isinstance(data.get("parameters"), dict):
        params.update(data["parameters"])
    for key in PARAM_KEYS:
        if key in data:
            params[key] = data[key]
    if "epochs" in params:
        try:
            params["epochs"] = int(params["epochs"])
        except (TypeError, ValueError):
            raise ValidationError("epochs must be an integer")
        if not 1 <= params["epochs"] <= settings.max_training_epochs:
            raise ValidationError(
                f"epochs must be between 1 and {settings.max_training_epochs}"
            )
    return TrainingConfig(
        symbol=validate_symbol(data.get("symbol")),
        timeframe=validate_timeframe(data.get("timeframe", "1d")),
        period=normalize_period(data.get("period", "730d")),
        sequence_length=_number(data, "sequence_length", 30, int, 2, 500),
        horizon=_number(data, "horizon", 5, int, 1, 60),
        test_size=_number(data, "test_size", 0.2, float, 0.05, 0.5),
        val_size=_number(data, "val_size", 0.1, float, 0.0, 0.3),
        params=params,
        activate=bool(data.get("activate", True)),
    )
