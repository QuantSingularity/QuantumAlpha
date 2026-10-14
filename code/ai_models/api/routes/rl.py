from ai_models.api.http import json_body, services, truthy
from ai_models.core.exceptions import ConflictError, ValidationError
from ai_models.rl.agents import ALGORITHMS
from flask import Blueprint, jsonify, request

bp = Blueprint("rl", __name__, url_prefix="/api/rl")


@bp.route("/algorithms", methods=["GET"])
def algorithms():
    return jsonify(list(ALGORITHMS))


@bp.route("/models", methods=["GET"])
def list_models():
    return jsonify(services().rl.list(request.args.get("status")))


@bp.route("/models", methods=["POST"])
def create_model():
    return jsonify(services().rl.create(json_body(required=True))), 201


@bp.route("/models/<model_id>", methods=["GET"])
def get_model(model_id: str):
    return jsonify(services().rl.get(model_id))


@bp.route("/models/<model_id>", methods=["PUT", "PATCH"])
def update_model(model_id: str):
    return jsonify(services().rl.update(model_id, json_body(required=True)))


@bp.route("/models/<model_id>", methods=["DELETE"])
def delete_model(model_id: str):
    return jsonify(services().rl.delete(model_id))


@bp.route("/train", methods=["POST"])
def train():
    data = json_body(required=True)
    model_id = data.get("model_id")
    if not model_id:
        raise ValidationError("Model ID is required")
    svc = services()
    if svc.rl_registry.get(model_id)["status"] == "training":
        raise ConflictError(f"Model is already training: {model_id}")
    if truthy(data.get("async", False)):
        job = svc.jobs.submit(
            "rl_train", svc.rl.train, model_id, data, meta={"model_id": model_id}
        )
        return jsonify(job), 202
    return jsonify(svc.rl.train(model_id, data))


@bp.route("/act", methods=["POST"])
def act():
    data = json_body(required=True)
    model_id = data.get("model_id")
    if not model_id:
        raise ValidationError("Model ID is required")
    return jsonify(services().rl.predict(model_id, data))
