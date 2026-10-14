from typing import Any, Dict

from ai_models.api.http import int_arg, json_body, optional_int, services, truthy
from ai_models.core.exceptions import ConflictError, ValidationError
from ai_models.data.features import (
    DEFAULT_FEATURES,
    supported_features,
    validate_features,
)
from ai_models.evaluation.evaluator import evaluate_bundle
from ai_models.inference.explain import permutation_importance
from ai_models.models.factory import DEFAULT_PARAMS, model_class, supported_types
from ai_models.registry.store import ModelRegistry
from ai_models.training.config import parse_training_config
from ai_models.training.tuning import DEFAULT_GRIDS, search
from ai_models.training.validation import walk_forward
from flask import Blueprint, jsonify, request

bp = Blueprint("models", __name__)


def _guard_not_training(model_id: str) -> None:
    if services().registry.get(model_id)["status"] == "training":
        raise ConflictError(f"Model is already training: {model_id}")


def _submit_or_run(kind: str, model_id: str, fn: Any, data: Dict[str, Any]):
    if truthy(data.get("async", False)):
        job = services().jobs.submit(kind, fn, meta={"model_id": model_id})
        return jsonify(job), 202
    return jsonify(fn()), 200


@bp.route("/api/catalog", methods=["GET"])
def catalog():
    return jsonify(
        {
            "model_types": [
                {
                    "type": t,
                    "family": model_class(t).family,
                    "defaults": DEFAULT_PARAMS.get(t, {}),
                    "search_space": DEFAULT_GRIDS.get(t, {}),
                }
                for t in supported_types()
            ],
            "features": supported_features(),
            "default_features": list(DEFAULT_FEATURES),
        }
    )


@bp.route("/api/models", methods=["GET"])
def list_models():
    return jsonify(
        services().registry.list(request.args.get("status"), request.args.get("type"))
    )


@bp.route("/api/models", methods=["POST"])
def create_model():
    data = json_body(required=True)
    kind = data.get("type")
    model_class(kind)
    features = validate_features(data.get("features")) or list(DEFAULT_FEATURES)
    parameters = data.get("parameters") or {}
    if not isinstance(parameters, dict):
        raise ValidationError("parameters must be an object")
    info = services().registry.create(
        data.get("name"),
        kind,
        data.get("description", ""),
        parameters,
        features,
        data.get("tags"),
    )
    return jsonify(ModelRegistry.detail(info)), 201


@bp.route("/api/models/<model_id>", methods=["GET"])
def get_model(model_id: str):
    return jsonify(ModelRegistry.detail(services().registry.get(model_id)))


@bp.route("/api/models/<model_id>", methods=["PUT", "PATCH"])
def update_model(model_id: str):
    data = json_body(required=True)
    changes = {
        k: data[k] for k in ("name", "description", "parameters", "tags") if k in data
    }
    if "features" in data:
        changes["features"] = validate_features(data["features"])
    return jsonify(ModelRegistry.detail(services().registry.update(model_id, changes)))


@bp.route("/api/models/<model_id>", methods=["DELETE"])
def delete_model(model_id: str):
    result = services().registry.delete(model_id)
    services().predictor.invalidate(model_id)
    return jsonify(result)


@bp.route("/api/train-model", methods=["POST"])
@bp.route("/api/models/<model_id>/train", methods=["POST"])
def train_model(model_id: str = None):
    data = json_body(required=True)
    model_id = model_id or data.get("model_id")
    if not model_id:
        raise ValidationError("Model ID is required")
    svc = services()
    svc.registry.get(model_id)
    config = parse_training_config(data, svc.settings)
    _guard_not_training(model_id)
    return _submit_or_run(
        "train", model_id, lambda: svc.trainer.train(model_id, config), data
    )


@bp.route("/api/models/<model_id>/evaluate", methods=["POST"])
def evaluate_model(model_id: str):
    data = json_body(required=True)
    svc = services()
    _, version, bundle = svc.predictor.load(model_id, optional_int(data, "version"))
    symbol = data.get("symbol") or bundle.meta.get("symbol")
    timeframe = data.get("timeframe", bundle.meta.get("timeframe", "1d"))
    period = data.get("period") or "730d"
    ohlcv = svc.data_client.fetch_ohlcv(symbol, timeframe, period)
    last_n = optional_int(data, "last_n") or 120
    metrics = evaluate_bundle(bundle, ohlcv, max(10, min(last_n, 2000)))
    return jsonify(
        {"model_id": model_id, "version": version, "symbol": symbol, "metrics": metrics}
    )


