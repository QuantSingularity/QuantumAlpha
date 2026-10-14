import hmac
import time
import uuid
from typing import Optional

from ai_models.api.container import Services, build_services
from ai_models.api.routes import models, predictions, rl, signals, system
from ai_models.core.exceptions import AIEngineError, AuthenticationError
from ai_models.core.logging import get_logger
from ai_models.core.settings import Settings, get_settings
from flask import Flask, g, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

logger = get_logger("api")

PUBLIC_PATHS = {"/health", "/ready", "/metrics"}


def _route_label() -> str:
    rule = request.url_rule
    return rule.rule if rule is not None else "unmatched"


def create_app(
    settings: Optional[Settings] = None, services: Optional[Services] = None
) -> Flask:
    settings = settings or get_settings()
    app = Flask(__name__)
    app.json.sort_keys = False
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
    CORS(app, origins=list(settings.cors_origins))
    app.extensions["services"] = services or build_services(settings)
    metrics = app.extensions["services"].metrics

    @app.before_request
    def before() -> None:
        g.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        g.started = time.perf_counter()
        if (
            not settings.api_key
            or request.method == "OPTIONS"
            or request.path in PUBLIC_PATHS
        ):
            return
        supplied = (
            request.headers.get("X-Internal-Key")
            or request.headers.get("X-API-Key")
            or ""
        )
        if not hmac.compare_digest(supplied.encode(), settings.api_key.encode()):
            raise AuthenticationError("Invalid or missing API key")

    @app.after_request
    def after(response):
        response.headers["X-Request-ID"] = g.get("request_id", "")
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        elapsed = time.perf_counter() - g.get("started", time.perf_counter())
        label = _route_label()
        metrics.inc(
            "ai_engine_requests_total",
            method=request.method,
            route=label,
            status=response.status_code,
        )
        metrics.observe("ai_engine_request_seconds", elapsed, route=label)
        return response

    @app.errorhandler(AIEngineError)
    def handle_engine_error(error: AIEngineError):
        if error.status_code >= 500:
            logger.error(
                "%s %s failed: %s", request.method, request.path, error.message
            )
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        return (
            jsonify(
                {
                    "error": error.description,
                    "code": error.name.upper().replace(" ", "_"),
                    "status_code": error.code,
                }
            ),
            error.code,
        )

    @app.errorhandler(Exception)
    def handle_unexpected(error: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.path)
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "code": "INTERNAL_ERROR",
                    "status_code": 500,
                }
            ),
            500,
        )

    for module in (system, models, predictions, signals, rl):
        app.register_blueprint(module.bp)
    return app
