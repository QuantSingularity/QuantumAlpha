"""
Performance attribution module for QuantumAlpha Analytics Service.
Provides detailed performance attribution and decomposition analysis.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from backend.common import ServiceError, ValidationError, setup_logger

logger = setup_logger("performance_attribution", logging.INFO)


class AttributionMethod(Enum):
    """Performance attribution methods"""

    BRINSON_HOOD_BEEBOWER = "brinson_hood_beebower"
    BRINSON_FACHLER = "brinson_fachler"
    GEOMETRIC_ATTRIBUTION = "geometric_attribution"
    ARITHMETIC_ATTRIBUTION = "arithmetic_attribution"
    FACTOR_BASED = "factor_based"
    RISK_ADJUSTED = "risk_adjusted"


class AttributionLevel(Enum):
    """Attribution analysis levels"""

    SECURITY = "security"
    SECTOR = "sector"
    ASSET_CLASS = "asset_class"
    GEOGRAPHY = "geography"
    CURRENCY = "currency"
    FACTOR = "factor"


@dataclass
class AttributionResult:
    """Performance attribution result"""

    total_return: float
    benchmark_return: float
    active_return: float
    allocation_effect: float
    selection_effect: float
    interaction_effect: float
    currency_effect: Optional[float] = None
    timing_effect: Optional[float] = None
    detailed_breakdown: Optional[Dict[str, Any]] = None


@dataclass
class SecurityAttribution:
    """Security-level attribution"""

    security_id: str
    security_name: str
    weight_portfolio: float
    weight_benchmark: float
    return_portfolio: float
    return_benchmark: float
    allocation_contribution: float
    selection_contribution: float
    total_contribution: float


class PerformanceAttributionEngine:
    """Comprehensive performance attribution engine"""

    def __init__(self, config_manager: Any, db_manager: Any) -> None:
        """Initialize performance attribution engine

        Args:
            config_manager: Configuration manager
            db_manager: Database manager
        """
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.default_method = AttributionMethod.BRINSON_HOOD_BEEBOWER
        self.default_frequency = "daily"
        self.risk_free_rate = 0.02
        self.factor_models = {}
        self._initialize_factor_models()
        logger.info("Performance attribution engine initialized")

    def calculate_attribution(
        self,
        portfolio_returns: pd.DataFrame,
        benchmark_returns: pd.DataFrame,
        portfolio_weights: pd.DataFrame,
        benchmark_weights: pd.DataFrame,
        method: str = "brinson_hood_beebower",
        level: str = "sector",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Calculate performance attribution

        Args:
            portfolio_returns: Portfolio returns data
            benchmark_returns: Benchmark returns data
            portfolio_weights: Portfolio weights data
            benchmark_weights: Benchmark weights data
            method: Attribution method
            level: Attribution level
            start_date: Analysis start date
            end_date: Analysis end date

        Returns:
            Attribution analysis results
        """
        try:
            logger.info(
                f"Calculating attribution using {method} method at {level} level"
            )
            self._validate_attribution_inputs(
                portfolio_returns,
                benchmark_returns,
                portfolio_weights,
                benchmark_weights,
            )
            if start_date or end_date:
                (
                    portfolio_returns,
                    benchmark_returns,
                    portfolio_weights,
                    benchmark_weights,
                ) = self._filter_by_date_range(
                    portfolio_returns,
                    benchmark_returns,
                    portfolio_weights,
                    benchmark_weights,
                    start_date,
                    end_date,
                )
            if method == AttributionMethod.BRINSON_HOOD_BEEBOWER.value:
                result = self._calculate_brinson_hood_beebower(
                    portfolio_returns,
                    benchmark_returns,
                    portfolio_weights,
                    benchmark_weights,
                    level,
                )
            elif method == AttributionMethod.BRINSON_FACHLER.value:
                result = self._calculate_brinson_fachler(
                    portfolio_returns,
                    benchmark_returns,
                    portfolio_weights,
                    benchmark_weights,
                    level,
                )
            elif method == AttributionMethod.GEOMETRIC_ATTRIBUTION.value:
                result = self._calculate_geometric_attribution(
                    portfolio_returns,
                    benchmark_returns,
                    portfolio_weights,
                    benchmark_weights,
                    level,
                )
            elif method == AttributionMethod.FACTOR_BASED.value:
                result = self._calculate_factor_based_attribution(
                    portfolio_returns,
                    benchmark_returns,
                    portfolio_weights,
                    benchmark_weights,
                    level,
                )
            else:
                result = self._calculate_arithmetic_attribution(
                    portfolio_returns,
                    benchmark_returns,
                    portfolio_weights,
                    benchmark_weights,
                    level,
                )
            result["method"] = method
            result["level"] = level
            result["period"] = {
                "start": (
                    portfolio_returns.index[0].isoformat()
                    if len(portfolio_returns) > 0
                    else None
                ),
                "end": (
                    portfolio_returns.index[-1].isoformat()
                    if len(portfolio_returns) > 0
                    else None
                ),
            }
            result["calculated_at"] = datetime.utcnow().isoformat()
            return result
        except Exception as e:
            logger.error(f"Error calculating attribution: {e}")
            raise ServiceError(f"Error calculating attribution: {str(e)}")

    def calculate_multi_period_attribution(
        self,
        portfolio_returns: pd.DataFrame,
        benchmark_returns: pd.DataFrame,
        portfolio_weights: pd.DataFrame,
        benchmark_weights: pd.DataFrame,
        periods: List[Tuple[datetime, datetime]],
        method: str = "brinson_hood_beebower",
        level: str = "sector",
    ) -> Dict[str, Any]:
        """Calculate attribution across multiple periods

        Args:
            portfolio_returns: Portfolio returns data
            benchmark_returns: Benchmark returns data
            portfolio_weights: Portfolio weights data
            benchmark_weights: Benchmark weights data
            periods: List of (start_date, end_date) tuples
            method: Attribution method
            level: Attribution level

        Returns:
            Multi-period attribution results
        """
        try:
            logger.info(
                f"Calculating multi-period attribution for {len(periods)} periods"
            )
            period_results = []
            for i, (start_date, end_date) in enumerate(periods):
                try:
                    period_result = self.calculate_attribution(
                        portfolio_returns,
                        benchmark_returns,
                        portfolio_weights,
                        benchmark_weights,
                        method,
                        level,
                        start_date,
                        end_date,
                    )
                    period_result["period_index"] = i
                    period_result["period_start"] = start_date.isoformat()
                    period_result["period_end"] = end_date.isoformat()
                    period_results.append(period_result)
                except Exception as e:
                    logger.warning(f"Error calculating attribution for period {i}: {e}")
                    period_results.append(
                        {
                            "period_index": i,
                            "period_start": start_date.isoformat(),
                            "period_end": end_date.isoformat(),
                            "error": str(e),
                        }
                    )
            valid_results = [r for r in period_results if "error" not in r]
            if valid_results:
                aggregate_stats = self._calculate_aggregate_attribution_stats(
                    valid_results
                )
            else:
                aggregate_stats = {}
            return {
                "period_results": period_results,
                "aggregate_statistics": aggregate_stats,
                "method": method,
                "level": level,
                "total_periods": len(periods),
                "successful_periods": len(valid_results),
                "calculated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error calculating multi-period attribution: {e}")
            raise ServiceError(f"Error calculating multi-period attribution: {str(e)}")

    def calculate_security_level_attribution(
        self,
        portfolio_data: Dict[str, Any],
        benchmark_data: Dict[str, Any],
        returns_data: Dict[str, pd.DataFrame],
        period_start: datetime,
        period_end: datetime,
    ) -> Dict[str, Any]:
        """Calculate security-level performance attribution

        Args:
            portfolio_data: Portfolio holdings data
            benchmark_data: Benchmark holdings data
            returns_data: Security returns data
            period_start: Analysis start date
            period_end: Analysis end date

        Returns:
            Security-level attribution results
        """
        try:
            logger.info("Calculating security-level attribution")
            security_attributions = []
            total_allocation_effect = 0
            total_selection_effect = 0
            portfolio_securities = set(portfolio_data.get("holdings", {}).keys())
            benchmark_securities = set(benchmark_data.get("holdings", {}).keys())
            all_securities = portfolio_securities.union(benchmark_securities)
            for security_id in all_securities:
                try:
                    portfolio_weight = (
                        portfolio_data.get("holdings", {})
                        .get(security_id, {})
                        .get("weight", 0)
                    )
                    benchmark_weight = (
                        benchmark_data.get("holdings", {})
                        .get(security_id, {})
                        .get("weight", 0)
                    )
                    if security_id in returns_data:
                        security_returns = returns_data[security_id]
                        period_returns = security_returns.loc[period_start:period_end]
                        if len(period_returns) > 0:
                            portfolio_return = period_returns.get("portfolio_return", 0)
                            benchmark_return = period_returns.get("benchmark_return", 0)
                        else:
                            portfolio_return = 0
                            benchmark_return = 0
                    else:
                        portfolio_return = 0
                        benchmark_return = 0
                    allocation_contribution = (
                        portfolio_weight - benchmark_weight
                    ) * benchmark_return
                    selection_contribution = benchmark_weight * (
                        portfolio_return - benchmark_return
                    )
                    total_contribution = (
                        allocation_contribution + selection_contribution
                    )
                    security_attribution = SecurityAttribution(
                        security_id=security_id,
                        security_name=portfolio_data.get("holdings", {})
                        .get(security_id, {})
                        .get("name", security_id),
                        weight_portfolio=portfolio_weight,
                        weight_benchmark=benchmark_weight,
                        return_portfolio=portfolio_return,
                        return_benchmark=benchmark_return,
                        allocation_contribution=allocation_contribution,
                        selection_contribution=selection_contribution,
                        total_contribution=total_contribution,
                    )
                    security_attributions.append(security_attribution)
                    total_allocation_effect += allocation_contribution
                    total_selection_effect += selection_contribution
                except Exception as e:
                    logger.warning(
                        f"Error calculating attribution for security {security_id}: {e}"
                    )
            security_attributions.sort(
                key=lambda x: abs(x.total_contribution), reverse=True
            )
            portfolio_return = sum(
                (
                    attr.weight_portfolio * attr.return_portfolio
                    for attr in security_attributions
                )
            )
            benchmark_return = sum(
                (
                    attr.weight_benchmark * attr.return_benchmark
                    for attr in security_attributions
                )
            )
            return {
                "total_return": portfolio_return,
                "benchmark_return": benchmark_return,
                "active_return": portfolio_return - benchmark_return,
                "allocation_effect": total_allocation_effect,
                "selection_effect": total_selection_effect,
                "interaction_effect": 0,
                "security_attributions": [
                    {
                        "security_id": attr.security_id,
                        "security_name": attr.security_name,
                        "weight_portfolio": attr.weight_portfolio,
                        "weight_benchmark": attr.weight_benchmark,
                        "return_portfolio": attr.return_portfolio,
                        "return_benchmark": attr.return_benchmark,
                        "allocation_contribution": attr.allocation_contribution,
                        "selection_contribution": attr.selection_contribution,
                        "total_contribution": attr.total_contribution,
                    }
                    for attr in security_attributions
                ],
                "top_contributors": [
                    {
                        "security_id": attr.security_id,
                        "security_name": attr.security_name,
                        "contribution": attr.total_contribution,
                    }
                    for attr in security_attributions[:10]
                ],
                "top_detractors": [
                    {
                        "security_id": attr.security_id,
                        "security_name": attr.security_name,
                        "contribution": attr.total_contribution,
                    }
                    for attr in sorted(
                        security_attributions, key=lambda x: x.total_contribution
                    )[:10]
                ],
            }
        except Exception as e:
            logger.error(f"Error calculating security-level attribution: {e}")
            raise ServiceError(
                f"Error calculating security-level attribution: {str(e)}"
            )

    def _calculate_brinson_hood_beebower(
        self,
        portfolio_returns: pd.DataFrame,
        benchmark_returns: pd.DataFrame,
        portfolio_weights: pd.DataFrame,
        benchmark_weights: pd.DataFrame,
        level: str,
    ) -> Dict[str, Any]:
        """Calculate Brinson-Hood-Beebower attribution

        Args:
            portfolio_returns: Portfolio returns
            benchmark_returns: Benchmark returns
            portfolio_weights: Portfolio weights
            benchmark_weights: Benchmark weights
            level: Attribution level

        Returns:
            BHB attribution results
        """
        try:
            common_index = portfolio_returns.index.intersection(benchmark_returns.index)
            common_columns = portfolio_returns.columns.intersection(
                benchmark_returns.columns
            )
            if len(common_index) == 0 or len(common_columns) == 0:
                raise ValidationError("No common data between portfolio and benchmark")
            port_ret = portfolio_returns.loc[common_index, common_columns]
            bench_ret = benchmark_returns.loc[common_index, common_columns]
            port_wgt = (
                portfolio_weights.loc[common_index, common_columns]
                if len(portfolio_weights) > 0
                else pd.DataFrame(0, index=common_index, columns=common_columns)
            )
            bench_wgt = (
                benchmark_weights.loc[common_index, common_columns]
                if len(benchmark_weights) > 0
                else pd.DataFrame(0, index=common_index, columns=common_columns)
            )
            port_total_return = (1 + port_ret).prod() - 1
            bench_total_return = (1 + bench_ret).prod() - 1
            portfolio_return = (port_wgt.iloc[-1] * port_total_return).sum()
            benchmark_return = (bench_wgt.iloc[-1] * bench_total_return).sum()
            allocation_effect = (
                (port_wgt.iloc[-1] - bench_wgt.iloc[-1]) * bench_total_return
            ).sum()
            selection_effect = (
                bench_wgt.iloc[-1] * (port_total_return - bench_total_return)
            ).sum()
            interaction_effect = (
                (port_wgt.iloc[-1] - bench_wgt.iloc[-1])
                * (port_total_return - bench_total_return)
            ).sum()
            detailed_breakdown = {}
            for col in common_columns:
                detailed_breakdown[col] = {
                    "portfolio_weight": float(port_wgt.iloc[-1][col]),
                    "benchmark_weight": float(bench_wgt.iloc[-1][col]),
                    "portfolio_return": float(port_total_return[col]),
                    "benchmark_return": float(bench_total_return[col]),
                    "allocation_effect": float(
                        (port_wgt.iloc[-1][col] - bench_wgt.iloc[-1][col])
                        * bench_total_return[col]
                    ),
                    "selection_effect": float(
                        bench_wgt.iloc[-1][col]
                        * (port_total_return[col] - bench_total_return[col])
                    ),
                    "interaction_effect": float(
                        (port_wgt.iloc[-1][col] - bench_wgt.iloc[-1][col])
                        * (port_total_return[col] - bench_total_return[col])
                    ),
                }
            return AttributionResult(
                total_return=float(portfolio_return),
                benchmark_return=float(benchmark_return),
                active_return=float(portfolio_return - benchmark_return),
                allocation_effect=float(allocation_effect),
                selection_effect=float(selection_effect),
                interaction_effect=float(interaction_effect),
                detailed_breakdown=detailed_breakdown,
            ).__dict__
        except Exception as e:
            logger.error(f"Error in BHB attribution: {e}")
            raise

    def _calculate_brinson_fachler(
        self,
        portfolio_returns: pd.DataFrame,
        benchmark_returns: pd.DataFrame,
        portfolio_weights: pd.DataFrame,
        benchmark_weights: pd.DataFrame,
        level: str,
    ) -> Dict[str, Any]:
        """Calculate Brinson-Fachler attribution (geometric)

        Args:
            portfolio_returns: Portfolio returns
            benchmark_returns: Benchmark returns
            portfolio_weights: Portfolio weights
            benchmark_weights: Benchmark weights
            level: Attribution level

        Returns:
            Brinson-Fachler attribution results
        """
        try:
            bhb_result = self._calculate_brinson_hood_beebower(
                portfolio_returns,
                benchmark_returns,
                portfolio_weights,
                benchmark_weights,
                level,
            )
            total_active = bhb_result["active_return"]
            allocation = bhb_result["allocation_effect"]
            selection = bhb_result["selection_effect"]
            interaction = bhb_result["interaction_effect"]
            geometric_adjustment = total_active - (allocation + selection + interaction)
            return AttributionResult(
                total_return=bhb_result["total_return"],
                benchmark_return=bhb_result["benchmark_return"],
                active_return=bhb_result["active_return"],
                allocation_effect=allocation,
                selection_effect=selection,
                interaction_effect=interaction + geometric_adjustment,
                detailed_breakdown=bhb_result["detailed_breakdown"],
            ).__dict__
        except Exception as e:
            logger.error(f"Error in Brinson-Fachler attribution: {e}")
            raise

    def _calculate_geometric_attribution(
        self,
        portfolio_returns: pd.DataFrame,
        benchmark_returns: pd.DataFrame,
        portfolio_weights: pd.DataFrame,
        benchmark_weights: pd.DataFrame,
        level: str,
    ) -> Dict[str, Any]:
        """Calculate geometric attribution

        Args:
            portfolio_returns: Portfolio returns
            benchmark_returns: Benchmark returns
            portfolio_weights: Portfolio weights
            benchmark_weights: Benchmark weights
            level: Attribution level

        Returns:
            Geometric attribution results
        """
        try:
            (1 + portfolio_returns).cumprod()
            (1 + benchmark_returns).cumprod()
            log_port_ret = np.log(1 + portfolio_returns)
            log_bench_ret = np.log(1 + benchmark_returns)
            bhb_result = self._calculate_brinson_hood_beebower(
                log_port_ret, log_bench_ret, portfolio_weights, benchmark_weights, level
            )
            total_return = np.exp(bhb_result["total_return"]) - 1
            benchmark_return = np.exp(bhb_result["benchmark_return"]) - 1
            return AttributionResult(
                total_return=float(total_return),
                benchmark_return=float(benchmark_return),
                active_return=float(total_return - benchmark_return),
                allocation_effect=bhb_result["allocation_effect"],
                selection_effect=bhb_result["selection_effect"],
                interaction_effect=bhb_result["interaction_effect"],
                detailed_breakdown=bhb_result["detailed_breakdown"],
            ).__dict__
        except Exception as e:
            logger.error(f"Error in geometric attribution: {e}")
            raise

    def _calculate_factor_based_attribution(
        self,
        portfolio_returns: pd.DataFrame,
        benchmark_returns: pd.DataFrame,
        portfolio_weights: pd.DataFrame,
        benchmark_weights: pd.DataFrame,
        level: str,
    ) -> Dict[str, Any]:
        """Calculate factor-based attribution

        Args:
            portfolio_returns: Portfolio returns
            benchmark_returns: Benchmark returns
            portfolio_weights: Portfolio weights
            benchmark_weights: Benchmark weights
            level: Attribution level

        Returns:
            Factor-based attribution results
        """
        try:
            market_factor = portfolio_returns.mean(axis=1)
            factor_loadings = {}
            factor_returns = {}
            for col in portfolio_returns.columns:
                y = portfolio_returns[col].dropna()
                x = market_factor.loc[y.index]
                if len(y) > 1 and len(x) > 1:
                    covariance = np.cov(x, y)[0, 1]
                    variance = np.var(x)
                    beta = covariance / variance if variance > 0 else 0
                    alpha = np.mean(y) - beta * np.mean(x)
                    factor_loadings[col] = {"market_beta": beta, "alpha": alpha}
                    factor_returns[col] = {
                        "market_return": np.mean(x),
                        "specific_return": alpha,
                    }
            portfolio_factor_exposure = sum(
                (
                    portfolio_weights.iloc[-1].get(col, 0)
                    * factor_loadings.get(col, {}).get("market_beta", 0)
                    for col in portfolio_returns.columns
                )
            )
            benchmark_factor_exposure = sum(
                (
                    benchmark_weights.iloc[-1].get(col, 0)
                    * factor_loadings.get(col, {}).get("market_beta", 0)
                    for col in benchmark_returns.columns
                )
            )
            market_return = market_factor.mean()
            factor_allocation = (
                portfolio_factor_exposure - benchmark_factor_exposure
            ) * market_return
            specific_selection = sum(
                (
                    portfolio_weights.iloc[-1].get(col, 0)
                    * factor_loadings.get(col, {}).get("alpha", 0)
                    for col in portfolio_returns.columns
                )
            )
            portfolio_return = (
                portfolio_weights.iloc[-1] * portfolio_returns.mean()
            ).sum()
            benchmark_return = (
                benchmark_weights.iloc[-1] * benchmark_returns.mean()
            ).sum()
            return AttributionResult(
                total_return=float(portfolio_return),
                benchmark_return=float(benchmark_return),
                active_return=float(portfolio_return - benchmark_return),
                allocation_effect=float(factor_allocation),
                selection_effect=float(specific_selection),
                interaction_effect=0,
                detailed_breakdown={
                    "factor_exposures": {
                        "portfolio_market_beta": float(portfolio_factor_exposure),
                        "benchmark_market_beta": float(benchmark_factor_exposure),
                        "active_market_beta": float(
                            portfolio_factor_exposure - benchmark_factor_exposure
                        ),
                    },
                    "factor_returns": factor_returns,
                    "factor_loadings": factor_loadings,
                },
            ).__dict__
        except Exception as e:
            logger.error(f"Error in factor-based attribution: {e}")
            raise

    def _calculate_arithmetic_attribution(
        self,
        portfolio_returns: pd.DataFrame,
        benchmark_returns: pd.DataFrame,
        portfolio_weights: pd.DataFrame,
        benchmark_weights: pd.DataFrame,
        level: str,
    ) -> Dict[str, Any]:
        """Calculate arithmetic attribution (simple)

        Args:
            portfolio_returns: Portfolio returns
            benchmark_returns: Benchmark returns
            portfolio_weights: Portfolio weights
            benchmark_weights: Benchmark weights
            level: Attribution level

        Returns:
            Arithmetic attribution results
        """
        try:
            portfolio_return = (
                portfolio_weights.iloc[-1] * portfolio_returns.mean()
            ).sum()
            benchmark_return = (
                benchmark_weights.iloc[-1] * benchmark_returns.mean()
            ).sum()
            allocation_effect = (
                (portfolio_weights.iloc[-1] - benchmark_weights.iloc[-1])
                * benchmark_returns.mean()
            ).sum()
            selection_effect = (
                benchmark_weights.iloc[-1]
                * (portfolio_returns.mean() - benchmark_returns.mean())
            ).sum()
            return AttributionResult(
                total_return=float(portfolio_return),
                benchmark_return=float(benchmark_return),
                active_return=float(portfolio_return - benchmark_return),
                allocation_effect=float(allocation_effect),
                selection_effect=float(selection_effect),
                interaction_effect=0,
                detailed_breakdown={},
            ).__dict__
        except Exception as e:
            logger.error(f"Error in arithmetic attribution: {e}")
            raise

    def _validate_attribution_inputs(
        self,
        portfolio_returns: pd.DataFrame,
        benchmark_returns: pd.DataFrame,
        portfolio_weights: pd.DataFrame,
        benchmark_weights: pd.DataFrame,
    ) -> None:
        """Validate attribution inputs"""
        if portfolio_returns.empty:
            raise ValidationError("Portfolio returns data is empty")
        if benchmark_returns.empty:
            raise ValidationError("Benchmark returns data is empty")
        common_dates = portfolio_returns.index.intersection(benchmark_returns.index)
        if len(common_dates) == 0:
            raise ValidationError(
                "No common dates between portfolio and benchmark returns"
            )
        common_securities = portfolio_returns.columns.intersection(
            benchmark_returns.columns
        )
        if len(common_securities) == 0:
            raise ValidationError(
                "No common securities/sectors between portfolio and benchmark"
            )

    def _filter_by_date_range(
        self,
        portfolio_returns: pd.DataFrame,
        benchmark_returns: pd.DataFrame,
        portfolio_weights: pd.DataFrame,
        benchmark_weights: pd.DataFrame,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Filter data by date range"""
        date_filter = pd.Series(True, index=portfolio_returns.index)
        if start_date:
            date_filter = date_filter & (portfolio_returns.index >= start_date)
        if end_date:
            date_filter = date_filter & (portfolio_returns.index <= end_date)
        filtered_port_ret = portfolio_returns.loc[date_filter]
        filtered_bench_ret = benchmark_returns.loc[
            benchmark_returns.index.isin(filtered_port_ret.index)
        ]
        if not portfolio_weights.empty:
            filtered_port_wgt = portfolio_weights.loc[
                portfolio_weights.index.isin(filtered_port_ret.index)
            ]
        else:
            filtered_port_wgt = portfolio_weights
        if not benchmark_weights.empty:
            filtered_bench_wgt = benchmark_weights.loc[
                benchmark_weights.index.isin(filtered_bench_ret.index)
            ]
        else:
            filtered_bench_wgt = benchmark_weights
        return (
            filtered_port_ret,
            filtered_bench_ret,
            filtered_port_wgt,
            filtered_bench_wgt,
        )

    def _calculate_aggregate_attribution_stats(
        self, period_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate aggregate statistics across periods"""
        try:
            total_returns = [r.get("total_return", 0) for r in period_results]
            benchmark_returns = [r.get("benchmark_return", 0) for r in period_results]
            active_returns = [r.get("active_return", 0) for r in period_results]
            allocation_effects = [r.get("allocation_effect", 0) for r in period_results]
            selection_effects = [r.get("selection_effect", 0) for r in period_results]
            return {
                "average_total_return": float(np.mean(total_returns)),
                "average_benchmark_return": float(np.mean(benchmark_returns)),
                "average_active_return": float(np.mean(active_returns)),
                "average_allocation_effect": float(np.mean(allocation_effects)),
                "average_selection_effect": float(np.mean(selection_effects)),
                "volatility_active_return": float(np.std(active_returns)),
                "information_ratio": (
                    float(np.mean(active_returns) / np.std(active_returns))
                    if np.std(active_returns) > 0
                    else 0
                ),
                "hit_rate": float(
                    sum((1 for ar in active_returns if ar > 0)) / len(active_returns)
                ),
                "cumulative_total_return": float(
                    np.prod([1 + r for r in total_returns]) - 1
                ),
                "cumulative_benchmark_return": float(
                    np.prod([1 + r for r in benchmark_returns]) - 1
                ),
                "cumulative_active_return": float(
                    np.prod([1 + r for r in active_returns]) - 1
                ),
            }
        except Exception as e:
            logger.error(f"Error calculating aggregate stats: {e}")
            return {}

    def _initialize_factor_models(self) -> None:
        """Initialize factor models for attribution"""
        self.factor_models["fama_french_3"] = {
            "factors": ["market", "size", "value"],
            "description": "Fama-French 3-factor model",
        }
        self.factor_models["fama_french_5"] = {
            "factors": ["market", "size", "value", "profitability", "investment"],
            "description": "Fama-French 5-factor model",
        }
        self.factor_models["carhart_4"] = {
            "factors": ["market", "size", "value", "momentum"],
            "description": "Carhart 4-factor model",
        }
        logger.info(f"Initialized {len(self.factor_models)} factor models")

    def generate_attribution_report(
        self, attribution_results: Dict[str, Any], include_charts: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive attribution report

        Args:
            attribution_results: Attribution analysis results
            include_charts: Whether to include chart data

        Returns:
            Attribution report
        """
        try:
            total_return = attribution_results.get("total_return", 0)
            benchmark_return = attribution_results.get("benchmark_return", 0)
            active_return = attribution_results.get("active_return", 0)
            allocation_effect = attribution_results.get("allocation_effect", 0)
            selection_effect = attribution_results.get("selection_effect", 0)
            interaction_effect = attribution_results.get("interaction_effect", 0)
            summary = {
                "performance_summary": {
                    "portfolio_return": f"{total_return:.2%}",
                    "benchmark_return": f"{benchmark_return:.2%}",
                    "active_return": f"{active_return:.2%}",
                    "outperformance": active_return > 0,
                },
                "attribution_summary": {
                    "allocation_effect": f"{allocation_effect:.2%}",
                    "selection_effect": f"{selection_effect:.2%}",
                    "interaction_effect": f"{interaction_effect:.2%}",
                    "total_effect": f"{allocation_effect + selection_effect + interaction_effect:.2%}",
                },
            }
            detailed_breakdown = attribution_results.get("detailed_breakdown", {})
            if detailed_breakdown:
                contributions = []
                for sector, data in detailed_breakdown.items():
                    total_contribution = data.get("allocation_effect", 0) + data.get(
                        "selection_effect", 0
                    )
                    contributions.append(
                        {
                            "sector": sector,
                            "total_contribution": total_contribution,
                            "allocation_effect": data.get("allocation_effect", 0),
                            "selection_effect": data.get("selection_effect", 0),
                        }
                    )
                contributions.sort(key=lambda x: x["total_contribution"], reverse=True)
                top_contributors = contributions[:5]
                top_detractors = contributions[-5:]
            else:
                top_contributors = []
                top_detractors = []
            chart_data = {}
            if include_charts:
                chart_data = {
                    "attribution_waterfall": {
                        "categories": [
                            "Benchmark",
                            "Allocation",
                            "Selection",
                            "Interaction",
                            "Portfolio",
                        ],
                        "values": [
                            benchmark_return,
                            allocation_effect,
                            selection_effect,
                            interaction_effect,
                            total_return,
                        ],
                    },
                    "sector_contribution": {
                        "sectors": [item["sector"] for item in contributions],
                        "contributions": [
                            item["total_contribution"] for item in contributions
                        ],
                    },
                }
            return {
                "summary": summary,
                "detailed_breakdown": detailed_breakdown,
                "top_contributors": top_contributors,
                "top_detractors": top_detractors,
                "chart_data": chart_data,
                "methodology": attribution_results.get("method", "unknown"),
                "analysis_level": attribution_results.get("level", "unknown"),
                "period": attribution_results.get("period", {}),
                "generated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error generating attribution report: {e}")
            raise ServiceError(f"Error generating attribution report: {str(e)}")


class RiskAdjustedAttribution:
    """Risk-adjusted performance attribution"""

    def __init__(self, attribution_engine: PerformanceAttributionEngine) -> None:
        """Initialize risk-adjusted attribution

        Args:
            attribution_engine: Performance attribution engine
        """
        self.attribution_engine = attribution_engine

    def calculate_risk_adjusted_attribution(
        self,
        portfolio_returns: pd.DataFrame,
        benchmark_returns: pd.DataFrame,
        portfolio_weights: pd.DataFrame,
        benchmark_weights: pd.DataFrame,
        risk_factors: pd.DataFrame,
        method: str = "sharpe_ratio",
    ) -> Dict[str, Any]:
        """Calculate risk-adjusted attribution

        Args:
            portfolio_returns: Portfolio returns
            benchmark_returns: Benchmark returns
            portfolio_weights: Portfolio weights
            benchmark_weights: Benchmark weights
            risk_factors: Risk factor data
            method: Risk adjustment method

        Returns:
            Risk-adjusted attribution results
        """
        try:
            standard_attribution = self.attribution_engine.calculate_attribution(
                portfolio_returns,
                benchmark_returns,
                portfolio_weights,
                benchmark_weights,
            )
            portfolio_vol = portfolio_returns.std().mean() * np.sqrt(252)
            benchmark_vol = benchmark_returns.std().mean() * np.sqrt(252)
            risk_free_rate = self.attribution_engine.risk_free_rate
            portfolio_sharpe = (
                (standard_attribution["total_return"] - risk_free_rate) / portfolio_vol
                if portfolio_vol > 0
                else 0
            )
            benchmark_sharpe = (
                (standard_attribution["benchmark_return"] - risk_free_rate)
                / benchmark_vol
                if benchmark_vol > 0
                else 0
            )
            risk_adjusted_active = portfolio_sharpe - benchmark_sharpe
            return {
                "standard_attribution": standard_attribution,
                "risk_metrics": {
                    "portfolio_volatility": float(portfolio_vol),
                    "benchmark_volatility": float(benchmark_vol),
                    "portfolio_sharpe_ratio": float(portfolio_sharpe),
                    "benchmark_sharpe_ratio": float(benchmark_sharpe),
                    "active_sharpe_ratio": float(risk_adjusted_active),
                },
                "risk_adjusted_effects": {
                    "volatility_adjusted_allocation": (
                        standard_attribution["allocation_effect"] / portfolio_vol
                        if portfolio_vol > 0
                        else 0
                    ),
                    "volatility_adjusted_selection": (
                        standard_attribution["selection_effect"] / portfolio_vol
                        if portfolio_vol > 0
                        else 0
                    ),
                },
            }
        except Exception as e:
            logger.error(f"Error calculating risk-adjusted attribution: {e}")
            raise ServiceError(f"Error calculating risk-adjusted attribution: {str(e)}")
