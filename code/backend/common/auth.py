import os
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import bcrypt
import pyotp
import redis
import structlog
from flask import jsonify, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from .audit import log_security_event
from .database import get_db_session
from .models import User, UserSession

logger = structlog.get_logger(__name__)


def _get_blocklist_client():
    try:
        from .database import db_manager

        client = db_manager.get_redis_client()
        if client is not None:
            return client
    except Exception:
        pass

    try:
        client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_AUTH_DB", 1)),
            decode_responses=True,
            socket_connect_timeout=2,
        )
        client.ping()
        return client
    except Exception:
        pass

    try:
        import fakeredis

        return fakeredis.FakeRedis(decode_responses=True)
    except Exception:
        return None


class _RedisProxy:

    def __getattr__(self, name):
        client = _get_blocklist_client()
        if client is None:
            raise AuthenticationError("Auth state store unavailable")
        return getattr(client, name)


redis_client = _RedisProxy()


class AuthenticationError(Exception):
    pass


class AuthorizationError(Exception):
    pass


class SecurityConfig:

    MIN_PASSWORD_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 30
    MAX_CONCURRENT_SESSIONS = 3
    SESSION_TIMEOUT = 8
    ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    MFA_TOKEN_VALIDITY = 300
    BACKUP_CODES_COUNT = 10


class AuthManager:

    def __init__(self, app: Optional[Any] = None) -> None:
        self.app = app
        self.jwt = JWTManager()
        if app:
            self.init_app(app)

    def init_app(self, app: "Flask") -> None:
        self.app = app
        self.jwt.init_app(app)
        app.config["JWT_SECRET_KEY"] = os.getenv(
            "JWT_SECRET_KEY", secrets.token_urlsafe(32)
        )
        app.config["JWT_ACCESS_TOKEN_EXPIRES"] = SecurityConfig.ACCESS_TOKEN_EXPIRES
        app.config["JWT_REFRESH_TOKEN_EXPIRES"] = SecurityConfig.REFRESH_TOKEN_EXPIRES
        app.config["JWT_ALGORITHM"] = "HS256"
        app.config["JWT_BLACKLIST_ENABLED"] = True
        app.config["JWT_BLACKLIST_TOKEN_CHECKS"] = ["access", "refresh"]
        self._register_jwt_callbacks()

    def _register_jwt_callbacks(self) -> None:

        @self.jwt.token_in_blocklist_loader
        def check_if_token_revoked(jwt_header, jwt_payload):
            jti = jwt_payload.get("jti")
            if not jti:
                return False
            try:
                client = _get_blocklist_client()
                if client is None:
                    return False
                return client.get(f"blacklist:{jti}") is not None
            except Exception as exc:
                logger.warning(
                    "Token blocklist check unavailable; failing open",
                    error=str(exc),
                )
                return False

        @self.jwt.expired_token_loader
        def expired_token_callback(jwt_header, jwt_payload):
            log_security_event(
                "token_expired",
                {"user_id": jwt_payload.get("sub"), "jti": jwt_payload.get("jti")},
            )
            return (jsonify({"error": "Token has expired"}), 401)

        @self.jwt.invalid_token_loader
        def invalid_token_callback(error):
            log_security_event("invalid_token", {"error": str(error)})
            return (jsonify({"error": "Invalid token"}), 401)

        @self.jwt.unauthorized_loader
        def missing_token_callback(error):
            return (jsonify({"error": "Authorization token required"}), 401)

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def create_access_token(
        self, identity: str, roles: Optional[List[str]] = None
    ) -> str:
        additional_claims: Dict[str, Any] = {}
        if roles is not None:
            additional_claims["roles"] = roles if isinstance(roles, list) else [roles]
        return create_access_token(
            identity=str(identity), additional_claims=additional_claims
        )

    def create_refresh_token(self, identity: str) -> str:
        return create_refresh_token(identity=str(identity))

    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    def generate_mfa_secret(self) -> str:
        return pyotp.random_base32()

    def verify_mfa_token(self, secret: str, token: str) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)

    def generate_backup_codes(self) -> List[str]:
        return [
            secrets.token_hex(4).upper()
            for _ in range(SecurityConfig.BACKUP_CODES_COUNT)
        ]

    def check_account_lockout(self, user_id: int) -> bool:
        key = f"lockout:{user_id}"
        lockout_data = redis_client.get(key)
        if lockout_data:
            return True
        return False

    def record_failed_attempt(self, user_id: int) -> None:
        key = f"attempts:{user_id}"
        attempts = redis_client.incr(key)
        redis_client.expire(key, SecurityConfig.LOCKOUT_DURATION * 60)
        if attempts >= SecurityConfig.MAX_LOGIN_ATTEMPTS:
            lockout_key = f"lockout:{user_id}"
            redis_client.setex(
                lockout_key, SecurityConfig.LOCKOUT_DURATION * 60, "locked"
            )
            log_security_event(
                "account_locked",
                {
                    "user_id": user_id,
                    "attempts": attempts,
                    "lockout_duration": SecurityConfig.LOCKOUT_DURATION,
                },
            )

    def clear_failed_attempts(self, user_id: int) -> None:
        redis_client.delete(f"attempts:{user_id}")

    def create_session(
        self, user: User, ip_address: str, user_agent: str
    ) -> Dict[str, Any]:
        self._enforce_session_limit(user.id)
        additional_claims = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "permissions": user.get_permissions(),
            "mfa_verified": user.mfa_enabled and user.mfa_verified,
            "session_id": secrets.token_urlsafe(16),
        }
        access_token = create_access_token(
            identity=str(user.id), additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(identity=str(user.id))
        session = UserSession(
            user_id=user.id,
            session_id=additional_claims["session_id"],
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=SecurityConfig.SESSION_TIMEOUT),
            is_active=True,
        )
        with get_db_session() as db_session:
            db_session.add(session)
            db_session.commit()
        log_security_event(
            "login_success",
            {
                "user_id": user.id,
                "email": user.email,
                "ip_address": ip_address,
                "session_id": additional_claims["session_id"],
            },
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": int(SecurityConfig.ACCESS_TOKEN_EXPIRES.total_seconds()),
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "mfa_enabled": user.mfa_enabled,
                "last_login": user.last_login.isoformat() if user.last_login else None,
            },
        }

    def _enforce_session_limit(self, user_id: int) -> None:
        with get_db_session() as db_session:
            active_sessions = (
                db_session.query(UserSession)
                .filter(
                    UserSession.user_id == user_id,
                    UserSession.is_active,
                    UserSession.expires_at > datetime.now(timezone.utc),
                )
                .order_by(UserSession.created_at.desc())
                .all()
            )
            if len(active_sessions) >= SecurityConfig.MAX_CONCURRENT_SESSIONS:
                sessions_to_deactivate = active_sessions[
                    SecurityConfig.MAX_CONCURRENT_SESSIONS - 1 :
                ]
                for session in sessions_to_deactivate:
                    session.is_active = False
                    self._blacklist_session_tokens(session.session_id)
                db_session.commit()

    def _blacklist_session_tokens(self, session_id: str) -> None:
        try:
            redis_client.setex(
                f"blacklist:session:{session_id}",
                int(SecurityConfig.SESSION_TIMEOUT * 3600),
                "blacklisted",
            )
            logger.info(f"Blacklisted tokens for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to blacklist session tokens: {e}")

    def logout(self, token_jti: str, user_id: int) -> None:
        redis_client.setex(
            f"blacklist:{token_jti}",
            int(SecurityConfig.ACCESS_TOKEN_EXPIRES.total_seconds()),
            "blacklisted",
        )
        with get_db_session() as db_session:
            session = (
                db_session.query(UserSession)
                .filter(UserSession.user_id == user_id, UserSession.is_active)
                .first()
            )
            if session:
                session.is_active = False
                db_session.commit()
        log_security_event("logout", {"user_id": user_id, "token_jti": token_jti})

    def authenticate_user(
        self, email: str, password: str, mfa_token: Optional[str] = None
    ) -> Optional[User]:
        with get_db_session() as db_session:
            user = db_session.query(User).filter(User.email == email).first()
            if not user:
                log_security_event(
                    "login_failed", {"email": email, "reason": "user_not_found"}
                )
                return None
            if self.check_account_lockout(user.id):
                log_security_event(
                    "login_blocked",
                    {"user_id": user.id, "email": email, "reason": "account_locked"},
                )
                raise AuthenticationError("Account is temporarily locked")
            if not self.verify_password(password, user.password_hash):
                self.record_failed_attempt(user.id)
                log_security_event(
                    "login_failed",
                    {"user_id": user.id, "email": email, "reason": "invalid_password"},
                )
                return None
            if user.mfa_enabled:
                if not mfa_token:
                    log_security_event(
                        "mfa_required", {"user_id": user.id, "email": email}
                    )
                    raise AuthenticationError("MFA token required")
                if not self.verify_mfa_token(user.mfa_secret, mfa_token):
                    self.record_failed_attempt(user.id)
                    log_security_event(
                        "mfa_failed", {"user_id": user.id, "email": email}
                    )
                    return None
                user.mfa_verified = True
            self.clear_failed_attempts(user.id)
            user.last_login = datetime.now(timezone.utc)
            db_session.commit()
            return user


