"""
Data processor for QuantumAlpha Data Service.
Handles data processing and feature engineering.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from backend.common import ServiceError, ValidationError, setup_logger
from sklearn.preprocessing import MinMaxScaler

logger = setup_logger("data_processor", logging.INFO)


class DataProcessor:
    """Data processor"""

    def __init__(self, config_manager: Any, db_manager: Any) -> None:
        self.config_manager = config_manager
        self.db_manager = db_manager
        logger.info("Data processor initialized")

    def process_market_data(
        self, data: List[Dict[str, Any]], features: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Process market data and calculate features."""
        try:
            if not data:
                raise ValidationError("Data is required")
            df = pd.DataFrame(data)
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df.set_index("timestamp", inplace=True)
            required_columns = ["open", "high", "low", "close", "volume"]
            for col in required_columns:
                if col not in df.columns:
                    raise ValidationError(f"Required column not found: {col}")
            if features:
                df = self._calculate_features(df, features)
            return df
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error processing market data: {e}")
            raise ServiceError(f"Error processing market data: {str(e)}")

    def _calculate_features(
        self, df: pd.DataFrame, features: List[str]
    ) -> pd.DataFrame:
        feature_map = {
            "sma": self._calculate_sma,
            "ema": self._calculate_ema,
            "rsi": self._calculate_rsi,
            "macd": self._calculate_macd,
            "bollinger_bands": self._calculate_bollinger_bands,
            "atr": self._calculate_atr,
            "obv": self._calculate_obv,
            "returns": self._calculate_returns,
            "log_returns": self._calculate_log_returns,
            "momentum": self._calculate_momentum,
        }
        for feature in features:
            if feature in feature_map:
                df = feature_map[feature](df)
            else:
                logger.warning(f"Unsupported feature: {feature}")
        return df

    def _calculate_sma(self, df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        df[f"sma_{window}"] = df["close"].rolling(window=window).mean()
        return df

    def _calculate_ema(self, df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        df[f"ema_{window}"] = df["close"].ewm(span=window, adjust=False).mean()
        return df

    def _calculate_rsi(self, df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        rs = avg_gain / avg_loss.replace(0, np.finfo(float).eps)
        df[f"rsi_{window}"] = 100 - (100 / (1 + rs))
        return df

    def _calculate_macd(
        self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> pd.DataFrame:
        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
        df["macd"] = ema_fast - ema_slow
        df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]
        return df

    def _calculate_bollinger_bands(
        self, df: pd.DataFrame, window: int = 20, num_std: float = 2.0
    ) -> pd.DataFrame:
        sma = df["close"].rolling(window=window).mean()
        std = df["close"].rolling(window=window).std()
        df["bb_upper"] = sma + num_std * std
        df["bb_middle"] = sma
        df["bb_lower"] = sma - num_std * std
        return df

    def _calculate_atr(self, df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df[f"atr_{window}"] = tr.rolling(window=window).mean()
        return df

    def _calculate_obv(self, df: pd.DataFrame) -> pd.DataFrame:
        direction = np.sign(df["close"].diff().fillna(0))
        df["obv"] = (direction * df["volume"]).cumsum()
        return df

    def _calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        df["returns"] = df["close"].pct_change()
        return df

    def _calculate_log_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        df["log_returns"] = np.log(df["close"] / df["close"].shift(1))
        return df

    def _calculate_momentum(self, df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        df[f"momentum_{window}"] = df["close"] - df["close"].shift(window)
        return df

    def normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize close and volume columns using min-max scaling."""
        try:
            result = df.copy()
            scaler = MinMaxScaler()
            for col in ["close", "volume"]:
                if col in result.columns:
                    values = result[col].values.reshape(-1, 1)
                    result[f"{col}_norm"] = scaler.fit_transform(values).flatten()
            return result
        except Exception as e:
            logger.error(f"Error normalizing data: {e}")
            raise ServiceError(f"Error normalizing data: {str(e)}")

    def prepare_data_for_ml(
        self,
        df: pd.DataFrame,
        target_column: str = "close",
        sequence_length: int = 60,
        target_shift: int = 1,
        test_size: float = 0.2,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, MinMaxScaler]:
        """Prepare sequence data for ML training."""
        try:
            feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns]
            data = df[feature_cols].values
            scaler = MinMaxScaler()
            data_scaled = scaler.fit_transform(data)

            target_idx = (
                feature_cols.index(target_column)
                if target_column in feature_cols
                else 0
            )
            X, y = [], []
            for i in range(sequence_length, len(data_scaled) - target_shift + 1):
                X.append(data_scaled[i - sequence_length : i])
                y.append(data_scaled[i + target_shift - 1, target_idx])

            X = np.array(X)
            y = np.array(y)
            split = int(len(X) * (1 - test_size))
            return X[:split], X[split:], y[:split], y[split:], scaler
        except Exception as e:
            logger.error(f"Error preparing data for ML: {e}")
            raise ServiceError(f"Error preparing data for ML: {str(e)}")

    def detect_anomalies(
        self,
        df: pd.DataFrame,
        column: str = "close",
        window: int = 20,
        threshold: float = 2.0,
    ) -> pd.DataFrame:
        """Detect anomalies using rolling z-score."""
        try:
            result = df.copy()
            rolling_mean = result[column].rolling(window=window).mean()
            rolling_std = result[column].rolling(window=window).std()
            z_score = (result[column] - rolling_mean) / rolling_std.replace(
                0, np.finfo(float).eps
            )
            result["z_score"] = z_score
            result["anomaly"] = z_score.abs() > threshold
            return result
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            raise ServiceError(f"Error detecting anomalies: {str(e)}")

    def generate_signals(
        self, df: pd.DataFrame, strategy: str = "sma_crossover"
    ) -> pd.DataFrame:
        """Generate trading signals."""
        try:
            result = df.copy()
            if strategy == "sma_crossover":
                result = self._calculate_sma(result, window=5)
                result = self._calculate_sma(result, window=20)
                short_col, long_col = "sma_5", "sma_20"
                result["signal"] = 0
                result.loc[result[short_col] > result[long_col], "signal"] = 1
                result.loc[result[short_col] < result[long_col], "signal"] = -1
                result["signal"] = result["signal"].fillna(0).astype(int)
            elif strategy == "rsi":
                result = self._calculate_rsi(result)
                result["signal"] = 0
                result.loc[result["rsi_14"] < 30, "signal"] = 1
                result.loc[result["rsi_14"] > 70, "signal"] = -1
                result["signal"] = result["signal"].fillna(0).astype(int)
            else:
                result["signal"] = 0
            return result
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            raise ServiceError(f"Error generating signals: {str(e)}")
