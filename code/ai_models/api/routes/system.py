import os
import time

from ai_models.api.http import services
from flask import Blueprint, Response, jsonify, request

bp = Blueprint("system", __name__)
STARTED = time.time()


@bp.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "healthy",
            "service": "ai-engine",
            "uptime_seconds": round(time.time() - STARTED, 1),
        }
    )


@bp.route("/ready", methods=["GET"])
def ready():
    svc = services()
    checks = {
        "registry": os.access(svc.settings.model_dir, os.W_OK),
        "database": svc.store.healthy(),
        "data_service": svc.data_client.healthy(),
    }
    required = checks["registry"] and checks["database"]
    body = {
        "status": "ready" if required else "not_ready",
        "checks": checks,
        "storage": svc.store.backend,
    }
    return jsonify(body), 200 if required else 503


@bp.route("/metrics", methods=["GET"])
def metrics():
    return Response(services().metrics.render(), mimetype="text/plain; version=0.0.4")


@bp.route("/api/models/<model_id>/drift", methods=["GET"])
def drift(model_id: str):
    return jsonify(
        services().tracker.drift(
            model_id,
            (request.args.get("symbol") or "").upper() or None,
            request.args.get("timeframe", "1d"),
            request.args.get("period", "730d"),
        )
    )


@bp.route("/api/models/<model_id>/health", methods=["GET"])
def model_health(model_id: str):
    symbol = (request.args.get("symbol") or "").upper() or None
    check = request.args.get("drift", "true").lower() != "false"
    return jsonify(services().tracker.health(model_id, symbol, check))
