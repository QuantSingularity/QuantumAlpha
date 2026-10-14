import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Tuple

import requests
from flask import Blueprint, Response, jsonify, request

logger = logging.getLogger(__name__)

READ_TIMEOUT = float(os.getenv("AI_GATEWAY_TIMEOUT", "30"))
LONG_TIMEOUT = float(os.getenv("AI_GATEWAY_LONG_TIMEOUT", "900"))
WRITE_ROLES = {"admin", "trader", "analyst"}
LONG_PATTERN = re.compile(r"^(models/[^/]+/(train|tune|validate|evaluate)|rl/train)$")
ALLOWED = re.compile(
    r"^(catalog|health|ready|jobs(/[^/]+)?|signals|predict(/batch|/ensemble|/[^/]+/[^/]+)?|predictions/[^/]+|"
    r"models|models/[^/]+|models/[^/]+/(train|evaluate|validate|tune|versions|explain|drift|health|performance|reconcile|predictions)|"
    r"models/[^/]+/versions/\d+(/promote)?|models/[^/]+/predictions/[^/]+|"
    r"rl/(algorithms|models|models/[^/]+|train|act))$"
)
READ_ONLY_POST = re.compile(
    r"^(predict(/batch|/ensemble)?|signals/generate|rl/act|models/[^/]+/evaluate)$"
)
ALIASES = {"signals/generate": "generate-signals"}


def resolve_upstream(subpath: str) -> Optional[str]:
    subpath = subpath.strip("/")
    if not ALLOWED.match(subpath) and subpath not in ALIASES:
        return None
    if subpath in ("health", "ready"):
        return f"/{subpath}"
    return "/api/" + ALIASES.get(subpath, subpath)


def is_write(method: str, subpath: str) -> bool:
    if method in ("GET", "HEAD", "OPTIONS"):
        return False
    return not (method == "POST" and READ_ONLY_POST.match(subpath.strip("/")))


class AIEngineClient:
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = session or requests.Session()

    def call(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        timeout: float = READ_TIMEOUT,
        request_id: Optional[str] = None,
    ) -> Tuple[int, Any]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["X-Internal-Key"] = self.api_key
        if request_id:
            headers["X-Request-ID"] = request_id
        try:
            response = self.session.request(
                method,
                f"{self.base_url}{path}",
                params=params,
                json=body if method in ("POST", "PUT", "PATCH") else None,
                headers=headers,
                timeout=timeout,
            )
        except requests.Timeout:
            return 504, {"error": "AI engine timed out", "code": "UPSTREAM_TIMEOUT"}
        except requests.RequestException as exc:
            logger.error("AI engine unreachable: %s", exc)
            return 503, {
                "error": "AI engine unavailable",
                "code": "UPSTREAM_UNAVAILABLE",
            }
        try:
            payload = response.json()
        except ValueError:
            payload = {
                "error": "AI engine returned a non-JSON response",
                "code": "UPSTREAM_ERROR",
            }
            return 502, payload
        return response.status_code, payload


def _envelope(status: int, payload: Any) -> Tuple[Response, int]:
    stamp = datetime.now(timezone.utc).isoformat()
    if status < 400:
        return jsonify({"success": True, "data": payload, "timestamp": stamp}), status
    message = payload.get("error") if isinstance(payload, dict) else str(payload)
    code = payload.get("code") if isinstance(payload, dict) else None
    return (
        jsonify({"success": False, "error": message, "code": code, "timestamp": stamp}),
        status,
    )


def create_ai_gateway_blueprint(
    auth_decorator: Optional[Callable[[Callable], Callable]] = None,
    envelope: bool = False,
    enforce_roles: bool = False,
    client: Optional[AIEngineClient] = None,
    name: str = "ai_gateway",
) -> Blueprint:
    bp = Blueprint(name, __name__, url_prefix="/api/ai")
    state: Dict[str, Optional[AIEngineClient]] = {"client": client}

    def get_client() -> AIEngineClient:
        if state["client"] is None:
            state["client"] = AIEngineClient(
                os.getenv("AI_ENGINE_URL")
                or f"http://{os.getenv('AI_ENGINE_HOST', 'localhost')}:{os.getenv('AI_ENGINE_PORT', '8082')}",
                os.getenv("AI_ENGINE_API_KEY") or None,
            )
        return state["client"]

    def respond(status: int, payload: Any):
        if envelope:
            return _envelope(status, payload)
        return jsonify(payload), status

    def has_write_role() -> bool:
        from flask_jwt_extended import get_jwt

        claims = get_jwt()
        roles = claims.get("roles")
        if roles is None:
            legacy = claims.get("role")
            roles = [legacy] if legacy else []
        return bool(WRITE_ROLES.intersection(roles))

    def proxy(subpath: str):
        upstream = resolve_upstream(subpath)
        if upstream is None:
            return respond(
                404, {"error": f"Unknown AI route: {subpath}", "code": "NOT_FOUND"}
            )
        if enforce_roles and is_write(request.method, subpath) and not has_write_role():
            return respond(
                403,
                {
                    "error": "Insufficient role for this AI operation",
                    "code": "FORBIDDEN",
                },
            )
        body = (
            request.get_json(silent=True)
            if request.method in ("POST", "PUT", "PATCH")
            else None
        )
        if request.method in ("POST", "PUT", "PATCH") and request.data and body is None:
            return respond(
                400,
                {
                    "error": "Request body must be valid JSON",
                    "code": "VALIDATION_ERROR",
                },
            )
        if (
            subpath == "signals/generate"
            and isinstance(body, dict)
            and "symbol" in body
            and "symbols" not in body
        ):
            body = {**body, "symbols": [body["symbol"]]}
        timeout = (
            LONG_TIMEOUT
            if LONG_PATTERN.match(subpath.strip("/")) and not (body or {}).get("async")
            else READ_TIMEOUT
        )
        status, payload = get_client().call(
            request.method,
            upstream,
            params=request.args.to_dict(flat=True) or None,
            body=body,
            timeout=timeout,
            request_id=request.headers.get("X-Request-ID"),
        )
        return respond(status, payload)

    if auth_decorator is None:
        view = proxy
    else:
        authed = auth_decorator(proxy)

        def view(subpath: str):
            if subpath.strip("/") == "health":
                return proxy(subpath)
            return authed(subpath)

        view.__name__ = "ai_gateway_proxy"

    bp.add_url_rule(
        "/<path:subpath>",
        endpoint="proxy",
        view_func=view,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    )
    return bp
