"""
Factor analysis module for QuantumAlpha Analytics Service.
Provides comprehensive factor analysis and risk decomposition tools.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import scipy.stats as stats
from backend.common import ServiceError, ValidationError, setup_logger
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler

logger = setup_logger("factor_analysis", logging.INFO)


class FactorModel(Enum):
    """Factor model types"""

    FAMA_FRENCH_3 = "fama_french_3"
    FAMA_FRENCH_5 = "fama_french_5"
    CARHART_4 = "carhart_4"
    BARRA_FUNDAMENTAL = "barra_fundamental"
    STATISTICAL_PCA = "statistical_pca"
    CUSTOM = "custom"


class RiskFactorType(Enum):
    """Risk factor types"""

    MARKET = "market"
    SIZE = "size"
    VALUE = "value"
    MOMENTUM = "momentum"
    PROFITABILITY = "profitability"
    INVESTMENT = "investment"
    QUALITY = "quality"
    VOLATILITY = "volatility"
    SECTOR = "sector"
    COUNTRY = "country"
    CURRENCY = "currency"
    INTEREST_RATE = "interest_rate"
    CREDIT = "credit"
    COMMODITY = "commodity"


@dataclass
class FactorExposure:
    """Factor exposure result"""

    factor_name: str
    factor_type: RiskFactorType
    exposure: float
    t_statistic: float
    p_value: float
    confidence_interval: Tuple[float, float]
    contribution_to_return: float
    contribution_to_risk: float


@dataclass
class FactorAnalysisResult:
    """Factor analysis result"""

    model_type: FactorModel
    r_squared: float
    adjusted_r_squared: float
    factor_exposures: List[FactorExposure]
    residual_risk: float
    systematic_risk: float
    total_risk: float
    alpha: float
    alpha_t_stat: float
    alpha_p_value: float
    tracking_error: float
    information_ratio: float


class FactorAnalysisEngine:
    """Comprehensive factor analysis engine"""

    def __init__(self, config_manager: Any, db_manager: Any) -> None:
        """Initialize factor analysis engine

        Args:
            config_manager: Configuration manager
            db_manager: Database manager
        """
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.factor_data = {}
        self.factor_models = {}
        self.default_lookback_days = 252
        self.min_observations = 60
        self.confidence_level = 0.95
        self._initialize_factor_models()
        self._load_factor_data()
        logger.info("Factor analysis engine initialized")

    def analyze_portfolio_factors(
        self,
        portfolio_returns: pd.Series,
        factor_model: str = "fama_french_3",
        benchmark_returns: Optional[pd.Series] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        frequency: str = "daily",
    ) -> Dict[str, Any]:
        """Analyze portfolio factor exposures

        Args:
            portfolio_returns: Portfolio return series
            factor_model: Factor model to use
            benchmark_returns: Optional benchmark returns
            start_date: Analysis start date
            end_date: Analysis end date
            frequency: Data frequency

        Returns:
            Factor analysis results
        """
        try:
            logger.info(f"Analyzing portfolio factors using {factor_model} model")
            if portfolio_returns.empty:
                raise ValidationError("Portfolio returns data is empty")
            if start_date or end_date:
                portfolio_returns = self._filter_series_by_date(
                    portfolio_returns, start_date, end_date
                )
                if benchmark_returns is not None:
                    benchmark_returns = self._filter_series_by_date(
                        benchmark_returns, start_date, end_date
                    )
            if len(portfolio_returns) < self.min_observations:
                raise ValidationError(
                    f"Insufficient data: {len(portfolio_returns)} observations, minimum {self.min_observations} required"
                )
            factor_data = self._get_factor_data(factor_model, portfolio_returns.index)
            if factor_data.empty:
                raise ValidationError(f"No factor data available for {factor_model}")
            aligned_data = self._align_data(
                portfolio_returns, factor_data, benchmark_returns
            )
            if factor_model == FactorModel.STATISTICAL_PCA.value:
                result = self._perform_pca_analysis(aligned_data)
            else:
                result = self._perform_regression_analysis(aligned_data, factor_model)
            result = self._calculate_additional_metrics(result, aligned_data)
            result["analysis_period"] = {
                "start": aligned_data["portfolio_returns"].index[0].isoformat(),
                "end": aligned_data["portfolio_returns"].index[-1].isoformat(),
                "observations": len(aligned_data["portfolio_returns"]),
            }
            result["factor_model"] = factor_model
            result["frequency"] = frequency
            result["analyzed_at"] = datetime.utcnow().isoformat()
            return result
        except Exception as e:
            logger.error(f"Error analyzing portfolio factors: {e}")
            raise ServiceError(f"Error analyzing portfolio factors: {str(e)}")

    def analyze_security_factors(
        self,
        security_returns: Dict[str, pd.Series],
        factor_model: str = "fama_french_3",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Analyze factor exposures for multiple securities

        Args:
            security_returns: Dictionary of security return series
            factor_model: Factor model to use
            start_date: Analysis start date
            end_date: Analysis end date

        Returns:
            Security factor analysis results
        """
        try:
            logger.info(f"Analyzing factors for {len(security_returns)} securities")
            security_results = {}
            for security_id, returns in security_returns.items():
                try:
                    result = self.analyze_portfolio_factors(
                        returns, factor_model, None, start_date, end_date
                    )
                    security_results[security_id] = result
                except Exception as e:
                    logger.warning(f"Error analyzing factors for {security_id}: {e}")
                    security_results[security_id] = {"error": str(e)}
            cross_sectional_stats = self._calculate_cross_sectional_stats(
                security_results
            )
            return {
                "security_results": security_results,
                "cross_sectional_statistics": cross_sectional_stats,
                "factor_model": factor_model,
                "total_securities": len(security_returns),
                "successful_analyses": len(
                    [r for r in security_results.values() if "error" not in r]
                ),
                "analyzed_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error analyzing security factors: {e}")
            raise ServiceError(f"Error analyzing security factors: {str(e)}")

    def calculate_factor_risk_decomposition(
        self,
        portfolio_weights: pd.Series,
        security_factor_exposures: Dict[str, Dict[str, float]],
        factor_covariance_matrix: pd.DataFrame,
        specific_risks: Dict[str, float],
    ) -> Dict[str, Any]:
        """Calculate portfolio risk decomposition by factors

        Args:
            portfolio_weights: Portfolio weights
            security_factor_exposures: Security factor exposures
            factor_covariance_matrix: Factor covariance matrix
            specific_risks: Security-specific risks

        Returns:
            Risk decomposition results
        """
        try:
            logger.info("Calculating factor risk decomposition")
            factors = factor_covariance_matrix.index.tolist()
            portfolio_exposures = {}
            for factor in factors:
                exposure = 0
                for security, weight in portfolio_weights.items():
                    if security in security_factor_exposures:
                        exposure += weight * security_factor_exposures[security].get(
                            factor, 0
                        )
                portfolio_exposures[factor] = exposure
            exposure_vector = np.array([portfolio_exposures[f] for f in factors])
            systematic_variance = np.dot(
                exposure_vector,
                np.dot(factor_covariance_matrix.values, exposure_vector),
            )
            systematic_risk = np.sqrt(systematic_variance)
            specific_variance = 0
            for security, weight in portfolio_weights.items():
                if security in specific_risks:
                    specific_variance += weight**2 * specific_risks[security] ** 2
            specific_risk = np.sqrt(specific_variance)
            total_variance = systematic_variance + specific_variance
            total_risk = np.sqrt(total_variance)
            factor_contributions = {}
            for i, factor in enumerate(factors):
                marginal_contrib = 0
                for j, other_factor in enumerate(factors):
                    marginal_contrib += (
                        exposure_vector[i]
                        * factor_covariance_matrix.iloc[i, j]
                        * exposure_vector[j]
                    )
                factor_contributions[factor] = {
                    "exposure": float(exposure_vector[i]),
                    "marginal_contribution": float(marginal_contrib),
                    "percentage_contribution": (
                        float(marginal_contrib / total_variance * 100)
                        if total_variance > 0
                        else 0
                    ),
                }
            return {
                "portfolio_factor_exposures": portfolio_exposures,
                "risk_decomposition": {
                    "total_risk": float(total_risk),
                    "systematic_risk": float(systematic_risk),
                    "specific_risk": float(specific_risk),
                    "systematic_percentage": (
                        float(systematic_variance / total_variance * 100)
                        if total_variance > 0
                        else 0
                    ),
                    "specific_percentage": (
                        float(specific_variance / total_variance * 100)
                        if total_variance > 0
                        else 0
                    ),
                },
                "factor_contributions": factor_contributions,
                "calculated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error calculating risk decomposition: {e}")
            raise ServiceError(f"Error calculating risk decomposition: {str(e)}")

    def perform_factor_timing_analysis(
        self,
        portfolio_returns: pd.Series,
        factor_returns: pd.DataFrame,
        rolling_window: int = 60,
    ) -> Dict[str, Any]:
        """Perform factor timing analysis

        Args:
            portfolio_returns: Portfolio return series
            factor_returns: Factor return data
            rolling_window: Rolling window for analysis

        Returns:
            Factor timing analysis results
        """
        try:
            logger.info("Performing factor timing analysis")
            common_index = portfolio_returns.index.intersection(factor_returns.index)
            port_ret = portfolio_returns.loc[common_index]
            fact_ret = factor_returns.loc[common_index]
            if len(common_index) < rolling_window + 10:
                raise ValidationError("Insufficient data for rolling analysis")
            rolling_exposures = {}
            rolling_r_squared = []
            for factor in fact_ret.columns:
                rolling_exposures[factor] = []
            for i in range(rolling_window, len(common_index)):
                window_start = i - rolling_window
                window_end = i
                y = port_ret.iloc[window_start:window_end]
                X = fact_ret.iloc[window_start:window_end]
                np.column_stack([np.ones(len(X)), X.values])
                try:
                    reg = LinearRegression().fit(X.values, y.values)
                    for j, factor in enumerate(fact_ret.columns):
                        rolling_exposures[factor].append(reg.coef_[j])
                    r_squared = reg.score(X.values, y.values)
                    rolling_r_squared.append(r_squared)
                except Exception as e:
                    logger.warning(f"Error in rolling regression at window {i}: {e}")
                    for factor in fact_ret.columns:
                        rolling_exposures[factor].append(np.nan)
                    rolling_r_squared.append(np.nan)
            exposure_dates = common_index[rolling_window:]
            exposure_df = pd.DataFrame(rolling_exposures, index=exposure_dates)
            r_squared_series = pd.Series(rolling_r_squared, index=exposure_dates)
            timing_stats = {}
            for factor in fact_ret.columns:
                exposures = exposure_df[factor].dropna()
                if len(exposures) > 0:
                    timing_stats[factor] = {
                        "mean_exposure": float(exposures.mean()),
                        "exposure_volatility": float(exposures.std()),
                        "min_exposure": float(exposures.min()),
                        "max_exposure": float(exposures.max()),
                        "exposure_range": float(exposures.max() - exposures.min()),
                        "timing_consistency": (
                            float(1 - exposures.std() / abs(exposures.mean()))
                            if exposures.mean() != 0
                            else 0
                        ),
                    }
            timing_effectiveness = self._calculate_timing_effectiveness(
                exposure_df, fact_ret.loc[exposure_dates]
            )
            return {
                "rolling_exposures": exposure_df.to_dict("index"),
                "rolling_r_squared": r_squared_series.to_dict(),
                "timing_statistics": timing_stats,
                "timing_effectiveness": timing_effectiveness,
                "analysis_parameters": {
                    "rolling_window": rolling_window,
                    "total_windows": len(exposure_dates),
                    "start_date": exposure_dates[0].isoformat(),
                    "end_date": exposure_dates[-1].isoformat(),
                },
                "analyzed_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error performing factor timing analysis: {e}")
            raise ServiceError(f"Error performing factor timing analysis: {str(e)}")

    def calculate_factor_attribution(
        self,
        portfolio_returns: pd.Series,
        factor_returns: pd.DataFrame,
        factor_exposures: Dict[str, float],
        benchmark_exposures: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Calculate factor-based return attribution

        Args:
            portfolio_returns: Portfolio return series
            factor_returns: Factor return data
            factor_exposures: Portfolio factor exposures
            benchmark_exposures: Optional benchmark factor exposures

        Returns:
            Factor attribution results
        """
        try:
            logger.info("Calculating factor attribution")
            common_index = portfolio_returns.index.intersection(factor_returns.index)
            port_ret = portfolio_returns.loc[common_index]
            fact_ret = factor_returns.loc[common_index]
            factor_contributions = {}
            total_factor_return = 0
            for factor, exposure in factor_exposures.items():
                if factor in fact_ret.columns:
                    factor_return = fact_ret[factor].mean()
                    contribution = exposure * factor_return
                    factor_contributions[factor] = {
                        "exposure": float(exposure),
                        "factor_return": float(factor_return),
                        "contribution": float(contribution),
                    }
                    total_factor_return += contribution
            portfolio_return = port_ret.mean()
            alpha = portfolio_return - total_factor_return
            active_attribution = {}
            if benchmark_exposures:
                for factor in factor_exposures:
                    if factor in benchmark_exposures and factor in fact_ret.columns:
                        active_exposure = (
                            factor_exposures[factor] - benchmark_exposures[factor]
                        )
                        factor_return = fact_ret[factor].mean()
                        active_contribution = active_exposure * factor_return
                        active_attribution[factor] = {
                            "portfolio_exposure": float(factor_exposures[factor]),
                            "benchmark_exposure": float(benchmark_exposures[factor]),
                            "active_exposure": float(active_exposure),
                            "factor_return": float(factor_return),
                            "active_contribution": float(active_contribution),
                        }
            return {
                "portfolio_return": float(portfolio_return),
                "total_factor_return": float(total_factor_return),
                "alpha": float(alpha),
                "factor_contributions": factor_contributions,
                "active_attribution": active_attribution,
                "attribution_summary": {
                    "explained_return": float(total_factor_return),
                    "unexplained_return": float(alpha),
                    "explanation_ratio": (
                        float(abs(total_factor_return) / abs(portfolio_return))
                        if portfolio_return != 0
                        else 0
                    ),
                },
                "calculated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error calculating factor attribution: {e}")
            raise ServiceError(f"Error calculating factor attribution: {str(e)}")

    def _perform_regression_analysis(
        self, aligned_data: Dict[str, pd.Series], factor_model: str
    ) -> Dict[str, Any]:
        """Perform regression-based factor analysis"""
        try:
            portfolio_returns = aligned_data["portfolio_returns"]
            factor_data = aligned_data["factor_data"]
            y = portfolio_returns.values
            X = factor_data.values
            X_with_const = np.column_stack([np.ones(len(X)), X])
            reg = LinearRegression().fit(X, y)
            y_pred = reg.predict(X)
            residuals = y - y_pred
            r_squared = r2_score(y, y_pred)
            n = len(y)
            k = X.shape[1]
            adjusted_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - k - 1)
            alpha = np.mean(residuals)
            mse = np.mean(residuals**2)
            X_with_const_T_X_inv = np.linalg.inv(X_with_const.T @ X_with_const)
            var_coef = mse * np.diag(X_with_const_T_X_inv)
            std_errors = np.sqrt(var_coef)
            alpha_std_error = std_errors[0]
            alpha_t_stat = alpha / alpha_std_error if alpha_std_error > 0 else 0
            alpha_p_value = 2 * (1 - stats.t.cdf(abs(alpha_t_stat), n - k - 1))
            factor_exposures = []
            for i, factor_name in enumerate(factor_data.columns):
                coef = reg.coef_[i]
                std_error = std_errors[i + 1]
                t_stat = coef / std_error if std_error > 0 else 0
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - k - 1))
                t_critical = stats.t.ppf((1 + self.confidence_level) / 2, n - k - 1)
                ci_lower = coef - t_critical * std_error
                ci_upper = coef + t_critical * std_error
                factor_returns = factor_data[factor_name]
                contribution_to_return = coef * factor_returns.mean()
                contribution_to_risk = coef**2 * factor_returns.var()
                factor_exposure = FactorExposure(
                    factor_name=factor_name,
                    factor_type=self._get_factor_type(factor_name),
                    exposure=float(coef),
                    t_statistic=float(t_stat),
                    p_value=float(p_value),
                    confidence_interval=(float(ci_lower), float(ci_upper)),
                    contribution_to_return=float(contribution_to_return),
                    contribution_to_risk=float(contribution_to_risk),
                )
                factor_exposures.append(factor_exposure)
            systematic_variance = np.var(y_pred)
            residual_variance = np.var(residuals)
            total_variance = np.var(y)
            return FactorAnalysisResult(
                model_type=FactorModel(factor_model),
                r_squared=float(r_squared),
                adjusted_r_squared=float(adjusted_r_squared),
                factor_exposures=factor_exposures,
                residual_risk=float(np.sqrt(residual_variance)),
                systematic_risk=float(np.sqrt(systematic_variance)),
                total_risk=float(np.sqrt(total_variance)),
                alpha=float(alpha),
                alpha_t_stat=float(alpha_t_stat),
                alpha_p_value=float(alpha_p_value),
                tracking_error=float(np.sqrt(residual_variance)),
                information_ratio=(
                    float(alpha / np.sqrt(residual_variance))
                    if residual_variance > 0
                    else 0
                ),
            ).__dict__
        except Exception as e:
            logger.error(f"Error in regression analysis: {e}")
            raise

    def _perform_pca_analysis(
        self, aligned_data: Dict[str, pd.Series]
    ) -> Dict[str, Any]:
        """Perform PCA-based factor analysis"""
        try:
            portfolio_returns = aligned_data["portfolio_returns"]
            factor_data = aligned_data["factor_data"]
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(factor_data.values)
            pca = PCA()
            pca.fit(X_scaled)
            y = portfolio_returns.values
            portfolio_pca = pca.transform(scaler.transform(factor_data.values))
            reg = LinearRegression().fit(portfolio_pca, y)
            explained_variance_ratio = pca.explained_variance_ratio_
            np.cumsum(explained_variance_ratio)
            pca.components_
            factor_exposures = []
            for i in range(len(pca.components_)):
                if i < len(reg.coef_):
                    factor_exposure = FactorExposure(
                        factor_name=f"PC{i + 1}",
                        factor_type=RiskFactorType.MARKET,
                        exposure=float(reg.coef_[i]),
                        t_statistic=0,
                        p_value=1,
                        confidence_interval=(0, 0),
                        contribution_to_return=float(
                            reg.coef_[i] * explained_variance_ratio[i]
                        ),
                        contribution_to_risk=float(explained_variance_ratio[i]),
                    )
                    factor_exposures.append(factor_exposure)
            y_pred = reg.predict(portfolio_pca)
            r_squared = r2_score(y, y_pred)
            return FactorAnalysisResult(
                model_type=FactorModel.STATISTICAL_PCA,
                r_squared=float(r_squared),
                adjusted_r_squared=float(r_squared),
                factor_exposures=factor_exposures,
                residual_risk=float(np.sqrt(np.var(y - y_pred))),
                systematic_risk=float(np.sqrt(np.var(y_pred))),
                total_risk=float(np.sqrt(np.var(y))),
                alpha=float(np.mean(y - y_pred)),
                alpha_t_stat=0,
                alpha_p_value=1,
                tracking_error=float(np.sqrt(np.var(y - y_pred))),
                information_ratio=0,
            ).__dict__
        except Exception as e:
            logger.error(f"Error in PCA analysis: {e}")
            raise

    def _calculate_additional_metrics(
        self, result: Dict[str, Any], aligned_data: Dict[str, pd.Series]
    ) -> Dict[str, Any]:
        """Calculate additional factor analysis metrics"""
        try:
            portfolio_returns = aligned_data["portfolio_returns"]
            result["time_varying_analysis"] = self._calculate_time_varying_exposures(
                portfolio_returns, aligned_data["factor_data"]
            )
            result["factor_correlations"] = self._calculate_factor_correlations(
                aligned_data["factor_data"]
            )
            result["regime_analysis"] = self._calculate_regime_analysis(
                portfolio_returns, aligned_data["factor_data"]
            )
            return result
        except Exception as e:
            logger.warning(f"Error calculating additional metrics: {e}")
            return result

    def _calculate_time_varying_exposures(
        self, portfolio_returns: pd.Series, factor_data: pd.DataFrame, window: int = 60
    ) -> Dict[str, Any]:
        """Calculate time-varying factor exposures"""
        try:
            if len(portfolio_returns) < window * 2:
                return {"error": "Insufficient data for time-varying analysis"}
            rolling_exposures = {}
            for factor in factor_data.columns:
                rolling_exposures[factor] = []
            dates = []
            for i in range(window, len(portfolio_returns)):
                window_start = i - window
                window_end = i
                y = portfolio_returns.iloc[window_start:window_end]
                X = factor_data.iloc[window_start:window_end]
                try:
                    reg = LinearRegression().fit(X.values, y.values)
                    for j, factor in enumerate(factor_data.columns):
                        rolling_exposures[factor].append(reg.coef_[j])
                    dates.append(portfolio_returns.index[i])
                except Exception:
                    for factor in factor_data.columns:
                        rolling_exposures[factor].append(np.nan)
                    dates.append(portfolio_returns.index[i])
            exposure_stats = {}
            for factor, exposures in rolling_exposures.items():
                clean_exposures = [e for e in exposures if not np.isnan(e)]
                if clean_exposures:
                    exposure_stats[factor] = {
                        "mean": float(np.mean(clean_exposures)),
                        "std": float(np.std(clean_exposures)),
                        "min": float(np.min(clean_exposures)),
                        "max": float(np.max(clean_exposures)),
                    }
            return {
                "rolling_exposures": rolling_exposures,
                "dates": [d.isoformat() for d in dates],
                "exposure_statistics": exposure_stats,
                "window_size": window,
            }
        except Exception as e:
            logger.error(f"Error calculating time-varying exposures: {e}")
            return {"error": str(e)}

    def _calculate_factor_correlations(
        self, factor_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate factor correlation matrix"""
        try:
            correlation_matrix = factor_data.corr()
            return {
                "correlation_matrix": correlation_matrix.to_dict(),
                "average_correlation": float(
                    correlation_matrix.values[
                        np.triu_indices_from(correlation_matrix.values, k=1)
                    ].mean()
                ),
                "max_correlation": float(
                    correlation_matrix.values[
                        np.triu_indices_from(correlation_matrix.values, k=1)
                    ].max()
                ),
                "min_correlation": float(
                    correlation_matrix.values[
                        np.triu_indices_from(correlation_matrix.values, k=1)
                    ].min()
                ),
            }
        except Exception as e:
            logger.error(f"Error calculating factor correlations: {e}")
            return {"error": str(e)}

    def _calculate_regime_analysis(
        self, portfolio_returns: pd.Series, factor_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate regime-based factor analysis"""
        try:
            market_vol = portfolio_returns.rolling(20).std()
            high_vol_threshold = market_vol.quantile(0.75)
            low_vol_threshold = market_vol.quantile(0.25)
            high_vol_periods = market_vol > high_vol_threshold
            low_vol_periods = market_vol < low_vol_threshold
            normal_periods = ~(high_vol_periods | low_vol_periods)
            regimes = {
                "high_volatility": high_vol_periods,
                "low_volatility": low_vol_periods,
                "normal": normal_periods,
            }
            regime_results = {}
            for regime_name, regime_mask in regimes.items():
                if regime_mask.sum() > 30:
                    regime_returns = portfolio_returns[regime_mask]
                    regime_factors = factor_data[regime_mask]
                    try:
                        reg = LinearRegression().fit(
                            regime_factors.values, regime_returns.values
                        )
                        r_squared = reg.score(
                            regime_factors.values, regime_returns.values
                        )
                        regime_results[regime_name] = {
                            "observations": int(regime_mask.sum()),
                            "r_squared": float(r_squared),
                            "factor_exposures": {
                                factor: float(coef)
                                for factor, coef in zip(
                                    regime_factors.columns, reg.coef_
                                )
                            },
                            "average_return": float(regime_returns.mean()),
                            "volatility": float(regime_returns.std()),
                        }
                    except Exception as e:
                        regime_results[regime_name] = {"error": str(e)}
            return regime_results
        except Exception as e:
            logger.error(f"Error calculating regime analysis: {e}")
            return {"error": str(e)}

    def _calculate_timing_effectiveness(
        self, exposure_df: pd.DataFrame, factor_returns: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate factor timing effectiveness"""
        try:
            timing_effectiveness = {}
            for factor in exposure_df.columns:
                if factor in factor_returns.columns:
                    exposures = exposure_df[factor].dropna()
                    returns = factor_returns[factor].loc[exposures.index]
                    if len(exposures) > 10:
                        lagged_exposures = exposures.shift(1).dropna()
                        aligned_returns = returns.loc[lagged_exposures.index]
                        if len(lagged_exposures) > 5:
                            correlation = np.corrcoef(
                                lagged_exposures, aligned_returns
                            )[0, 1]
                            timing_value = (
                                correlation
                                * np.std(aligned_returns)
                                * np.std(lagged_exposures)
                            )
                            timing_effectiveness[factor] = {
                                "timing_correlation": float(correlation),
                                "timing_value": float(timing_value),
                                "observations": len(lagged_exposures),
                            }
            return timing_effectiveness
        except Exception as e:
            logger.error(f"Error calculating timing effectiveness: {e}")
            return {"error": str(e)}

    def _calculate_cross_sectional_stats(
        self, security_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate cross-sectional statistics"""
        try:
            valid_results = {
                k: v for k, v in security_results.items() if "error" not in v
            }
            if not valid_results:
                return {"error": "No valid results for cross-sectional analysis"}
            r_squareds = [r.get("r_squared", 0) for r in valid_results.values()]
            alphas = [r.get("alpha", 0) for r in valid_results.values()]
            factor_exposures = {}
            for result in valid_results.values():
                for exposure in result.get("factor_exposures", []):
                    factor_name = exposure["factor_name"]
                    if factor_name not in factor_exposures:
                        factor_exposures[factor_name] = []
                    factor_exposures[factor_name].append(exposure["exposure"])
            factor_stats = {}
            for factor, exposures in factor_exposures.items():
                factor_stats[factor] = {
                    "mean_exposure": float(np.mean(exposures)),
                    "median_exposure": float(np.median(exposures)),
                    "std_exposure": float(np.std(exposures)),
                    "min_exposure": float(np.min(exposures)),
                    "max_exposure": float(np.max(exposures)),
                }
            return {
                "summary_statistics": {
                    "mean_r_squared": float(np.mean(r_squareds)),
                    "median_r_squared": float(np.median(r_squareds)),
                    "mean_alpha": float(np.mean(alphas)),
                    "median_alpha": float(np.median(alphas)),
                    "alpha_t_test": (
                        float(stats.ttest_1samp(alphas, 0)[1]) if len(alphas) > 1 else 1
                    ),
                },
                "factor_exposure_statistics": factor_stats,
                "valid_securities": len(valid_results),
                "total_securities": len(security_results),
            }
        except Exception as e:
            logger.error(f"Error calculating cross-sectional stats: {e}")
            return {"error": str(e)}

    def _initialize_factor_models(self) -> None:
        """Initialize factor model definitions"""
        self.factor_models = {
            FactorModel.FAMA_FRENCH_3.value: {
                "factors": ["market_excess", "smb", "hml"],
                "description": "Fama-French 3-factor model",
                "source": "Kenneth French Data Library",
            },
            FactorModel.FAMA_FRENCH_5.value: {
                "factors": ["market_excess", "smb", "hml", "rmw", "cma"],
                "description": "Fama-French 5-factor model",
                "source": "Kenneth French Data Library",
            },
            FactorModel.CARHART_4.value: {
                "factors": ["market_excess", "smb", "hml", "mom"],
                "description": "Carhart 4-factor model",
                "source": "Kenneth French Data Library + Momentum",
            },
        }

    def _load_factor_data(self) -> None:
        """Load factor data (mock implementation)"""
        dates = pd.date_range("2020-01-01", "2024-01-01", freq="D")
        np.random.seed(42)
        self.factor_data["fama_french_3"] = pd.DataFrame(
            {
                "market_excess": np.random.normal(0.0005, 0.01, len(dates)),
                "smb": np.random.normal(0.0001, 0.005, len(dates)),
                "hml": np.random.normal(0.0001, 0.005, len(dates)),
            },
            index=dates,
        )
        self.factor_data["fama_french_5"] = pd.DataFrame(
            {
                "market_excess": np.random.normal(0.0005, 0.01, len(dates)),
                "smb": np.random.normal(0.0001, 0.005, len(dates)),
                "hml": np.random.normal(0.0001, 0.005, len(dates)),
                "rmw": np.random.normal(0.0001, 0.004, len(dates)),
                "cma": np.random.normal(0.0001, 0.004, len(dates)),
            },
            index=dates,
        )
        self.factor_data["carhart_4"] = pd.DataFrame(
            {
                "market_excess": np.random.normal(0.0005, 0.01, len(dates)),
                "smb": np.random.normal(0.0001, 0.005, len(dates)),
                "hml": np.random.normal(0.0001, 0.005, len(dates)),
                "mom": np.random.normal(0.0002, 0.006, len(dates)),
            },
            index=dates,
        )
        logger.info(f"Loaded factor data for {len(self.factor_data)} models")

    def _get_factor_data(
        self, factor_model: str, date_index: pd.DatetimeIndex
    ) -> pd.DataFrame:
        """Get factor data for specified model and dates"""
        if factor_model not in self.factor_data:
            return pd.DataFrame()
        factor_df = self.factor_data[factor_model]
        common_dates = factor_df.index.intersection(date_index)
        return factor_df.loc[common_dates]

    def _align_data(
        self,
        portfolio_returns: pd.Series,
        factor_data: pd.DataFrame,
        benchmark_returns: Optional[pd.Series] = None,
    ) -> Dict[str, pd.Series]:
        """Align portfolio, factor, and benchmark data"""
        common_index = portfolio_returns.index.intersection(factor_data.index)
        if benchmark_returns is not None:
            common_index = common_index.intersection(benchmark_returns.index)
        aligned_data = {
            "portfolio_returns": portfolio_returns.loc[common_index],
            "factor_data": factor_data.loc[common_index],
        }
        if benchmark_returns is not None:
            aligned_data["benchmark_returns"] = benchmark_returns.loc[common_index]
        return aligned_data

    def _filter_series_by_date(
        self,
        series: pd.Series,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> pd.Series:
        """Filter series by date range"""
        if start_date:
            series = series[series.index >= start_date]
        if end_date:
            series = series[series.index <= end_date]
        return series

    def _get_factor_type(self, factor_name: str) -> RiskFactorType:
        """Get factor type from factor name"""
        factor_name_lower = factor_name.lower()
        if "market" in factor_name_lower:
            return RiskFactorType.MARKET
        elif "smb" in factor_name_lower or "size" in factor_name_lower:
            return RiskFactorType.SIZE
        elif "hml" in factor_name_lower or "value" in factor_name_lower:
            return RiskFactorType.VALUE
        elif "mom" in factor_name_lower or "momentum" in factor_name_lower:
            return RiskFactorType.MOMENTUM
        elif "rmw" in factor_name_lower or "profitability" in factor_name_lower:
            return RiskFactorType.PROFITABILITY
        elif "cma" in factor_name_lower or "investment" in factor_name_lower:
            return RiskFactorType.INVESTMENT
        else:
            return RiskFactorType.MARKET
