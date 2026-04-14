"""
Comprehensive Audit Logging System for QuantumAlpha
Implements immutable audit trails for financial compliance and security monitoring
"""

import hashlib
import json
import threading
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, List, Optional

import structlog
from flask import g, request
from flask_jwt_extended import get_jwt, get_jwt_identity

from .database import get_db_session
from .models import AuditAction, AuditLog, User

logger = structlog.get_logger(__name__)


class AuditLogger:
    """Centralized audit logging system"""

    def __init__(self) -> None:
        self._local = threading.local()
        self.risk_calculator = RiskCalculator()

    def log_event(
        self,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
    ) -> AuditLog:
        """
        Log an audit event with comprehensive details

        Args:
            action: Type of action performed
            resource_type: Type of resource affected
            resource_id: ID of the specific resource
            old_values: Previous values (for updates)
            new_values: New values (for creates/updates)
            metadata: Additional context information
            user_id: ID of user performing action
            session_id: Session identifier
            ip_address: Client IP address
            user_agent: Client user agent
            endpoint: API endpoint accessed
            method: HTTP method used

        Returns:
            Created AuditLog instance
        """
        try:
            if not user_id and hasattr(g, "current_user_id"):
                user_id = g.current_user_id
            elif not user_id:
                try:
                    user_id = get_jwt_identity()
                except Exception:
                    pass
            if not session_id:
                try:
                    claims = get_jwt()
                    session_id = claims.get("session_id")
                except Exception:
                    pass
            if not ip_address and request:
                ip_address = self._get_client_ip()
            if not user_agent and request:
                user_agent = request.headers.get("User-Agent")
            if not endpoint and request:
                endpoint = request.endpoint
            if not method and request:
                method = request.method
            risk_score = self.risk_calculator.calculate_risk_score(
                action, resource_type, user_id, metadata
            )
            compliance_flags = self._check_compliance_flags(
                action, resource_type, old_values, new_values, metadata
            )
            audit_log = AuditLog(
                user_id=user_id,
                session_id=session_id,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                ip_address=ip_address,
                user_agent=user_agent,
                endpoint=endpoint,
                method=method,
                old_values=old_values,
                new_values=new_values,
                extra_metadata=metadata or {},
                risk_score=risk_score,
                compliance_flags=compliance_flags,
            )
            audit_log.hash_value = self._generate_hash(audit_log)
            with get_db_session() as db_session:
                db_session.add(audit_log)
                db_session.commit()
            self._log_to_external_systems(audit_log)
            if risk_score and risk_score > 0.8:
                self._handle_high_risk_event(audit_log)
            return audit_log
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}", exc_info=True)
            return None

    def _get_client_ip(self) -> str:
        """Get client IP address from request"""
        if request.headers.get("X-Forwarded-For"):
            return request.headers.get("X-Forwarded-For").split(",")[0].strip()
        elif request.headers.get("X-Real-IP"):
            return request.headers.get("X-Real-IP")
        else:
            return request.remote_addr

    def _generate_hash(self, audit_log: AuditLog) -> str:
        """Generate SHA-256 hash for audit log integrity"""
        hash_data = {
            "user_id": audit_log.user_id,
            "action": audit_log.action.value if audit_log.action else None,
            "resource_type": audit_log.resource_type,
            "resource_id": audit_log.resource_id,
            "timestamp": (
                audit_log.created_at.isoformat() if audit_log.created_at else None
            ),
            "old_values": audit_log.old_values,
            "new_values": audit_log.new_values,
            "metadata": audit_log.extra_metadata,
        }
        hash_string = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def _check_compliance_flags(
        self,
        action: AuditAction,
        resource_type: str,
        old_values: Optional[Dict],
        new_values: Optional[Dict],
        metadata: Optional[Dict],
    ) -> List[str]:
        """Check for compliance violations or flags"""
        flags = []
        if resource_type == "order" and new_values:
            order_value = new_values.get("quantity", 0) * new_values.get("price", 0)
            if order_value > 100000:
                flags.append("high_value_transaction")
        now = datetime.now(timezone.utc)
        if now.hour < 9 or now.hour > 16:
            if resource_type == "order" and action == AuditAction.CREATE:
                flags.append("after_hours_trading")
        if metadata and metadata.get("rapid_trading_detected"):
            flags.append("rapid_trading")
        if resource_type == "user" and old_values and new_values:
            old_role = old_values.get("role")
            new_role = new_values.get("role")
            if old_role != new_role:
                flags.append("privilege_change")
        if resource_type == "position" and new_values:
            position_value = new_values.get("market_value", 0)
            if position_value > 500000:
                flags.append("large_position")
        return flags

    def _log_to_external_systems(self, audit_log: AuditLog) -> None:
        """Send audit log to external monitoring systems"""
        try:
            log_data = {
                "timestamp": audit_log.created_at.isoformat(),
                "user_id": audit_log.user_id,
                "action": audit_log.action.value if audit_log.action else None,
                "resource_type": audit_log.resource_type,
                "resource_id": audit_log.resource_id,
                "ip_address": audit_log.ip_address,
                "risk_score": audit_log.risk_score,
                "compliance_flags": audit_log.compliance_flags,
                "hash": audit_log.hash_value,
            }
            logger.info("audit_event", **log_data)
        except Exception as e:
            logger.error(f"Failed to log to external systems: {e}")

    def _handle_high_risk_event(self, audit_log: AuditLog) -> None:
        """Handle high-risk audit events"""
        try:
            logger.warning(
                "high_risk_audit_event",
                user_id=audit_log.user_id,
                action=audit_log.action.value if audit_log.action else None,
                resource_type=audit_log.resource_type,
                risk_score=audit_log.risk_score,
                compliance_flags=audit_log.compliance_flags,
            )
            if audit_log.risk_score > 0.95:
                pass
        except Exception as e:
            logger.error(f"Failed to handle high-risk event: {e}")


