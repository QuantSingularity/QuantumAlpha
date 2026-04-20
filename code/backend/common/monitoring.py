"""
Comprehensive Monitoring and Health Check System for QuantumAlpha
Implements real-time monitoring, alerting, and system health tracking
"""

import json
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Optional

import psutil
import structlog
from flask import jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

from .database import db_manager, get_db_session, get_redis_client
from .models import Order, Portfolio, User

logger = structlog.get_logger(__name__)


class HealthStatus(Enum):
    """Health status enumeration"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    """Health check result"""

    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    response_time_ms: float
    details: Optional[Dict[str, Any]] = None


@dataclass
class SystemMetrics:
    """System performance metrics"""

    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    active_connections: int
    request_rate: float
    error_rate: float
    response_time_avg: float


@dataclass
class Alert:
    """System alert"""

    id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    source: str
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class MetricsCollector:
    """Prometheus metrics collector"""

    def __init__(self) -> None:
        self.request_count = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
        )
        self.request_duration = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration",
            ["method", "endpoint"],
        )
        self.orders_total = Counter(
            "orders_total", "Total orders placed", ["status", "symbol"]
        )
        self.portfolio_value = Gauge(
            "portfolio_value_total", "Total portfolio value", ["portfolio_id"]
        )
        self.active_users = Gauge("active_users_total", "Number of active users")
        self.cpu_usage = Gauge("cpu_usage_percent", "CPU usage percentage")
        self.memory_usage = Gauge("memory_usage_percent", "Memory usage percentage")
        self.disk_usage = Gauge("disk_usage_percent", "Disk usage percentage")
        self.db_connections = Gauge(
            "database_connections_active", "Active database connections"
        )
        self.error_count = Counter(
            "errors_total", "Total errors", ["error_type", "severity"]
        )
        self.security_events = Counter(
            "security_events_total", "Security events", ["event_type"]
        )

    def record_request(
        self, method: str, endpoint: str, status: int, duration: float
    ) -> None:
        """Record HTTP request metrics"""
        self.request_count.labels(method=method, endpoint=endpoint, status=status).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)

    def record_order(self, status: str, symbol: str) -> None:
        """Record order metrics"""
        self.orders_total.labels(status=status, symbol=symbol).inc()

    def update_portfolio_value(self, portfolio_id: str, value: float) -> None:
        """Update portfolio value metric"""
        self.portfolio_value.labels(portfolio_id=portfolio_id).set(value)

    def update_system_metrics(self, metrics: SystemMetrics) -> None:
        """Update system performance metrics"""
        self.cpu_usage.set(metrics.cpu_usage)
        self.memory_usage.set(metrics.memory_usage)
        self.disk_usage.set(metrics.disk_usage)
        self.db_connections.set(metrics.active_connections)

    def record_error(self, error_type: str, severity: str) -> None:
        """Record error metrics"""
        self.error_count.labels(error_type=error_type, severity=severity).inc()

    def record_security_event(self, event_type: str) -> None:
        """Record security event metrics"""
        self.security_events.labels(event_type=event_type).inc()


class HealthChecker:
    """System health monitoring"""

    def __init__(self) -> None:
        self.checks = {}
        self.last_check_time = {}
        self.check_interval = 30

    def register_check(self, name: str, check_func: Callable[[], HealthCheck]) -> None:
        """Register a health check function"""
        self.checks[name] = check_func
        self.last_check_time[name] = None

    async def run_check(self, name: str) -> HealthCheck:
        """Run a specific health check"""
        if name not in self.checks:
            return HealthCheck(
                name=name,
                status=HealthStatus.UNKNOWN,
                message="Check not found",
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0,
            )
        start_time = time.time()
        try:
            result = self.checks[name]()
            response_time = (time.time() - start_time) * 1000
            result.response_time_ms = response_time
            result.timestamp = datetime.now(timezone.utc)
            self.last_check_time[name] = result.timestamp
            return result
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(e)}",
                timestamp=datetime.now(timezone.utc),
                response_time_ms=response_time,
            )

    async def run_all_checks(self) -> Dict[str, HealthCheck]:
        """Run all registered health checks"""
        results = {}
        for name in self.checks:
            results[name] = await self.run_check(name)
        return results

    def get_overall_status(self, check_results: Dict[str, HealthCheck]) -> HealthStatus:
        """Determine overall system health status"""
        if not check_results:
            return HealthStatus.UNKNOWN
        statuses = [check.status for check in check_results.values()]
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        elif all((status == HealthStatus.HEALTHY for status in statuses)):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN


class SystemMonitor:
    """System performance monitoring"""

    def __init__(self) -> None:
        self.metrics_collector = MetricsCollector()
        self.monitoring_active = False
        self.monitor_thread = None

    def start_monitoring(self) -> None:
        """Start system monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop, daemon=True
            )
            self.monitor_thread.start()
            logger.info("System monitoring started")

    def stop_monitoring(self) -> None:
        """Stop system monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("System monitoring stopped")

    def _monitor_loop(self) -> object:
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                metrics = self.collect_system_metrics()
                self.metrics_collector.update_system_metrics(metrics)
                self._check_system_alerts(metrics)
                time.sleep(10)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            disk = psutil.disk_usage("/")
            disk_usage = disk.percent
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
            }
            db_stats = db_manager.get_connection_stats()
            active_connections = db_stats.get("active_connections", 0)
            return SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                active_connections=active_connections,
                request_rate=0.0,
                error_rate=0.0,
                response_time_avg=0.0,
            )
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_io={},
                active_connections=0,
                request_rate=0.0,
                error_rate=0.0,
                response_time_avg=0.0,
            )

    def _check_system_alerts(self, metrics: SystemMetrics) -> object:
        """Check for system alert conditions"""
        alerts = []
        if metrics.cpu_usage > 90:
            alerts.append(
                Alert(
                    id=f"cpu_high_{int(time.time())}",
                    severity=AlertSeverity.CRITICAL,
                    title="High CPU Usage",
                    message=f"CPU usage is {metrics.cpu_usage:.1f}%",
                    timestamp=datetime.now(timezone.utc),
                    source="system_monitor",
                )
            )
        elif metrics.cpu_usage > 80:
            alerts.append(
                Alert(
                    id=f"cpu_warning_{int(time.time())}",
                    severity=AlertSeverity.WARNING,
                    title="Elevated CPU Usage",
                    message=f"CPU usage is {metrics.cpu_usage:.1f}%",
                    timestamp=datetime.now(timezone.utc),
                    source="system_monitor",
                )
            )
        if metrics.memory_usage > 90:
            alerts.append(
                Alert(
                    id=f"memory_high_{int(time.time())}",
                    severity=AlertSeverity.CRITICAL,
                    title="High Memory Usage",
                    message=f"Memory usage is {metrics.memory_usage:.1f}%",
                    timestamp=datetime.now(timezone.utc),
                    source="system_monitor",
                )
            )
        if metrics.disk_usage > 90:
            alerts.append(
                Alert(
                    id=f"disk_high_{int(time.time())}",
                    severity=AlertSeverity.CRITICAL,
                    title="High Disk Usage",
                    message=f"Disk usage is {metrics.disk_usage:.1f}%",
                    timestamp=datetime.now(timezone.utc),
                    source="system_monitor",
                )
            )
        for alert in alerts:
            self._send_alert(alert)

    def _send_alert(self, alert: Alert) -> object:
        """Send system alert"""
        try:
            logger.warning(
                "system_alert",
                alert_id=alert.id,
                severity=alert.severity.value,
                title=alert.title,
                message=alert.message,
                source=alert.source,
            )
            redis_client = get_redis_client()
            if redis_client:
                alert_data = asdict(alert)
                alert_data["timestamp"] = alert.timestamp.isoformat()
                redis_client.setex(
                    f"alert:{alert.id}", 3600, json.dumps(alert_data, default=str)
                )
        except Exception as e:
            logger.error(f"Error sending alert: {e}")


class HealthCheckRegistry:
    """Registry of health check functions"""

    @staticmethod
    def database_check() -> HealthCheck:
        """Check database connectivity"""
        try:
            health_status = db_manager.health_check()
            pg_status = health_status.get("postgresql", {})
            if pg_status.get("status") != "healthy":
                return HealthCheck(
                    name="database",
                    status=HealthStatus.UNHEALTHY,
                    message=f"PostgreSQL unhealthy: {pg_status.get('error', 'Unknown error')}",
                    timestamp=datetime.now(timezone.utc),
                    response_time_ms=0,
                    details=health_status,
                )
            return HealthCheck(
                name="database",
                status=HealthStatus.HEALTHY,
                message="All database connections healthy",
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0,
                details=health_status,
            )
        except Exception as e:
            return HealthCheck(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database check failed: {str(e)}",
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0,
            )

    @staticmethod
    def redis_check() -> HealthCheck:
        """Check Redis connectivity"""
        try:
            redis_client = get_redis_client()
            if not redis_client:
                return HealthCheck(
                    name="redis",
                    status=HealthStatus.UNKNOWN,
                    message="Redis not configured",
                    timestamp=datetime.now(timezone.utc),
                    response_time_ms=0,
                )
            start_time = time.time()
            redis_client.ping()
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis connection healthy",
                timestamp=datetime.now(timezone.utc),
                response_time_ms=response_time,
            )
        except Exception as e:
            return HealthCheck(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis check failed: {str(e)}",
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0,
            )

    @staticmethod
    def application_check() -> HealthCheck:
        """Check application health"""
        try:
            from .database import get_db_session

            with get_db_session() as session:
                user_count = session.query(User).count()
            return HealthCheck(
                name="application",
                status=HealthStatus.HEALTHY,
                message=f"Application healthy, {user_count} users in system",
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0,
                details={"user_count": user_count},
            )
        except Exception as e:
            return HealthCheck(
                name="application",
                status=HealthStatus.UNHEALTHY,
                message=f"Application check failed: {str(e)}",
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0,
            )


class MonitoringService:
    """Main monitoring service orchestrator"""

    def __init__(self) -> None:
        self.health_checker = HealthChecker()
        self.system_monitor = SystemMonitor()
        self.metrics_collector = MetricsCollector()
        self.health_checker.register_check(
            "database", HealthCheckRegistry.database_check
        )
        self.health_checker.register_check("redis", HealthCheckRegistry.redis_check)
        self.health_checker.register_check(
            "application", HealthCheckRegistry.application_check
        )

    def start(self) -> None:
        """Start monitoring services"""
        self.system_monitor.start_monitoring()
        logger.info("Monitoring service started")

    def stop(self) -> None:
        """Stop monitoring services"""
        self.system_monitor.stop_monitoring()
        logger.info("Monitoring service stopped")

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        check_results = await self.health_checker.run_all_checks()
        overall_status = self.health_checker.get_overall_status(check_results)
        return {
            "status": overall_status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {name: asdict(check) for name, check in check_results.items()},
            "system_metrics": asdict(self.system_monitor.collect_system_metrics()),
        }

    def check_health(self) -> Dict[str, Any]:
        """Synchronous health check returning basic status"""
        try:
            metrics = self.system_monitor.collect_system_metrics()
            return {
                "status": "healthy",
                "cpu_usage": metrics.cpu_usage,
                "memory_usage": metrics.memory_usage,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def get_metrics(self) -> str:
        """Get Prometheus metrics"""
        return generate_latest()


_monitoring_service = None


def get_monitoring_service():
    """Get or create monitoring service instance"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service


