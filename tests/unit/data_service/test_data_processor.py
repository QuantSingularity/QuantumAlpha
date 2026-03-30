from typing import Any

"""
Unit tests for the Data Service's Data Processor.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock
import numpy as np
import pandas as pd

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
try:
    from backend.common.exceptions import ServiceError, ValidationError
    from backend.data_service.data_processor import DataProcessor
except ImportError:

    class DataProcessor:
        pass

    class ValidationError(Exception):
        pass

    class ServiceError(Exception):
        pass


class TestDataProcessor(unittest.TestCase):
    """Unit tests for DataProcessor class."""

    def setUp(self) -> Any:
        """Set up test fixtures."""
        self.config_manager = MagicMock()
        self.config_manager.get_config.return_value = {
            "data_service": {"cache_dir": "/tmp/cache", "data_dir": "/tmp/data"}
        }
        self.db_manager = MagicMock()
        self.market_data = pd.DataFrame(
            {
                "timestamp": pd.date_range(start="2023-01-01", periods=100),
                "open": np.random.normal(100, 2, 100),
                "high": np.random.normal(102, 2, 100),
                "low": np.random.normal(98, 2, 100),
                "close": np.random.normal(100, 2, 100),
                "volume": np.random.normal(1000000, 100000, 100),
                "symbol": "AAPL",
            }
        )
        self.data_processor = DataProcessor(self.config_manager, self.db_manager)

    def test_init(self) -> Any:
        """Test DataProcessor initialization."""
        data_processor = DataProcessor(self.config_manager, self.db_manager)
        self.assertEqual(data_processor.config_manager, self.config_manager)
        self.assertEqual(data_processor.db_manager, self.db_manager)
        self.assertEqual(data_processor.cache_dir, "/tmp/cache")
        self.assertEqual(data_processor.data_dir, "/tmp/data")

    def test_clean_data(self) -> Any:
        """Test data cleaning."""
        df = self.market_data.copy()
        df.loc[10:15, "close"] = np.nan
        df.loc[20:25, "volume"] = np.nan
        cleaned_df = self.data_processor.clean_data(df)
        self.assertEqual(len(cleaned_df), len(df))
        self.assertFalse(cleaned_df["close"].isna().any())
        self.assertFalse(cleaned_df["volume"].isna().any())

    def test_clean_data_empty(self) -> Any:
        """Test cleaning empty data."""
        df = pd.DataFrame()
        with self.assertRaises(ValidationError):
            self.data_processor.clean_data(df)

    def test_clean_data_missing_columns(self) -> Any:
        """Test cleaning data with missing columns."""
        df = pd.DataFrame(
            {
                "timestamp": pd.date_range(start="2023-01-01", periods=100),
                "close": np.random.normal(100, 2, 100),
                "symbol": "AAPL",
            }
        )
        with self.assertRaises(ValidationError):
            self.data_processor.clean_data(df)

    def test_calculate_technical_indicators(self) -> Any:
        """Test technical indicator calculation."""
        df = self.data_processor.calculate_technical_indicators(self.market_data)
        self.assertEqual(len(df), len(self.market_data))
        self.assertIn("sma_20", df.columns)
        self.assertIn("sma_50", df.columns)
        self.assertIn("ema_20", df.columns)
        self.assertIn("rsi_14", df.columns)
        self.assertIn("macd", df.columns)
        self.assertIn("macd_signal", df.columns)
        self.assertIn("macd_hist", df.columns)
        self.assertIn("bb_upper", df.columns)
        self.assertIn("bb_middle", df.columns)
        self.assertIn("bb_lower", df.columns)

    def test_calculate_technical_indicators_empty(self) -> Any:
        """Test calculating indicators for empty data."""
        df = pd.DataFrame()
        with self.assertRaises(ValidationError):
            self.data_processor.calculate_technical_indicators(df)

    def test_calculate_technical_indicators_missing_columns(self) -> Any:
        """Test calculating indicators for data with missing columns."""
        df = pd.DataFrame(
            {
                "timestamp": pd.date_range(start="2023-01-01", periods=100),
                "symbol": "AAPL",
            }
        )
        with self.assertRaises(ValidationError):
            self.data_processor.calculate_technical_indicators(df)

    def test_calculate_sma(self) -> Any:
        """Test SMA calculation."""
        df = self.data_processor._calculate_sma(self.market_data, window=20)
        self.assertEqual(len(df), len(self.market_data))
        self.assertIn("sma_20", df.columns)
        self.assertTrue(df["sma_20"].isna().sum() < len(df))

    def test_calculate_ema(self) -> Any:
        """Test EMA calculation."""
        df = self.data_processor._calculate_ema(self.market_data, window=20)
        self.assertEqual(len(df), len(self.market_data))
        self.assertIn("ema_20", df.columns)
        self.assertTrue(df["ema_20"].isna().sum() < len(df))

    def test_calculate_rsi(self) -> Any:
        """Test RSI calculation."""
        df = self.data_processor._calculate_rsi(self.market_data, window=14)
        self.assertEqual(len(df), len(self.market_data))
        self.assertIn("rsi_14", df.columns)
        self.assertTrue(df["rsi_14"].isna().sum() < len(df))
        self.assertTrue((df["rsi_14"] >= 0).all() and (df["rsi_14"] <= 100).all())

    def test_calculate_macd(self) -> Any:
        """Test MACD calculation."""
        df = self.data_processor._calculate_macd(self.market_data)
        self.assertEqual(len(df), len(self.market_data))
        self.assertIn("macd", df.columns)
        self.assertIn("macd_signal", df.columns)
        self.assertIn("macd_hist", df.columns)
        self.assertTrue(df["macd"].isna().sum() < len(df))
        self.assertTrue(df["macd_signal"].isna().sum() < len(df))
        self.assertTrue(df["macd_hist"].isna().sum() < len(df))

    def test_calculate_bollinger_bands(self) -> Any:
        """Test Bollinger Bands calculation."""
        df = self.data_processor._calculate_bollinger_bands(
            self.market_data, window=20, num_std=2
        )
        self.assertEqual(len(df), len(self.market_data))
        self.assertIn("bb_upper", df.columns)
        self.assertIn("bb_middle", df.columns)
        self.assertIn("bb_lower", df.columns)
        self.assertTrue(df["bb_upper"].isna().sum() < len(df))
        self.assertTrue(df["bb_middle"].isna().sum() < len(df))
        self.assertTrue(df["bb_lower"].isna().sum() < len(df))
        valid_idx = ~df["bb_upper"].isna()
        self.assertTrue(
            (df.loc[valid_idx, "bb_upper"] >= df.loc[valid_idx, "bb_middle"]).all()
        )
        self.assertTrue(
            (df.loc[valid_idx, "bb_middle"] >= df.loc[valid_idx, "bb_lower"]).all()
        )

    def test_detect_anomalies(self) -> Any:
        """Test anomaly detection."""
        df = self.data_processor.detect_anomalies(
            self.market_data, column="close", window=20, threshold=3.0
        )
        self.assertEqual(len(df), len(self.market_data))
        self.assertIn("anomaly", df.columns)
        self.assertTrue(set(df["anomaly"].unique()).issubset({0, 1}))

    def test_detect_anomalies_invalid_column(self) -> Any:
        """Test anomaly detection with invalid column."""
        with self.assertRaises(ValidationError):
            self.data_processor.detect_anomalies(
                self.market_data, column="invalid", window=20, threshold=3.0
            )

    def test_generate_signals(self) -> Any:
        """Test signal generation."""
        df = self.data_processor.generate_signals(
            self.market_data, strategy="sma_crossover"
        )
        self.assertEqual(len(df), len(self.market_data))
        self.assertIn("signal", df.columns)
        self.assertTrue(set(df["signal"].unique()).issubset({-1, 0, 1}))

    def test_generate_signals_invalid_strategy(self) -> Any:
        """Test signal generation with invalid strategy."""
        with self.assertRaises(ValidationError):
            self.data_processor.generate_signals(self.market_data, strategy="invalid")

    def test_generate_sma_crossover_signals(self) -> Any:
        """Test SMA crossover signal generation."""
        df = self.data_processor._generate_sma_crossover_signals(self.market_data)
        self.assertEqual(len(df), len(self.market_data))
        self.assertIn("signal", df.columns)
        self.assertTrue(set(df["signal"].unique()).issubset({-1, 0, 1}))

    def test_generate_macd_signals(self) -> Any:
        """Test MACD signal generation."""
        df = self.data_processor._generate_macd_signals(self.market_data)
        self.assertEqual(len(df), len(self.market_data))
        self.assertIn("signal", df.columns)
        self.assertTrue(set(df["signal"].unique()).issubset({-1, 0, 1}))

    def test_generate_rsi_signals(self) -> Any:
        """Test RSI signal generation."""
        df = self.data_processor._generate_rsi_signals(self.market_data)
        self.assertEqual(len(df), len(self.market_data))
        self.assertIn("signal", df.columns)
        self.assertTrue(set(df["signal"].unique()).issubset({-1, 0, 1}))

    def test_generate_bollinger_bands_signals(self) -> Any:
        """Test Bollinger Bands signal generation."""
        df = self.data_processor._generate_bollinger_bands_signals(self.market_data)
        self.assertEqual(len(df), len(self.market_data))
        self.assertIn("signal", df.columns)
        self.assertTrue(set(df["signal"].unique()).issubset({-1, 0, 1}))

    def test_prepare_data_for_ml(self) -> Any:
        """Test data preparation for machine learning."""
        X_train, X_test, y_train, y_test, scaler = (
            self.data_processor.prepare_data_for_ml(
                df=self.market_data,
                target_column="close",
                sequence_length=10,
                target_shift=1,
                test_size=0.2,
            )
        )
        self.assertIsInstance(X_train, np.ndarray)
        self.assertIsInstance(X_test, np.ndarray)
        self.assertIsInstance(y_train, np.ndarray)
        self.assertIsInstance(y_test, np.ndarray)
        self.assertIsNotNone(scaler)
        self.assertEqual(X_train.shape[1], 10)
        self.assertEqual(X_test.shape[1], 10)
        self.assertEqual(len(y_train.shape), 1)
        self.assertEqual(len(y_test.shape), 1)
        total_samples = len(X_train) + len(X_test)
        self.assertAlmostEqual(len(X_test) / total_samples, 0.2, delta=0.1)

    def test_prepare_data_for_ml_invalid_target(self) -> Any:
        """Test data preparation with invalid target column."""
        with self.assertRaises(ValidationError):
            self.data_processor.prepare_data_for_ml(
                df=self.market_data,
                target_column="invalid",
                sequence_length=10,
                target_shift=1,
                test_size=0.2,
            )

    def test_prepare_data_for_ml_invalid_sequence_length(self) -> Any:
        """Test data preparation with invalid sequence length."""
        with self.assertRaises(ValidationError):
            self.data_processor.prepare_data_for_ml(
                df=self.market_data,
                target_column="close",
                sequence_length=0,
                target_shift=1,
                test_size=0.2,
            )

    def test_prepare_data_for_ml_invalid_test_size(self) -> Any:
        """Test data preparation with invalid test size."""
        with self.assertRaises(ValidationError):
            self.data_processor.prepare_data_for_ml(
                df=self.market_data,
                target_column="close",
                sequence_length=10,
                target_shift=1,
                test_size=1.5,
            )

    def test_create_sequences(self) -> Any:
        """Test sequence creation."""
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        X, y = self.data_processor._create_sequences(
            data, sequence_length=3, target_shift=1
        )
        self.assertEqual(X.shape, (7, 3))
        self.assertEqual(y.shape, (7,))
        np.testing.assert_array_equal(X[0], [1, 2, 3])
        self.assertEqual(y[0], 4)
        np.testing.assert_array_equal(X[-1], [7, 8, 9])
        self.assertEqual(y[-1], 10)

    def test_create_sequences_invalid_length(self) -> Any:
        """Test sequence creation with invalid length."""
        data = np.array([1, 2])
        with self.assertRaises(ValidationError):
            self.data_processor._create_sequences(
                data, sequence_length=3, target_shift=1
            )


if __name__ == "__main__":
    unittest.main()
