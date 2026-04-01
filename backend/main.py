import asyncio
import logging
import os
import signal
from datetime import datetime, timezone
from decimal import Decimal
from typing import Callable, List, Optional

from common.audit import audit_logger, log_security_event
from common.auth import auth_manager, require_auth, require_role
from common.database import cleanup_database, db_manager, initialize_database
from common.logging_config import setup_logging
from common.models import AuditAction
from common.monitoring import (
    create_monitoring_blueprint,
    create_request_monitoring_middleware,
    get_monitoring_service,
)
from common.validation import (
    OrderSchema,
    UserLoginSchema,
    UserRegistrationSchema,
    ValidationError,
    validate_json,
)
from config import Config
from flask import Flask, g, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt_identity, verify_jwt_in_request
from services.portfolio_service import portfolio_service
from services.trading_engine import OrderRequest, OrderSide, OrderType, trading_engine

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuantumAlphaApp:

    def __init__(self) -> None:
        self.app: Optional[Flask] = None
        self.jwt: Optional[JWTManager] = None
        self.shutdown_handlers: List[Callable[[], None]] = []

    def create_app(self) -> Flask:
        """Create and configure Flask application"""
        app = Flask(__name__)
        self._load_config(app)
        self._init_extensions(app)
        self._register_error_handlers(app)
        self._register_request_handlers(app)
        self._register_blueprints(app)
        self._register_routes(app)
        self.app = app
        return app

    def _load_config(self, app: Flask) -> None:
        """Load application configuration"""
        app.config.from_object(Config)
        logger.info("Application configuration loaded")

    def _init_extensions(self, app: Flask) -> None:
        """Initialize Flask extensions"""
        CORS(app, origins=app.config["CORS_ORIGINS"])
        self.jwt = JWTManager(app)
        auth_manager.init_app(app)
        logger.info("Flask extensions initialized")

    def _register_error_handlers(self, app: Flask) -> None:
        """Register global error handlers"""

        @app.errorhandler(ValidationError)
        def handle_validation_error(error):
            """Handle validation errors"""
            logger.warning("Validation error: %s", error)
            return (
                jsonify(
                    {
                        "error": "Validation failed",
                        "message": str(error),
                        "code": "VALIDATION_ERROR",
                    }
                ),
                400,
            )

        @app.errorhandler(PermissionError)
        def handle_permission_error(error):
            """Handle permission errors"""
            logger.warning("Permission error: %s", error)
            log_security_event(
                "permission_denied",
                {
                    "user_id": (
                        get_jwt_identity()
                        if request.headers.get("Authorization")
                        else None
                    ),
                    "endpoint": request.endpoint,
                    "error": str(error),
                },
            )
            return (
                jsonify(
                    {
                        "error": "Permission denied",
                        "message": "Insufficient permissions for this operation",
                        "code": "PERMISSION_DENIED",
                    }
                ),
                403,
            )

        @app.errorhandler(404)
        def handle_not_found(error):
            """Handle 404 errors"""
            return (
                jsonify(
                    {
                        "error": "Not found",
                        "message": "The requested resource was not found",
                        "code": "NOT_FOUND",
                    }
                ),
                404,
            )

        @app.errorhandler(500)
        def handle_internal_error(error):
            """Handle internal server errors"""
            error_id = f"error_{int(datetime.now(timezone.utc).timestamp())}"
            logger.error(
                "Internal server error [%s]: %s", error_id, error, exc_info=True
            )
            audit_logger.log_event(
                action=AuditAction.ERROR,
                resource_type="system",
                metadata={
                    "error_id": error_id,
                    "error_type": "internal_server_error",
                    "endpoint": request.endpoint,
                    "method": request.method,
                },
            )
            return (
                jsonify(
                    {
                        "error": "Internal server error",
                        "message": "An unexpected error occurred",
                        "code": "INTERNAL_ERROR",
                        "error_id": error_id,
                    }
                ),
                500,
            )

        @app.errorhandler(Exception)
        def handle_unexpected_error(error):
            """Handle unexpected errors"""
            error_id = f"error_{int(datetime.now(timezone.utc).timestamp())}"
            logger.error("Unexpected error [%s]: %s", error_id, error, exc_info=True)
            return (
                jsonify(
                    {
                        "error": "Unexpected error",
                        "message": "An unexpected error occurred",
                        "code": "UNEXPECTED_ERROR",
                        "error_id": error_id,
                    }
                ),
                500,
            )

    def _register_request_handlers(self, app: Flask) -> None:
        """Register request handlers for monitoring and security"""
        before_request, after_request = create_request_monitoring_middleware()

        @app.before_request
        def before_request_handler():
            """Before request handler"""
            before_request()
            try:
                if request.headers.get("Authorization"):
                    verify_jwt_in_request(optional=True)
                    user_id = get_jwt_identity()
                    if user_id:
                        g.current_user_id = user_id
            except Exception:
                pass

        @app.after_request
        def after_request_handler(response):
            """After request handler"""
            return after_request(response)

    def _register_blueprints(self, app: Flask) -> None:
        """Register Flask blueprints"""
        monitoring_bp = create_monitoring_blueprint()
        app.register_blueprint(monitoring_bp)
        logger.info("Blueprints registered")

    def _register_routes(self, app: Flask) -> None:
        """Register API routes"""

        @app.route("/health", methods=["GET"])
        def health_check():
            """Public health check endpoint"""
            return jsonify(
                {
                    "status": "ok",
                    "service": "quantumalpha-backend",
                    "version": "2.0.0",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

        @app.route("/api/auth/register", methods=["POST"])
        @validate_json(UserRegistrationSchema)
        def register(validated_data):
            """User registration endpoint"""
            try:
                from common.database import get_db_session
                from common.models import User

                with get_db_session() as session:
                    existing_user = (
                        session.query(User)
                        .filter(User.email == validated_data["email"])
                        .first()
                    )
                    if existing_user:
                        return (
                            jsonify(
                                {"error": "User already exists", "code": "USER_EXISTS"}
                            ),
                            409,
                        )
                    user = User(
                        email=validated_data["email"],
                        password_hash=auth_manager.hash_password(
                            validated_data["password"]
                        ),
                        name=validated_data["name"],
                        is_verified=False,
                        terms_accepted_at=datetime.now(timezone.utc),
                    )
                    session.add(user)
                    session.commit()
                    session.refresh(user)
                    audit_logger.log_event(
                        action=AuditAction.CREATE,
                        resource_type="user",
                        resource_id=str(user.id),
                        new_values={"email": user.email, "name": user.name},
                        user_id=user.id,
                    )
                    return (
                        jsonify(
                            {
                                "message": "User registered successfully",
                                "user_id": user.id,
                            }
                        ),
                        201,
                    )
            except Exception as e:
                logger.error("Error during registration: %s", e, exc_info=True)
                return (
                    jsonify(
                        {
                            "error": "Registration failed",
                            "message": str(e),
                            "code": "REGISTRATION_FAILED",
                        }
                    ),
                    500,
                )

        @app.route("/api/auth/login", methods=["POST"])
        @validate_json(UserLoginSchema)
        def login(validated_data):
            """User login endpoint"""
            try:
                from common.database import get_db_session
                from common.models import User

                with get_db_session() as session:
                    user = (
                        session.query(User)
                        .filter(User.email == validated_data["email"])
                        .first()
                    )
                    if user and auth_manager.verify_password(
                        validated_data["password"], user.password_hash
                    ):
                        access_token = auth_manager.create_access_token(
                            identity=user.id, roles=user.roles
                        )
                        audit_logger.log_event(
                            action=AuditAction.LOGIN,
                            resource_type="user",
                            resource_id=str(user.id),
                            user_id=user.id,
                        )
                        return (
                            jsonify(
                                {
                                    "message": "Login successful",
                                    "access_token": access_token,
                                    "user_id": user.id,
                                }
                            ),
                            200,
                        )
                    else:
                        log_security_event(
                            "login_failed",
                            {
                                "email": validated_data["email"],
                                "ip_address": request.remote_addr,
                            },
                        )
                        return (
                            jsonify(
                                {
                                    "error": "Invalid credentials",
                                    "code": "INVALID_CREDENTIALS",
                                }
                            ),
                            401,
                        )
            except Exception as e:
                logger.error("Error during login: %s", e, exc_info=True)
                return (
                    jsonify(
                        {
                            "error": "Login failed",
                            "message": str(e),
                            "code": "LOGIN_FAILED",
                        }
                    ),
                    500,
                )

        @app.route("/api/auth/logout", methods=["POST"])
        @require_auth
        def logout():
            """User logout endpoint"""
            user_id = get_jwt_identity()
            audit_logger.log_event(
                action=AuditAction.LOGOUT,
                resource_type="user",
                resource_id=str(user_id),
                user_id=user_id,
            )
            return (jsonify({"message": "Logout successful"}), 200)

        @app.route("/api/auth/me", methods=["GET"])
        @require_auth
        def get_current_user():
            """Get current user details"""
            try:
                from common.database import get_db_session
                from common.models import User

                user_id = get_jwt_identity()
                with get_db_session() as session:
                    user = session.query(User).filter(User.id == user_id).first()
                    if user:
                        return (
                            jsonify(
                                {
                                    "id": user.id,
                                    "email": user.email,
                                    "name": user.name,
                                    "roles": user.roles,
                                }
                            ),
                            200,
                        )
                    else:
                        return (
                            jsonify(
                                {"error": "User not found", "code": "USER_NOT_FOUND"}
                            ),
                            404,
                        )
            except Exception as e:
                logger.error("Error getting current user: %s", e, exc_info=True)
                return (
                    jsonify(
                        {
                            "error": "Failed to get user details",
                            "message": str(e),
                            "code": "USER_DETAILS_FAILED",
                        }
                    ),
                    500,
                )

        @app.route("/api/portfolio", methods=["GET"])
        @require_auth
        def get_portfolio_summary():
            """Get user's portfolio summary"""
            try:
                user_id = get_jwt_identity()
                summary = portfolio_service.get_portfolio_summary(user_id)
                return (jsonify(summary), 200)
            except Exception as e:
                logger.error("Error getting portfolio summary: %s", e, exc_info=True)
                return (
                    jsonify(
                        {
                            "error": "Failed to get portfolio summary",
                            "message": str(e),
                            "code": "PORTFOLIO_SUMMARY_FAILED",
                        }
                    ),
                    500,
                )

        @app.route("/api/portfolio/positions", methods=["GET"])
        @require_auth
        def get_portfolio_positions():
            """Get user's portfolio positions"""
            try:
                user_id = get_jwt_identity()
                positions = portfolio_service.get_portfolio_positions(user_id)
                return (jsonify(positions), 200)
            except Exception as e:
                logger.error("Error getting portfolio positions: %s", e, exc_info=True)
                return (
                    jsonify(
                        {
                            "error": "Failed to get portfolio positions",
                            "message": str(e),
                            "code": "PORTFOLIO_POSITIONS_FAILED",
                        }
                    ),
                    500,
                )

        @app.route("/api/trade/order", methods=["POST"])
        @require_auth
        @validate_json(OrderSchema)
        def place_order(validated_data):
            """Place a new trade order"""
            try:
                user_id = get_jwt_identity()
                order_request = OrderRequest(
                    user_id=user_id,
                    portfolio_id=validated_data.get("portfolio_id", 0),
                    symbol=validated_data["symbol"],
                    side=OrderSide(validated_data["side"]),
                    order_type=OrderType(
                        validated_data.get(
                            "type", validated_data.get("order_type", "market")
                        )
                    ),
                    quantity=Decimal(str(validated_data["quantity"])),
                    price=(
                        Decimal(str(validated_data.get("price")))
                        if validated_data.get("price")
                        else None
                    ),
                )
                order_result = trading_engine.place_order(order_request)
                audit_logger.log_event(
                    action=AuditAction.CREATE,
                    resource_type="order",
                    resource_id=str(order_result.order_id),
                    new_values=validated_data,
                    user_id=user_id,
                )
                return (
                    jsonify(
                        {
                            "message": "Order placed successfully",
                            "order_id": order_result.order_id,
                            "status": order_result.status.value,
                        }
                    ),
                    201,
                )
            except ValueError as e:
                logger.warning("Invalid order request: %s", e)
                return (
                    jsonify(
                        {
                            "error": "Invalid order request",
                            "message": str(e),
                            "code": "INVALID_ORDER",
                        }
                    ),
                    400,
                )
            except Exception as e:
                logger.error("Error placing order: %s", e, exc_info=True)
                return (
                    jsonify(
                        {
                            "error": "Failed to place order",
                            "message": str(e),
                            "code": "ORDER_PLACEMENT_FAILED",
                        }
                    ),
                    500,
                )

        @app.route("/api/trade/orders", methods=["GET"])
        @require_auth
        def get_orders():
            """Get user's trade orders"""
            try:
                user_id = get_jwt_identity()
                orders = trading_engine.get_orders(user_id)
                return (jsonify(orders), 200)
            except Exception as e:
                logger.error("Error getting orders: %s", e, exc_info=True)
                return (
                    jsonify(
                        {
                            "error": "Failed to get orders",
                            "message": str(e),
                            "code": "GET_ORDERS_FAILED",
                        }
                    ),
                    500,
                )

        @app.route("/api/admin/users", methods=["GET"])
        @require_auth
        @require_role("admin")
        def get_all_users():
            """Get a list of all users (Admin only)"""
            try:
                from common.database import get_db_session
                from common.models import User

                with get_db_session() as session:
                    users = session.query(User).all()
                    user_list = [
                        {
                            "id": user.id,
                            "email": user.email,
                            "name": user.name,
                            "roles": user.roles,
                            "is_verified": user.is_verified,
                        }
                        for user in users
                    ]
                    return (jsonify(user_list), 200)
            except Exception as e:
                logger.error("Error getting all users: %s", e, exc_info=True)
                return (
                    jsonify(
                        {
                            "error": "Failed to get user list",
                            "message": str(e),
                            "code": "GET_USERS_FAILED",
                        }
                    ),
                    500,
                )

        @app.route("/api/system/shutdown", methods=["POST"])
        @require_auth
        @require_role("admin")
        def shutdown_system():
            """Initiate graceful system shutdown (Admin only)"""
            logger.info("System shutdown initiated by user %s", get_jwt_identity())

            def shutdown_handler():
                for handler in self.shutdown_handlers:
                    handler()
                os.kill(os.getpid(), signal.SIGINT)

            asyncio.get_event_loop().call_later(1, shutdown_handler)
            return (jsonify({"message": "System shutdown initiated"}), 200)

        @app.route("/api/system/status", methods=["GET"])
        @require_auth
        def get_system_status():
            """Get system status and health checks"""
            try:
                status = {
                    "database": db_manager.check_health(),
                    "trading_engine": trading_engine.check_health(),
                    "monitoring": get_monitoring_service().check_health(),
                    "version": app.config.get("VERSION", "unknown"),
                    "debug_mode": app.config.get("DEBUG", False),
                }
                return (jsonify(status), 200)
            except Exception as e:
                logger.error("Error getting system status: %s", e, exc_info=True)
                return (
                    jsonify(
                        {
                            "error": "Failed to get system status",
                            "message": str(e),
                            "code": "SYSTEM_STATUS_FAILED",
                        }
                    ),
                    500,
                )

    def run(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False) -> None:
        """Run the Flask application"""
        app = self.create_app()
        app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    app_instance = QuantumAlphaApp()
    with app_instance.create_app().app_context():
        initialize_database()
        app_instance.shutdown_handlers.append(cleanup_database)
        trading_engine.start()
        app_instance.shutdown_handlers.append(trading_engine.stop)
        port = int(os.environ.get("PORT", 5000))
        app_instance.run(port=port, debug=app_instance.app.config.get("DEBUG", False))