@bp.route("/api/models/<model_id>/validate", methods=["POST"])
def validate_model(model_id: str):
    data = json_body(required=True)
    svc = services()
    info = svc.registry.get(model_id)
    config = parse_training_config(data, svc.settings)
    splits = optional_int(data, "n_splits") or 4
    if not 2 <= splits <= 10:
        raise ValidationError("n_splits must be between 2 and 10")

    def run() -> Dict[str, Any]:
        ohlcv = svc.data_client.fetch_ohlcv(
            config.symbol, config.timeframe, config.period
        )
        params = {**(info.get("parameters") or {}), **config.params}
        result = walk_forward(
            ohlcv,
            info["type"],
            params,
            info.get("features"),
            config.sequence_length,
            config.horizon,
            splits,
        )
        result.update(model_id=model_id, symbol=config.symbol)
        return result

    return _submit_or_run("validate", model_id, run, data)


@bp.route("/api/models/<model_id>/tune", methods=["POST"])
def tune_model(model_id: str):
    data = json_body(required=True)
    svc = services()
    info = svc.registry.get(model_id)
    config = parse_training_config(data, svc.settings)
    trials = optional_int(data, "trials") or 10
    grid = data.get("search_space")
    if grid is not None and not isinstance(grid, dict):
        raise ValidationError("search_space must be an object")
    apply = truthy(data.get("apply", False))

    def run() -> Dict[str, Any]:
        ohlcv = svc.data_client.fetch_ohlcv(
            config.symbol, config.timeframe, config.period
        )
        base = {**(info.get("parameters") or {}), **config.params}
        result = search(
            ohlcv,
            info["type"],
            info.get("features"),
            config.sequence_length,
            config.horizon,
            grid,
            base,
            trials,
        )
        if apply:
            svc.registry.update(
                model_id,
                {
                    "parameters": {
                        **(info.get("parameters") or {}),
                        **result["best_params"],
                    }
                },
            )
        result.update(model_id=model_id, applied=apply)
        return result

    return _submit_or_run("tune", model_id, run, data)


@bp.route("/api/models/<model_id>/versions", methods=["GET"])
def list_versions(model_id: str):
    return jsonify(ModelRegistry.detail(services().registry.get(model_id))["versions"])


@bp.route("/api/models/<model_id>/versions/<int:version>/promote", methods=["POST"])
def promote_version(model_id: str, version: int):
    info = services().registry.promote(model_id, version)
    services().predictor.invalidate(model_id)
    return jsonify(ModelRegistry.detail(info))


@bp.route("/api/models/<model_id>/versions/<int:version>", methods=["DELETE"])
def delete_version(model_id: str, version: int):
    result = services().registry.delete_version(model_id, version)
    services().predictor.invalidate(model_id)
    return jsonify(result)


@bp.route("/api/models/<model_id>/explain", methods=["GET"])
def explain_model(model_id: str):
    svc = services()
    _, version, bundle = svc.predictor.load(model_id)
    symbol = request.args.get("symbol") or bundle.meta.get("symbol")
    timeframe = request.args.get("timeframe", bundle.meta.get("timeframe", "1d"))
    ohlcv = svc.data_client.fetch_ohlcv(
        symbol, timeframe, request.args.get("period") or "730d"
    )
    result = permutation_importance(bundle, ohlcv, int_arg("samples", 200, 20, 1000))
    result.update(model_id=model_id, version=version, symbol=symbol)
    return jsonify(result)


@bp.route("/api/jobs", methods=["GET"])
def list_jobs():
    return jsonify(
        services().jobs.list(request.args.get("kind"), int_arg("limit", 50, 1, 200))
    )


@bp.route("/api/jobs/<job_id>", methods=["GET"])
def get_job(job_id: str):
    return jsonify(services().jobs.get(job_id))
