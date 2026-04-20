"""
Regulatory reporting module for QuantumAlpha Compliance Service.
Handles comprehensive regulatory reporting and compliance monitoring.
"""

import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from backend.common import NotFoundError, ServiceError, ValidationError, setup_logger

logger = setup_logger("regulatory_reporting", logging.INFO)


class ReportType(Enum):
    """Regulatory report types"""

    FORM_PF = "form_pf"
    FORM_ADV = "form_adv"
    FORM_13F = "form_13f"
    CFTC_FORM_CPO_PQR = "cftc_form_cpo_pqr"
    EMIR_TRADE_REPORTING = "emir_trade_reporting"
    MIFID_II_TRANSACTION_REPORTING = "mifid_ii_transaction_reporting"
    BASEL_III_CAPITAL_ADEQUACY = "basel_iii_capital_adequacy"
    SOLVENCY_II = "solvency_ii"
    LIQUIDITY_COVERAGE_RATIO = "liquidity_coverage_ratio"
    NET_STABLE_FUNDING_RATIO = "net_stable_funding_ratio"
    STRESS_TEST_RESULTS = "stress_test_results"
    RISK_METRICS_REPORT = "risk_metrics_report"
    PORTFOLIO_COMPOSITION = "portfolio_composition"
    COUNTERPARTY_EXPOSURE = "counterparty_exposure"
    OPERATIONAL_RISK = "operational_risk"


class RegulatoryJurisdiction(Enum):
    """Regulatory jurisdictions"""

    US_SEC = "us_sec"
    US_CFTC = "us_cftc"
    EU_ESMA = "eu_esma"
    UK_FCA = "uk_fca"
    BASEL_COMMITTEE = "basel_committee"
    IOSCO = "iosco"


@dataclass
class ReportingRequirement:
    """Regulatory reporting requirement"""

    report_type: ReportType
    jurisdiction: RegulatoryJurisdiction
    frequency: str
    deadline_days: int
    mandatory_fields: List[str]
    optional_fields: List[str]
    validation_rules: Dict[str, Any]
    format_requirements: Dict[str, Any]


