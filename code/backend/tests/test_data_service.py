"""
Unit tests for the Data Service.
"""

import unittest
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
from backend.common import ValidationError
from backend.data_service.data_processor import DataProcessor


class TestDataProcessor(unittest.TestCase):
    """Test cases for DataProcessor"""

    def setUp(self) -> None:
        """Set up test environment"""
        self.config_manager = MagicMock()
        self.config_manager.get.return_value = "test_value"
        self.db_manager = MagicMock()
        self.data_processor = DataProcessor(self.config_manager, self.db_manager)
        self.market_data = [
            {
                "timestamp": "2023-01-01T00:00:00Z",
                "open": 100.0,
                "high": 105.0,
                "low": 95.0,
                "close": 102.0,
                "volume": 1000,
            },
            {
                "timestamp": "2023-01-02T00:00:00Z",
                "open": 102.0,
                "high": 107.0,
                "low": 100.0,
                "close": 105.0,
                "volume": 1200,
            },
            {
                "timestamp": "2023-01-03T00:00:00Z",
                "open": 105.0,
                "high": 110.0,
                "low": 103.0,
                "close": 108.0,
                "volume": 1500,
            },
            {
                "timestamp": "2023-01-04T00:00:00Z",
                "open": 108.0,
                "high": 112.0,
                "low": 106.0,
                "close": 110.0,
                "volume": 1300,
            },
            {
                "timestamp": "2023-01-05T00:00:00Z",
                "open": 110.0,
                "high": 115.0,
                "low": 108.0,
                "close": 112.0,
                "volume": 1400,
            },
        ]

    def test_process_market_data_basic(self) -> None:
        """Test basic market data processing"""
        df = self.data_processor.process_market_data(self.market_data)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 5)
        self.assertTrue("open" in df.columns)
        self.assertTrue("high" in df.columns)
        self.assertTrue("low" in df.columns)
        self.assertTrue("close" in df.columns)
        self.assertTrue("volume" in df.columns)

    def test_process_market_data_with_features(self) -> None:
        """Test market data processing with features"""
        df = self.data_processor.process_market_data(
            self.market_data, features=["sma", "rsi"]
        )
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 5)
        self.assertTrue("sma_20" in df.columns)
        self.assertTrue("rsi_14" in df.columns)

    def test_process_market_data_empty(self) -> None:
        """Test market data processing with empty data"""
        with self.assertRaises(ValidationError):
            self.data_processor.process_market_data([])

    def test_process_market_data_missing_columns(self) -> None:
        """Test market data processing with missing columns"""
        data = [
            {
                "timestamp": "2023-01-01T00:00:00Z",
                "open": 100.0,
                "high": 105.0,
                "low": 95.0,
            }
        ]
        with self.assertRaises(ValidationError):
            self.data_processor.process_market_data(data)

    def test_normalize_data(self) -> None:
        """Test data normalization"""
        df = self.data_processor.process_market_data(self.market_data)
        df_normalized = self.data_processor.normalize_data(df)
        self.assertIsInstance(df_normalized, pd.DataFrame)
        self.assertEqual(len(df_normalized), 5)
        self.assertTrue("close_norm" in df_normalized.columns)
        self.assertTrue("volume_norm" in df_normalized.columns)
        self.assertTrue(
            0
            <= df_normalized["close_norm"].min()
            <= df_normalized["close_norm"].max()
            <= 1
        )
        self.assertTrue(
            0
            <= df_normalized["volume_norm"].min()
            <= df_normalized["volume_norm"].max()
            <= 1
        )

    def test_prepare_data_for_ml(self) -> None:
        """Test data preparation for machine learning"""
        df = self.data_processor.process_market_data(self.market_data)
        X_train, X_test, y_train, y_test, scaler = (
            self.data_processor.prepare_data_for_ml(
                df=df,
                target_column="close",
                sequence_length=2,
                target_shift=1,
                test_size=0.5,
            )
        )
        self.assertIsInstance(X_train, np.ndarray)
        self.assertIsInstance(X_test, np.ndarray)
        self.assertIsInstance(y_train, np.ndarray)
        self.assertIsInstance(y_test, np.ndarray)
        self.assertEqual(X_train.shape[1], 2)
        self.assertEqual(X_train.shape[2], 5)

    def test_detect_anomalies(self) -> None:
        """Test anomaly detection"""
        df = self.data_processor.process_market_data(self.market_data)
        df_anomalies = self.data_processor.detect_anomalies(
            df=df, column="close", window=2, threshold=2.0
        )
        self.assertIsInstance(df_anomalies, pd.DataFrame)
        self.assertEqual(len(df_anomalies), 5)
        self.assertTrue("anomaly" in df_anomalies.columns)

    def test_generate_signals(self) -> None:
        """Test signal generation"""
        df = self.data_processor.process_market_data(self.market_data)
        df_signals = self.data_processor.generate_signals(
            df=df, strategy="sma_crossover"
        )
        self.assertIsInstance(df_signals, pd.DataFrame)
        self.assertEqual(len(df_signals), 5)
        self.assertTrue("signal" in df_signals.columns)
        self.assertTrue(df_signals["signal"].isin([-1, 0, 1]).all())


if __name__ == "__main__":
    unittest.main()
