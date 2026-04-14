"""
Market data service for QuantumAlpha Data Service.
Handles market data collection, storage, and retrieval.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

import requests
from backend.common import (
    RateLimiter,
    ServiceError,
    SimpleCache,
    ValidationError,
    parse_period,
    setup_logger,
)
from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS

logger = setup_logger("market_data_service", logging.INFO)


class MarketDataService:
    """Market data service"""

    def __init__(self, config_manager: Any, db_manager: Any) -> None:
        """Initialize market data service

        Args:
            config_manager: Configuration manager
            db_manager: Database manager
        """
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.data_sources = {
            "alpha_vantage": {
                "api_key": config_manager.get("api_keys.alpha_vantage"),
                "base_url": "https://www.alphavantage.co/query",
                "rate_limiter": RateLimiter(0.2),
            },
            "polygon": {
                "api_key": config_manager.get("api_keys.polygon"),
                "base_url": "https://api.polygon.io",
                "rate_limiter": RateLimiter(5.0),
            },
            "yahoo_finance": {
                "base_url": "https://query1.finance.yahoo.com/v8/finance/chart",
                "rate_limiter": RateLimiter(2.0),
            },
        }
        self.cache = SimpleCache(max_size=1000, ttl=300)
        logger.info("Market data service initialized")

    def get_market_data(
        self,
        symbol: str,
        timeframe: str = "1d",
        period: Optional[str] = None,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        source: str = "alpha_vantage",
    ) -> Dict[str, Any]:
        """Get market data for a symbol

        Args:
            symbol: Symbol to get data for
            timeframe: Data timeframe (e.g., '1m', '5m', '1h', '1d')
            period: Historical period (e.g., '1d', '1wk', '1mo', '1y')
            start_date: Start date for custom range
            end_date: End date for custom range
            source: Data source to use

        Returns:
            Market data

        Raises:
            ValidationError: If parameters are invalid
            NotFoundError: If data is not found
            ServiceError: If there is an error getting data
        """
        logger.info(f"Getting market data for {symbol} ({timeframe})")
        if not symbol:
            raise ValidationError("Symbol is required")
        if not timeframe:
            raise ValidationError("Timeframe is required")
        if period and (not (start_date or end_date)):
            start_date = parse_period(period)
            end_date = datetime.now(timezone.utc)
        elif start_date and (not end_date):
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end_date = datetime.now(timezone.utc)
        elif end_date and (not start_date):
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            start_date = end_date - timedelta(days=30)
        elif not (start_date or end_date):
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=30)
        else:
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        cache_key = f"market_data:{symbol}:{timeframe}:{start_date.isoformat()}:{end_date.isoformat()}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.debug(f"Using cached data for {symbol}")
            return cached_data
        data = self._get_data_from_db(symbol, timeframe, start_date, end_date)
        if data and len(data["data"]) > 0:
            logger.debug(f"Using database data for {symbol}")
            self.cache.set(cache_key, data)
            return data
        if source not in self.data_sources:
            raise ValidationError(f"Invalid data source: {source}")
        if source == "alpha_vantage":
            data = self._get_data_from_alpha_vantage(
                symbol, timeframe, start_date, end_date
            )
        elif source == "polygon":
            data = self._get_data_from_polygon(symbol, timeframe, start_date, end_date)
        elif source == "yahoo_finance":
            data = self._get_data_from_yahoo_finance(
                symbol, timeframe, start_date, end_date
            )
        else:
            raise ValidationError(f"Unsupported data source: {source}")
        self._store_data_in_db(data)
        self.cache.set(cache_key, data)
        return data

    def _get_data_from_db(
        self, symbol: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get market data from database

        Args:
            symbol: Symbol to get data for
            timeframe: Data timeframe
            start_date: Start date
            end_date: End date

        Returns:
            Market data
        """
        try:
            influxdb_client = self.db_manager.get_influxdb_client()
            query_api = influxdb_client.query_api()
            query = f'\n            from(bucket: "{self.config_manager.get('influxdb.bucket')}")\n                |> range(start: {start_date.isoformat()}, stop: {end_date.isoformat()})\n                |> filter(fn: (r) => r["_measurement"] == "market_data")\n                |> filter(fn: (r) => r["symbol"] == "{symbol}")\n                |> filter(fn: (r) => r["timeframe"] == "{timeframe}")\n                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")\n            '
            tables = query_api.query(query, org=self.config_manager.get("influxdb.org"))
            data_points = []
            for table in tables:
                for record in table.records:
                    data_point = {
                        "timestamp": record.get_time().isoformat(),
                        "open": record.get_value("open"),
                        "high": record.get_value("high"),
                        "low": record.get_value("low"),
                        "close": record.get_value("close"),
                        "volume": record.get_value("volume"),
                    }
                    data_points.append(data_point)
            data_points.sort(key=lambda x: x["timestamp"])
            return {"symbol": symbol, "timeframe": timeframe, "data": data_points}
        except Exception as e:
            logger.error(f"Error getting data from database: {e}")
            return {"symbol": symbol, "timeframe": timeframe, "data": []}

    def _store_data_in_db(self, data: Dict[str, Any]) -> None:
        """Store market data in database

        Args:
            data: Market data to store
        """
        try:
            influxdb_client = self.db_manager.get_influxdb_client()
            write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
            points = []
            for point in data["data"]:
                p = (
                    Point("market_data")
                    .tag("symbol", data["symbol"])
                    .tag("timeframe", data["timeframe"])
                    .field("open", float(point["open"]))
                    .field("high", float(point["high"]))
                    .field("low", float(point["low"]))
                    .field("close", float(point["close"]))
                    .field("volume", float(point["volume"]))
                    .time(
                        datetime.fromisoformat(
                            point["timestamp"].replace("Z", "+00:00")
                        )
                    )
                )
                points.append(p)
            write_api.write(
                bucket=self.config_manager.get("influxdb.bucket"),
                org=self.config_manager.get("influxdb.org"),
                record=points,
            )
            logger.debug(f"Stored {len(points)} data points in database")
        except Exception as e:
            logger.error(f"Error storing data in database: {e}")

    def _get_data_from_alpha_vantage(
        self, symbol: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get market data from Alpha Vantage

        Args:
            symbol: Symbol to get data for
            timeframe: Data timeframe
            start_date: Start date
            end_date: End date

        Returns:
            Market data

        Raises:
            ServiceError: If there is an error getting data
        """
        try:
            self.data_sources["alpha_vantage"]["rate_limiter"].wait()
            interval_map = {
                "1m": "1min",
                "5m": "5min",
                "15m": "15min",
                "30m": "30min",
                "1h": "60min",
                "1d": "daily",
                "1wk": "weekly",
                "1mo": "monthly",
            }
            if timeframe not in interval_map:
                raise ValidationError(
                    f"Unsupported timeframe for Alpha Vantage: {timeframe}"
                )
            av_interval = interval_map[timeframe]
            if av_interval in ["1min", "5min", "15min", "30min", "60min"]:
                function = "TIME_SERIES_INTRADAY"
                params = {
                    "function": function,
                    "symbol": symbol,
                    "interval": av_interval,
                    "outputsize": "full",
                    "apikey": self.data_sources["alpha_vantage"]["api_key"],
                }
            else:
                if av_interval == "daily":
                    function = "TIME_SERIES_DAILY"
                elif av_interval == "weekly":
                    function = "TIME_SERIES_WEEKLY"
                else:
                    function = "TIME_SERIES_MONTHLY"
                params = {
                    "function": function,
                    "symbol": symbol,
                    "outputsize": "full",
                    "apikey": self.data_sources["alpha_vantage"]["api_key"],
                }
            response = requests.get(
                self.data_sources["alpha_vantage"]["base_url"], params=params
            )
            if response.status_code != 200:
                raise ServiceError(
                    f"Error getting data from Alpha Vantage: {response.text}"
                )
            response_data = response.json()
            if "Error Message" in response_data:
                raise ServiceError(
                    f"Alpha Vantage error: {response_data['Error Message']}"
                )
            time_series_key = None
            for key in response_data:
                if key.startswith("Time Series"):
                    time_series_key = key
                    break
            if not time_series_key:
                raise ServiceError(
                    "No time series data found in Alpha Vantage response"
                )
            time_series = response_data[time_series_key]
            data_points = []
            for timestamp, values in time_series.items():
                dt = datetime.fromisoformat(timestamp.replace(" ", "T"))
                if dt < start_date or dt > end_date:
                    continue
                data_point = {
                    "timestamp": dt.isoformat(),
                    "open": float(values["1. open"]),
                    "high": float(values["2. high"]),
                    "low": float(values["3. low"]),
                    "close": float(values["4. close"]),
                    "volume": float(values["5. volume"]),
                }
                data_points.append(data_point)
            data_points.sort(key=lambda x: x["timestamp"])
            return {"symbol": symbol, "timeframe": timeframe, "data": data_points}
        except Exception as e:
            logger.error(f"Error getting data from Alpha Vantage: {e}")
            raise ServiceError(f"Error getting data from Alpha Vantage: {str(e)}")

    def _get_data_from_polygon(
        self, symbol: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get market data from Polygon

        Args:
            symbol: Symbol to get data for
            timeframe: Data timeframe
            start_date: Start date
            end_date: End date

        Returns:
            Market data

        Raises:
            ServiceError: If there is an error getting data
        """
        try:
            self.data_sources["polygon"]["rate_limiter"].wait()
            timeframe_map = {
                "1m": (1, "minute"),
                "5m": (5, "minute"),
                "15m": (15, "minute"),
                "30m": (30, "minute"),
                "1h": (1, "hour"),
                "1d": (1, "day"),
                "1wk": (1, "week"),
                "1mo": (1, "month"),
            }
            if timeframe not in timeframe_map:
                raise ValidationError(f"Unsupported timeframe for Polygon: {timeframe}")
            multiplier, timespan = timeframe_map[timeframe]
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            url = f"{self.data_sources['polygon']['base_url']}/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{start_date_str}/{end_date_str}"
            response = requests.get(
                url,
                params={
                    "apiKey": self.data_sources["polygon"]["api_key"],
                    "sort": "asc",
                },
            )
            if response.status_code != 200:
                raise ServiceError(f"Error getting data from Polygon: {response.text}")
            response_data = response.json()
            if response_data.get("status") != "OK":
                raise ServiceError(f"Polygon error: {response_data.get('error')}")
            data_points = []
            for result in response_data.get("results", []):
                dt = datetime.fromtimestamp(result["t"] / 1000)
                data_point = {
                    "timestamp": dt.isoformat(),
                    "open": float(result["o"]),
                    "high": float(result["h"]),
                    "low": float(result["l"]),
                    "close": float(result["c"]),
                    "volume": float(result["v"]),
                }
                data_points.append(data_point)
            return {"symbol": symbol, "timeframe": timeframe, "data": data_points}
        except Exception as e:
            logger.error(f"Error getting data from Polygon: {e}")
            raise ServiceError(f"Error getting data from Polygon: {str(e)}")

    def _get_data_from_yahoo_finance(
        self, symbol: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get market data from Yahoo Finance

        Args:
            symbol: Symbol to get data for
            timeframe: Data timeframe
            start_date: Start date
            end_date: End date

        Returns:
            Market data

        Raises:
            ServiceError: If there is an error getting data
        """
        try:
            self.data_sources["yahoo_finance"]["rate_limiter"].wait()
            interval_map = {
                "1m": "1m",
                "5m": "5m",
                "15m": "15m",
                "30m": "30m",
                "1h": "1h",
                "1d": "1d",
                "1wk": "1wk",
                "1mo": "1mo",
            }
            if timeframe not in interval_map:
                raise ValidationError(
                    f"Unsupported timeframe for Yahoo Finance: {timeframe}"
                )
            yf_interval = interval_map[timeframe]
            start_timestamp = int(start_date.timestamp())
            end_timestamp = int(end_date.timestamp())
            url = f"{self.data_sources['yahoo_finance']['base_url']}/{symbol}"
            response = requests.get(
                url,
                params={
                    "period1": start_timestamp,
                    "period2": end_timestamp,
                    "interval": yf_interval,
                    "includePrePost": "true",
                    "events": "div,splits",
                },
            )
            if response.status_code != 200:
                raise ServiceError(
                    f"Error getting data from Yahoo Finance: {response.text}"
                )
            response_data = response.json()
            if response_data.get("chart", {}).get("error"):
                raise ServiceError(
                    f"Yahoo Finance error: {response_data['chart']['error']}"
                )
            result = response_data.get("chart", {}).get("result", [])
            if not result:
                raise ServiceError("No data found in Yahoo Finance response")
            timestamps = result[0].get("timestamp", [])
            indicators = result[0].get("indicators", {})
            quote = indicators.get("quote", [{}])[0]
            data_points = []
            for i, timestamp in enumerate(timestamps):
                dt = datetime.fromtimestamp(timestamp)
                data_point = {
                    "timestamp": dt.isoformat(),
                    "open": float(quote.get("open", [])[i] or 0),
                    "high": float(quote.get("high", [])[i] or 0),
                    "low": float(quote.get("low", [])[i] or 0),
                    "close": float(quote.get("close", [])[i] or 0),
                    "volume": float(quote.get("volume", [])[i] or 0),
                }
                data_points.append(data_point)
            return {"symbol": symbol, "timeframe": timeframe, "data": data_points}
        except Exception as e:
            logger.error(f"Error getting data from Yahoo Finance: {e}")
            raise ServiceError(f"Error getting data from Yahoo Finance: {str(e)}")

    def get_data_sources(self) -> List[Dict[str, Any]]:
        """Get all data sources

        Returns:
            List of data sources
        """
        data_sources = []
        for name, config in self.data_sources.items():
            data_source = {
                "name": name,
                "base_url": config["base_url"],
                "status": "active" if config.get("api_key") else "inactive",
            }
            data_sources.append(data_source)
        return data_sources

    def create_data_source(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new data source

        Args:
            data: Data source configuration

        Returns:
            Created data source

        Raises:
            ValidationError: If data is invalid
        """
        if not data.get("name"):
            raise ValidationError("Data source name is required")
        if not data.get("type"):
            raise ValidationError("Data source type is required")
        if not data.get("config"):
            raise ValidationError("Data source configuration is required")
        data_source = {
            "id": f"ds_{uuid.uuid4().hex}",
            "name": data["name"],
            "type": data["type"],
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.data_sources[data["name"]] = {
            "api_key": data["config"].get("api_key"),
            "base_url": data["config"].get("base_url"),
            "rate_limiter": RateLimiter(data["config"].get("rate_limit", 1.0)),
        }
        return data_source

    def get_asset_class_data(
        self,
        asset_class: str,
        timeframe: str = "1d",
        period: Optional[str] = None,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        source: str = "alpha_vantage",
    ) -> Dict[str, Any]:
        """Get market data for a specific asset class (e.g., 'fixed_income', 'commodities', 'crypto').
        This method would typically aggregate data from multiple symbols within that asset class.
        For simplicity, this example will fetch data for a representative symbol.

        Args:
            asset_class: The asset class to retrieve data for.
            timeframe: Data timeframe (e.g., '1m', '1d').
            period: Historical period (e.g., '1y').
            start_date: Start date for custom range.
            end_date: End date for custom range.
            source: Data source to use.

        Returns:
            Market data for the asset class.

        Raises:
            ValidationError: If asset class is not supported.
            ServiceError: If there is an error getting data.
        """
        logger.info(f"Getting market data for asset class: {asset_class}")
        asset_class_symbols = {
            "fixed_income": "AGG",
            "commodities": "GSG",
            "crypto": "BTC-USD",
        }
        if asset_class not in asset_class_symbols:
            raise ValidationError(f"Unsupported asset class: {asset_class}")
        symbol = asset_class_symbols[asset_class]
        return self.get_market_data(
            symbol, timeframe, period, start_date, end_date, source
        )