class RegulatoryReportingEngine:
    """Comprehensive regulatory reporting engine"""

    def __init__(self, config_manager: object, db_manager: object) -> None:
        """Initialize regulatory reporting engine

        Args:
            config_manager: Configuration manager
            db_manager: Database manager
        """
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.reporting_requirements = self._initialize_reporting_requirements()
        self.report_templates = self._initialize_report_templates()
        self.validation_rules = self._initialize_validation_rules()
        self.report_storage_path = "/tmp/regulatory_reports"
        os.makedirs(self.report_storage_path, exist_ok=True)
        logger.info("Regulatory reporting engine initialized")

    def generate_report(
        self,
        report_type: str,
        jurisdiction: str,
        period_start: datetime,
        period_end: datetime,
        portfolio_data: Optional[Dict[str, Any]] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a regulatory report

        Args:
            report_type: Type of report to generate
            jurisdiction: Regulatory jurisdiction
            period_start: Report period start date
            period_end: Report period end date
            portfolio_data: Portfolio data for the report
            additional_data: Additional data required for the report

        Returns:
            Generated report

        Raises:
            ValidationError: If parameters are invalid
            ServiceError: If report generation fails
        """
        try:
            logger.info(f"Generating {report_type} report for {jurisdiction}")
            self._validate_report_request(
                report_type, jurisdiction, period_start, period_end
            )
            requirement = self._get_reporting_requirement(report_type, jurisdiction)
            report_data = self._collect_report_data(
                requirement, period_start, period_end, portfolio_data, additional_data
            )
            if report_type == ReportType.FORM_PF.value:
                report = self._generate_form_pf(report_data, requirement)
            elif report_type == ReportType.FORM_13F.value:
                report = self._generate_form_13f(report_data, requirement)
            elif report_type == ReportType.BASEL_III_CAPITAL_ADEQUACY.value:
                report = self._generate_basel_iii_capital_adequacy(
                    report_data, requirement
                )
            elif report_type == ReportType.STRESS_TEST_RESULTS.value:
                report = self._generate_stress_test_results(report_data, requirement)
            elif report_type == ReportType.RISK_METRICS_REPORT.value:
                report = self._generate_risk_metrics_report(report_data, requirement)
            elif report_type == ReportType.PORTFOLIO_COMPOSITION.value:
                report = self._generate_portfolio_composition(report_data, requirement)
            elif report_type == ReportType.LIQUIDITY_COVERAGE_RATIO.value:
                report = self._generate_liquidity_coverage_ratio(
                    report_data, requirement
                )
            else:
                report = self._generate_generic_report(report_data, requirement)
            validation_result = self._validate_report(report, requirement)
            report_id = self._save_report(report, report_type, jurisdiction)
            response = {
                "report_id": report_id,
                "report_type": report_type,
                "jurisdiction": jurisdiction,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "report_data": report,
                "validation_result": validation_result,
                "generated_at": datetime.utcnow().isoformat(),
            }
            return response
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise ServiceError(f"Error generating report: {str(e)}")

    def _generate_form_pf(
        self, report_data: Dict[str, Any], requirement: ReportingRequirement
    ) -> Dict[str, Any]:
        """Generate Form PF report (Private Fund Adviser Reporting)

        Args:
            report_data: Collected report data
            requirement: Reporting requirement

        Returns:
            Form PF report
        """
        portfolio_data = report_data.get("portfolio_data", {})
        risk_data = report_data.get("risk_data", {})
        total_aum = sum(
            (pos.get("market_value", 0) for pos in portfolio_data.get("positions", []))
        )
        gross_notional = sum(
            (
                abs(pos.get("notional_value", pos.get("market_value", 0)))
                for pos in portfolio_data.get("positions", [])
            )
        )
        leverage_ratio = gross_notional / total_aum if total_aum > 0 else 0
        positions = portfolio_data.get("positions", [])
        if positions:
            position_values = [pos.get("market_value", 0) for pos in positions]
            position_values.sort(reverse=True)
            top_5_concentration = (
                sum(position_values[:5]) / total_aum if total_aum > 0 else 0
            )
        else:
            top_5_concentration = 0
        liquid_assets = sum(
            (
                pos.get("market_value", 0)
                for pos in positions
                if pos.get("liquidity_category") in ["daily", "weekly"]
            )
        )
        liquidity_ratio = liquid_assets / total_aum if total_aum > 0 else 0
        form_pf = {
            "fund_information": {
                "fund_name": portfolio_data.get("fund_name", "QuantumAlpha Fund"),
                "fund_type": portfolio_data.get("fund_type", "hedge_fund"),
                "reporting_period_end": report_data["period_end"],
                "total_aum": total_aum,
                "number_of_investors": portfolio_data.get("investor_count", 0),
            },
            "leverage_information": {
                "gross_notional_exposure": gross_notional,
                "leverage_ratio": leverage_ratio,
                "borrowing_amount": portfolio_data.get("borrowing_amount", 0),
                "derivative_exposure": sum(
                    (
                        pos.get("notional_value", 0)
                        for pos in positions
                        if pos.get("asset_type") == "derivative"
                    )
                ),
            },
            "liquidity_information": {
                "liquid_assets": liquid_assets,
                "liquidity_ratio": liquidity_ratio,
                "redemption_frequency": portfolio_data.get(
                    "redemption_frequency", "monthly"
                ),
                "notice_period_days": portfolio_data.get("notice_period_days", 30),
            },
            "risk_metrics": {
                "var_95": risk_data.get("var_95", 0),
                "var_99": risk_data.get("var_99", 0),
                "expected_shortfall": risk_data.get("expected_shortfall", 0),
                "maximum_drawdown": risk_data.get("maximum_drawdown", 0),
                "sharpe_ratio": risk_data.get("sharpe_ratio", 0),
                "volatility": risk_data.get("volatility", 0),
            },
            "concentration_information": {
                "top_5_concentration": top_5_concentration,
                "single_issuer_limit": portfolio_data.get("single_issuer_limit", 0.1),
                "sector_concentrations": self._calculate_sector_concentrations(
                    positions
                ),
                "geographic_concentrations": self._calculate_geographic_concentrations(
                    positions
                ),
            },
            "counterparty_information": {
                "prime_brokers": portfolio_data.get("prime_brokers", []),
                "counterparty_exposures": self._calculate_counterparty_exposures(
                    positions
                ),
                "collateral_posted": portfolio_data.get("collateral_posted", 0),
                "collateral_received": portfolio_data.get("collateral_received", 0),
            },
        }
        return form_pf

    def _generate_form_13f(
        self, report_data: Dict[str, Any], requirement: ReportingRequirement
    ) -> Dict[str, Any]:
        """Generate Form 13F report (Institutional Investment Manager Filing)

        Args:
            report_data: Collected report data
            requirement: Reporting requirement

        Returns:
            Form 13F report
        """
        portfolio_data = report_data.get("portfolio_data", {})
        positions = portfolio_data.get("positions", [])
        eligible_positions = [
            pos
            for pos in positions
            if pos.get("asset_type") == "equity"
            and pos.get("market_value", 0) >= 200000
        ]
        total_value = sum((pos.get("market_value", 0) for pos in eligible_positions))
        holdings = []
        for pos in eligible_positions:
            holdings.append(
                {
                    "name_of_issuer": pos.get("issuer_name", ""),
                    "title_of_class": pos.get("security_class", "Common Stock"),
                    "cusip": pos.get("cusip", ""),
                    "value": pos.get("market_value", 0),
                    "shares_or_principal_amount": pos.get("quantity", 0),
                    "shares_or_principal": "SH",
                    "investment_discretion": pos.get("investment_discretion", "SOLE"),
                    "voting_authority": {
                        "sole": pos.get("voting_sole", 0),
                        "shared": pos.get("voting_shared", 0),
                        "none": pos.get("voting_none", 0),
                    },
                }
            )
        form_13f = {
            "cover_page": {
                "institution_name": portfolio_data.get(
                    "institution_name", "QuantumAlpha Management"
                ),
                "form_13f_file_number": portfolio_data.get("form_13f_file_number", ""),
                "period_of_report": report_data["period_end"],
                "total_value_of_holdings": total_value,
                "number_of_holdings": len(holdings),
            },
            "summary_page": {
                "list_of_other_managers": portfolio_data.get("other_managers", []),
                "total_entries": len(holdings),
                "total_value": total_value,
            },
            "information_table": {"holdings": holdings},
        }
        return form_13f

    def _generate_basel_iii_capital_adequacy(
        self, report_data: Dict[str, Any], requirement: ReportingRequirement
    ) -> Dict[str, Any]:
        """Generate Basel III Capital Adequacy report

        Args:
            report_data: Collected report data
            requirement: Reporting requirement

        Returns:
            Basel III Capital Adequacy report
        """
        portfolio_data = report_data.get("portfolio_data", {})
        capital_data = report_data.get("capital_data", {})
        positions = portfolio_data.get("positions", [])
        total_rwa = 0
        for pos in positions:
            market_value = pos.get("market_value", 0)
            risk_weight = self._get_basel_risk_weight(pos)
            total_rwa += market_value * risk_weight
        cet1_capital = capital_data.get("cet1_capital", 0)
        tier1_capital = capital_data.get("tier1_capital", 0)
        total_capital = capital_data.get("total_capital", 0)
        cet1_ratio = cet1_capital / total_rwa if total_rwa > 0 else 0
        tier1_ratio = tier1_capital / total_rwa if total_rwa > 0 else 0
        total_capital_ratio = total_capital / total_rwa if total_rwa > 0 else 0
        tier1_leverage_ratio = (
            tier1_capital / portfolio_data.get("total_exposure", 1)
            if portfolio_data.get("total_exposure", 0) > 0
            else 0
        )
        basel_iii_report = {
            "capital_adequacy": {
                "cet1_capital": cet1_capital,
                "tier1_capital": tier1_capital,
                "total_capital": total_capital,
                "risk_weighted_assets": total_rwa,
                "cet1_ratio": cet1_ratio,
                "tier1_ratio": tier1_ratio,
                "total_capital_ratio": total_capital_ratio,
                "minimum_cet1_ratio": 0.045,
                "minimum_tier1_ratio": 0.06,
                "minimum_total_capital_ratio": 0.08,
            },
            "leverage_ratio": {
                "tier1_capital": tier1_capital,
                "total_exposure": portfolio_data.get("total_exposure", 0),
                "leverage_ratio": tier1_leverage_ratio,
                "minimum_leverage_ratio": 0.03,
            },
            "capital_buffers": {
                "capital_conservation_buffer": 0.025,
                "countercyclical_buffer": capital_data.get("countercyclical_buffer", 0),
                "systemic_risk_buffer": capital_data.get("systemic_risk_buffer", 0),
                "total_buffer_requirement": 0.025
                + capital_data.get("countercyclical_buffer", 0)
                + capital_data.get("systemic_risk_buffer", 0),
            },
            "risk_weighted_assets_breakdown": {
                "credit_risk_rwa": sum(
                    (
                        pos.get("market_value", 0) * self._get_basel_risk_weight(pos)
                        for pos in positions
                        if pos.get("risk_type") == "credit"
                    )
                ),
                "market_risk_rwa": sum(
                    (
                        pos.get("market_value", 0) * self._get_basel_risk_weight(pos)
                        for pos in positions
                        if pos.get("risk_type") == "market"
                    )
                ),
                "operational_risk_rwa": capital_data.get("operational_risk_rwa", 0),
            },
        }
        return basel_iii_report

    def _generate_stress_test_results(
        self, report_data: Dict[str, Any], requirement: ReportingRequirement
    ) -> Dict[str, Any]:
        """Generate stress test results report

        Args:
            report_data: Collected report data
            requirement: Reporting requirement

        Returns:
            Stress test results report
        """
        stress_test_data = report_data.get("stress_test_data", {})
        portfolio_data = report_data.get("portfolio_data", {})
        base_portfolio_value = sum(
            (pos.get("market_value", 0) for pos in portfolio_data.get("positions", []))
        )
        stress_test_report = {
            "base_case": {
                "portfolio_value": base_portfolio_value,
                "var_95": stress_test_data.get("base_var_95", 0),
                "expected_shortfall": stress_test_data.get(
                    "base_expected_shortfall", 0
                ),
                "leverage_ratio": stress_test_data.get("base_leverage_ratio", 0),
            },
            "adverse_scenario": {
                "scenario_description": "Moderate economic downturn with increased market volatility",
                "portfolio_value_change": stress_test_data.get(
                    "adverse_portfolio_change", -0.15
                ),
                "portfolio_value_stressed": base_portfolio_value
                * (1 + stress_test_data.get("adverse_portfolio_change", -0.15)),
                "var_95_stressed": stress_test_data.get("adverse_var_95", 0),
                "expected_shortfall_stressed": stress_test_data.get(
                    "adverse_expected_shortfall", 0
                ),
                "leverage_ratio_stressed": stress_test_data.get(
                    "adverse_leverage_ratio", 0
                ),
            },
            "severely_adverse_scenario": {
                "scenario_description": "Severe global recession with financial market disruption",
                "portfolio_value_change": stress_test_data.get(
                    "severe_portfolio_change", -0.35
                ),
                "portfolio_value_stressed": base_portfolio_value
                * (1 + stress_test_data.get("severe_portfolio_change", -0.35)),
                "var_95_stressed": stress_test_data.get("severe_var_95", 0),
                "expected_shortfall_stressed": stress_test_data.get(
                    "severe_expected_shortfall", 0
                ),
                "leverage_ratio_stressed": stress_test_data.get(
                    "severe_leverage_ratio", 0
                ),
            },
            "liquidity_stress": {
                "scenario_description": "Severe liquidity stress with limited market access",
                "liquid_assets_available": stress_test_data.get("liquid_assets", 0),
                "funding_requirements": stress_test_data.get("funding_requirements", 0),
                "liquidity_gap": stress_test_data.get("liquidity_gap", 0),
                "survival_period_days": stress_test_data.get("survival_period_days", 0),
            },
            "sensitivity_analysis": {
                "interest_rate_shock": {
                    "up_200bp": stress_test_data.get("ir_shock_up_200bp", 0),
                    "down_200bp": stress_test_data.get("ir_shock_down_200bp", 0),
                },
                "equity_shock": {
                    "down_30pct": stress_test_data.get("equity_shock_down_30pct", 0),
                    "down_50pct": stress_test_data.get("equity_shock_down_50pct", 0),
                },
                "credit_spread_shock": {
                    "up_300bp": stress_test_data.get("credit_spread_shock_300bp", 0)
                },
                "fx_shock": {
                    "major_currencies_15pct": stress_test_data.get("fx_shock_15pct", 0)
                },
            },
        }
        return stress_test_report

    def _generate_risk_metrics_report(
        self, report_data: Dict[str, Any], requirement: ReportingRequirement
    ) -> Dict[str, Any]:
        """Generate comprehensive risk metrics report

        Args:
            report_data: Collected report data
            requirement: Reporting requirement

        Returns:
            Risk metrics report
        """
        risk_data = report_data.get("risk_data", {})
        portfolio_data = report_data.get("portfolio_data", {})
        risk_metrics_report = {
            "market_risk": {
                "var_95_1day": risk_data.get("var_95_1day", 0),
                "var_99_1day": risk_data.get("var_99_1day", 0),
                "var_95_10day": risk_data.get("var_95_10day", 0),
                "expected_shortfall_95": risk_data.get("expected_shortfall_95", 0),
                "expected_shortfall_99": risk_data.get("expected_shortfall_99", 0),
                "maximum_drawdown": risk_data.get("maximum_drawdown", 0),
                "volatility_annualized": risk_data.get("volatility_annualized", 0),
                "beta_to_market": risk_data.get("beta_to_market", 0),
                "correlation_to_market": risk_data.get("correlation_to_market", 0),
            },
            "credit_risk": {
                "total_credit_exposure": risk_data.get("total_credit_exposure", 0),
                "expected_credit_loss": risk_data.get("expected_credit_loss", 0),
                "credit_var_95": risk_data.get("credit_var_95", 0),
                "default_probability": risk_data.get("default_probability", 0),
                "recovery_rate": risk_data.get("recovery_rate", 0.4),
                "concentration_risk": risk_data.get("concentration_risk", 0),
            },
            "liquidity_risk": {
                "liquidity_coverage_ratio": risk_data.get(
                    "liquidity_coverage_ratio", 0
                ),
                "net_stable_funding_ratio": risk_data.get(
                    "net_stable_funding_ratio", 0
                ),
                "liquid_assets_ratio": risk_data.get("liquid_assets_ratio", 0),
                "funding_concentration": risk_data.get("funding_concentration", 0),
                "maturity_mismatch": risk_data.get("maturity_mismatch", 0),
            },
            "operational_risk": {
                "operational_var": risk_data.get("operational_var", 0),
                "key_risk_indicators": risk_data.get("key_risk_indicators", {}),
                "loss_events": risk_data.get("loss_events", []),
                "control_effectiveness": risk_data.get("control_effectiveness", 0),
            },
            "concentration_risk": {
                "single_name_concentration": self._calculate_single_name_concentration(
                    portfolio_data.get("positions", [])
                ),
                "sector_concentration": self._calculate_sector_concentrations(
                    portfolio_data.get("positions", [])
                ),
                "geographic_concentration": self._calculate_geographic_concentrations(
                    portfolio_data.get("positions", [])
                ),
                "currency_concentration": self._calculate_currency_concentrations(
                    portfolio_data.get("positions", [])
                ),
            },
            "performance_metrics": {
                "sharpe_ratio": risk_data.get("sharpe_ratio", 0),
                "sortino_ratio": risk_data.get("sortino_ratio", 0),
                "calmar_ratio": risk_data.get("calmar_ratio", 0),
                "information_ratio": risk_data.get("information_ratio", 0),
                "tracking_error": risk_data.get("tracking_error", 0),
                "alpha": risk_data.get("alpha", 0),
            },
        }
        return risk_metrics_report

    def _generate_portfolio_composition(
        self, report_data: Dict[str, Any], requirement: ReportingRequirement
    ) -> Dict[str, Any]:
        """Generate portfolio composition report

        Args:
            report_data: Collected report data
            requirement: Reporting requirement

        Returns:
            Portfolio composition report
        """
        portfolio_data = report_data.get("portfolio_data", {})
        positions = portfolio_data.get("positions", [])
        total_value = sum((pos.get("market_value", 0) for pos in positions))
        asset_classes = {}
        for pos in positions:
            asset_class = pos.get("asset_class", "unknown")
            if asset_class not in asset_classes:
                asset_classes[asset_class] = {"value": 0, "count": 0}
            asset_classes[asset_class]["value"] += pos.get("market_value", 0)
            asset_classes[asset_class]["count"] += 1
        for asset_class in asset_classes:
            asset_classes[asset_class]["percentage"] = (
                asset_classes[asset_class]["value"] / total_value
                if total_value > 0
                else 0
            )
        sorted_positions = sorted(
            positions, key=lambda x: x.get("market_value", 0), reverse=True
        )
        top_holdings = []
        for pos in sorted_positions[:20]:
            top_holdings.append(
                {
                    "symbol": pos.get("symbol", ""),
                    "name": pos.get("name", ""),
                    "market_value": pos.get("market_value", 0),
                    "percentage": (
                        pos.get("market_value", 0) / total_value
                        if total_value > 0
                        else 0
                    ),
                    "asset_class": pos.get("asset_class", ""),
                    "sector": pos.get("sector", ""),
                    "country": pos.get("country", ""),
                }
            )
        portfolio_composition_report = {
            "summary": {
                "total_portfolio_value": total_value,
                "number_of_positions": len(positions),
                "reporting_date": report_data["period_end"],
            },
            "asset_class_breakdown": asset_classes,
            "sector_breakdown": self._calculate_sector_concentrations(positions),
            "geographic_breakdown": self._calculate_geographic_concentrations(
                positions
            ),
            "currency_breakdown": self._calculate_currency_concentrations(positions),
            "top_holdings": top_holdings,
            "risk_statistics": {
                "portfolio_beta": portfolio_data.get("portfolio_beta", 0),
                "portfolio_volatility": portfolio_data.get("portfolio_volatility", 0),
                "active_share": portfolio_data.get("active_share", 0),
                "tracking_error": portfolio_data.get("tracking_error", 0),
            },
        }
        return portfolio_composition_report

    def _generate_liquidity_coverage_ratio(
        self, report_data: Dict[str, Any], requirement: ReportingRequirement
    ) -> Dict[str, Any]:
        """Generate Liquidity Coverage Ratio (LCR) report

        Args:
            report_data: Collected report data
            requirement: Reporting requirement

        Returns:
            LCR report
        """
        liquidity_data = report_data.get("liquidity_data", {})
        report_data.get("portfolio_data", {})
        hqla_level_1 = liquidity_data.get("hqla_level_1", 0)
        hqla_level_2a = liquidity_data.get("hqla_level_2a", 0)
        hqla_level_2b = liquidity_data.get("hqla_level_2b", 0)
        adjusted_hqla_level_2a = hqla_level_2a * 0.85
        adjusted_hqla_level_2b = hqla_level_2b * 0.5
        level_2_cap = hqla_level_1 * 0.67
        level_2b_cap = (hqla_level_1 + adjusted_hqla_level_2a) * 0.176
        effective_level_2a = min(adjusted_hqla_level_2a, level_2_cap)
        effective_level_2b = min(adjusted_hqla_level_2b, level_2b_cap)
        total_hqla = hqla_level_1 + effective_level_2a + effective_level_2b
        retail_deposits = liquidity_data.get("retail_deposits", 0)
        wholesale_deposits = liquidity_data.get("wholesale_deposits", 0)
        secured_funding = liquidity_data.get("secured_funding", 0)
        derivatives_outflows = liquidity_data.get("derivatives_outflows", 0)
        credit_facilities = liquidity_data.get("credit_facilities", 0)
        other_outflows = liquidity_data.get("other_outflows", 0)
        retail_outflows = retail_deposits * 0.05
        wholesale_outflows = wholesale_deposits * 0.25
        secured_funding_outflows = secured_funding * 0.0
        total_outflows = (
            retail_outflows
            + wholesale_outflows
            + secured_funding_outflows
            + derivatives_outflows
            + credit_facilities
            + other_outflows
        )
        contractual_inflows = liquidity_data.get("contractual_inflows", 0)
        capped_inflows = min(contractual_inflows, total_outflows * 0.75)
        net_cash_outflows = max(total_outflows - capped_inflows, total_outflows * 0.25)
        lcr = total_hqla / net_cash_outflows if net_cash_outflows > 0 else float("inf")
        lcr_report = {
            "high_quality_liquid_assets": {
                "level_1_assets": hqla_level_1,
                "level_2a_assets": hqla_level_2a,
                "level_2a_adjusted": effective_level_2a,
                "level_2b_assets": hqla_level_2b,
                "level_2b_adjusted": effective_level_2b,
                "total_hqla": total_hqla,
            },
            "cash_outflows": {
                "retail_deposits": retail_deposits,
                "retail_outflows": retail_outflows,
                "wholesale_deposits": wholesale_deposits,
                "wholesale_outflows": wholesale_outflows,
                "secured_funding": secured_funding,
                "secured_funding_outflows": secured_funding_outflows,
                "derivatives_outflows": derivatives_outflows,
                "credit_facilities": credit_facilities,
                "other_outflows": other_outflows,
                "total_outflows": total_outflows,
            },
            "cash_inflows": {
                "contractual_inflows": contractual_inflows,
                "capped_inflows": capped_inflows,
            },
            "lcr_calculation": {
                "net_cash_outflows": net_cash_outflows,
                "liquidity_coverage_ratio": lcr,
                "minimum_requirement": 1.0,
                "compliance_status": "compliant" if lcr >= 1.0 else "non_compliant",
            },
        }
        return lcr_report

    def _generate_generic_report(
        self, report_data: Dict[str, Any], requirement: ReportingRequirement
    ) -> Dict[str, Any]:
        """Generate a generic regulatory report

        Args:
            report_data: Collected report data
            requirement: Reporting requirement

        Returns:
            Generic report
        """
        return {
            "report_type": requirement.report_type.value,
            "jurisdiction": requirement.jurisdiction.value,
            "reporting_period": {
                "start": report_data["period_start"],
                "end": report_data["period_end"],
            },
            "data": report_data,
            "compliance_status": "pending_review",
        }

    def _initialize_reporting_requirements(self) -> Dict[str, ReportingRequirement]:
        """Initialize regulatory reporting requirements"""
        requirements = {}
        requirements["form_pf_us_sec"] = ReportingRequirement(
            report_type=ReportType.FORM_PF,
            jurisdiction=RegulatoryJurisdiction.US_SEC,
            frequency="quarterly",
            deadline_days=60,
            mandatory_fields=["fund_name", "aum", "leverage_ratio", "var"],
            optional_fields=["stress_test_results", "liquidity_metrics"],
            validation_rules={"aum": {"min": 0}, "leverage_ratio": {"min": 0}},
            format_requirements={"file_format": "xml", "schema_version": "2.0"},
        )
        requirements["form_13f_us_sec"] = ReportingRequirement(
            report_type=ReportType.FORM_13F,
            jurisdiction=RegulatoryJurisdiction.US_SEC,
            frequency="quarterly",
            deadline_days=45,
            mandatory_fields=["institution_name", "holdings_value", "holdings_list"],
            optional_fields=["other_managers"],
            validation_rules={"holdings_value": {"min": 100000000}},
            format_requirements={"file_format": "xml", "schema_version": "1.0"},
        )
        requirements["basel_iii_capital_adequacy"] = ReportingRequirement(
            report_type=ReportType.BASEL_III_CAPITAL_ADEQUACY,
            jurisdiction=RegulatoryJurisdiction.BASEL_COMMITTEE,
            frequency="quarterly",
            deadline_days=30,
            mandatory_fields=[
                "cet1_ratio",
                "tier1_ratio",
                "total_capital_ratio",
                "leverage_ratio",
            ],
            optional_fields=["capital_buffers", "stress_test_results"],
            validation_rules={
                "cet1_ratio": {"min": 0.045},
                "tier1_ratio": {"min": 0.06},
                "total_capital_ratio": {"min": 0.08},
                "leverage_ratio": {"min": 0.03},
            },
            format_requirements={"file_format": "csv", "decimal_places": 4},
        )
        return requirements

    def _initialize_report_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize report templates"""
        return {
            "form_pf": {
                "sections": [
                    "fund_information",
                    "leverage_information",
                    "liquidity_information",
                    "risk_metrics",
                ],
                "required_calculations": ["leverage_ratio", "var", "liquidity_ratio"],
            },
            "form_13f": {
                "sections": ["cover_page", "summary_page", "information_table"],
                "required_calculations": ["total_value", "holdings_count"],
            },
        }

    def _initialize_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize validation rules"""
        return {
            "numeric_ranges": {
                "leverage_ratio": {"min": 0, "max": 10},
                "var": {"min": 0, "max": 1},
                "capital_ratio": {"min": 0, "max": 1},
            },
            "required_fields": {
                "form_pf": ["fund_name", "aum", "leverage_ratio"],
                "form_13f": ["institution_name", "total_value"],
            },
        }

    def _validate_report_request(
        self,
        report_type: str,
        jurisdiction: str,
        period_start: datetime,
        period_end: datetime,
    ) -> None:
        """Validate report generation request"""
        if not report_type:
            raise ValidationError("Report type is required")
        if not jurisdiction:
            raise ValidationError("Jurisdiction is required")
        if period_start >= period_end:
            raise ValidationError("Period start must be before period end")
        requirement_key = f"{report_type}_{jurisdiction}"
        if requirement_key not in self.reporting_requirements:
            logger.warning(
                f"No specific requirement found for {requirement_key}, using generic template"
            )

    def _get_reporting_requirement(
        self, report_type: str, jurisdiction: str
    ) -> ReportingRequirement:
        """Get reporting requirement for report type and jurisdiction"""
        requirement_key = f"{report_type}_{jurisdiction}"
        if requirement_key in self.reporting_requirements:
            return self.reporting_requirements[requirement_key]
        return ReportingRequirement(
            report_type=ReportType(report_type),
            jurisdiction=RegulatoryJurisdiction(jurisdiction),
            frequency="quarterly",
            deadline_days=30,
            mandatory_fields=[],
            optional_fields=[],
            validation_rules={},
            format_requirements={},
        )

    def _collect_report_data(
        self,
        requirement: ReportingRequirement,
        period_start: datetime,
        period_end: datetime,
        portfolio_data: Optional[Dict[str, Any]],
        additional_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Collect data required for report generation"""
        report_data = {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "portfolio_data": portfolio_data or {},
            "additional_data": additional_data or {},
        }
        if not portfolio_data:
            report_data["portfolio_data"] = self._generate_mock_portfolio_data()
        report_data["risk_data"] = self._generate_mock_risk_data()
        if requirement.report_type == ReportType.BASEL_III_CAPITAL_ADEQUACY:
            report_data["capital_data"] = self._generate_mock_capital_data()
        if requirement.report_type == ReportType.STRESS_TEST_RESULTS:
            report_data["stress_test_data"] = self._generate_mock_stress_test_data()
        if requirement.report_type == ReportType.LIQUIDITY_COVERAGE_RATIO:
            report_data["liquidity_data"] = self._generate_mock_liquidity_data()
        return report_data

    def _generate_mock_portfolio_data(self) -> Dict[str, Any]:
        """Generate mock portfolio data for demonstration"""
        return {
            "fund_name": "QuantumAlpha Hedge Fund",
            "fund_type": "hedge_fund",
            "institution_name": "QuantumAlpha Management LLC",
            "investor_count": 150,
            "redemption_frequency": "monthly",
            "notice_period_days": 30,
            "borrowing_amount": 50000000,
            "total_exposure": 500000000,
            "positions": [
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "market_value": 25000000,
                    "quantity": 100000,
                    "asset_class": "equity",
                    "asset_type": "equity",
                    "sector": "technology",
                    "country": "US",
                    "currency": "USD",
                    "liquidity_category": "daily",
                    "cusip": "037833100",
                },
                {
                    "symbol": "MSFT",
                    "name": "Microsoft Corporation",
                    "market_value": 20000000,
                    "quantity": 80000,
                    "asset_class": "equity",
                    "asset_type": "equity",
                    "sector": "technology",
                    "country": "US",
                    "currency": "USD",
                    "liquidity_category": "daily",
                    "cusip": "594918104",
                },
                {
                    "symbol": "AGG",
                    "name": "iShares Core U.S. Aggregate Bond ETF",
                    "market_value": 15000000,
                    "quantity": 150000,
                    "asset_class": "fixed_income",
                    "asset_type": "etf",
                    "sector": "fixed_income",
                    "country": "US",
                    "currency": "USD",
                    "liquidity_category": "daily",
                    "cusip": "464287200",
                },
            ],
        }

    def _generate_mock_risk_data(self) -> Dict[str, Any]:
        """Generate mock risk data for demonstration"""
        return {
            "var_95_1day": 2500000,
            "var_99_1day": 3500000,
            "var_95_10day": 7500000,
            "expected_shortfall_95": 3000000,
            "expected_shortfall_99": 4200000,
            "maximum_drawdown": 0.12,
            "volatility_annualized": 0.18,
            "sharpe_ratio": 1.25,
            "sortino_ratio": 1.45,
            "beta_to_market": 0.85,
            "correlation_to_market": 0.75,
            "total_credit_exposure": 100000000,
            "expected_credit_loss": 500000,
            "credit_var_95": 2000000,
            "liquidity_coverage_ratio": 1.15,
            "net_stable_funding_ratio": 1.05,
        }

    def _generate_mock_capital_data(self) -> Dict[str, Any]:
        """Generate mock capital data for Basel III reports"""
        return {
            "cet1_capital": 80000000,
            "tier1_capital": 85000000,
            "total_capital": 95000000,
            "countercyclical_buffer": 0.01,
            "systemic_risk_buffer": 0.005,
            "operational_risk_rwa": 50000000,
        }

    def _generate_mock_stress_test_data(self) -> Dict[str, Any]:
        """Generate mock stress test data"""
        return {
            "base_var_95": 2500000,
            "base_expected_shortfall": 3000000,
            "base_leverage_ratio": 0.15,
            "adverse_portfolio_change": -0.15,
            "adverse_var_95": 3500000,
            "adverse_expected_shortfall": 4200000,
            "adverse_leverage_ratio": 0.18,
            "severe_portfolio_change": -0.35,
            "severe_var_95": 6000000,
            "severe_expected_shortfall": 7500000,
            "severe_leverage_ratio": 0.25,
            "liquid_assets": 50000000,
            "funding_requirements": 30000000,
            "liquidity_gap": -20000000,
            "survival_period_days": 45,
        }

    def _generate_mock_liquidity_data(self) -> Dict[str, Any]:
        """Generate mock liquidity data for LCR reports"""
        return {
            "hqla_level_1": 100000000,
            "hqla_level_2a": 50000000,
            "hqla_level_2b": 25000000,
            "retail_deposits": 200000000,
            "wholesale_deposits": 150000000,
            "secured_funding": 75000000,
            "derivatives_outflows": 10000000,
            "credit_facilities": 25000000,
            "other_outflows": 5000000,
            "contractual_inflows": 30000000,
        }

    def _calculate_sector_concentrations(
        self, positions: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate sector concentrations"""
        total_value = sum((pos.get("market_value", 0) for pos in positions))
        sectors = {}
        for pos in positions:
            sector = pos.get("sector", "unknown")
            if sector not in sectors:
                sectors[sector] = 0
            sectors[sector] += pos.get("market_value", 0)
        for sector in sectors:
            sectors[sector] = sectors[sector] / total_value if total_value > 0 else 0
        return sectors

    def _calculate_geographic_concentrations(
        self, positions: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate geographic concentrations"""
        total_value = sum((pos.get("market_value", 0) for pos in positions))
        countries = {}
        for pos in positions:
            country = pos.get("country", "unknown")
            if country not in countries:
                countries[country] = 0
            countries[country] += pos.get("market_value", 0)
        for country in countries:
            countries[country] = (
                countries[country] / total_value if total_value > 0 else 0
            )
        return countries

    def _calculate_currency_concentrations(
        self, positions: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate currency concentrations"""
        total_value = sum((pos.get("market_value", 0) for pos in positions))
        currencies = {}
        for pos in positions:
            currency = pos.get("currency", "USD")
            if currency not in currencies:
                currencies[currency] = 0
            currencies[currency] += pos.get("market_value", 0)
        for currency in currencies:
            currencies[currency] = (
                currencies[currency] / total_value if total_value > 0 else 0
            )
        return currencies

    def _calculate_single_name_concentration(
        self, positions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate single name concentration metrics"""
        total_value = sum((pos.get("market_value", 0) for pos in positions))
        if not positions or total_value == 0:
            return {
                "largest_position": 0,
                "top_5_concentration": 0,
                "top_10_concentration": 0,
            }
        sorted_positions = sorted(
            positions, key=lambda x: x.get("market_value", 0), reverse=True
        )
        largest_position = sorted_positions[0].get("market_value", 0) / total_value
        top_5_concentration = (
            sum((pos.get("market_value", 0) for pos in sorted_positions[:5]))
            / total_value
        )
        top_10_concentration = (
            sum((pos.get("market_value", 0) for pos in sorted_positions[:10]))
            / total_value
        )
        return {
            "largest_position": largest_position,
            "top_5_concentration": top_5_concentration,
            "top_10_concentration": top_10_concentration,
        }

    def _calculate_counterparty_exposures(
        self, positions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate counterparty exposures"""
        counterparties = {}
        for pos in positions:
            counterparty = pos.get("counterparty", "unknown")
            if counterparty not in counterparties:
                counterparties[counterparty] = {"exposure": 0, "positions": 0}
            counterparties[counterparty]["exposure"] += pos.get("market_value", 0)
            counterparties[counterparty]["positions"] += 1
        exposures = []
        for counterparty, data in counterparties.items():
            exposures.append(
                {
                    "counterparty": counterparty,
                    "exposure": data["exposure"],
                    "positions": data["positions"],
                }
            )
        return sorted(exposures, key=lambda x: x["exposure"], reverse=True)

    def _get_basel_risk_weight(self, position: Dict[str, Any]) -> float:
        """Get Basel III risk weight for a position"""
        asset_type = position.get("asset_type", "equity")
        position.get("credit_rating", "unrated")
        risk_weights = {
            "government_bond": 0.0,
            "corporate_bond_aaa": 0.2,
            "corporate_bond_aa": 0.5,
            "corporate_bond_a": 0.5,
            "corporate_bond_bbb": 1.0,
            "corporate_bond_below_bbb": 1.5,
            "equity": 1.0,
            "derivative": 1.0,
            "cash": 0.0,
        }
        return risk_weights.get(asset_type, 1.0)

    def _validate_report(
        self, report: Dict[str, Any], requirement: ReportingRequirement
    ) -> Dict[str, Any]:
        """Validate generated report"""
        validation_result = {"is_valid": True, "errors": [], "warnings": []}
        for field in requirement.mandatory_fields:
            if not self._check_field_exists(report, field):
                validation_result["errors"].append(f"Missing mandatory field: {field}")
                validation_result["is_valid"] = False
        for field, rules in requirement.validation_rules.items():
            value = self._get_field_value(report, field)
            if value is not None:
                if "min" in rules and value < rules["min"]:
                    validation_result["errors"].append(
                        f"Field {field} below minimum: {value} < {rules['min']}"
                    )
                    validation_result["is_valid"] = False
                if "max" in rules and value > rules["max"]:
                    validation_result["errors"].append(
                        f"Field {field} above maximum: {value} > {rules['max']}"
                    )
                    validation_result["is_valid"] = False
        return validation_result

    def _check_field_exists(self, report: Dict[str, Any], field_path: str) -> bool:
        """Check if a field exists in the report"""
        try:
            keys = field_path.split(".")
            current = report
            for key in keys:
                if key in current:
                    current = current[key]
                else:
                    return False
            return True
        except Exception:
            return False

    def _get_field_value(self, report: Dict[str, Any], field_path: str) -> object:
        """Get field value from report"""
        try:
            keys = field_path.split(".")
            current = report
            for key in keys:
                current = current[key]
            return current
        except Exception:
            return None

    def _save_report(
        self, report: Dict[str, Any], report_type: str, jurisdiction: str
    ) -> str:
        """Save report to storage"""
        try:
            report_id = f"report_{uuid.uuid4().hex}"
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_type}_{jurisdiction}_{timestamp}_{report_id}.json"
            filepath = os.path.join(self.report_storage_path, filename)
            with open(filepath, "w") as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Report saved: {filepath}")
            return report_id
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            raise ServiceError(f"Error saving report: {str(e)}")

    def get_report(self, report_id: str) -> Dict[str, Any]:
        """Retrieve a saved report

        Args:
            report_id: Report ID

        Returns:
            Report data

        Raises:
            NotFoundError: If report is not found
        """
        try:
            for filename in os.listdir(self.report_storage_path):
                if report_id in filename:
                    filepath = os.path.join(self.report_storage_path, filename)
                    with open(filepath, "r") as f:
                        return json.load(f)
            raise NotFoundError(f"Report not found: {report_id}")
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving report: {e}")
            raise ServiceError(f"Error retrieving report: {str(e)}")

    def list_reports(
        self,
        report_type: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """List saved reports with optional filters

        Args:
            report_type: Filter by report type
            jurisdiction: Filter by jurisdiction
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            List of report metadata
        """
        try:
            reports = []
            for filename in os.listdir(self.report_storage_path):
                if filename.endswith(".json"):
                    parts = filename.replace(".json", "").split("_")
                    if len(parts) >= 4:
                        file_report_type = parts[0]
                        file_jurisdiction = parts[1]
                        file_timestamp = parts[2]
                        file_report_id = "_".join(parts[3:])
                        if report_type and file_report_type != report_type:
                            continue
                        if jurisdiction and file_jurisdiction != jurisdiction:
                            continue
                        try:
                            file_date = datetime.strptime(
                                file_timestamp, "%Y%m%d_%H%M%S"
                            )
                            if start_date and file_date < start_date:
                                continue
                            if end_date and file_date > end_date:
                                continue
                        except Exception:
                            continue
                        reports.append(
                            {
                                "report_id": file_report_id,
                                "report_type": file_report_type,
                                "jurisdiction": file_jurisdiction,
                                "generated_at": file_date.isoformat(),
                                "filename": filename,
                            }
                        )
            reports.sort(key=lambda x: x["generated_at"], reverse=True)
            return reports
        except Exception as e:
            logger.error(f"Error listing reports: {e}")
            raise ServiceError(f"Error listing reports: {str(e)}")
