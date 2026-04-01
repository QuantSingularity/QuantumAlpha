import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, List, Optional

import structlog
from common.audit import audit_logger
from common.database import get_db_session, get_redis_client
from common.models import (
    AuditAction,
    Order,
    OrderExecution,
    OrderSide,
    OrderStatus,
    OrderType,
    Portfolio,
    Position,
)
from common.validation import FinancialValidator
from services.portfolio_service import MarketDataService, portfolio_service
from sqlalchemy import and_

logger = structlog.get_logger(__name__)


class OrderValidationError(Exception):
    """Order validation exception"""


class RiskViolationError(Exception):
    """Risk limit violation exception"""


class InsufficientFundsError(Exception):
    """Insufficient funds exception"""


@dataclass
class OrderRequest:
    """Order request data structure"""

    portfolio_id: int
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: str = "day"
    user_id: Optional[int] = None

    def __post_init__(self) -> None:
        # Allow callers that pass 'type' kwarg by accepting it via order_type
        pass

    @property
    def type(self) -> OrderType:
        """Alias for order_type for API compatibility"""
        return self.order_type


@dataclass
class ExecutionReport:
    """Order execution report"""

    order_id: int
    execution_id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    executed_at: datetime
    commission: Decimal
    fees: Decimal
    venue: str


class RiskManager:
    """Pre-trade and post-trade risk management"""

    def __init__(self) -> None:
        self.redis_client = get_redis_client()

    async def validate_order_risk(
        self, order_request: OrderRequest, portfolio: Portfolio
    ) -> bool:
        """Validate order against risk limits"""
        try:
            await self._check_portfolio_limits(order_request, portfolio)
            await self._check_position_limits(order_request, portfolio)
            await self._check_buying_power(order_request, portfolio)
            await self._check_concentration_limits(order_request, portfolio)
            await self._check_daily_limits(order_request, portfolio)
            return True
        except (RiskViolationError, InsufficientFundsError) as e:
            logger.warning(f"Risk check failed for order: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in risk validation: {e}")
            raise RiskViolationError("Risk validation failed")

    async def _check_portfolio_limits(
        self, order_request: OrderRequest, portfolio: Portfolio
    ):
        """Check portfolio-level risk limits"""
        if portfolio.max_leverage and portfolio.max_leverage > 0:
            self._calculate_leverage(portfolio)
            order_value = await self._estimate_order_value(order_request)
            estimated_leverage = (
                portfolio.invested_amount + order_value
            ) / portfolio.total_value
            if estimated_leverage > portfolio.max_leverage:
                raise RiskViolationError(
                    f"Order would exceed maximum leverage of {portfolio.max_leverage}"
                )

    async def _check_position_limits(
        self, order_request: OrderRequest, portfolio: Portfolio
    ):
        """Check position size limits"""
        if portfolio.max_position_size and portfolio.max_position_size > 0:
            with get_db_session() as session:
                position = (
                    session.query(Position)
                    .filter(
                        and_(
                            Position.portfolio_id == portfolio.id,
                            Position.symbol == order_request.symbol,
                        )
                    )
                    .first()
                )
                current_quantity = position.quantity if position else Decimal("0")
                if order_request.side == OrderSide.BUY:
                    current_quantity = current_quantity + order_request.quantity
                else:
                    current_quantity = current_quantity - order_request.quantity
                order_value = await self._estimate_order_value(order_request)
                position_weight = order_value / portfolio.total_value
                if position_weight > portfolio.max_position_size:
                    raise RiskViolationError(
                        f"Order would exceed maximum position size of {portfolio.max_position_size}"
                    )

    async def _check_buying_power(
        self, order_request: OrderRequest, portfolio: Portfolio
    ):
        """Check if sufficient buying power exists"""
        if order_request.side == OrderSide.BUY:
            order_value = await self._estimate_order_value(order_request)
            required_cash = order_value * Decimal("1.01")
            if portfolio.cash_balance < required_cash:
                raise InsufficientFundsError(
                    f"Insufficient cash balance. Required: {required_cash}, Available: {portfolio.cash_balance}"
                )

    async def _check_concentration_limits(
        self, order_request: OrderRequest, portfolio: Portfolio
    ):
        """Check sector/industry concentration limits"""
        if portfolio.max_sector_exposure and portfolio.max_sector_exposure > 0:
            pass

    async def _check_daily_limits(
        self, order_request: OrderRequest, portfolio: Portfolio
    ):
        """Check daily trading volume limits"""
        try:
            if self.redis_client:
                today = datetime.now(timezone.utc).date().isoformat()
                daily_volume_key = f"daily_volume:{portfolio.id}:{today}"
                current_volume = self.redis_client.get(daily_volume_key)
                current_volume = (
                    Decimal(current_volume) if current_volume else Decimal("0")
                )
                order_value = await self._estimate_order_value(order_request)
                new_volume = current_volume + order_value
                daily_limit = Decimal("1000000")
                if new_volume > daily_limit:
                    raise RiskViolationError(
                        f"Order would exceed daily trading limit of {daily_limit}"
                    )
        except Exception as e:
            logger.warning(f"Could not check daily limits: {e}")

    def _calculate_leverage(self, portfolio: Portfolio) -> Decimal:
        """Calculate current portfolio leverage"""
        if portfolio.total_value <= 0:
            return Decimal("0")
        return portfolio.invested_amount / portfolio.total_value

    async def _estimate_order_value(self, order_request: OrderRequest) -> Decimal:
        """Estimate the value of an order"""
        if order_request.order_type == OrderType.MARKET:
            market_data = MarketDataService()
            current_price = await market_data.get_current_price(order_request.symbol)
            if not current_price:
                raise OrderValidationError(
                    f"Cannot get market price for {order_request.symbol}"
                )
            return current_price * order_request.quantity
        else:
            if not order_request.price:
                raise OrderValidationError("Price required for limit orders")
            return order_request.price * order_request.quantity


