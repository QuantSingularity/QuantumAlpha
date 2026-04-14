"""
Feature engineering service for QuantumAlpha Data Service.
Handles feature engineering and technical indicators.
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from backend.common import NotFoundError, SimpleCache, ValidationError, setup_logger
from backend.data_service.market_data import MarketDataService

logger = setup_logger("feature_engineering_service", logging.INFO)


class FeatureEngineeringService:
    """Feature engineering service"""

    def __init__(self, config_manager: Any, db_manager: Any) -> None:
        """Initialize feature engineering service

        Args:
            config_manager: Configuration manager
            db_manager: Database manager
        """
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.market_data_service = MarketDataService(config_manager, db_manager)
        self.cache = SimpleCache(max_size=1000, ttl=300)
        self.available_features = {
            "sma": self._calculate_sma,
            "ema": self._calculate_ema,
            "rsi": self._calculate_rsi,
            "macd": self._calculate_macd,
            "bollinger_bands": self._calculate_bollinger_bands,
            "atr": self._calculate_atr,
            "obv": self._calculate_obv,
            "returns": self._calculate_returns,
            "log_returns": self._calculate_log_returns,
        }
        logger.info("Feature engineering service initialized")

    def get_features(
        self, symbol: str, timeframe: str = "1d", features: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get engineered features for a symbol

        Args:
            symbol: Symbol to get features for
            timeframe: Data timeframe (e.g., '1m', '5m', '1h', '1d')
            features: List of features to calculate (if None, calculate all)

        Returns:
            Engineered features

        Raises:
            ValidationError: If parameters are invalid
            NotFoundError: If data is not found
            ServiceError: If there is an error calculating features
        """
        logger.info(f"Getting features for {symbol} ({timeframe})")
        if not symbol:
            raise ValidationError("Symbol is required")
        if not timeframe:
            raise ValidationError("Timeframe is required")
        if not features:
            features = list(self.available_features.keys())
        for feature in features:
            if feature not in self.available_features:
                raise ValidationError(f"Unsupported feature: {feature}")
        cache_key = f"features:{symbol}:{timeframe}:{','.join(sorted(features))}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.debug(f"Using cached features for {symbol}")
            return cached_data
        market_data = self.market_data_service.get_market_data(
            symbol=symbol, timeframe=timeframe, period="1y"
        )
        if not market_data or not market_data["data"]:
            raise NotFoundError(f"No market data found for {symbol}")
        df = pd.DataFrame(market_data["data"])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        feature_data = {}
        timestamps = df.index.strftime("%Y-%m-%dT%H:%M:%S").tolist()
        for feature in features:
            try:
                feature_data[feature] = self.available_features[feature](df)
            except Exception as e:
                logger.error(f"Error calculating feature {feature}: {e}")
                feature_data[feature] = [None] * len(df)
        response = {
            "symbol": symbol,
            "timeframe": timeframe,
            "features": feature_data,
            "timestamps": timestamps,
        }
        self.cache.set(cache_key, response)
        return response

    def _calculate_sma(self, df: pd.DataFrame, window: int = 20) -> List[float]:
        """Calculate Simple Moving Average

        Args:
            df: DataFrame with market data
            window: Window size

        Returns:
            List of SMA values
        """
        sma = df["close"].rolling(window=window).mean()
        return sma.tolist()

    def _calculate_ema(self, df: pd.DataFrame, window: int = 20) -> List[float]:
        """Calculate Exponential Moving Average

        Args:
            df: DataFrame with market data
            window: Window size

        Returns:
            List of EMA values
        """
        ema = df["close"].ewm(span=window, adjust=False).mean()
        return ema.tolist()

    def _calculate_rsi(self, df: pd.DataFrame, window: int = 14) -> List[float]:
        """Calculate Relative Strength Index

        Args:
            df: DataFrame with market data
            window: Window size

        Returns:
            List of RSI values
        """
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - 100 / (1 + rs)
        return rsi.tolist()

    def _calculate_macd(
        self,
        df: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> List[float]:
        """Calculate Moving Average Convergence Divergence

        Args:
            df: DataFrame with market data
            fast_period: Fast period
            slow_period: Slow period
            signal_period: Signal period

        Returns:
            List of MACD values
        """
        fast_ema = df["close"].ewm(span=fast_period, adjust=False).mean()
        slow_ema = df["close"].ewm(span=slow_period, adjust=False).mean()
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        macd_line - signal_line
        return macd_line.tolist()

    def _calculate_bollinger_bands(
        self, df: pd.DataFrame, window: int = 20, num_std: float = 2.0
    ) -> Dict[str, List[float]]:
        """Calculate Bollinger Bands

        Args:
            df: DataFrame with market data
            window: Window size
            num_std: Number of standard deviations

        Returns:
            Dictionary with upper and lower bands
        """
        sma = df["close"].rolling(window=window).mean()
        std = df["close"].rolling(window=window).std()
        upper_band = sma + std * num_std
        lower_band = sma - std * num_std
        return {
            "middle": sma.tolist(),
            "upper": upper_band.tolist(),
            "lower": lower_band.tolist(),
        }

    def _calculate_atr(self, df: pd.DataFrame, window: int = 14) -> List[float]:
        """Calculate Average True Range

        Args:
            df: DataFrame with market data
            window: Window size

        Returns:
            List of ATR values
        """
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=window).mean()
        return atr.tolist()

    def _calculate_obv(self, df: pd.DataFrame) -> List[float]:
        """Calculate On-Balance Volume

        Args:
            df: DataFrame with market data

        Returns:
            List of OBV values
        """
        price_change = df["close"].diff()
        obv = pd.Series(0, index=df.index)
        obv.iloc[1:] = np.where(
            price_change.iloc[1:] > 0,
            df["volume"].iloc[1:],
            np.where(price_change.iloc[1:] < 0, -df["volume"].iloc[1:], 0),
        ).cumsum()
        return obv.tolist()

    def _calculate_returns(self, df: pd.DataFrame) -> List[float]:
        """Calculate returns

        Args:
            df: DataFrame with market data

        Returns:
            List of return values
        """
        returns = df["close"].pct_change()
        return returns.tolist()

    def _calculate_log_returns(self, df: pd.DataFrame) -> List[float]:
        """Calculate logarithmic returns

        Args:
            df: DataFrame with market data

        Returns:
            List of log return values
        """
        log_returns = np.log(df["close"] / df["close"].shift(1))
        return log_returns.tolist()
