from ai_models.api.http import int_arg, json_body, services, truthy
from flask import Blueprint, jsonify, request

bp = Blueprint("signals", __name__)


@bp.route("/api/generate-signals", methods=["POST"])
def generate_signals():
    data = json_body(required=True)
    weights = data.get("weights")
    return jsonify(
        services().signals.generate(
            data.get("symbols"),
            data.get("model_id"),
            data.get("timeframe", "1d"),
            data.get("period"),
            data.get("strategy", "prediction"),
            weights if isinstance(weights, dict) else None,
            truthy(data.get("persist", False)),
        )
    )


@bp.route("/api/signals", methods=["GET"])
def recent_signals():
    symbol = request.args.get("symbol")
    return jsonify(
        services().store.recent_signals(
            symbol.upper() if symbol else None, int_arg("limit", 50, 1, 500)
        )
    )
