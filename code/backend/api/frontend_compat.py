from backend.common.auth import require_auth
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity

compat_bp = Blueprint("frontend_compat", __name__)


def _not_implemented(feature: str, detail: str):
    return (
        jsonify(
            {
                "error": "Not implemented",
                "message": detail,
                "code": "NOT_IMPLEMENTED",
                "feature": feature,
            }
        ),
        501,
    )


@compat_bp.route("/api/auth/user", methods=["GET"])
@require_auth
def auth_user_alias():
    from backend.common.database import get_db_session
    from backend.common.models import User

    user_id = int(get_jwt_identity())
    with get_db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return (
                jsonify({"error": "User not found", "code": "USER_NOT_FOUND"}),
                404,
            )
        return jsonify(
            {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "roles": user.roles,
            }
        )


@compat_bp.route("/api/auth/refresh", methods=["POST"])
def auth_refresh():
    from flask_jwt_extended import decode_token

    data = request.get_json(silent=True) or {}
    refresh_token = data.get("refreshToken") or data.get("refresh_token")
    if not refresh_token:
        return (
            jsonify(
                {
                    "error": "Missing refresh token",
                    "code": "MISSING_REFRESH_TOKEN",
                }
            ),
            400,
        )
    try:
        decoded = decode_token(refresh_token)
        if decoded.get("type") != "refresh":
            raise ValueError("not a refresh token")
        user_id = decoded["sub"]
    except Exception:
        return (
            jsonify(
                {
                    "error": "Invalid refresh token",
                    "code": "INVALID_REFRESH_TOKEN",
                }
            ),
            401,
        )
    access_token = create_access_token(identity=str(user_id))
    return jsonify({"token": access_token, "token_type": "Bearer"}), 200


@compat_bp.route("/api/trades", methods=["GET"])
@require_auth
def trades_alias():
    from backend.trading_engine.trading_engine import trading_engine

    user_id = int(get_jwt_identity())
    orders = trading_engine.get_orders(user_id)
    return jsonify(orders), 200


@compat_bp.route("/api/strategies", methods=["GET", "POST"])
@compat_bp.route("/api/strategies/<strategy_id>", methods=["GET", "PATCH", "DELETE"])
@require_auth
def strategies_stub(strategy_id=None):
    return _not_implemented(
        "strategies",
        "Strategy management endpoints are not yet implemented on the backend.",
    )


@compat_bp.route("/api/portfolio/history", methods=["GET"])
@require_auth
def portfolio_history_stub():
    return _not_implemented(
        "portfolio_history",
        "Portfolio history is not yet implemented on the backend.",
    )


@compat_bp.route("/api/market-data/<symbol>", methods=["GET"])
@require_auth
def market_data_stub(symbol):
    return _not_implemented(
        "market_data",
        "Market data is served by the data-service; this gateway route is not "
        "yet wired to it.",
    )


@compat_bp.route("/api/risk/metrics/<strategy_id>", methods=["GET"])
@require_auth
def risk_metrics_stub(strategy_id):
    return _not_implemented(
        "risk_metrics",
        "Risk metrics are served by the risk-service; this gateway route is not "
        "yet wired to it.",
    )
