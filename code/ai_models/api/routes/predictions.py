from ai_models.api.http import int_arg, json_body, optional_int, services, truthy
from ai_models.core.exceptions import ValidationError
from flask import Blueprint, jsonify, request

bp = Blueprint("predictions", __name__)


def _horizon(data, default=None):
    value = optional_int(data, "horizon")
    return value if value is not None else default


@bp.route("/api/predict", methods=["POST"])
def predict():
    data = json_body(required=True)
    return jsonify(
        services().predictor.predict(
            data.get("model_id"),
            data.get("symbol"),
            data.get("timeframe", "1d"),
            data.get("period"),
            _horizon(data),
            optional_int(data, "version"),
            truthy(data.get("persist", False)),
        )
    )


@bp.route("/api/predict/<model_id>/<symbol>", methods=["GET"])
def predict_get(model_id: str, symbol: str):
    return jsonify(
        services().predictor.predict(
            model_id,
            symbol,
            request.args.get("timeframe", "1d"),
            request.args.get("period"),
            int_arg("horizon", None, 1, 60),
            int_arg("version", None, 1, 100000),
            truthy(request.args.get("persist", False)),
        )
    )


@bp.route("/api/predict/batch", methods=["POST"])
def predict_batch():
    data = json_body(required=True)
    return jsonify(
        services().predictor.predict_many(
            data.get("model_id"),
            data.get("symbols"),
            data.get("timeframe", "1d"),
            data.get("period"),
            _horizon(data),
            truthy(data.get("persist", False)),
        )
    )


@bp.route("/api/predict/ensemble", methods=["POST"])
def predict_ensemble():
    data = json_body(required=True)
    return jsonify(
        services().ensemble.predict(
            data.get("model_ids"),
            data.get("symbol"),
            data.get("timeframe", "1d"),
            data.get("period"),
            _horizon(data),
            data.get("weights"),
            data.get("mode", "skill"),
        )
    )


@bp.route("/api/models/<model_id>/predictions/<symbol>", methods=["GET"])
def prediction_history(model_id: str, symbol: str):
    services().registry.get(model_id)
    return jsonify(
        services().store.history(
            model_id,
            symbol.upper(),
            request.args.get("start_date"),
            request.args.get("end_date"),
            int_arg("limit", 1000, 1, 10000),
        )
    )


@bp.route("/api/models/<model_id>/predictions", methods=["POST"])
def save_prediction(model_id: str):
    data = json_body(required=True)
    svc = services()
    info = svc.registry.get(model_id)
    for key in ("symbol", "timestamp", "prediction"):
        if data.get(key) in (None, ""):
            raise ValidationError(f"{key} is required")
    saved = svc.store.save_prediction(
        model_id,
        str(data["symbol"]).upper(),
        data["timestamp"],
        data["prediction"],
        data.get("actual"),
        svc.predictor._model_info(info),
    )
    return jsonify(saved), 201


@bp.route("/api/predictions/<prediction_id>", methods=["PUT"])
def update_prediction(prediction_id: str):
    data = json_body(required=True)
    if "actual" not in data:
        raise ValidationError("actual is required")
    return jsonify(services().store.update_actual(prediction_id, data["actual"]))


@bp.route("/api/models/<model_id>/performance", methods=["GET"])
def model_performance(model_id: str):
    services().registry.get(model_id)
    symbol = request.args.get("symbol")
    return jsonify(
        services().store.performance(
            model_id,
            symbol.upper() if symbol else None,
            request.args.get("start_date"),
            request.args.get("end_date"),
        )
    )


@bp.route("/api/models/<model_id>/reconcile", methods=["POST"])
def reconcile(model_id: str):
    data = json_body()
    symbol = data.get("symbol")
    return jsonify(
        services().tracker.reconcile(model_id, symbol.upper() if symbol else None)
    )
