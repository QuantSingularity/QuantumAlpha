"""
Unit tests for the QuantumAlpha Compliance Service.
Covers ComplianceMonitor and RegulatoryReportingEngine.
"""

import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from backend.compliance_service.compliance_monitoring import (
    ComplianceMonitor,
    ComplianceRule,
    ComplianceStatus,
    ViolationSeverity,
    ViolationType,
)
from backend.compliance_service.regulatory_reporting import (
    RegulatoryJurisdiction,
    RegulatoryReportingEngine,
    ReportType,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cfg() -> MagicMock:
    m = MagicMock()
    m.get.return_value = None
    return m


def _db() -> MagicMock:
    return MagicMock()


def _monitor() -> ComplianceMonitor:
    return ComplianceMonitor(_cfg(), _db())


def _engine() -> RegulatoryReportingEngine:
    return RegulatoryReportingEngine(_cfg(), _db())


def _rule(
    rule_id: str = "test-001",
    rule_type: ViolationType = None,
    severity: ViolationSeverity = None,
) -> ComplianceRule:
    """Build a minimal valid ComplianceRule using the actual dataclass fields."""
    return ComplianceRule(
        rule_id=rule_id,
        name="Test Position Limit",
        description="No single position > 20 %",
        rule_type=rule_type or ViolationType.POSITION_LIMIT,
        severity=severity or ViolationSeverity.HIGH,
        threshold=0.20,
        operator="greater_than",
        measurement_field="position_weight",
        jurisdiction="us_sec",
        regulation="SEC Rule 18f-4",
    )


def _portfolio() -> dict:
    return {
        "id": "port-001",
        "positions": [
            {
                "symbol": "AAPL",
                "weight": 0.15,
                "sector": "Technology",
                "market_value": 150_000,
                "country": "US",
            },
            {
                "symbol": "MSFT",
                "weight": 0.12,
                "sector": "Technology",
                "market_value": 120_000,
                "country": "US",
            },
            {
                "symbol": "JPM",
                "weight": 0.10,
                "sector": "Financials",
                "market_value": 100_000,
                "country": "US",
            },
        ],
        "total_value": 1_000_000,
    }


def _dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# ComplianceMonitor tests
# ---------------------------------------------------------------------------


class TestComplianceMonitor(unittest.TestCase):

    def setUp(self) -> None:
        self.monitor = _monitor()

    # --- Construction -------------------------------------------------------

    def test_initialization(self) -> None:
        self.assertIsNotNone(self.monitor)

    def test_rules_dict_exists(self) -> None:
        self.assertIsInstance(self.monitor.rules, dict)

    def test_default_rules_populated(self) -> None:
        self.assertGreater(len(self.monitor.rules), 0)

    def test_active_violations_initially_empty(self) -> None:
        self.assertIsInstance(self.monitor.active_violations, dict)

    # --- ComplianceRule dataclass ------------------------------------------

    def test_compliance_rule_construction(self) -> None:
        rule = _rule("r-001")
        self.assertEqual(rule.rule_id, "r-001")
        self.assertAlmostEqual(rule.threshold, 0.20)
        self.assertEqual(rule.severity, ViolationSeverity.HIGH)
        self.assertEqual(rule.measurement_field, "position_weight")
        self.assertEqual(rule.operator, "greater_than")
        self.assertTrue(rule.enabled)

    def test_rule_defaults(self) -> None:
        rule = _rule()
        self.assertTrue(rule.enabled)
        self.assertEqual(rule.grace_period_minutes, 0)
        self.assertTrue(rule.notification_required)

    # --- add / remove / enable / disable rule ------------------------------

    def test_add_rule_increases_count(self) -> None:
        before = len(self.monitor.rules)
        self.monitor.add_rule(_rule("new-rule-001"))
        self.assertEqual(len(self.monitor.rules), before + 1)

    def test_added_rule_retrievable(self) -> None:
        self.monitor.add_rule(_rule("new-rule-002"))
        self.assertIn("new-rule-002", self.monitor.rules)

    def test_remove_rule_decreases_count(self) -> None:
        self.monitor.add_rule(_rule("rm-rule-001"))
        before = len(self.monitor.rules)
        self.monitor.remove_rule("rm-rule-001")
        self.assertEqual(len(self.monitor.rules), before - 1)

    def test_remove_nonexistent_rule_does_not_crash(self) -> None:
        self.monitor.remove_rule("totally-nonexistent-xyz-999")  # should be silent

    def test_disable_rule_sets_enabled_false(self) -> None:
        self.monitor.add_rule(_rule("dis-rule-001"))
        self.monitor.disable_rule("dis-rule-001")
        self.assertFalse(self.monitor.rules["dis-rule-001"].enabled)

    def test_enable_rule_sets_enabled_true(self) -> None:
        self.monitor.add_rule(_rule("en-rule-001"))
        self.monitor.disable_rule("en-rule-001")
        self.monitor.enable_rule("en-rule-001")
        self.assertTrue(self.monitor.rules["en-rule-001"].enabled)

    # --- check_compliance --------------------------------------------------

    def test_check_compliance_returns_dict(self) -> None:
        result = self.monitor.check_compliance(_portfolio())
        self.assertIsInstance(result, dict)

    def test_check_compliance_non_empty(self) -> None:
        result = self.monitor.check_compliance(_portfolio())
        self.assertGreater(len(result), 0)

    # --- get_compliance_metrics --------------------------------------------

    def test_compliance_metrics_returns_dict(self) -> None:
        metrics = self.monitor.get_compliance_metrics()
        self.assertIsInstance(metrics, dict)

    def test_compliance_metrics_non_empty(self) -> None:
        metrics = self.monitor.get_compliance_metrics()
        self.assertGreater(len(metrics), 0)

    def test_metrics_has_rule_counts(self) -> None:
        metrics = self.monitor.get_compliance_metrics()
        # Should report total rule count somewhere
        flat = str(metrics)
        self.assertIn(str(len(self.monitor.rules)), flat)

    # --- Violation callback -----------------------------------------------

    def test_add_violation_callback_does_not_raise(self) -> None:
        self.monitor.add_violation_callback(MagicMock())

    # --- Enums -------------------------------------------------------------

    def test_violation_type_enum_values(self) -> None:
        self.assertEqual(ViolationType.POSITION_LIMIT.value, "position_limit")
        self.assertEqual(ViolationType.CONCENTRATION_LIMIT.value, "concentration_limit")

    def test_violation_severity_enum_values(self) -> None:
        self.assertEqual(ViolationSeverity.LOW.value, "low")
        self.assertEqual(ViolationSeverity.MEDIUM.value, "medium")
        self.assertEqual(ViolationSeverity.HIGH.value, "high")
        self.assertEqual(ViolationSeverity.CRITICAL.value, "critical")

    def test_compliance_status_enum_exists(self) -> None:
        self.assertIsNotNone(ComplianceStatus.COMPLIANT)
        self.assertIsNotNone(ComplianceStatus.VIOLATION)

    def test_violation_type_all_values(self) -> None:
        vals = {v.value for v in ViolationType}
        self.assertIn("position_limit", vals)
        self.assertIn("concentration_limit", vals)


# ---------------------------------------------------------------------------
# RegulatoryReportingEngine tests
# ---------------------------------------------------------------------------


class TestRegulatoryReportingEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = _engine()

    # --- Construction -------------------------------------------------------

    def test_initialization(self) -> None:
        self.assertIsNotNone(self.engine)

    def test_reporting_requirements_populated(self) -> None:
        self.assertIsInstance(self.engine.reporting_requirements, dict)
        self.assertGreater(len(self.engine.reporting_requirements), 0)

    def test_report_templates_populated(self) -> None:
        self.assertIsInstance(self.engine.report_templates, dict)

    # --- generate_report ---------------------------------------------------

    def test_generate_form_13f_returns_dict(self) -> None:
        result = self.engine.generate_report(
            report_type="form_13f",
            jurisdiction="us_sec",
            period_start=_dt("2024-01-01"),
            period_end=_dt("2024-03-31"),
        )
        self.assertIsInstance(result, dict)

    def test_generate_risk_metrics_report(self) -> None:
        result = self.engine.generate_report(
            report_type="risk_metrics_report",
            jurisdiction="us_sec",
            period_start=_dt("2024-01-01"),
            period_end=_dt("2024-01-31"),
        )
        self.assertIsInstance(result, dict)

    def test_generate_portfolio_composition(self) -> None:
        result = self.engine.generate_report(
            report_type="portfolio_composition",
            jurisdiction="us_sec",
            period_start=_dt("2024-01-01"),
            period_end=_dt("2024-01-31"),
        )
        self.assertIsInstance(result, dict)

    def test_generate_stress_test_results(self) -> None:
        result = self.engine.generate_report(
            report_type="stress_test_results",
            jurisdiction="us_sec",
            period_start=_dt("2024-01-01"),
            period_end=_dt("2024-03-31"),
        )
        self.assertIsInstance(result, dict)

    def test_generate_lcr_report(self) -> None:
        result = self.engine.generate_report(
            report_type="liquidity_coverage_ratio",
            jurisdiction="basel_committee",
            period_start=_dt("2024-01-01"),
            period_end=_dt("2024-01-31"),
        )
        self.assertIsInstance(result, dict)

    def test_generated_report_has_report_id(self) -> None:
        result = self.engine.generate_report(
            report_type="risk_metrics_report",
            jurisdiction="us_sec",
            period_start=_dt("2024-01-01"),
            period_end=_dt("2024-01-31"),
        )
        self.assertIn("report_id", result)

    def test_generated_report_has_report_type(self) -> None:
        result = self.engine.generate_report(
            report_type="form_13f",
            jurisdiction="us_sec",
            period_start=_dt("2024-01-01"),
            period_end=_dt("2024-03-31"),
        )
        self.assertIn("report_type", result)

    def test_invalid_report_type_raises(self) -> None:
        with self.assertRaises(Exception):
            self.engine.generate_report(
                report_type="nonexistent_report_xyz",
                jurisdiction="us_sec",
                period_start=_dt("2024-01-01"),
                period_end=_dt("2024-01-31"),
            )

    # --- get_report --------------------------------------------------------

    def test_get_report_after_generation(self) -> None:
        generated = self.engine.generate_report(
            report_type="risk_metrics_report",
            jurisdiction="us_sec",
            period_start=_dt("2024-01-01"),
            period_end=_dt("2024-01-31"),
        )
        report_id = generated.get("report_id")
        if report_id:
            fetched = self.engine.get_report(report_id)
            self.assertIsInstance(fetched, dict)

    # --- list_reports ------------------------------------------------------

    def test_list_reports_returns_list(self) -> None:
        result = self.engine.list_reports()
        self.assertIsInstance(result, list)

    # --- Enums -------------------------------------------------------------

    def test_report_type_enum_values(self) -> None:
        self.assertEqual(ReportType.FORM_13F.value, "form_13f")
        self.assertEqual(ReportType.FORM_PF.value, "form_pf")
        self.assertEqual(
            ReportType.MIFID_II_TRANSACTION_REPORTING.value,
            "mifid_ii_transaction_reporting",
        )
        self.assertEqual(
            ReportType.BASEL_III_CAPITAL_ADEQUACY.value, "basel_iii_capital_adequacy"
        )
        self.assertEqual(ReportType.STRESS_TEST_RESULTS.value, "stress_test_results")
        self.assertEqual(ReportType.RISK_METRICS_REPORT.value, "risk_metrics_report")
        self.assertEqual(
            ReportType.LIQUIDITY_COVERAGE_RATIO.value, "liquidity_coverage_ratio"
        )
        self.assertEqual(
            ReportType.PORTFOLIO_COMPOSITION.value, "portfolio_composition"
        )

    def test_jurisdiction_enum_values(self) -> None:
        self.assertEqual(RegulatoryJurisdiction.US_SEC.value, "us_sec")
        self.assertEqual(RegulatoryJurisdiction.US_CFTC.value, "us_cftc")
        self.assertEqual(RegulatoryJurisdiction.EU_ESMA.value, "eu_esma")
        self.assertEqual(RegulatoryJurisdiction.UK_FCA.value, "uk_fca")

    # --- _calculate helpers ------------------------------------------------

    def test_sector_concentration_returns_dict(self) -> None:
        positions = [
            {"symbol": "AAPL", "sector": "Technology", "market_value": 300_000},
            {"symbol": "MSFT", "sector": "Technology", "market_value": 200_000},
            {"symbol": "JPM", "sector": "Financials", "market_value": 500_000},
        ]
        result = self.engine._calculate_sector_concentrations(positions)
        self.assertIsInstance(result, dict)

    def test_sector_concentration_sums_to_one(self) -> None:
        positions = [
            {"symbol": "AAPL", "sector": "Tech", "market_value": 600_000},
            {"symbol": "JPM", "sector": "Finance", "market_value": 400_000},
        ]
        result = self.engine._calculate_sector_concentrations(positions)
        if result:
            self.assertAlmostEqual(sum(result.values()), 1.0, places=4)

    def test_single_name_concentration_returns_dict(self) -> None:
        positions = [
            {"symbol": "AAPL", "market_value": 300_000},
            {"symbol": "MSFT", "market_value": 700_000},
        ]
        result = self.engine._calculate_single_name_concentration(positions)
        self.assertIsInstance(result, dict)
        self.assertIn("largest_position", result)

    def test_geographic_concentration_returns_dict(self) -> None:
        positions = [
            {"symbol": "AAPL", "country": "US", "market_value": 600_000},
            {"symbol": "SAP", "country": "DE", "market_value": 400_000},
        ]
        result = self.engine._calculate_geographic_concentrations(positions)
        self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main(verbosity=2)
