"""
Unit tests for the QuantumAlpha Analytics Service.
Covers FactorAnalysisEngine and PerformanceAttributionEngine.
"""

import unittest
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
from backend.analytics_service.factor_analysis import (
    FactorAnalysisEngine,
    FactorAnalysisResult,
    FactorExposure,
    FactorModel,
    RiskFactorType,
)
from backend.analytics_service.performance_attribution import (
    AttributionLevel,
    AttributionMethod,
    PerformanceAttributionEngine,
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


def _returns(n: int = 252, seed: int = 42) -> pd.Series:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    return pd.Series(rng.normal(0.0005, 0.015, n), index=idx, name="portfolio")


def _returns_df(assets: list, n: int = 120, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-01-01", periods=n, freq="B")
    data = rng.normal(0.0005, 0.015, (n, len(assets)))
    return pd.DataFrame(data, index=idx, columns=assets)


def _weights_df(assets: list, n: int = 120) -> pd.DataFrame:
    idx = pd.date_range("2023-01-01", periods=n, freq="B")
    w = np.ones((n, len(assets))) / len(assets)
    return pd.DataFrame(w, index=idx, columns=assets)


# ---------------------------------------------------------------------------
# FactorAnalysisEngine tests
# ---------------------------------------------------------------------------


class TestFactorAnalysisEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = FactorAnalysisEngine(_cfg(), _db())
        self.returns = _returns()

    def test_initialization_sets_defaults(self) -> None:
        self.assertEqual(self.engine.default_lookback_days, 252)
        self.assertEqual(self.engine.min_observations, 60)
        self.assertAlmostEqual(self.engine.confidence_level, 0.95)

    def test_factor_models_dict_populated(self) -> None:
        self.assertIsInstance(self.engine.factor_models, dict)
        self.assertGreater(len(self.engine.factor_models), 0)

    def test_fama_french_3_in_models(self) -> None:
        self.assertIn(FactorModel.FAMA_FRENCH_3.value, self.engine.factor_models)

    def test_analyze_returns_dict(self) -> None:
        result = self.engine.analyze_portfolio_factors(
            self.returns, factor_model="fama_french_3"
        )
        self.assertIsInstance(result, dict)

    def test_analyze_contains_required_keys(self) -> None:
        result = self.engine.analyze_portfolio_factors(self.returns)
        for key in ("model_type", "r_squared", "factor_exposures", "alpha"):
            self.assertIn(key, result)

    def test_r_squared_numeric(self) -> None:
        result = self.engine.analyze_portfolio_factors(self.returns)
        r2 = result["r_squared"]
        self.assertIsInstance(r2, float)
        self.assertLessEqual(r2, 1.0)

    def test_factor_exposures_is_list(self) -> None:
        result = self.engine.analyze_portfolio_factors(self.returns)
        self.assertIsInstance(result["factor_exposures"], list)

    def test_carhart_4_model_accepted(self) -> None:
        result = self.engine.analyze_portfolio_factors(
            self.returns, factor_model="carhart_4"
        )
        self.assertIsInstance(result, dict)

    def test_raises_on_too_few_observations(self) -> None:
        tiny = _returns(n=10)
        with self.assertRaises(Exception):
            self.engine.analyze_portfolio_factors(tiny)

    def test_factor_model_enum_values(self) -> None:
        self.assertEqual(FactorModel.FAMA_FRENCH_3.value, "fama_french_3")
        self.assertEqual(FactorModel.FAMA_FRENCH_5.value, "fama_french_5")
        self.assertEqual(FactorModel.CARHART_4.value, "carhart_4")
        self.assertEqual(FactorModel.STATISTICAL_PCA.value, "statistical_pca")
        self.assertEqual(FactorModel.BARRA_FUNDAMENTAL.value, "barra_fundamental")
        self.assertEqual(FactorModel.CUSTOM.value, "custom")

    def test_risk_factor_type_enum_values(self) -> None:
        self.assertEqual(RiskFactorType.MARKET.value, "market")
        self.assertEqual(RiskFactorType.SIZE.value, "size")
        self.assertEqual(RiskFactorType.VALUE.value, "value")
        self.assertEqual(RiskFactorType.MOMENTUM.value, "momentum")
        self.assertEqual(RiskFactorType.PROFITABILITY.value, "profitability")
        self.assertEqual(RiskFactorType.INVESTMENT.value, "investment")

    def test_factor_exposure_dataclass_construction(self) -> None:
        fe = FactorExposure(
            factor_name="market",
            factor_type=RiskFactorType.MARKET,
            exposure=0.95,
            t_statistic=8.2,
            p_value=0.0001,
            confidence_interval=(0.80, 1.10),
            contribution_to_return=0.042,
            contribution_to_risk=0.18,
        )
        self.assertEqual(fe.factor_name, "market")
        self.assertAlmostEqual(fe.exposure, 0.95)
        self.assertAlmostEqual(fe.t_statistic, 8.2)
        self.assertEqual(fe.factor_type, RiskFactorType.MARKET)

    def test_factor_analysis_result_dataclass(self) -> None:
        fe = FactorExposure(
            "mkt", RiskFactorType.MARKET, 1.0, 10.0, 0.001, (0.9, 1.1), 0.05, 0.20
        )
        far = FactorAnalysisResult(
            model_type=FactorModel.FAMA_FRENCH_3,
            r_squared=0.82,
            adjusted_r_squared=0.81,
            factor_exposures=[fe],
            residual_risk=0.08,
            systematic_risk=0.12,
            total_risk=0.15,
            alpha=0.001,
            alpha_t_stat=2.1,
            alpha_p_value=0.04,
            tracking_error=0.05,
            information_ratio=0.72,
        )
        self.assertAlmostEqual(far.r_squared, 0.82)
        self.assertEqual(len(far.factor_exposures), 1)
        self.assertEqual(far.model_type, FactorModel.FAMA_FRENCH_3)

    def test_analyze_with_benchmark(self) -> None:
        benchmark = _returns(seed=99)
        result = self.engine.analyze_portfolio_factors(
            self.returns,
            factor_model="fama_french_3",
            benchmark_returns=benchmark,
        )
        self.assertIsInstance(result, dict)

    def test_analyze_result_has_model_type(self) -> None:
        result = self.engine.analyze_portfolio_factors(self.returns)
        mt = result["model_type"]
        # model_type may be a FactorModel enum or its string value
        valid = [m for m in FactorModel] + [m.value for m in FactorModel]
        self.assertIn(mt, valid)


# ---------------------------------------------------------------------------
# PerformanceAttributionEngine tests
# ---------------------------------------------------------------------------


class TestPerformanceAttributionEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = PerformanceAttributionEngine(_cfg(), _db())
        assets = ["AAPL", "MSFT", "JPM", "JNJ", "XOM"]
        self.port_returns = _returns_df(assets, n=120)
        self.bench_returns = _returns_df(assets, n=120, seed=99)
        self.port_weights = _weights_df(assets, n=120)
        self.bench_weights = _weights_df(assets, n=120)

    def test_initialization(self) -> None:
        self.assertIsNotNone(self.engine)

    def test_calculate_attribution_returns_dict(self) -> None:
        result = self.engine.calculate_attribution(
            portfolio_returns=self.port_returns,
            benchmark_returns=self.bench_returns,
            portfolio_weights=self.port_weights,
            benchmark_weights=self.bench_weights,
            method="brinson_hood_beebower",
        )
        self.assertIsInstance(result, dict)

    def test_attribution_has_meaningful_keys(self) -> None:
        result = self.engine.calculate_attribution(
            portfolio_returns=self.port_returns,
            benchmark_returns=self.bench_returns,
            portfolio_weights=self.port_weights,
            benchmark_weights=self.bench_weights,
        )
        self.assertGreater(len(result), 0)

    def test_brinson_fachler_method_accepted(self) -> None:
        result = self.engine.calculate_attribution(
            portfolio_returns=self.port_returns,
            benchmark_returns=self.bench_returns,
            portfolio_weights=self.port_weights,
            benchmark_weights=self.bench_weights,
            method="brinson_fachler",
        )
        self.assertIsInstance(result, dict)

    def test_attribution_method_enum_values(self) -> None:
        self.assertIsNotNone(AttributionMethod.BRINSON_HOOD_BEEBOWER)
        self.assertIsNotNone(AttributionMethod.BRINSON_FACHLER)

    def test_attribution_level_enum_values(self) -> None:
        self.assertIsNotNone(AttributionLevel.SECTOR)
        self.assertIsNotNone(AttributionLevel.SECURITY)

    def test_generate_report_returns_dict(self) -> None:
        attribution = self.engine.calculate_attribution(
            portfolio_returns=self.port_returns,
            benchmark_returns=self.bench_returns,
            portfolio_weights=self.port_weights,
            benchmark_weights=self.bench_weights,
        )
        report = self.engine.generate_attribution_report(attribution)
        self.assertIsInstance(report, dict)

    def test_generate_report_non_empty(self) -> None:
        attribution = self.engine.calculate_attribution(
            portfolio_returns=self.port_returns,
            benchmark_returns=self.bench_returns,
            portfolio_weights=self.port_weights,
            benchmark_weights=self.bench_weights,
        )
        report = self.engine.generate_attribution_report(attribution)
        self.assertGreater(len(report), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