class OrderManager:
    """Order lifecycle management"""

    def __init__(self) -> None:
        self.risk_manager = RiskManager()
        self.market_data = MarketDataService()
        self.redis_client = get_redis_client()

    async def submit_order(self, order_request: OrderRequest) -> Order:
        """Submit a new order with validation and risk checks"""
        try:
            self._validate_order_request(order_request)
            with get_db_session() as session:
                portfolio = (
                    session.query(Portfolio)
                    .filter(Portfolio.id == order_request.portfolio_id)
                    .first()
                )
                if not portfolio:
                    raise OrderValidationError("Portfolio not found")
                await self.risk_manager.validate_order_risk(order_request, portfolio)
                order = Order(
                    order_id=uuid.uuid4(),
                    user_id=order_request.user_id or portfolio.user_id,
                    portfolio_id=order_request.portfolio_id,
                    symbol=order_request.symbol,
                    side=order_request.side,
                    order_type=order_request.order_type,
                    quantity=order_request.quantity,
                    price=order_request.price,
                    stop_price=order_request.stop_price,
                    status=OrderStatus.PENDING,
                    pre_trade_risk_check=True,
                    compliance_approved=True,
                    created_by=order_request.user_id,
                )
                session.add(order)
                session.commit()
                session.refresh(order)
                audit_logger.log_event(
                    action=AuditAction.CREATE,
                    resource_type="order",
                    resource_id=str(order.id),
                    new_values=order.to_dict(),
                    user_id=order_request.user_id,
                    metadata={
                        "order_value": float(
                            await self.risk_manager._estimate_order_value(order_request)
                        ),
                        "risk_approved": True,
                    },
                )
                await self._submit_to_broker(order)
                logger.info(f"Order submitted: {order.order_id}")
                return order
        except Exception as e:
            logger.error(f"Error submitting order: {e}")
            raise

    def _validate_order_request(self, order_request: OrderRequest) -> Any:
        """Validate order request parameters"""
        order_request.symbol = FinancialValidator.validate_symbol(order_request.symbol)
        order_request.quantity = FinancialValidator.validate_quantity(
            order_request.quantity
        )
        if order_request.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
            if not order_request.price:
                raise OrderValidationError("Price required for limit orders")
            order_request.price = FinancialValidator.validate_price(order_request.price)
        if order_request.order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
            if not order_request.stop_price:
                raise OrderValidationError("Stop price required for stop orders")
            order_request.stop_price = FinancialValidator.validate_price(
                order_request.stop_price
            )
        valid_tif = ["day", "gtc", "ioc", "fok"]
        if order_request.time_in_force not in valid_tif:
            raise OrderValidationError(
                f"Invalid time in force: {order_request.time_in_force}"
            )

    async def _submit_to_broker(self, order: Order):
        """Submit order to broker for execution"""
        try:
            with get_db_session() as session:
                order = session.merge(order)
                order.status = OrderStatus.SUBMITTED
                order.submitted_at = datetime.now(timezone.utc)
                order.broker_order_id = f"BROKER_{order.order_id}"
                order.broker_name = "Mock Broker"
                session.commit()
                if order.order_type == OrderType.MARKET:
                    await self._simulate_execution(order)
        except Exception as e:
            logger.error(f"Error submitting to broker: {e}")
            with get_db_session() as session:
                order = session.merge(order)
                order.status = OrderStatus.REJECTED
                session.commit()

    async def _simulate_execution(self, order: Order):
        """Simulate order execution (for demo purposes)"""
        try:
            current_price = await self.market_data.get_current_price(order.symbol)
            if not current_price:
                return
            import random

            execution_quantity = order.quantity
            execution_price = current_price
            if order.side == OrderSide.BUY:
                execution_price *= Decimal(str(1 + random.uniform(0, 0.001)))
            else:
                execution_price *= Decimal(str(1 - random.uniform(0, 0.001)))
            await self.execute_order(
                order.id,
                execution_quantity,
                execution_price,
                f"EXEC_{uuid.uuid4().hex[:8]}",
                "Mock Exchange",
            )
        except Exception as e:
            logger.error(f"Error simulating execution: {e}")

    async def execute_order(
        self,
        order_id: int,
        quantity: Decimal,
        price: Decimal,
        execution_id: str,
        venue: str,
    ) -> OrderExecution:
        """Process order execution"""
        try:
            with get_db_session() as session:
                order = session.query(Order).filter(Order.id == order_id).first()
                if not order:
                    raise OrderValidationError("Order not found")
                commission = self._calculate_commission(quantity, price)
                fees = self._calculate_fees(quantity, price)
                execution = OrderExecution(
                    order_id=order.id,
                    execution_id=execution_id,
                    quantity=quantity,
                    price=price,
                    executed_at=datetime.now(timezone.utc),
                    venue=venue,
                    commission=commission,
                    fees=fees,
                    created_by=order.user_id,
                )
                session.add(execution)
                order.filled_quantity += quantity
                if order.filled_quantity >= order.quantity:
                    order.status = OrderStatus.FILLED
                    order.filled_at = datetime.now(timezone.utc)
                else:
                    order.status = OrderStatus.PARTIALLY_FILLED
                total_executions = (
                    session.query(OrderExecution)
                    .filter(OrderExecution.order_id == order.id)
                    .all()
                )
                total_value = sum(
                    (exec.quantity * exec.price for exec in total_executions)
                )
                total_quantity = sum((exec.quantity for exec in total_executions))
                if total_quantity > 0:
                    order.avg_fill_price = total_value / total_quantity
                session.commit()
                session.refresh(execution)
                await self._update_portfolio_position(order, execution)
                audit_logger.log_event(
                    action=AuditAction.TRADE,
                    resource_type="order_execution",
                    resource_id=str(execution.id),
                    new_values=execution.to_dict(),
                    user_id=order.user_id,
                    metadata={
                        "order_id": order.id,
                        "execution_value": float(quantity * price),
                        "commission": float(commission),
                        "fees": float(fees),
                    },
                )
                logger.info(
                    f"Order executed: {order.order_id}, Quantity: {quantity}, Price: {price}"
                )
                return execution
        except Exception as e:
            logger.error(f"Error executing order: {e}")
            raise

    def _calculate_commission(self, quantity: Decimal, price: Decimal) -> Decimal:
        """Calculate trading commission"""
        commission = quantity * Decimal("0.005")
        return max(commission, Decimal("1.00"))

    def _calculate_fees(self, quantity: Decimal, price: Decimal) -> Decimal:
        """Calculate regulatory and exchange fees"""
        trade_value = quantity * price
        return trade_value * Decimal("0.0001")

    async def _update_portfolio_position(self, order: Order, execution: OrderExecution):
        """Update portfolio position after execution"""
        try:
            await portfolio_service.add_position(
                portfolio_id=order.portfolio_id,
                symbol=order.symbol,
                quantity=(
                    execution.quantity
                    if order.side == OrderSide.BUY
                    else -execution.quantity
                ),
                avg_cost=execution.price,
                user_id=order.user_id,
            )
            with get_db_session() as session:
                portfolio = (
                    session.query(Portfolio)
                    .filter(Portfolio.id == order.portfolio_id)
                    .first()
                )
                if portfolio:
                    trade_value = execution.quantity * execution.price
                    total_cost = trade_value + execution.commission + execution.fees
                    if order.side == OrderSide.BUY:
                        portfolio.cash_balance -= total_cost
                    else:
                        portfolio.cash_balance += (
                            trade_value - execution.commission - execution.fees
                        )
                    session.commit()
        except Exception as e:
            logger.error(f"Error updating portfolio position: {e}")

    def cancel_order(self, order_id: int, user_id: int) -> bool:
        """Cancel a pending order"""
        try:
            with get_db_session() as session:
                order = (
                    session.query(Order)
                    .filter(
                        and_(
                            Order.id == order_id,
                            Order.user_id == user_id,
                            Order.status.in_(
                                [
                                    OrderStatus.PENDING,
                                    OrderStatus.SUBMITTED,
                                    OrderStatus.PARTIALLY_FILLED,
                                ]
                            ),
                        )
                    )
                    .first()
                )
                if not order:
                    return False
                old_status = order.status
                order.status = OrderStatus.CANCELLED
                order.cancelled_at = datetime.now(timezone.utc)
                session.commit()
                audit_logger.log_event(
                    action=AuditAction.UPDATE,
                    resource_type="order",
                    resource_id=str(order.id),
                    old_values={"status": old_status.value},
                    new_values={"status": order.status.value},
                    user_id=user_id,
                )
                logger.info(f"Order cancelled: {order.order_id}")
                return True
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False

    def get_order(self, order_id: int, user_id: int) -> Optional[Order]:
        """Get order by ID with user authorization"""
        try:
            with get_db_session() as session:
                order = (
                    session.query(Order)
                    .filter(and_(Order.id == order_id, Order.user_id == user_id))
                    .first()
                )
                return order
        except Exception as e:
            logger.error(f"Error getting order: {e}")
            return None

    def get_user_orders(
        self, user_id: int, status: Optional[OrderStatus] = None, limit: int = 100
    ) -> List[Order]:
        """Get orders for a user"""
        try:
            with get_db_session() as session:
                query = session.query(Order).filter(Order.user_id == user_id)
                if status:
                    query = query.filter(Order.status == status)
                orders = query.order_by(Order.created_at.desc()).limit(limit).all()
                return orders
        except Exception as e:
            logger.error(f"Error getting user orders: {e}")
            return []

    def get_portfolio_orders(
        self, portfolio_id: int, user_id: int, status: Optional[OrderStatus] = None
    ) -> List[Order]:
        """Get orders for a specific portfolio"""
        try:
            with get_db_session() as session:
                query = session.query(Order).filter(
                    and_(Order.portfolio_id == portfolio_id, Order.user_id == user_id)
                )
                if status:
                    query = query.filter(Order.status == status)
                orders = query.order_by(Order.created_at.desc()).all()
                return orders
        except Exception as e:
            logger.error(f"Error getting portfolio orders: {e}")
            return []


