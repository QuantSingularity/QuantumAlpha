from typing import Any, Dict, Optional

from ai_models.api.container import Services
from ai_models.core.exceptions import ValidationError
from flask import current_app, request


def services() -> Services:
    return current_app.extensions["services"]


def json_body(required: bool = False) -> Dict[str, Any]:
    data = request.get_json(silent=True)
    if data is None:
        if required:
            raise ValidationError("A JSON request body is required")
        return {}
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")
    return data


def int_arg(name: str, default: Optional[int], low: int, high: int) -> Optional[int]:
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ValidationError(f"{name} must be an integer")
    if value < low or value > high:
        raise ValidationError(f"{name} must be between {low} and {high}")
    return value


def truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def optional_int(data: Dict[str, Any], key: str) -> Optional[int]:
    value = data.get(key)
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{key} must be an integer")