class RiskCalculator:
    """Calculate risk scores for audit events"""

    def calculate_risk_score(
        self,
        action: AuditAction,
        resource_type: str,
        user_id: Optional[int],
        metadata: Optional[Dict],
    ) -> float:
        """
        Calculate risk score (0.0 - 1.0) for an audit event

        Returns:
            Risk score between 0.0 (low risk) and 1.0 (high risk)
        """
        try:
            base_score = self._get_base_risk_score(action, resource_type)
            user_multiplier = self._get_user_risk_multiplier(user_id)
            metadata_multiplier = self._get_metadata_risk_multiplier(metadata)
            timing_multiplier = self._get_timing_risk_multiplier()
            final_score = min(
                1.0,
                base_score * user_multiplier * metadata_multiplier * timing_multiplier,
            )
            return round(final_score, 3)
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 0.5

    def _get_base_risk_score(self, action: AuditAction, resource_type: str) -> float:
        """Get base risk score for action/resource combination"""
        risk_matrix = {
            (AuditAction.DELETE, "user"): 0.9,
            (AuditAction.UPDATE, "user"): 0.7,
            (AuditAction.CREATE, "order"): 0.6,
            (AuditAction.UPDATE, "order"): 0.8,
            (AuditAction.DELETE, "order"): 0.7,
            (AuditAction.CREATE, "portfolio"): 0.5,
            (AuditAction.UPDATE, "portfolio"): 0.6,
            (AuditAction.DELETE, "portfolio"): 0.8,
            (AuditAction.READ, "user"): 0.3,
            (AuditAction.READ, "order"): 0.2,
            (AuditAction.READ, "portfolio"): 0.2,
            (AuditAction.LOGIN, "session"): 0.3,
            (AuditAction.LOGOUT, "session"): 0.1,
            (AuditAction.RISK_BREACH, "portfolio"): 0.9,
            (AuditAction.TRADE, "order"): 0.5,
        }
        return risk_matrix.get((action, resource_type), 0.3)

    def _get_user_risk_multiplier(self, user_id: Optional[int]) -> float:
        """Get risk multiplier based on user characteristics"""
        if not user_id:
            return 1.2
        try:
            with get_db_session() as db_session:
                user = db_session.query(User).filter(User.id == user_id).first()
                if not user:
                    return 1.2
                multiplier = 1.0
                if (
                    user.created_at
                    and (datetime.now(timezone.utc) - user.created_at).days < 30
                ):
                    multiplier *= 1.3
                if user.failed_login_attempts > 0:
                    multiplier *= 1.2
                if user.role.value == "admin":
                    multiplier *= 1.1
                return min(2.0, multiplier)
        except Exception as e:
            logger.error(f"Error calculating user risk multiplier: {e}")
            return 1.0

    def _get_metadata_risk_multiplier(self, metadata: Optional[Dict]) -> float:
        """Get risk multiplier based on metadata"""
        if not metadata:
            return 1.0
        multiplier = 1.0
        if "amount" in metadata:
            amount = metadata["amount"]
            if amount > 1000000:
                multiplier *= 1.5
            elif amount > 100000:
                multiplier *= 1.2
        if "unusual_ip" in metadata and metadata["unusual_ip"]:
            multiplier *= 1.3
        if "validation_failures" in metadata:
            failures = metadata["validation_failures"]
            if failures > 3:
                multiplier *= 1.4
        return min(2.0, multiplier)

    def _get_timing_risk_multiplier(self) -> float:
        """Get risk multiplier based on timing"""
        now = datetime.now(timezone.utc)
        if now.weekday() >= 5:
            return 1.2
        if now.hour < 9 or now.hour > 16:
            return 1.1
        return 1.0