def require_auth(f: Callable[..., Any]) -> Callable[..., Any]:

    @wraps(f)
    @jwt_required()
    def decorated_function(*args: object, **kwargs: object) -> object:
        return f(*args, **kwargs)

    return decorated_function


def require_role(
    required_role: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:

        @wraps(f)
        @jwt_required()
        def decorated_function(*args: object, **kwargs: object) -> object:
            claims = get_jwt()
            user_roles = claims.get("roles")
            if user_roles is None:
                legacy = claims.get("role")
                user_roles = [legacy] if legacy else []
            if required_role not in user_roles:
                log_security_event(
                    "authorization_failed",
                    {
                        "user_id": get_jwt_identity(),
                        "required_role": required_role,
                        "user_roles": user_roles,
                    },
                )
                raise AuthorizationError(f"Role '{required_role}' required")
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_permission(
    permission: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:

        @wraps(f)
        @jwt_required()
        def decorated_function(*args: object, **kwargs: object) -> object:
            claims = get_jwt()
            user_permissions = claims.get("permissions", [])
            if permission not in user_permissions:
                log_security_event(
                    "authorization_failed",
                    {
                        "user_id": get_jwt_identity(),
                        "required_permission": permission,
                        "user_permissions": user_permissions,
                    },
                )
                raise AuthorizationError(f"Permission '{permission}' required")
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_mfa(f: Callable[..., Any]) -> Callable[..., Any]:

    @wraps(f)
    @jwt_required()
    def decorated_function(*args: object, **kwargs: object) -> object:
        claims = get_jwt()
        mfa_verified = claims.get("mfa_verified", False)
        if not mfa_verified:
            log_security_event(
                "mfa_required",
                {"user_id": get_jwt_identity(), "endpoint": request.endpoint},
            )
            return (jsonify({"error": "MFA verification required"}), 403)
        return f(*args, **kwargs)

    return decorated_function


auth_manager = AuthManager()
