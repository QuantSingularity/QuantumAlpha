"""
Alternative data service for QuantumAlpha Data Service.
Handles alternative data collection, processing, and retrieval.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

import requests
from backend.common import (
    RateLimiter,
    ServiceError,
    SimpleCache,
    ValidationError,
    setup_logger,
)

logger = setup_logger("alternative_data_service", logging.INFO)


class AlternativeDataService:
    """Alternative data service"""

    def __init__(self, config_manager: object, db_manager: object) -> None:
        """Initialize alternative data service

        Args:
            config_manager: Configuration manager
            db_manager: Database manager
        """
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.data_sources = {
            "news_api": {
                "api_key": config_manager.get("api_keys.news_api"),
                "base_url": "https://newsapi.org/v2",
                "rate_limiter": RateLimiter(0.1),
            },
            "twitter": {
                "api_key": config_manager.get("api_keys.twitter"),
                "base_url": "https://api.twitter.com/2",
                "rate_limiter": RateLimiter(1.0),
            },
            "sec_filings": {
                "base_url": "https://www.sec.gov/Archives/edgar/data",
                "rate_limiter": RateLimiter(0.1),
            },
        }
        self.cache = SimpleCache(max_size=1000, ttl=300)
        logger.info("Alternative data service initialized")

    def get_alternative_data(
        self,
        source: str,
        symbol: Optional[str] = None,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> Dict[str, Any]:
        """Get alternative data from a source

        Args:
            source: Data source (e.g., news, twitter, sec)
            symbol: Filter by symbol (optional)
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            Alternative data

        Raises:
            ValidationError: If parameters are invalid
            NotFoundError: If data is not found
            ServiceError: If there is an error getting data
        """
        logger.info(f"Getting alternative data from {source}")
        if not source:
            raise ValidationError("Source is required")
        if start_date and isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if end_date and isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=7)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        cache_key = f"alternative_data:{source}:{symbol or 'all'}:{start_date.isoformat()}:{end_date.isoformat()}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.debug(f"Using cached data for {source}")
            return cached_data
        data = self._get_data_from_db(source, symbol, start_date, end_date)
        if data and len(data["data"]) > 0:
            logger.debug(f"Using database data for {source}")
            self.cache.set(cache_key, data)
            return data
        if source == "news":
            data = self._get_data_from_news_api(symbol, start_date, end_date)
        elif source == "twitter":
            data = self._get_data_from_twitter(symbol, start_date, end_date)
        elif source == "sec":
            data = self._get_data_from_sec_filings(symbol, start_date, end_date)
        else:
            raise ValidationError(f"Unsupported data source: {source}")
        self._store_data_in_db(source, data)
        self.cache.set(cache_key, data)
        return data

    def _get_data_from_db(
        self,
        source: str,
        symbol: Optional[str],
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Get alternative data from database

        Args:
            source: Data source
            symbol: Filter by symbol
            start_date: Start date
            end_date: End date

        Returns:
            Alternative data
        """
        try:
            mongodb_client = self.db_manager.get_mongodb_client()
            db = mongodb_client[self.config_manager.get("mongodb.database")]
            collection_map = {
                "news": "news",
                "twitter": "social_media",
                "sec": "sec_filings",
            }
            if source not in collection_map:
                return {"source": source, "data": []}
            collection = db[collection_map[source]]
            query = {"published_at": {"$gte": start_date, "$lte": end_date}}
            if symbol:
                query["symbols"] = symbol
            cursor = collection.find(query)
            data_points = []
            for document in cursor:
                if "_id" in document:
                    del document["_id"]
                data_points.append(document)
            data_points.sort(key=lambda x: x["published_at"])
            return {"source": source, "data": data_points}
        except Exception as e:
            logger.error(f"Error getting data from database: {e}")
            return {"source": source, "data": []}

    def _store_data_in_db(self, source: str, data: Dict[str, Any]) -> None:
        """Store alternative data in database

        Args:
            source: Data source
            data: Alternative data to store
        """
        try:
            mongodb_client = self.db_manager.get_mongodb_client()
            db = mongodb_client[self.config_manager.get("mongodb.database")]
            collection_map = {
                "news": "news",
                "twitter": "social_media",
                "sec": "sec_filings",
            }
            if source not in collection_map:
                logger.warning(
                    f"Unsupported data source for database storage: {source}"
                )
                return
            collection = db[collection_map[source]]
            for point in data["data"]:
                if "created_at" not in point:
                    point["created_at"] = datetime.now(timezone.utc)
                collection.update_one(
                    (
                        {"url": point.get("url")}
                        if "url" in point
                        else {"id": point.get("id")}
                    ),
                    {"$set": point},
                    upsert=True,
                )
            logger.debug(f"Stored {len(data['data'])} data points in database")
        except Exception as e:
            logger.error(f"Error storing data in database: {e}")

    def _get_data_from_news_api(
        self, symbol: Optional[str], start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get news data from News API

        Args:
            symbol: Filter by symbol
            start_date: Start date
            end_date: End date

        Returns:
            News data

        Raises:
            ServiceError: If there is an error getting data
        """
        try:
            if not self.data_sources["news_api"]["api_key"]:
                raise ServiceError("News API key not configured")
            self.data_sources["news_api"]["rate_limiter"].wait()
            query = symbol if symbol else "stock market OR finance OR investing"
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            url = f"{self.data_sources['news_api']['base_url']}/everything"
            response = requests.get(
                url,
                params={
                    "q": query,
                    "from": start_date_str,
                    "to": end_date_str,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "apiKey": self.data_sources["news_api"]["api_key"],
                },
            )
            if response.status_code != 200:
                raise ServiceError(f"Error getting data from News API: {response.text}")
            response_data = response.json()
            if response_data.get("status") != "ok":
                raise ServiceError(f"News API error: {response_data.get('message')}")
            data_points = []
            for article in response_data.get("articles", []):
                published_at = datetime.fromisoformat(
                    article["publishedAt"].replace("Z", "+00:00")
                )
                symbols = []
                if symbol:
                    symbols.append(symbol)
                data_point = {
                    "headline": article["title"],
                    "source": article["source"]["name"],
                    "url": article["url"],
                    "content": article["content"],
                    "symbols": symbols,
                    "published_at": published_at.isoformat(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                data_point["sentiment"] = 0.0
                data_points.append(data_point)
            return {"source": "news", "data": data_points}
        except Exception as e:
            logger.error(f"Error getting data from News API: {e}")
            raise ServiceError(f"Error getting data from News API: {str(e)}")

    def _get_data_from_twitter(
        self, symbol: Optional[str], start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get Twitter data

        Args:
            symbol: Filter by symbol
            start_date: Start date
            end_date: End date

        Returns:
            Twitter data

        Raises:
            ServiceError: If there is an error getting data
        """
        logger.warning("Twitter API integration not implemented")
        return {"source": "twitter", "data": []}

    def _get_data_from_sec_filings(
        self, symbol: Optional[str], start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get SEC filings data

        Args:
            symbol: Filter by symbol
            start_date: Start date
            end_date: End date

        Returns:
            SEC filings data

        Raises:
            ServiceError: If there is an error getting data
        """
        logger.warning("SEC filings API integration not implemented")
        return {"source": "sec", "data": []}