def audit_action(action: AuditAction, resource_type: str) -> Any:
    """Decorator to automatically audit function calls"""

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            old_values = None
            if action == AuditAction.UPDATE and "id" in kwargs:
                try:
                    old_values = _get_resource_values(resource_type, kwargs["id"])
                except Exception:
                    pass
            result = func(*args, **kwargs)
            new_values = None
            if action in [AuditAction.CREATE, AuditAction.UPDATE]:
                try:
                    new_values = _extract_values_from_result(result)
                except Exception:
                    pass
            resource_id = _extract_resource_id(result, kwargs)
            audit_logger.log_event(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=old_values,
                new_values=new_values,
                metadata={"function": func.__name__},
            )
            return result

        return wrapper

    return decorator


def _get_resource_values(resource_type: str, resource_id: str) -> Optional[Dict]:
    """Get current values of a resource before modification"""
    return None


def _extract_values_from_result(result: Any) -> Optional[Dict]:
    """Extract values from function result"""
    if hasattr(result, "to_dict"):
        return result.to_dict()
    elif isinstance(result, dict):
        return result
    return None


def _extract_resource_id(result: Any, kwargs: Any) -> Optional[str]:
    """Extract resource ID from result or kwargs"""
    if hasattr(result, "id"):
        return str(result.id)
    elif "id" in kwargs:
        return str(kwargs["id"])
    return None


def log_security_event(event_type: str, details: Dict[str, Any]) -> None:
    """Log security-related events"""
    audit_logger.log_event(
        action=AuditAction.READ,
        resource_type="security",
        metadata={"event_type": event_type, "details": details, "security_event": True},
    )


def log_compliance_event(event_type: str, details: Dict[str, Any]) -> None:
    """Log compliance-related events"""
    audit_logger.log_event(
        action=AuditAction.READ,
        resource_type="compliance",
        metadata={
            "event_type": event_type,
            "details": details,
            "compliance_event": True,
        },
    )


audit_logger = AuditLogger()
__all__ = [
    "AuditLogger",
    "audit_logger",
    "audit_action",
    "log_security_event",
    "log_compliance_event",
]
