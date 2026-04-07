import enum
import os
import uuid
from datetime import datetime, timezone
from typing import Any, List

import structlog
from cryptography.fernet import Fernet
from sqlalchemy import JSON, Boolean, CheckConstraint, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates

logger = structlog.get_logger(__name__)
Base = declarative_base()
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)


class UserRole(enum.Enum):
    """User roles with hierarchical permissions"""

    ADMIN = "admin"
    TRADER = "trader"
    ANALYST = "analyst"
    VIEWER = "viewer"
    COMPLIANCE = "compliance"
    RISK_MANAGER = "risk_manager"


class OrderStatus(enum.Enum):
    """Order status enumeration"""

    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderType(enum.Enum):
    """Order type enumeration"""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(enum.Enum):
    """Order side enumeration"""

    BUY = "buy"
    SELL = "sell"


class AuditAction(enum.Enum):
    """Audit action types"""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    TRADE = "trade"
    RISK_BREACH = "risk_breach"
    ERROR = "error"


class BaseModel(Base):
    """Base model with common fields and audit functionality"""

    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    def to_dict(self, include_sensitive: Any = False) -> Any:
        """Convert model to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, enum.Enum):
                value = value.value
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[column.name] = value
        return result


class User(BaseModel):
    __tablename__ = "users"
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.VIEWER)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(32), nullable=True)
    mfa_verified = Column(Boolean, default=False, nullable=False)
    backup_codes = Column(JSON, nullable=True)
    last_password_change = Column(DateTime(timezone=True), nullable=True)
    terms_accepted_at = Column(DateTime(timezone=True), nullable=True)
    privacy_policy_accepted_at = Column(DateTime(timezone=True), nullable=True)
    sessions = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs = relationship(
        "AuditLog", foreign_keys="AuditLog.user_id", back_populates="user"
    )
    portfolios = relationship("Portfolio", back_populates="user")
    orders = relationship("Order", back_populates="user")
    __table_args__ = (
        CheckConstraint(
            "email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name="valid_email",
        ),
        Index("idx_user_email_active", "email", "is_active"),
    )

    @validates("email")
    def validate_email(self, key: Any, email: Any) -> str:
        """Validate email format"""
        import re

        if not re.match("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$", email):
            raise ValueError("Invalid email format")
        return email.lower()

    @property
    def roles(self) -> List[str]:
        """Return user roles as a list for JWT claims compatibility"""
        if self.role is None:
            return []
        return [self.role.value if isinstance(self.role, UserRole) else str(self.role)]

    def get_permissions(self) -> List[str]:
        """Get user permissions based on role"""
        role_permissions = {
            UserRole.ADMIN: [
                "user.create",
                "user.read",
                "user.update",
                "user.delete",
                "portfolio.create",
                "portfolio.read",
                "portfolio.update",
                "portfolio.delete",
                "order.create",
                "order.read",
                "order.update",
                "order.cancel",
                "strategy.create",
                "strategy.read",
                "strategy.update",
                "strategy.delete",
                "risk.read",
                "risk.update",
                "compliance.read",
                "audit.read",
            ],
            UserRole.TRADER: [
                "portfolio.read",
                "portfolio.update",
                "order.create",
                "order.read",
                "order.update",
                "order.cancel",
                "strategy.read",
                "strategy.update",
                "risk.read",
            ],
            UserRole.ANALYST: [
                "portfolio.read",
                "strategy.read",
                "strategy.create",
                "strategy.update",
                "risk.read",
                "market_data.read",
            ],
            UserRole.VIEWER: ["portfolio.read", "strategy.read", "market_data.read"],
            UserRole.COMPLIANCE: [
                "audit.read",
                "compliance.read",
                "user.read",
                "order.read",
                "portfolio.read",
                "risk.read",
            ],
            UserRole.RISK_MANAGER: [
                "risk.read",
                "risk.update",
                "portfolio.read",
                "order.read",
                "strategy.read",
                "compliance.read",
            ],
        }
        return role_permissions.get(self.role, [])

    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return cipher_suite.encrypt(data.encode()).decode()

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return cipher_suite.decrypt(encrypted_data.encode()).decode()


class UserSession(BaseModel):
    """User session tracking for security"""

    __tablename__ = "user_sessions"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_activity = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    user = relationship("User", back_populates="sessions")
    __table_args__ = (
        Index("idx_session_user_active", "user_id", "is_active"),
        Index("idx_session_expires", "expires_at"),
    )


class AuditLog(BaseModel):
    """Comprehensive audit logging for compliance"""

    __tablename__ = "audit_logs"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(255), nullable=True)
    action = Column(SQLEnum(AuditAction), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    extra_metadata = Column(JSONB, nullable=True)
    risk_score = Column(Float, nullable=True)
    compliance_flags = Column(JSON, nullable=True)
    hash_value = Column(String(64), nullable=False)
    user = relationship("User", foreign_keys=[user_id], back_populates="audit_logs")
    __table_args__ = (
        Index("idx_audit_user_action", "user_id", "action"),
        Index("idx_audit_timestamp", "created_at"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
    )


class Portfolio(BaseModel):
    __tablename__ = "portfolios"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    total_value = Column(Float, nullable=False, default=0.0)
    cash_balance = Column(Float, nullable=False, default=0.0)
    invested_amount = Column(Float, nullable=False, default=0.0)
    unrealized_pnl = Column(Float, nullable=False, default=0.0)
    realized_pnl = Column(Float, nullable=False, default=0.0)
    var_1d = Column(Float, nullable=True)
    var_5d = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    max_position_size = Column(Float, nullable=True)
    max_sector_exposure = Column(Float, nullable=True)
    max_leverage = Column(Float, nullable=True, default=1.0)
    is_active = Column(Boolean, default=True, nullable=False)
    user = relationship("User", back_populates="portfolios")
    positions = relationship(
        "Position", back_populates="portfolio", cascade="all, delete-orphan"
    )
    orders = relationship("Order", back_populates="portfolio")
    __table_args__ = (
        CheckConstraint("total_value >= 0", name="positive_total_value"),
        CheckConstraint("cash_balance >= 0", name="positive_cash_balance"),
        Index("idx_portfolio_user", "user_id"),
    )


class Position(BaseModel):
    """Portfolio position with real-time tracking"""

    __tablename__ = "positions"
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)
    avg_cost = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    market_value = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, nullable=True)
    realized_pnl = Column(Float, nullable=False, default=0.0)
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    country = Column(String(50), nullable=True)
    currency = Column(String(3), nullable=False, default="USD")
    position_var = Column(Float, nullable=True)
    position_beta = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    portfolio = relationship("Portfolio", back_populates="positions")
    __table_args__ = (
        UniqueConstraint("portfolio_id", "symbol", name="unique_portfolio_position"),
        CheckConstraint("quantity != 0", name="non_zero_quantity"),
        Index("idx_position_portfolio_symbol", "portfolio_id", "symbol"),
    )


class Order(BaseModel):
    __tablename__ = "orders"
    order_id = Column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    side = Column(SQLEnum(OrderSide), nullable=False)
    order_type = Column(SQLEnum(OrderType), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    filled_quantity = Column(Float, nullable=False, default=0.0)
    avg_fill_price = Column(Float, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    filled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    broker_order_id = Column(String(255), nullable=True)
    broker_name = Column(String(100), nullable=True)
    pre_trade_risk_check = Column(Boolean, default=False, nullable=False)
    compliance_approved = Column(Boolean, default=False, nullable=False)
    risk_score = Column(Float, nullable=True)
    compliance_notes = Column(Text, nullable=True)
    commission = Column(Float, nullable=True)
    fees = Column(Float, nullable=True)
    execution_venue = Column(String(100), nullable=True)
    user = relationship("User", back_populates="orders")
    portfolio = relationship("Portfolio", back_populates="orders")
    executions = relationship(
        "OrderExecution", back_populates="order", cascade="all, delete-orphan"
    )
    __table_args__ = (
        CheckConstraint("quantity > 0", name="positive_quantity"),
        CheckConstraint("filled_quantity >= 0", name="non_negative_filled"),
        CheckConstraint(
            "filled_quantity <= quantity", name="filled_not_exceed_quantity"
        ),
        Index("idx_order_user_status", "user_id", "status"),
        Index("idx_order_symbol_status", "symbol", "status"),
        Index("idx_order_submitted", "submitted_at"),
    )


class OrderExecution(BaseModel):
    """Order execution details for audit trail"""

    __tablename__ = "order_executions"
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    execution_id = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    executed_at = Column(DateTime(timezone=True), nullable=False)
    venue = Column(String(100), nullable=True)
    venue_order_id = Column(String(255), nullable=True)
    commission = Column(Float, nullable=True)
    fees = Column(Float, nullable=True)
    order = relationship("Order", back_populates="executions")
    __table_args__ = (
        CheckConstraint("quantity > 0", name="positive_execution_quantity"),
        CheckConstraint("price > 0", name="positive_execution_price"),
        Index("idx_execution_order", "order_id"),
        Index("idx_execution_time", "executed_at"),
    )


class Execution(Base):
    """Execution model for tracking order executions (simplified for execution service)"""

    __tablename__ = "executions"
    id = Column(String(255), primary_key=True)
    order_id = Column(String(255), nullable=False, index=True)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    broker_execution_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        result = {}
        for col in self.__table__.columns:
            value = getattr(self, col.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[col.name] = value
        return result


class Strategy(BaseModel):
    """Trading strategy configuration and tracking"""

    __tablename__ = "strategies"
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    strategy_type = Column(String(100), nullable=False)
    parameters = Column(JSONB, nullable=True)
    risk_parameters = Column(JSONB, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    is_paper_trading = Column(Boolean, default=True, nullable=False)
    total_return = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    var_limit = Column(Float, nullable=True)
    max_position_size = Column(Float, nullable=True)
    max_leverage = Column(Float, nullable=True)
    __table_args__ = (
        Index("idx_strategy_active", "is_active"),
        Index("idx_strategy_type", "strategy_type"),
    )


class RiskLimit(BaseModel):
    """Risk limits and controls"""

    __tablename__ = "risk_limits"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)
    symbol = Column(String(20), nullable=True)
    sector = Column(String(100), nullable=True)
    limit_type = Column(String(50), nullable=False)
    limit_value = Column(Float, nullable=False)
    warning_threshold = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    breach_count = Column(Integer, default=0, nullable=False)
    last_breach_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        CheckConstraint("limit_value > 0", name="positive_limit_value"),
        Index("idx_risk_limit_scope", "user_id", "portfolio_id", "symbol"),
    )


class ComplianceRule(BaseModel):
    """Compliance rules and monitoring"""

    __tablename__ = "compliance_rules"
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(String(100), nullable=False)
    conditions = Column(JSONB, nullable=False)
    actions = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    severity = Column(String(20), nullable=False, default="medium")
    violation_count = Column(Integer, default=0, nullable=False)
    last_violation_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        Index("idx_compliance_rule_type", "rule_type"),
        Index("idx_compliance_active", "is_active"),
    )


class MarketData(BaseModel):
    """Market data storage with time-series optimization"""

    __tablename__ = "market_data"
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    bid_price = Column(Float, nullable=True)
    ask_price = Column(Float, nullable=True)
    bid_size = Column(Float, nullable=True)
    ask_size = Column(Float, nullable=True)
    source = Column(String(100), nullable=False)
    data_quality = Column(Float, nullable=True)
    __table_args__ = (
        UniqueConstraint(
            "symbol", "timestamp", "source", name="unique_market_data_point"
        ),
        Index("idx_market_data_symbol_time", "symbol", "timestamp"),
        Index("idx_market_data_timestamp", "timestamp"),
    )


def create_tables(engine: Any) -> Any:
    """Create all database tables"""
    Base.metadata.create_all(engine)
    logger.info("Database tables created successfully")


def init_database(engine: Any) -> Any:
    """Initialize database with default data"""
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        admin_user = (
            session.query(User).filter(User.email == "admin@quantumalpha.com").first()
        )
        if not admin_user:
            from .auth import AuthManager

            auth_manager = AuthManager()
            admin_user = User(
                email="admin@quantumalpha.com",
                password_hash=auth_manager.hash_password("QuantumAlpha2024!"),
                name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
            )
            session.add(admin_user)
            session.commit()
            logger.info("Default admin user created")
        default_rules = [
            {
                "name": "Maximum Position Size",
                "description": "Limit individual position size to 10% of portfolio",
                "rule_type": "trading",
                "conditions": {"position_weight": {"max": 0.1}},
                "actions": {"block_order": True, "alert": True},
            },
            {
                "name": "Daily Trading Limit",
                "description": "Limit daily trading volume",
                "rule_type": "trading",
                "conditions": {"daily_volume": {"max": 1000000}},
                "actions": {"block_order": True, "alert": True},
            },
        ]
        for rule_data in default_rules:
            existing_rule = (
                session.query(ComplianceRule)
                .filter(ComplianceRule.name == rule_data["name"])
                .first()
            )
            if not existing_rule:
                rule = ComplianceRule(**rule_data)
                session.add(rule)
        session.commit()
        logger.info("Default compliance rules created")
    except Exception as e:
        session.rollback()
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        session.close()
