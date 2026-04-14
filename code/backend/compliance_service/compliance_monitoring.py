"""
Compliance monitoring module for QuantumAlpha Compliance Service.
Handles real-time compliance monitoring and violation detection.
"""

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from queue import Empty, Queue
from typing import Any, Callable, Dict, List, Optional

from backend.common import ServiceError, setup_logger

logger = setup_logger("compliance_monitoring", logging.INFO)


class ViolationType(Enum):
    """Types of compliance violations"""

    POSITION_LIMIT = "position_limit"
    CONCENTRATION_LIMIT = "concentration_limit"
    LEVERAGE_LIMIT = "leverage_limit"
    LIQUIDITY_REQUIREMENT = "liquidity_requirement"
    RISK_LIMIT = "risk_limit"
    TRADING_RESTRICTION = "trading_restriction"
    DISCLOSURE_REQUIREMENT = "disclosure_requirement"
    CAPITAL_REQUIREMENT = "capital_requirement"
    REPORTING_DEADLINE = "reporting_deadline"
    INVESTMENT_RESTRICTION = "investment_restriction"


class ViolationSeverity(Enum):
    """Severity levels for violations"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceStatus(Enum):
    """Compliance status"""

    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL_VIOLATION = "critical_violation"


@dataclass
class ComplianceRule:
    """Compliance rule definition"""

    rule_id: str
    name: str
    description: str
    rule_type: ViolationType
    severity: ViolationSeverity
    threshold: float
    operator: str
    measurement_field: str
    jurisdiction: str
    regulation: str
    enabled: bool = True
    grace_period_minutes: int = 0
    notification_required: bool = True


@dataclass
class ComplianceViolation:
    """Compliance violation record"""

    violation_id: str
    rule_id: str
    rule_name: str
    violation_type: ViolationType
    severity: ViolationSeverity
    current_value: float
    threshold_value: float
    description: str
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    status: str = "active"
    portfolio_id: Optional[str] = None
    position_id: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class ComplianceMonitor:
    """Real-time compliance monitoring system"""

    def __init__(self, config_manager: Any, db_manager: Any) -> None:
        """Initialize compliance monitor

        Args:
            config_manager: Configuration manager
            db_manager: Database manager
        """
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.rules = {}
        self.rule_groups = {}
        self.active_violations = {}
        self.violation_history = []
        self.monitoring_active = False
        self.monitoring_thread = None
        self.check_interval = 60
        self.event_queue = Queue(maxsize=10000)
        self.violation_callbacks = []
        self.metrics = {
            "rules_checked": 0,
            "violations_detected": 0,
            "false_positives": 0,
            "last_check": None,
            "check_duration_ms": 0,
        }
        self._initialize_default_rules()
        logger.info("Compliance monitor initialized")

    def start_monitoring(self) -> None:
        """Start real-time compliance monitoring"""
        try:
            if self.monitoring_active:
                logger.warning("Compliance monitoring is already active")
                return
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop, daemon=True
            )
            self.monitoring_thread.start()
            logger.info("Compliance monitoring started")
        except Exception as e:
            logger.error(f"Error starting compliance monitoring: {e}")
            raise ServiceError(f"Error starting compliance monitoring: {str(e)}")

    def stop_monitoring(self) -> None:
        """Stop real-time compliance monitoring"""
        try:
            self.monitoring_active = False
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            logger.info("Compliance monitoring stopped")
        except Exception as e:
            logger.error(f"Error stopping compliance monitoring: {e}")

    def add_rule(self, rule: ComplianceRule) -> None:
        """Add a compliance rule

        Args:
            rule: Compliance rule to add
        """
        self.rules[rule.rule_id] = rule
        logger.info(f"Added compliance rule: {rule.name}")

    def remove_rule(self, rule_id: str) -> None:
        """Remove a compliance rule

        Args:
            rule_id: Rule ID to remove
        """
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed compliance rule: {rule_id}")

    def enable_rule(self, rule_id: str) -> None:
        """Enable a compliance rule

        Args:
            rule_id: Rule ID to enable
        """
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            logger.info(f"Enabled compliance rule: {rule_id}")

    def disable_rule(self, rule_id: str) -> None:
        """Disable a compliance rule

        Args:
            rule_id: Rule ID to disable
        """
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            logger.info(f"Disabled compliance rule: {rule_id}")

    def check_compliance(
        self,
        portfolio_data: Dict[str, Any],
        position_data: Optional[List[Dict[str, Any]]] = None,
        market_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Check compliance against all rules

        Args:
            portfolio_data: Portfolio data to check
            position_data: Position data
            market_data: Market data for calculations

        Returns:
            Compliance check results
        """
        try:
            start_time = time.time()
            violations = []
            warnings = []
            compliant_rules = []
            for rule_id, rule in self.rules.items():
                if not rule.enabled:
                    continue
                try:
                    result = self._check_rule(
                        rule, portfolio_data, position_data, market_data
                    )
                    if result["status"] == "violation":
                        violation = self._create_violation(rule, result, portfolio_data)
                        violations.append(violation)
                        self._handle_violation(violation)
                    elif result["status"] == "warning":
                        warnings.append(
                            {
                                "rule_id": rule_id,
                                "rule_name": rule.name,
                                "current_value": result["current_value"],
                                "threshold": result["threshold"],
                                "message": result["message"],
                            }
                        )
                    else:
                        compliant_rules.append(rule_id)
                    self.metrics["rules_checked"] += 1
                except Exception as e:
                    logger.error(f"Error checking rule {rule_id}: {e}")
            if violations:
                critical_violations = [
                    v for v in violations if v.severity == ViolationSeverity.CRITICAL
                ]
                if critical_violations:
                    overall_status = ComplianceStatus.CRITICAL_VIOLATION
                else:
                    overall_status = ComplianceStatus.VIOLATION
            elif warnings:
                overall_status = ComplianceStatus.WARNING
            else:
                overall_status = ComplianceStatus.COMPLIANT
            check_duration = (time.time() - start_time) * 1000
            self.metrics["check_duration_ms"] = check_duration
            self.metrics["last_check"] = datetime.utcnow().isoformat()
            self.metrics["violations_detected"] += len(violations)
            return {
                "overall_status": overall_status.value,
                "violations": [self._violation_to_dict(v) for v in violations],
                "warnings": warnings,
                "compliant_rules": compliant_rules,
                "total_rules_checked": len(
                    [r for r in self.rules.values() if r.enabled]
                ),
                "check_duration_ms": check_duration,
                "checked_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error checking compliance: {e}")
            raise ServiceError(f"Error checking compliance: {str(e)}")

    def get_active_violations(self) -> List[Dict[str, Any]]:
        """Get all active violations

        Returns:
            List of active violations
        """
        return [self._violation_to_dict(v) for v in self.active_violations.values()]

    def resolve_violation(self, violation_id: str, resolution_note: str = "") -> None:
        """Resolve a compliance violation

        Args:
            violation_id: Violation ID to resolve
            resolution_note: Optional resolution note
        """
        if violation_id in self.active_violations:
            violation = self.active_violations[violation_id]
            violation.resolved_at = datetime.utcnow()
            violation.status = "resolved"
            violation.additional_data = violation.additional_data or {}
            violation.additional_data["resolution_note"] = resolution_note
            self.violation_history.append(violation)
            del self.active_violations[violation_id]
            logger.info(f"Resolved violation: {violation_id}")

    def add_violation_callback(
        self, callback: Callable[[ComplianceViolation], None]
    ) -> None:
        """Add a callback for violation events

        Args:
            callback: Callback function
        """
        self.violation_callbacks.append(callback)

    def get_compliance_metrics(self) -> Dict[str, Any]:
        """Get compliance monitoring metrics

        Returns:
            Compliance metrics
        """
        return {
            "metrics": self.metrics.copy(),
            "active_violations_count": len(self.active_violations),
            "total_rules": len(self.rules),
            "enabled_rules": len([r for r in self.rules.values() if r.enabled]),
            "monitoring_active": self.monitoring_active,
            "retrieved_at": datetime.utcnow().isoformat(),
        }

    def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._process_events()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)

    def _process_events(self) -> None:
        """Process events from the event queue"""
        try:
            while not self.event_queue.empty():
                try:
                    event = self.event_queue.get(timeout=1)
                    self._process_event(event)
                    self.event_queue.task_done()
                except Empty:
                    break
        except Exception as e:
            logger.error(f"Error processing events: {e}")

    def _process_event(self, event: Dict[str, Any]) -> None:
        """Process a single compliance event

        Args:
            event: Event data
        """
        try:
            event_type = event.get("type")
            if event_type == "portfolio_update":
                portfolio_data = event.get("portfolio_data", {})
                position_data = event.get("position_data", [])
                self.check_compliance(portfolio_data, position_data)
            elif event_type == "position_change":
                position_data = event.get("position_data", {})
                portfolio_data = event.get("portfolio_data", {})
                self._check_position_rules(position_data, portfolio_data)
            elif event_type == "market_data_update":
                market_data = event.get("market_data", {})
                self._check_market_sensitive_rules(market_data)
        except Exception as e:
            logger.error(f"Error processing event: {e}")

    def _check_rule(
        self,
        rule: ComplianceRule,
        portfolio_data: Dict[str, Any],
        position_data: Optional[List[Dict[str, Any]]],
        market_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Check a single compliance rule

        Args:
            rule: Rule to check
            portfolio_data: Portfolio data
            position_data: Position data
            market_data: Market data

        Returns:
            Rule check result
        """
        try:
            current_value = self._get_measurement_value(
                rule.measurement_field, portfolio_data, position_data, market_data
            )
            if current_value is None:
                return {
                    "status": "error",
                    "message": f"Could not calculate {rule.measurement_field}",
                }
            violation = self._evaluate_threshold(
                current_value, rule.threshold, rule.operator
            )
            if violation:
                if self._is_within_grace_period(rule):
                    return {
                        "status": "warning",
                        "current_value": current_value,
                        "threshold": rule.threshold,
                        "message": f"Rule {rule.name} in grace period",
                    }
                else:
                    return {
                        "status": "violation",
                        "current_value": current_value,
                        "threshold": rule.threshold,
                        "message": f"Rule {rule.name} violated: {current_value} {rule.operator} {rule.threshold}",
                    }
            else:
                return {
                    "status": "compliant",
                    "current_value": current_value,
                    "threshold": rule.threshold,
                    "message": f"Rule {rule.name} compliant",
                }
        except Exception as e:
            logger.error(f"Error checking rule {rule.rule_id}: {e}")
            return {"status": "error", "message": f"Error checking rule: {str(e)}"}

    def _get_measurement_value(
        self,
        measurement_field: str,
        portfolio_data: Dict[str, Any],
        position_data: Optional[List[Dict[str, Any]]],
        market_data: Optional[Dict[str, Any]],
    ) -> Optional[float]:
        """Get measurement value for a field

        Args:
            measurement_field: Field to measure
            portfolio_data: Portfolio data
            position_data: Position data
            market_data: Market data

        Returns:
            Measurement value
        """
        try:
            if measurement_field == "total_portfolio_value":
                return portfolio_data.get("total_value", 0)
            elif measurement_field == "leverage_ratio":
                total_value = portfolio_data.get("total_value", 0)
                gross_exposure = portfolio_data.get("gross_exposure", 0)
                return gross_exposure / total_value if total_value > 0 else 0
            elif measurement_field == "cash_ratio":
                total_value = portfolio_data.get("total_value", 0)
                cash_value = portfolio_data.get("cash_value", 0)
                return cash_value / total_value if total_value > 0 else 0
            elif measurement_field == "var_percentage":
                total_value = portfolio_data.get("total_value", 0)
                var_amount = portfolio_data.get("var_amount", 0)
                return var_amount / total_value if total_value > 0 else 0
            elif measurement_field == "single_position_concentration":
                if not position_data:
                    return 0
                total_value = portfolio_data.get("total_value", 0)
                if total_value == 0:
                    return 0
                max_position = max(
                    (pos.get("market_value", 0) for pos in position_data)
                )
                return max_position / total_value
            elif measurement_field == "sector_concentration":
                if not position_data:
                    return 0
                return self._calculate_max_sector_concentration(
                    position_data, portfolio_data
                )
            elif measurement_field == "liquidity_ratio":
                if not position_data:
                    return 0
                total_value = portfolio_data.get("total_value", 0)
                if total_value == 0:
                    return 0
                liquid_value = sum(
                    (
                        pos.get("market_value", 0)
                        for pos in position_data
                        if pos.get("liquidity_category") in ["daily", "weekly"]
                    )
                )
                return liquid_value / total_value
            elif measurement_field == "derivative_exposure":
                if not position_data:
                    return 0
                return sum(
                    (
                        pos.get("notional_value", 0)
                        for pos in position_data
                        if pos.get("asset_type") == "derivative"
                    )
                )
            elif measurement_field == "foreign_exposure":
                if not position_data:
                    return 0
                total_value = portfolio_data.get("total_value", 0)
                if total_value == 0:
                    return 0
                foreign_value = sum(
                    (
                        pos.get("market_value", 0)
                        for pos in position_data
                        if pos.get("country") != "US"
                    )
                )
                return foreign_value / total_value
            else:
                return portfolio_data.get(measurement_field)
        except Exception as e:
            logger.error(f"Error calculating {measurement_field}: {e}")
            return None

    def _calculate_max_sector_concentration(
        self, position_data: List[Dict[str, Any]], portfolio_data: Dict[str, Any]
    ) -> float:
        """Calculate maximum sector concentration

        Args:
            position_data: Position data
            portfolio_data: Portfolio data

        Returns:
            Maximum sector concentration
        """
        total_value = portfolio_data.get("total_value", 0)
        if total_value == 0:
            return 0
        sectors = {}
        for pos in position_data:
            sector = pos.get("sector", "unknown")
            if sector not in sectors:
                sectors[sector] = 0
            sectors[sector] += pos.get("market_value", 0)
        if not sectors:
            return 0
        max_sector_value = max(sectors.values())
        return max_sector_value / total_value

    def _evaluate_threshold(
        self, current_value: float, threshold: float, operator: str
    ) -> bool:
        """Evaluate if current value violates threshold

        Args:
            current_value: Current measurement value
            threshold: Threshold value
            operator: Comparison operator

        Returns:
            True if violation, False if compliant
        """
        if operator == ">":
            return current_value > threshold
        elif operator == "<":
            return current_value < threshold
        elif operator == ">=":
            return current_value >= threshold
        elif operator == "<=":
            return current_value <= threshold
        elif operator == "==":
            return current_value == threshold
        elif operator == "!=":
            return current_value != threshold
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False

    def _is_within_grace_period(self, rule: ComplianceRule) -> bool:
        """Check if rule is within grace period

        Args:
            rule: Compliance rule

        Returns:
            True if within grace period
        """
        if rule.grace_period_minutes == 0:
            return False
        for violation in self.active_violations.values():
            if violation.rule_id == rule.rule_id:
                time_since_detection = datetime.utcnow() - violation.detected_at
                return (
                    time_since_detection.total_seconds()
                    < rule.grace_period_minutes * 60
                )
        return True

    def _create_violation(
        self,
        rule: ComplianceRule,
        check_result: Dict[str, Any],
        portfolio_data: Dict[str, Any],
    ) -> ComplianceViolation:
        """Create a compliance violation record

        Args:
            rule: Violated rule
            check_result: Rule check result
            portfolio_data: Portfolio data

        Returns:
            Compliance violation
        """
        violation_id = f"violation_{int(time.time() * 1000)}"
        return ComplianceViolation(
            violation_id=violation_id,
            rule_id=rule.rule_id,
            rule_name=rule.name,
            violation_type=rule.rule_type,
            severity=rule.severity,
            current_value=check_result["current_value"],
            threshold_value=rule.threshold,
            description=check_result["message"],
            detected_at=datetime.utcnow(),
            portfolio_id=portfolio_data.get("portfolio_id"),
            additional_data={
                "operator": rule.operator,
                "measurement_field": rule.measurement_field,
                "jurisdiction": rule.jurisdiction,
                "regulation": rule.regulation,
            },
        )

    def _handle_violation(self, violation: ComplianceViolation) -> None:
        """Handle a compliance violation

        Args:
            violation: Compliance violation
        """
        self.active_violations[violation.violation_id] = violation
        for callback in self.violation_callbacks:
            try:
                callback(violation)
            except Exception as e:
                logger.error(f"Error in violation callback: {e}")
        logger.warning(
            f"Compliance violation detected: {violation.rule_name} - {violation.description}"
        )

    def _violation_to_dict(self, violation: ComplianceViolation) -> Dict[str, Any]:
        """Convert violation to dictionary

        Args:
            violation: Compliance violation

        Returns:
            Violation dictionary
        """
        return {
            "violation_id": violation.violation_id,
            "rule_id": violation.rule_id,
            "rule_name": violation.rule_name,
            "violation_type": violation.violation_type.value,
            "severity": violation.severity.value,
            "current_value": violation.current_value,
            "threshold_value": violation.threshold_value,
            "description": violation.description,
            "detected_at": violation.detected_at.isoformat(),
            "resolved_at": (
                violation.resolved_at.isoformat() if violation.resolved_at else None
            ),
            "status": violation.status,
            "portfolio_id": violation.portfolio_id,
            "position_id": violation.position_id,
            "additional_data": violation.additional_data,
        }

    def _check_position_rules(
        self, position_data: Dict[str, Any], portfolio_data: Dict[str, Any]
    ) -> None:
        """Check position-specific compliance rules

        Args:
            position_data: Position data
            portfolio_data: Portfolio data
        """
        logger.debug(
            f"Checking position rules for {position_data.get('symbol', 'unknown')}"
        )

    def _check_market_sensitive_rules(self, market_data: Dict[str, Any]) -> None:
        """Check market-sensitive compliance rules

        Args:
            market_data: Market data
        """
        logger.debug("Checking market-sensitive compliance rules")

    def _initialize_default_rules(self) -> None:
        """Initialize default compliance rules"""
        self.add_rule(
            ComplianceRule(
                rule_id="single_position_limit",
                name="Single Position Concentration Limit",
                description="No single position should exceed 10% of portfolio value",
                rule_type=ViolationType.CONCENTRATION_LIMIT,
                severity=ViolationSeverity.HIGH,
                threshold=0.1,
                operator=">",
                measurement_field="single_position_concentration",
                jurisdiction="US",
                regulation="Investment Company Act of 1940",
                grace_period_minutes=30,
            )
        )
        self.add_rule(
            ComplianceRule(
                rule_id="leverage_limit",
                name="Maximum Leverage Ratio",
                description="Portfolio leverage should not exceed 3:1",
                rule_type=ViolationType.LEVERAGE_LIMIT,
                severity=ViolationSeverity.CRITICAL,
                threshold=3.0,
                operator=">",
                measurement_field="leverage_ratio",
                jurisdiction="US",
                regulation="SEC Rule 3a-4",
                grace_period_minutes=0,
            )
        )
        self.add_rule(
            ComplianceRule(
                rule_id="liquidity_requirement",
                name="Minimum Liquidity Requirement",
                description="At least 20% of portfolio must be in liquid assets",
                rule_type=ViolationType.LIQUIDITY_REQUIREMENT,
                severity=ViolationSeverity.MEDIUM,
                threshold=0.2,
                operator="<",
                measurement_field="liquidity_ratio",
                jurisdiction="US",
                regulation="SEC Rule 22e-4",
                grace_period_minutes=60,
            )
        )
        self.add_rule(
            ComplianceRule(
                rule_id="var_limit",
                name="Value at Risk Limit",
                description="Daily VaR should not exceed 2% of portfolio value",
                rule_type=ViolationType.RISK_LIMIT,
                severity=ViolationSeverity.HIGH,
                threshold=0.02,
                operator=">",
                measurement_field="var_percentage",
                jurisdiction="US",
                regulation="Internal Risk Policy",
                grace_period_minutes=15,
            )
        )
        self.add_rule(
            ComplianceRule(
                rule_id="sector_concentration_limit",
                name="Sector Concentration Limit",
                description="No single sector should exceed 25% of portfolio value",
                rule_type=ViolationType.CONCENTRATION_LIMIT,
                severity=ViolationSeverity.MEDIUM,
                threshold=0.25,
                operator=">",
                measurement_field="sector_concentration",
                jurisdiction="US",
                regulation="Investment Company Act of 1940",
                grace_period_minutes=120,
            )
        )
        self.add_rule(
            ComplianceRule(
                rule_id="cash_minimum",
                name="Minimum Cash Requirement",
                description="Portfolio must maintain at least 5% in cash",
                rule_type=ViolationType.LIQUIDITY_REQUIREMENT,
                severity=ViolationSeverity.LOW,
                threshold=0.05,
                operator="<",
                measurement_field="cash_ratio",
                jurisdiction="US",
                regulation="Internal Liquidity Policy",
                grace_period_minutes=240,
            )
        )
        self.add_rule(
            ComplianceRule(
                rule_id="foreign_exposure_limit",
                name="Foreign Exposure Limit",
                description="Foreign investments should not exceed 30% of portfolio",
                rule_type=ViolationType.INVESTMENT_RESTRICTION,
                severity=ViolationSeverity.MEDIUM,
                threshold=0.3,
                operator=">",
                measurement_field="foreign_exposure",
                jurisdiction="US",
                regulation="Investment Company Act of 1940",
                grace_period_minutes=180,
            )
        )
        logger.info(f"Initialized {len(self.rules)} default compliance rules")


class ComplianceReporter:
    """Compliance reporting and analytics"""

    def __init__(self, compliance_monitor: ComplianceMonitor) -> None:
        """Initialize compliance reporter

        Args:
            compliance_monitor: Compliance monitor instance
        """
        self.compliance_monitor = compliance_monitor

    def generate_compliance_report(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Generate compliance report for a period

        Args:
            start_date: Report start date
            end_date: Report end date

        Returns:
            Compliance report
        """
        period_violations = [
            v
            for v in self.compliance_monitor.violation_history
            if start_date <= v.detected_at <= end_date
        ]
        total_violations = len(period_violations)
        violations_by_type = {}
        violations_by_severity = {}
        for violation in period_violations:
            vtype = violation.violation_type.value
            if vtype not in violations_by_type:
                violations_by_type[vtype] = 0
            violations_by_type[vtype] += 1
            severity = violation.severity.value
            if severity not in violations_by_severity:
                violations_by_severity[severity] = 0
            violations_by_severity[severity] += 1
        resolved_violations = [v for v in period_violations if v.resolved_at]
        if resolved_violations:
            resolution_times = [
                (v.resolved_at - v.detected_at).total_seconds() / 3600
                for v in resolved_violations
            ]
            avg_resolution_time = sum(resolution_times) / len(resolution_times)
        else:
            avg_resolution_time = 0
        return {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "summary": {
                "total_violations": total_violations,
                "resolved_violations": len(resolved_violations),
                "active_violations": len(self.compliance_monitor.active_violations),
                "resolution_rate": (
                    len(resolved_violations) / total_violations
                    if total_violations > 0
                    else 0
                ),
                "average_resolution_time_hours": avg_resolution_time,
            },
            "violations_by_type": violations_by_type,
            "violations_by_severity": violations_by_severity,
            "detailed_violations": [
                self.compliance_monitor._violation_to_dict(v) for v in period_violations
            ],
            "generated_at": datetime.utcnow().isoformat(),
        }
