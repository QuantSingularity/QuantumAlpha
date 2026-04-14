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
    def __init__(self, config_manager: Any, db_manager: Any) -> None:
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
        logger.info(f"Getting market data for {symbol} ({timeframe})")

        if not symbol:
            raise ValidationError("Symbol is required")

        now = datetime.now(timezone.utc)
        if period and not (start_date or end_date):
            start_date = parse_period(period)
            end_date = now
        elif start_date and not end_date:
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end_date = now
        elif not (start_date or end_date):
            end_date = now
            start_date = end_date - timedelta(days=30)
        else:
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        cache_key = f"market_data:{symbol}:{timeframe}:{start_date.isoformat()}:{end_date.isoformat()}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data

        data = self._get_data_from_db(symbol, timeframe, start_date, end_date)
        if data and len(data.get("data", [])) > 0:
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

        self._store_data_in_db(data)
        self.cache.set(cache_key, data)
        return data

    def _get_data_from_db(
        self, symbol: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        try:
            client = self.db_manager.get_influxdb_client()
            query_api = client.query_api()
            bucket = self.config_manager.get("influxdb.bucket")

            query = f"""
                from(bucket: "{bucket}")
                    |> range(start: {start_date.isoformat()}, stop: {end_date.isoformat()})
                    |> filter(fn: (r) => r["_measurement"] == "market_data")
                    |> filter(fn: (r) => r["symbol"] == "{symbol}")
                    |> filter(fn: (r) => r["timeframe"] == "{timeframe}")
                    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                    |> sort(columns: ["_time"])
            """

            tables = query_api.query(query, org=self.config_manager.get("influxdb.org"))
            data_points = []
            for table in tables:
                for record in table.records:
                    data_points.append(
                        {
                            "timestamp": record.get_time().isoformat(),
                            "open": record.get_value("open"),
                            "high": record.get_value("high"),
                            "low": record.get_value("low"),
                            "close": record.get_value("close"),
                            "volume": record.get_value("volume"),
                        }
                    )
            return {"symbol": symbol, "timeframe": timeframe, "data": data_points}
        except Exception as e:
            logger.error(f"Database read error: {e}")
            return {"symbol": symbol, "timeframe": timeframe, "data": []}

    def _store_data_in_db(self, data: Dict[str, Any]) -> None:
        try:
            client = self.db_manager.get_influxdb_client()
            write_api = client.write_api(write_options=SYNCHRONOUS)
            points = []

            for pt in data["data"]:
                p = (
                    Point("market_data")
                    .tag("symbol", data["symbol"])
                    .tag("timeframe", data["timeframe"])
                    .field("open", float(pt["open"]))
                    .field("high", float(pt["high"]))
                    .field("low", float(pt["low"]))
                    .field("close", float(pt["close"]))
                    .field("volume", float(pt["volume"]))
                    .time(
                        datetime.fromisoformat(pt["timestamp"].replace("Z", "+00:00"))
                    )
                )
                points.append(p)

            write_api.write(
                bucket=self.config_manager.get("influxdb.bucket"),
                org=self.config_manager.get("influxdb.org"),
                record=points,
            )
        except Exception as e:
            logger.error(f"Database write error: {e}")

    def _get_data_from_alpha_vantage(
        self, symbol: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        self.data_sources["alpha_vantage"]["rate_limiter"].wait()

        interval_map = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "30m": "30min",
            "1h": "60min",
            "1d": "daily",
        }

        if timeframe not in interval_map:
            raise ValidationError(f"Alpha Vantage unsupported timeframe: {timeframe}")

        av_interval = interval_map[timeframe]
        params = {
            "symbol": symbol,
            "apikey": self.data_sources["alpha_vantage"]["api_key"],
            "outputsize": "full",
        }

        if av_interval.endswith("min"):
            params.update({"function": "TIME_SERIES_INTRADAY", "interval": av_interval})
        else:
            params.update({"function": "TIME_SERIES_DAILY"})

        response = requests.get(
            self.data_sources["alpha_vantage"]["base_url"], params=params
        )
        res_data = response.json()

        if "Error Message" in res_data:
            raise ServiceError(f"Alpha Vantage: {res_data['Error Message']}")

        ts_key = next((k for k in res_data if "Time Series" in k), None)
        if not ts_key:
            raise ServiceError("No time series data returned from Alpha Vantage")

        data_points = []
        for ts, vals in res_data[ts_key].items():
            dt = datetime.fromisoformat(ts.replace(" ", "T")).replace(
                tzinfo=timezone.utc
            )
            if start_date <= dt <= end_date:
                data_points.append(
                    {
                        "timestamp": dt.isoformat(),
                        "open": float(vals["1. open"]),
                        "high": float(vals["2. high"]),
                        "low": float(vals["3. low"]),
                        "close": float(vals["4. close"]),
                        "volume": float(vals["5. volume"]),
                    }
                )

        data_points.sort(key=lambda x: x["timestamp"])
        return {"symbol": symbol, "timeframe": timeframe, "data": data_points}

    def _get_data_from_polygon(
        self, symbol: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
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
                dt = datetime.fromtimestamp(result["t"] / 1000, tz=timezone.utc)
                data_points.append(
                    {
                        "timestamp": dt.isoformat(),
                        "open": float(result["o"]),
                        "high": float(result["h"]),
                        "low": float(result["l"]),
                        "close": float(result["c"]),
                        "volume": float(result["v"]),
                    }
                )
            return {"symbol": symbol, "timeframe": timeframe, "data": data_points}
        except Exception as e:
            logger.error(f"Error getting data from Polygon: {e}")
            raise ServiceError(f"Error getting data from Polygon: {str(e)}")

    def _get_data_from_yahoo_finance(
        self, symbol: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        self.data_sources["yahoo_finance"]["rate_limiter"].wait()

        url = f"{self.data_sources['yahoo_finance']['base_url']}/{symbol}"
        params = {
            "period1": int(start_date.timestamp()),
            "period2": int(end_date.timestamp()),
            "interval": timeframe,
            "includePrePost": "true",
        }

        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise ServiceError(f"Yahoo Finance API failure: {response.status_code}")

        res_data = response.json()
        result = res_data.get("chart", {}).get("result", [])
        if not result:
            raise ServiceError("No Yahoo Finance results found")

        timestamps = result[0].get("timestamp", [])
        quote = result[0].get("indicators", {}).get("quote", [{}])[0]

        data_points = []
        for i, ts in enumerate(timestamps):
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            data_points.append(
                {
                    "timestamp": dt.isoformat(),
                    "open": float(quote.get("open", [])[i] or 0),
                    "high": float(quote.get("high", [])[i] or 0),
                    "low": float(quote.get("low", [])[i] or 0),
                    "close": float(quote.get("close", [])[i] or 0),
                    "volume": float(quote.get("volume", [])[i] or 0),
                }
            )

        return {"symbol": symbol, "timeframe": timeframe, "data": data_points}

    def get_data_sources(self) -> List[Dict[str, Any]]:
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
