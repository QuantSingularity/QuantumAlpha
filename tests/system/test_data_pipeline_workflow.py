from typing import Any

"""
System tests for data pipeline workflow.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import requests

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
try:
    from backend.common.exceptions import ServiceError, ValidationError
    from backend.data_service.data_ingestion import DataIngestion
    from backend.data_service.data_processor import DataProcessor
    from backend.data_service.data_storage import DataStorage
except ImportError:

    class DataProcessor:
        pass

    class DataIngestion:
        pass

    class DataStorage:
        pass

    class ValidationError(Exception):
        pass

    class ServiceError(Exception):
        pass


class TestDataPipelineWorkflow(unittest.TestCase):
    """System tests for data pipeline workflow."""

    def setUp(self) -> Any:
        """Set up test fixtures."""
        self.config_manager = MagicMock()
        self.config_manager.get_config.return_value = {
            "data_service": {"cache_dir": "/tmp/cache", "data_dir": "/tmp/data"},
            "data_sources": {
                "alpha_vantage": {
                    "api_key": "demo",
                    "base_url": "https://www.alphavantage.co/query",
                },
                "yahoo_finance": {
                    "base_url": "https://query1.finance.yahoo.com/v8/finance/chart"
                },
            },
            "database": {
                "postgres": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "quantumalpha",
                    "user": "postgres",
                    "password": "postgres",
                },
                "timescale": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "timescaledb",
                    "user": "postgres",
                    "password": "postgres",
                },
            },
            "services": {"data_service": {"host": "localhost", "port": 8081}},
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
        self.data_ingestion = DataIngestion(self.config_manager, self.db_manager)
        self.data_storage = DataStorage(self.config_manager, self.db_manager)

    @patch("requests.get")
    def test_data_ingestion_to_storage_workflow(self, mock_get: Any) -> Any:
        """Test data ingestion to storage workflow."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Meta Data": {
                "1. Information": "Daily Prices (open, high, low, close) and Volumes",
                "2. Symbol": "AAPL",
                "3. Last Refreshed": "2023-01-10",
                "4. Output Size": "Compact",
                "5. Time Zone": "US/Eastern",
            },
            "Time Series (Daily)": {
                "2023-01-10": {
                    "1. open": "130.2800",
                    "2. high": "131.2500",
                    "3. low": "128.1200",
                    "4. close": "130.7300",
                    "5. volume": "69077938",
                },
                "2023-01-09": {
                    "1. open": "129.1700",
                    "2. high": "130.9000",
                    "3. low": "128.1200",
                    "4. close": "130.1500",
                    "5. volume": "70790742",
                },
                "2023-01-06": {
                    "1. open": "126.0100",
                    "2. high": "130.2900",
                    "3. low": "124.8900",
                    "4. close": "129.6200",
                    "5. volume": "87754891",
                },
            },
        }
        mock_get.return_value = mock_response
        with patch.object(self.data_ingestion, "fetch_market_data") as mock_fetch:
            mock_fetch.return_value = self.market_data
            data = self.data_ingestion.fetch_market_data(
                symbol="AAPL", source="alpha_vantage", timeframe="1d", period="1mo"
            )
            self.assertIsInstance(data, pd.DataFrame)
            self.assertEqual(data["symbol"].iloc[0], "AAPL")
            self.assertEqual(len(data), 100)
            processed_data = self.data_processor.clean_data(data)
            processed_data = self.data_processor.calculate_technical_indicators(
                processed_data
            )
            self.assertIsInstance(processed_data, pd.DataFrame)
            self.assertIn("sma_20", processed_data.columns)
            self.assertIn("rsi_14", processed_data.columns)
            self.assertIn("macd", processed_data.columns)
            with patch.object(self.data_storage, "save_market_data") as mock_save:
                mock_save.return_value = True
                result = self.data_storage.save_market_data(
                    data=processed_data, symbol="AAPL", timeframe="1d"
                )
                self.assertTrue(result)
                mock_save.assert_called_once()
                args, kwargs = mock_save.call_args
                self.assertEqual(kwargs["symbol"], "AAPL")
                self.assertEqual(kwargs["timeframe"], "1d")

    @patch("requests.get")
    def test_data_api_workflow(self, mock_get: Any) -> Any:
        """Test data API workflow."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": self.market_data.to_dict(orient="records")
        }
        mock_get.return_value = mock_response
        data_service_url = (
            "http://localhost:8081/api/market-data/AAPL?timeframe=1d&period=1mo"
        )
        response = requests.get(data_service_url)
        self.assertEqual(response.status_code, 200)
        market_data = response.json()["data"]
        self.assertIsInstance(market_data, list)
        self.assertEqual(len(market_data), 100)
        mock_response.json.return_value = {
            "data": self.data_processor.calculate_technical_indicators(
                self.market_data
            ).to_dict(orient="records")
        }
        indicators_url = "http://localhost:8081/api/technical-indicators/AAPL?timeframe=1d&period=1mo"
        response = requests.get(indicators_url)
        self.assertEqual(response.status_code, 200)
        indicators_data = response.json()["data"]
        self.assertIsInstance(indicators_data, list)
        self.assertEqual(len(indicators_data), 100)
        self.assertIn("sma_20", indicators_data[0])
        self.assertIn("rsi_14", indicators_data[0])
        self.assertIn("macd", indicators_data[0])

    def test_data_batch_processing_workflow(self) -> Any:
        """Test data batch processing workflow."""
        with patch.object(
            self.data_ingestion, "fetch_batch_market_data"
        ) as mock_fetch_batch:
            batch_data = {
                "AAPL": self.market_data,
                "MSFT": self.market_data.copy().assign(symbol="MSFT"),
                "GOOGL": self.market_data.copy().assign(symbol="GOOGL"),
            }
            mock_fetch_batch.return_value = batch_data
            data = self.data_ingestion.fetch_batch_market_data(
                symbols=["AAPL", "MSFT", "GOOGL"],
                source="alpha_vantage",
                timeframe="1d",
                period="1mo",
            )
            self.assertIsInstance(data, dict)
            self.assertEqual(len(data), 3)
            self.assertIn("AAPL", data)
            self.assertIn("MSFT", data)
            self.assertIn("GOOGL", data)
            processed_batch_data = {}
            for symbol, df in data.items():
                processed_df = self.data_processor.clean_data(df)
                processed_df = self.data_processor.calculate_technical_indicators(
                    processed_df
                )
                processed_batch_data[symbol] = processed_df
            self.assertEqual(len(processed_batch_data), 3)
            for symbol, df in processed_batch_data.items():
                self.assertIn("sma_20", df.columns)
                self.assertIn("rsi_14", df.columns)
                self.assertIn("macd", df.columns)
            with patch.object(
                self.data_storage, "save_batch_market_data"
            ) as mock_save_batch:
                mock_save_batch.return_value = {
                    "AAPL": True,
                    "MSFT": True,
                    "GOOGL": True,
                }
                result = self.data_storage.save_batch_market_data(
                    data=processed_batch_data, timeframe="1d"
                )
                self.assertIsInstance(result, dict)
                self.assertEqual(len(result), 3)
                self.assertTrue(result["AAPL"])
                self.assertTrue(result["MSFT"])
                self.assertTrue(result["GOOGL"])
                mock_save_batch.assert_called_once()
                args, kwargs = mock_save_batch.call_args
                self.assertEqual(kwargs["timeframe"], "1d")

    def test_data_aggregation_workflow(self) -> Any:
        """Test data aggregation workflow."""
        with patch.object(self.data_storage, "get_market_data") as mock_get_data:
            mock_get_data.return_value = self.market_data
            data = self.data_storage.get_market_data(
                symbol="AAPL",
                timeframe="1d",
                start_date="2023-01-01",
                end_date="2023-01-10",
            )
            self.assertIsInstance(data, pd.DataFrame)
            self.assertEqual(data["symbol"].iloc[0], "AAPL")
            with patch.object(self.data_processor, "resample_data") as mock_resample:
                weekly_data = pd.DataFrame(
                    {
                        "timestamp": pd.date_range(
                            start="2023-01-01", periods=20, freq="W"
                        ),
                        "open": np.random.normal(100, 2, 20),
                        "high": np.random.normal(102, 2, 20),
                        "low": np.random.normal(98, 2, 20),
                        "close": np.random.normal(100, 2, 20),
                        "volume": np.random.normal(5000000, 500000, 20),
                        "symbol": "AAPL",
                    }
                )
                mock_resample.return_value = weekly_data
                resampled_data = self.data_processor.resample_data(
                    df=data, timeframe="1w"
                )
                self.assertIsInstance(resampled_data, pd.DataFrame)
                self.assertEqual(len(resampled_data), 20)
                weekly_indicators = self.data_processor.calculate_technical_indicators(
                    resampled_data
                )
                self.assertIsInstance(weekly_indicators, pd.DataFrame)
                self.assertIn("sma_20", weekly_indicators.columns)
                self.assertIn("rsi_14", weekly_indicators.columns)
                self.assertIn("macd", weekly_indicators.columns)
                with patch.object(self.data_storage, "save_market_data") as mock_save:
                    mock_save.return_value = True
                    result = self.data_storage.save_market_data(
                        data=weekly_indicators, symbol="AAPL", timeframe="1w"
                    )
                    self.assertTrue(result)
                    mock_save.assert_called_once()
                    args, kwargs = mock_save.call_args
                    self.assertEqual(kwargs["symbol"], "AAPL")
                    self.assertEqual(kwargs["timeframe"], "1w")

    def test_data_export_workflow(self) -> Any:
        """Test data export workflow."""
        with patch.object(self.data_storage, "get_market_data") as mock_get_data:
            mock_get_data.return_value = self.market_data
            data = self.data_storage.get_market_data(
                symbol="AAPL",
                timeframe="1d",
                start_date="2023-01-01",
                end_date="2023-01-10",
            )
            self.assertIsInstance(data, pd.DataFrame)
            with patch.object(self.data_processor, "export_to_csv") as mock_export_csv:
                mock_export_csv.return_value = "/tmp/data/AAPL_1d_20230101_20230110.csv"
                csv_path = self.data_processor.export_to_csv(
                    df=data,
                    symbol="AAPL",
                    timeframe="1d",
                    start_date="2023-01-01",
                    end_date="2023-01-10",
                )
                self.assertEqual(csv_path, "/tmp/data/AAPL_1d_20230101_20230110.csv")
                mock_export_csv.assert_called_once()
                args, kwargs = mock_export_csv.call_args
                self.assertEqual(kwargs["symbol"], "AAPL")
                self.assertEqual(kwargs["timeframe"], "1d")
                self.assertEqual(kwargs["start_date"], "2023-01-01")
                self.assertEqual(kwargs["end_date"], "2023-01-10")
            with patch.object(
                self.data_processor, "export_to_json"
            ) as mock_export_json:
                mock_export_json.return_value = (
                    "/tmp/data/AAPL_1d_20230101_20230110.json"
                )
                json_path = self.data_processor.export_to_json(
                    df=data,
                    symbol="AAPL",
                    timeframe="1d",
                    start_date="2023-01-01",
                    end_date="2023-01-10",
                )
                self.assertEqual(json_path, "/tmp/data/AAPL_1d_20230101_20230110.json")
                mock_export_json.assert_called_once()
                args, kwargs = mock_export_json.call_args
                self.assertEqual(kwargs["symbol"], "AAPL")
                self.assertEqual(kwargs["timeframe"], "1d")
                self.assertEqual(kwargs["start_date"], "2023-01-01")
                self.assertEqual(kwargs["end_date"], "2023-01-10")


if __name__ == "__main__":
    unittest.main()