# For backward compatibility
monitoring_service = None


def create_monitoring_blueprint() -> None:
    """Create Flask blueprint for monitoring endpoints"""
    from flask import Blueprint

    monitoring_bp = Blueprint("monitoring", __name__, url_prefix="/monitoring")

    @monitoring_bp.route("/health", methods=["GET"])
    async def health_endpoint():
        """Health check endpoint"""
        try:
            health_status = await monitoring_service.get_health_status()
            status_code = 200 if health_status["status"] == "healthy" else 503
            return (jsonify(health_status), status_code)
        except Exception as e:
            logger.error(f"Health check endpoint error: {e}")
            return (
                jsonify(
                    {
                        "status": "unhealthy",
                        "error": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                503,
            )

    @monitoring_bp.route("/metrics", methods=["GET"])
    def metrics_endpoint():
        """Prometheus metrics endpoint"""
        try:
            metrics = monitoring_service.get_metrics()
            return (metrics, 200, {"Content-Type": CONTENT_TYPE_LATEST})
        except Exception as e:
            logger.error(f"Metrics endpoint error: {e}")
            return (f"# Error generating metrics: {str(e)}", 500)

    @monitoring_bp.route("/status", methods=["GET"])
    def status_endpoint():
        """Detailed status endpoint"""
        try:
            system_metrics = monitoring_service.system_monitor.collect_system_metrics()
            db_stats = db_manager.get_connection_stats()
            with get_db_session() as session:
                user_count = session.query(User).count()
                portfolio_count = session.query(Portfolio).count()
                order_count = session.query(Order).count()
            return jsonify(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "system": asdict(system_metrics),
                    "database": db_stats,
                    "application": {
                        "users": user_count,
                        "portfolios": portfolio_count,
                        "orders": order_count,
                    },
                }
            )
        except Exception as e:
            logger.error(f"Status endpoint error: {e}")
            return (jsonify({"error": str(e)}), 500)

    return monitoring_bp


def create_request_monitoring_middleware() -> None:
    """Create middleware for request monitoring"""

    def before_request():
        """Before request handler"""
        request.start_time = time.time()

    def after_request(response):
        """After request handler"""
        try:
            if hasattr(request, "start_time"):
                duration = time.time() - request.start_time
                monitoring_service.metrics_collector.record_request(
                    method=request.method,
                    endpoint=request.endpoint or "unknown",
                    status=response.status_code,
                    duration=duration,
                )
                if duration > 5.0:
                    logger.warning(
                        "slow_request",
                        method=request.method,
                        endpoint=request.endpoint,
                        duration=duration,
                        status=response.status_code,
                    )
        except Exception as e:
            logger.error(f"Error in request monitoring: {e}")
        return response

    return (before_request, after_request)


__all__ = [
    "MonitoringService",
    "HealthChecker",
    "SystemMonitor",
    "MetricsCollector",
    "HealthStatus",
    "AlertSeverity",
    "monitoring_service",
    "create_monitoring_blueprint",
    "create_request_monitoring_middleware",
]