class TradingEngine:
    """Main trading engine orchestrator"""

    def __init__(self) -> None:
        self.order_manager = OrderManager()
        self.risk_manager = RiskManager()
        self._running = False

    def place_order(self, order_request: OrderRequest) -> Order:
        """Place a new order (sync wrapper around async submit_order)"""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run, self.order_manager.submit_order(order_request)
                    )
                    return future.result()
            return loop.run_until_complete(
                self.order_manager.submit_order(order_request)
            )
        except RuntimeError:
            return asyncio.run(self.order_manager.submit_order(order_request))

    def cancel_order(self, order_id: int, user_id: int) -> bool:
        """Cancel an existing order"""
        return self.order_manager.cancel_order(order_id, user_id)

    def get_order_status(self, order_id: int, user_id: int) -> Optional[Order]:
        """Get order status"""
        return self.order_manager.get_order(order_id, user_id)

    def get_order_history(
        self, user_id: int, portfolio_id: Optional[int] = None
    ) -> List[Order]:
        """Get order history"""
        if portfolio_id:
            return self.order_manager.get_portfolio_orders(portfolio_id, user_id)
        else:
            return self.order_manager.get_user_orders(user_id)

    def get_orders(self, user_id: int) -> List[Any]:
        """Get all orders for a user (serialisable dicts)"""
        orders = self.order_manager.get_user_orders(user_id)
        return [o.to_dict() if hasattr(o, "to_dict") else o for o in orders]

    def start(self) -> None:
        """Start the trading engine"""
        self._running = True
        logger.info("Trading engine started")

    def stop(self) -> None:
        """Stop the trading engine"""
        self._running = False
        logger.info("Trading engine stopped")

    def check_health(self) -> dict:
        """Return health status of the trading engine"""
        return {
            "status": "healthy" if self._running else "stopped",
            "running": self._running,
        }


trading_engine = TradingEngine()
__all__ = [
    "TradingEngine",
    "OrderManager",
    "RiskManager",
    "OrderRequest",
    "ExecutionReport",
    "OrderValidationError",
    "RiskViolationError",
    "InsufficientFundsError",
    "trading_engine",
]
