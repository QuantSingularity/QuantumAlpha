"""
Data processor for QuantumAlpha Data Service.
Handles data processing and feature engineering.
"""

import logging
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pywt
import seaborn as sns
import statsmodels.api as sm
import talib
from common.exceptions import NotFoundError, ServiceError, ValidationError
from common.logging_config import setup_logging
from hurst import compute_Hc
from pykalman import KalmanFilter
from scipy import stats
from sklearn.preprocessing import MinMaxScaler
from statsmodels.tsa.stattools import coint, grangercausalitytests

setup_logging(logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessor:
    """Data processor"""

    def __init__(self, config_manager: Any, db_manager: Any) -> None:
        """
        Initializes the DataProcessor with configuration and database managers.

        :param config_manager: Configuration manager instance.
        :param db_manager: Database manager instance.
        """
        self.config_manager = config_manager
        self.db_manager = db_manager
        logger.info("Data processor initialized")

    def process_market_data(
        self, data: List[Dict[str, Any]], features: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Process market data and calculate features

        Args:
            data: Market data
            features: List of features to calculate

        Returns:
            Processed data as DataFrame

        Raises:
            ValidationError: If data is invalid
        """
        try:
            logger.info("Processing market data")
            if not data:
                raise ValidationError("Data is required")
            df = pd.DataFrame(data)
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df.set_index("timestamp", inplace=True)
            required_columns = ["open", "high", "low", "close", "volume"]
            for column in required_columns:
                if column not in df.columns:
                    raise ValidationError(f"Required column not found: {column}")
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
        """Calculate features

        Args:
            df: DataFrame with market data
            features: List of features to calculate

        Returns:
            DataFrame with calculated features
        """
        feature_functions = {
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
            "roc": self._calculate_roc,
            "stochastic": self._calculate_stochastic,
            "williams_r": self._calculate_williams_r,
            "adx": self._calculate_adx,
            "cci": self._calculate_cci,
            "aroon": self._calculate_aroon,
            "ichimoku": self._calculate_ichimoku,
        }
        for feature in features:
            if feature in feature_functions:
                df = feature_functions[feature](df)
            else:
                logger.warning(f"Unsupported feature: {feature}")
        return df

    def _calculate_sma(self, df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """Calculate Simple Moving Average

        Args:
            df: DataFrame with market data
            window: Window size

        Returns:
            DataFrame with SMA
        """
        df[f"sma_{window}"] = talib.SMA(df["close"].values, timeperiod=window)
        return df

    def _calculate_ema(self, df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """Calculate Exponential Moving Average

        Args:
            df: DataFrame with market data
            window: Window size

        Returns:
            DataFrame with EMA
        """
        df[f"ema_{window}"] = talib.EMA(df["close"].values, timeperiod=window)
        return df

    def _calculate_rsi(self, df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """Calculate Relative Strength Index

        Args:
            df: DataFrame with market data
            window: Window size

        Returns:
            DataFrame with RSI
        """
        df[f"rsi_{window}"] = talib.RSI(df["close"].values, timeperiod=window)
        return df

    def _calculate_macd(
        self,
        df: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> pd.DataFrame:
        """Calculate Moving Average Convergence Divergence

        Args:
            df: DataFrame with market data
            fast_period: Fast period
            slow_period: Slow period
            signal_period: Signal period

        Returns:
            DataFrame with MACD
        """
        macd, signal, hist = talib.MACD(
            df["close"].values,
            fastperiod=fast_period,
            slowperiod=slow_period,
            signalperiod=signal_period,
        )
        df["macd"] = macd
        df["macd_signal"] = signal
        df["macd_hist"] = hist
        return df

    def _calculate_bollinger_bands(
        self, df: pd.DataFrame, window: int = 20, num_std: float = 2.0
    ) -> pd.DataFrame:
        """Calculate Bollinger Bands

        Args:
            df: DataFrame with market data
            window: Window size
            num_std: Number of standard deviations

        Returns:
            DataFrame with Bollinger Bands
        """
        upper, middle, lower = talib.BBANDS(
            df["close"].values,
            timeperiod=window,
            nbdevup=num_std,
            nbdevdn=num_std,
            matype=0,
        )
        df["bb_upper"] = upper
        df["bb_middle"] = middle
        df["bb_lower"] = lower
        return df

    def _calculate_atr(self, df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """Calculate Average True Range

        Args:
            df: DataFrame with market data
            window: Window size

        Returns:
            DataFrame with ATR
        """
        df[f"atr_{window}"] = talib.ATR(
            df["high"].values, df["low"].values, df["close"].values, timeperiod=window
        )
        return df

    def _calculate_obv(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate On-Balance Volume

        Args:
            df: DataFrame with market data

        Returns:
            DataFrame with OBV
        """
        df["obv"] = talib.OBV(df["close"].values, df["volume"].values)
        return df

    def _calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate returns

        Args:
            df: DataFrame with market data

        Returns:
            DataFrame with returns
        """
        df["returns"] = df["close"].pct_change()
        return df

    def _calculate_log_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate logarithmic returns

        Args:
            df: DataFrame with market data

        Returns:
            DataFrame with log returns
        """
        df["log_returns"] = np.log(df["close"] / df["close"].shift(1))
        return df

    def _calculate_momentum(self, df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        """Calculate momentum

        Args:
            df: DataFrame with market data
            window: Window size

        Returns:
            DataFrame with momentum
        """
        df[f"momentum_{window}"] = df["close"] - df["close"].shift(window)
        return df

    def _calculate_roc(self, df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        """Calculate Rate of Change

        Args:
            df: DataFrame with market data
            window: Window size

        Returns:
            DataFrame with ROC
        """
        df[f"roc_{window}"] = talib.ROC(df["close"].values, timeperiod=window)
        return df

    def _calculate_stochastic(
        self,
        df: pd.DataFrame,
        fastk_period: int = 5,
        slowk_period: int = 3,
        slowd_period: int = 3,
    ) -> pd.DataFrame:
        """Calculate Stochastic Oscillator

        Args:
            df: DataFrame with market data
            fastk_period: Fast K period
            slowk_period: Slow K period
            slowd_period: Slow D period

        Returns:
            DataFrame with Stochastic Oscillator
        """
        slowk, slowd = talib.STOCH(
            df["high"].values,
            df["low"].values,
            df["close"].values,
            fastk_period=fastk_period,
            slowk_period=slowk_period,
            slowk_matype=0,
            slowd_period=slowd_period,
            slowd_matype=0,
        )
        df["stoch_k"] = slowk
        df["stoch_d"] = slowd
        return df

    def _calculate_williams_r(self, df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """Calculate Williams %R

        Args:
            df: DataFrame with market data
            window: Window size

        Returns:
            DataFrame with Williams %R
        """
        df[f"williams_r_{window}"] = talib.WILLR(
            df["high"].values, df["low"].values, df["close"].values, timeperiod=window
        )
        return df

    def _calculate_adx(self, df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """Calculate Average Directional Index

        Args:
            df: DataFrame with market data
            window: Window size

        Returns:
            DataFrame with ADX
        """
        df[f"adx_{window}"] = talib.ADX(
            df["high"].values, df["low"].values, df["close"].values, timeperiod=window
        )
        return df

    def _calculate_cci(self, df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """Calculate Commodity Channel Index

        Args:
            df: DataFrame with market data
            window: Window size

        Returns:
            DataFrame with CCI
        """
        df[f"cci_{window}"] = talib.CCI(
            df["high"].values, df["low"].values, df["close"].values, timeperiod=window
        )
        return df

    def _calculate_aroon(self, df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """Calculate Aroon Oscillator

        Args:
            df: DataFrame with market data
            window: Window size

        Returns:
            DataFrame with Aroon Oscillator
        """
        aroon_down, aroon_up = talib.AROON(
            df["high"].values, df["low"].values, timeperiod=window
        )
        df[f"aroon_up_{window}"] = aroon_up
        df[f"aroon_down_{window}"] = aroon_down
        df[f"aroon_oscillator_{window}"] = aroon_up - aroon_down
        return df

    def _calculate_ichimoku(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Ichimoku Cloud components

        Args:
            df: DataFrame with market data

        Returns:
            DataFrame with Ichimoku Cloud components
        """
        high_9 = df["high"].rolling(window=9).max()
        low_9 = df["low"].rolling(window=9).min()
        df["tenkan_sen"] = (high_9 + low_9) / 2
        high_26 = df["high"].rolling(window=26).max()
        low_26 = df["low"].rolling(window=26).min()
        df["kijun_sen"] = (high_26 + low_26) / 2
        df["senkou_span_a"] = ((df["tenkan_sen"] + df["kijun_sen"]) / 2).shift(26)
        high_52 = df["high"].rolling(window=52).max()
        low_52 = df["low"].rolling(window=52).min()
        df["senkou_span_b"] = ((high_52 + low_52) / 2).shift(26)
        df["chikou_span"] = df["close"].shift(-26)
        return df

    def normalize_data(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """Normalize data using MinMaxScaler

        Args:
            df: DataFrame with data
            columns: List of columns to normalize

        Returns:
            DataFrame with normalized data
        """
        try:
            logger.info(f"Normalizing columns: {columns}")
            scaler = MinMaxScaler()
            df[columns] = scaler.fit_transform(df[columns])
            return df
        except Exception as e:
            logger.error(f"Error normalizing data: {e}")
            raise ServiceError(f"Error normalizing data: {str(e)}")

    def denormalize_data(
        self, df: pd.DataFrame, columns: List[str], scaler: MinMaxScaler
    ) -> pd.DataFrame:
        """Denormalize data using MinMaxScaler

        Args:
            df: DataFrame with normalized data
            columns: List of columns to denormalize
            scaler: MinMaxScaler instance used for normalization

        Returns:
            DataFrame with denormalized data
        """
        try:
            logger.info(f"Denormalizing columns: {columns}")
            df[columns] = scaler.inverse_transform(df[columns])
            return df
        except Exception as e:
            logger.error(f"Error denormalizing data: {e}")
            raise ServiceError(f"Error denormalizing data: {str(e)}")

    def resample_data(
        self, df: pd.DataFrame, rule: str = "D", aggregation: str = "last"
    ) -> pd.DataFrame:
        """Resample data to a different frequency

        Args:
            df: DataFrame with data
            rule: Resampling rule (e.g., 'D' for daily, 'W' for weekly)
            aggregation: Aggregation method ('first', 'last', 'mean', 'sum')

        Returns:
            DataFrame with resampled data
        """
        try:
            logger.info(f"Resampling data to {rule} with {aggregation} aggregation")
            aggregation_methods = {
                "first": "first",
                "last": "last",
                "mean": "mean",
                "sum": "sum",
            }
            if aggregation not in aggregation_methods:
                raise ValidationError(f"Unsupported aggregation method: {aggregation}")
            df_resampled = df.resample(rule).agg(aggregation_methods[aggregation])
            return df_resampled
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error resampling data: {e}")
            raise ServiceError(f"Error resampling data: {str(e)}")

    def fill_missing_data(
        self, df: pd.DataFrame, method: str = "ffill"
    ) -> pd.DataFrame:
        """Fill missing data

        Args:
            df: DataFrame with data
            method: Filling method ('ffill', 'bfill', 'mean', 'median')

        Returns:
            DataFrame with filled data
        """
        try:
            logger.info(f"Filling missing data with method: {method}")
            filling_methods = {
                "ffill": "ffill",
                "bfill": "bfill",
                "mean": "mean",
                "median": "median",
            }
            if method not in filling_methods:
                raise ValidationError(f"Unsupported filling method: {method}")
            if method == "ffill":
                df_filled = df.ffill()
            elif method == "bfill":
                df_filled = df.bfill()
            elif method == "mean":
                df_filled = df.fillna(df.mean())
            elif method == "median":
                df_filled = df.fillna(df.median())
            else:
                df_filled = df
            return df_filled
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error filling missing data: {e}")
            raise ServiceError(f"Error filling missing data: {str(e)}")

    def remove_outliers(
        self, df: pd.DataFrame, columns: List[str], method: str = "iqr"
    ) -> pd.DataFrame:
        """Remove outliers

        Args:
            df: DataFrame with data
            columns: List of columns to remove outliers from
            method: Outlier removal method ('iqr', 'zscore')

        Returns:
            DataFrame with outliers removed
        """
        try:
            logger.info(
                f"Removing outliers from columns: {columns} with method: {method}"
            )
            outlier_methods = {
                "iqr": self._remove_outliers_iqr,
                "zscore": self._remove_outliers_zscore,
            }
            if method not in outlier_methods:
                raise ValidationError(f"Unsupported outlier removal method: {method}")
            df_cleaned = outlier_methods[method](df, columns)
            return df_cleaned
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error removing outliers: {e}")
            raise ServiceError(f"Error removing outliers: {str(e)}")

    def _remove_outliers_iqr(
        self, df: pd.DataFrame, columns: List[str]
    ) -> pd.DataFrame:
        """Remove outliers using Interquartile Range (IQR)

        Args:
            df: DataFrame with data
            columns: List of columns to remove outliers from

        Returns:
            DataFrame with outliers removed
        """
        df_cleaned = df.copy()
        for column in columns:
            Q1 = df_cleaned[column].quantile(0.25)
            Q3 = df_cleaned[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df_cleaned = df_cleaned[
                (df_cleaned[column] >= lower_bound)
                & (df_cleaned[column] <= upper_bound)
            ]
        return df_cleaned

    def _remove_outliers_zscore(
        self, df: pd.DataFrame, columns: List[str], threshold: float = 3.0
    ) -> pd.DataFrame:
        """Remove outliers using Z-score

        Args:
            df: DataFrame with data
            columns: List of columns to remove outliers from
            threshold: Z-score threshold

        Returns:
            DataFrame with outliers removed
        """
        df_cleaned = df.copy()
        for column in columns:
            z_scores = np.abs(
                (df_cleaned[column] - df_cleaned[column].mean())
                / df_cleaned[column].std()
            )
            df_cleaned = df_cleaned[z_scores < threshold]
        return df_cleaned

    def create_lagged_features(
        self, df: pd.DataFrame, columns: List[str], lags: List[int]
    ) -> pd.DataFrame:
        """Create lagged features

        Args:
            df: DataFrame with data
            columns: List of columns to create lagged features from
            lags: List of lag periods

        Returns:
            DataFrame with lagged features
        """
        try:
            logger.info(
                f"Creating lagged features for columns: {columns} with lags: {lags}"
            )
            for column in columns:
                for lag in lags:
                    df[f"{column}_lag_{lag}"] = df[column].shift(lag)
            return df
        except Exception as e:
            logger.error(f"Error creating lagged features: {e}")
            raise ServiceError(f"Error creating lagged features: {str(e)}")

    def create_rolling_features(
        self, df: pd.DataFrame, columns: List[str], windows: List[int]
    ) -> pd.DataFrame:
        """Create rolling window features

        Args:
            df: DataFrame with data
            columns: List of columns to create rolling features from
            windows: List of rolling window sizes

        Returns:
            DataFrame with rolling features
        """
        try:
            logger.info(
                f"Creating rolling features for columns: {columns} with windows: {windows}"
            )
            for column in columns:
                for window in windows:
                    df[f"{column}_rolling_mean_{window}"] = (
                        df[column].rolling(window=window).mean()
                    )
                    df[f"{column}_rolling_std_{window}"] = (
                        df[column].rolling(window=window).std()
                    )
            return df
        except Exception as e:
            logger.error(f"Error creating rolling features: {e}")
            raise ServiceError(f"Error creating rolling features: {str(e)}")

    def create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create time-based features

        Args:
            df: DataFrame with data (index must be datetime)

        Returns:
            DataFrame with time-based features
        """
        try:
            logger.info("Creating time-based features")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for time features"
                )
            df["year"] = df.index.year
            df["month"] = df.index.month
            df["day"] = df.index.day
            df["dayofweek"] = df.index.dayofweek
            df["dayofyear"] = df.index.dayofyear
            df["weekofyear"] = df.index.isocalendar().week.astype(int)
            df["quarter"] = df.index.quarter
            df["is_month_start"] = df.index.is_month_start.astype(int)
            df["is_month_end"] = df.index.is_month_end.astype(int)
            df["is_quarter_start"] = df.index.is_quarter_start.astype(int)
            df["is_quarter_end"] = df.index.is_quarter_end.astype(int)
            df["is_year_start"] = df.index.is_year_start.astype(int)
            df["is_year_end"] = df.index.is_year_end.astype(int)
            return df
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating time-based features: {e}")
            raise ServiceError(f"Error creating time-based features: {str(e)}")

    def create_target_variable(
        self, df: pd.DataFrame, column: str = "close", periods: int = 1
    ) -> pd.DataFrame:
        """Create a target variable (e.g., future returns)

        Args:
            df: DataFrame with data
            column: Column to use for target variable
            periods: Number of periods to shift for the future value

        Returns:
            DataFrame with target variable
        """
        try:
            logger.info(
                f"Creating target variable from {column} with {periods} periods shift"
            )
            df["target_return"] = df[column].pct_change(periods=periods).shift(-periods)
            return df
        except Exception as e:
            logger.error(f"Error creating target variable: {e}")
            raise ServiceError(f"Error creating target variable: {str(e)}")

    def split_data(
        self,
        df: pd.DataFrame,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
    ) -> Dict[str, pd.DataFrame]:
        """Split data into training, validation, and test sets

        Args:
            df: DataFrame with data
            train_ratio: Training set ratio
            val_ratio: Validation set ratio
            test_ratio: Test set ratio

        Returns:
            Dictionary with split DataFrames
        """
        try:
            logger.info(
                f"Splitting data with train_ratio: {train_ratio}, val_ratio: {val_ratio}, test_ratio: {test_ratio}"
            )
            if not np.isclose(train_ratio + val_ratio + test_ratio, 1.0):
                raise ValidationError("Ratios must sum to 1.0")
            n = len(df)
            train_end = int(n * train_ratio)
            val_end = train_end + int(n * val_ratio)
            train_df = df.iloc[:train_end]
            val_df = df.iloc[train_end:val_end]
            test_df = df.iloc[val_end:]
            return {"train": train_df, "val": val_df, "test": test_df}
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error splitting data: {e}")
            raise ServiceError(f"Error splitting data: {str(e)}")

    def save_processed_data(
        self, df: pd.DataFrame, file_path: str, file_format: str = "csv"
    ) -> None:
        """Save processed data to a file

        Args:
            df: DataFrame with processed data
            file_path: Path to save the file
            file_format: File format ('csv', 'parquet', 'json')
        """
        try:
            logger.info(f"Saving processed data to {file_path} in {file_format} format")
            saving_methods = {
                "csv": df.to_csv,
                "parquet": df.to_parquet,
                "json": df.to_json,
            }
            if file_format not in saving_methods:
                raise ValidationError(f"Unsupported file format: {file_format}")
            saving_methods[file_format](file_path)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error saving processed data: {e}")
            raise ServiceError(f"Error saving processed data: {str(e)}")

    def load_processed_data(
        self, file_path: str, file_format: str = "csv"
    ) -> pd.DataFrame:
        """Load processed data from a file

        Args:
            file_path: Path to the file
            file_format: File format ('csv', 'parquet', 'json')

        Returns:
            DataFrame with loaded data
        """
        try:
            logger.info(
                f"Loading processed data from {file_path} in {file_format} format"
            )
            loading_methods = {
                "csv": pd.read_csv,
                "parquet": pd.read_parquet,
                "json": pd.read_json,
            }
            if file_format not in loading_methods:
                raise ValidationError(f"Unsupported file format: {file_format}")
            df = loading_methods[file_format](file_path)
            return df
        except ValidationError:
            raise
        except FileNotFoundError:
            raise NotFoundError(f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Error loading processed data: {e}")
            raise ServiceError(f"Error loading processed data: {str(e)}")

    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get a summary of the data

        Args:
            df: DataFrame with data

        Returns:
            Dictionary with data summary
        """
        try:
            logger.info("Getting data summary")
            summary = df.describe(include="all").to_dict()
            missing_values = df.isnull().sum().to_dict()
            data_types = df.dtypes.astype(str).to_dict()
            return {
                "summary": summary,
                "missing_values": missing_values,
                "data_types": data_types,
                "shape": df.shape,
            }
        except Exception as e:
            logger.error(f"Error getting data summary: {e}")
            raise ServiceError(f"Error getting data summary: {str(e)}")

    def get_feature_importance(
        self, model: Any, feature_names: List[str]
    ) -> Dict[str, float]:
        """Get feature importance from a trained model

        Args:
            model: Trained model (e.g., scikit-learn model with feature_importances_ attribute)
            feature_names: List of feature names

        Returns:
            Dictionary with feature importance scores
        """
        try:
            logger.info("Getting feature importance")
            if hasattr(model, "feature_importances_"):
                importance = model.feature_importances_
            elif hasattr(model, "coef_"):
                importance = model.coef_
            else:
                raise ValidationError(
                    "Model does not have feature importance attribute"
                )
            feature_importance = dict(zip(feature_names, importance))
            return feature_importance
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            raise ServiceError(f"Error getting feature importance: {str(e)}")

    def get_model_predictions(self, model: Any, X: pd.DataFrame) -> np.ndarray:
        """Get model predictions

        Args:
            model: Trained model
            X: DataFrame with features

        Returns:
            Array with model predictions
        """
        try:
            logger.info("Getting model predictions")
            predictions = model.predict(X)
            return predictions
        except Exception as e:
            logger.error(f"Error getting model predictions: {e}")
            raise ServiceError(f"Error getting model predictions: {str(e)}")

    def get_model_metrics(
        self, y_true: np.ndarray, y_pred: np.ndarray, metrics: List[str]
    ) -> Dict[str, float]:
        """Get model metrics

        Args:
            y_true: True target values
            y_pred: Predicted target values
            metrics: List of metrics to calculate ('mse', 'rmse', 'mae', 'r2')

        Returns:
            Dictionary with model metrics
        """
        try:
            logger.info(f"Getting model metrics: {metrics}")
            metric_functions = {
                "mse": lambda y_true, y_pred: np.mean((y_true - y_pred) ** 2),
                "rmse": lambda y_true, y_pred: np.sqrt(np.mean((y_true - y_pred) ** 2)),
                "mae": lambda y_true, y_pred: np.mean(np.abs(y_true - y_pred)),
                "r2": lambda y_true, y_pred: 1
                - np.sum((y_true - y_pred) ** 2)
                / np.sum((y_true - np.mean(y_true)) ** 2),
            }
            model_metrics = {}
            for metric in metrics:
                if metric in metric_functions:
                    model_metrics[metric] = metric_functions[metric](y_true, y_pred)
                else:
                    logger.warning(f"Unsupported metric: {metric}")
            return model_metrics
        except Exception as e:
            logger.error(f"Error getting model metrics: {e}")
            raise ServiceError(f"Error getting model metrics: {str(e)}")

    def get_model_performance(
        self, model: Any, X: pd.DataFrame, y_true: np.ndarray, metrics: List[str]
    ) -> Dict[str, float]:
        """Get model performance

        Args:
            model: Trained model
            X: DataFrame with features
            y_true: True target values
            metrics: List of metrics to calculate

        Returns:
            Dictionary with model performance metrics
        """
        try:
            logger.info("Getting model performance")
            y_pred = self.get_model_predictions(model, X)
            model_metrics = self.get_model_metrics(y_true, y_pred, metrics)
            return model_metrics
        except Exception as e:
            logger.error(f"Error getting model performance: {e}")
            raise ServiceError(f"Error getting model performance: {str(e)}")

    def get_model_summary(self, model: Any) -> Dict[str, Any]:
        """Get a summary of the trained model

        Args:
            model: Trained model

        Returns:
            Dictionary with model summary
        """
        try:
            logger.info("Getting model summary")
            model_type = type(model).__name__
            model_params = model.get_params()
            return {"model_type": model_type, "model_params": model_params}
        except Exception as e:
            logger.error(f"Error getting model summary: {e}")
            raise ServiceError(f"Error getting model summary: {str(e)}")

    def get_model_visualization(
        self, model: Any, X: pd.DataFrame, y_true: np.ndarray
    ) -> Any:
        """Get model visualization (e.g., prediction vs actual plot)

        Args:
            model: Trained model
            X: DataFrame with features
            y_true: True target values
        """
        try:
            logger.info("Getting model visualization")
            y_pred = self.get_model_predictions(model, X)
            plt.figure(figsize=(12, 6))
            plt.plot(y_true, label="Actual")
            plt.plot(y_pred, label="Prediction")
            plt.title("Model Prediction vs Actual")
            plt.xlabel("Time")
            plt.ylabel("Value")
            plt.legend()
            plt.show()
        except Exception as e:
            logger.error(f"Error getting model visualization: {e}")
            raise ServiceError(f"Error getting model visualization: {str(e)}")

    def get_feature_correlation(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get feature correlation matrix

        Args:
            df: DataFrame with data

        Returns:
            DataFrame with correlation matrix
        """
        try:
            logger.info("Getting feature correlation")
            correlation_matrix = df.corr()
            return correlation_matrix
        except Exception as e:
            logger.error(f"Error getting feature correlation: {e}")
            raise ServiceError(f"Error getting feature correlation: {str(e)}")

    def get_feature_distribution(self, df: pd.DataFrame, column: str) -> Any:
        """Get feature distribution plot

        Args:
            df: DataFrame with data
            column: Column to plot distribution for
        """
        try:
            logger.info(f"Getting feature distribution for column: {column}")
            plt.figure(figsize=(10, 6))
            sns.histplot(df[column], kde=True)
            plt.title(f"Distribution of {column}")
            plt.xlabel(column)
            plt.ylabel("Frequency")
            plt.show()
        except Exception as e:
            logger.error(f"Error getting feature distribution: {e}")
            raise ServiceError(f"Error getting feature distribution: {str(e)}")

    def get_time_series_plot(self, df: pd.DataFrame, column: str) -> Any:
        """Get time series plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to plot
        """
        try:
            logger.info(f"Getting time series plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for time series plot"
                )
            plt.figure(figsize=(12, 6))
            plt.plot(df[column])
            plt.title(f"Time Series of {column}")
            plt.xlabel("Time")
            plt.ylabel(column)
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting time series plot: {e}")
            raise ServiceError(f"Error getting time series plot: {str(e)}")

    def get_candlestick_plot(self, df: pd.DataFrame) -> Any:
        """Get candlestick plot

        Args:
            df: DataFrame with market data (index must be datetime)
        """
        try:
            logger.info("Getting candlestick plot")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for candlestick plot"
                )
            fig = go.Figure(
                data=[
                    go.Candlestick(
                        x=df.index,
                        open=df["open"],
                        high=df["high"],
                        low=df["low"],
                        close=df["close"],
                    )
                ]
            )
            fig.update_layout(
                title="Candlestick Plot",
                xaxis_title="Time",
                yaxis_title="Price",
                xaxis_rangeslider_visible=False,
            )
            fig.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting candlestick plot: {e}")
            raise ServiceError(f"Error getting candlestick plot: {str(e)}")

    def get_technical_indicator_plot(
        self, df: pd.DataFrame, indicator: str, column: str = "close"
    ) -> Any:
        """Get technical indicator plot

        Args:
            df: DataFrame with market data (index must be datetime)
            indicator: Technical indicator to plot (e.g., 'sma', 'rsi')
            column: Column to use for indicator calculation
        """
        try:
            logger.info(f"Getting technical indicator plot for {indicator}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for technical indicator plot"
                )
            if indicator == "sma":
                df = self._calculate_sma(df)
                indicator_column = "sma_20"
            elif indicator == "ema":
                df = self._calculate_ema(df)
                indicator_column = "ema_20"
            elif indicator == "rsi":
                df = self._calculate_rsi(df)
                indicator_column = "rsi_14"
            elif indicator == "macd":
                df = self._calculate_macd(df)
                indicator_column = "macd"
            elif indicator == "bollinger_bands":
                df = self._calculate_bollinger_bands(df)
                indicator_column = "bb_middle"
            elif indicator == "atr":
                df = self._calculate_atr(df)
                indicator_column = "atr_14"
            elif indicator == "obv":
                df = self._calculate_obv(df)
                indicator_column = "obv"
            elif indicator == "returns":
                df = self._calculate_returns(df)
                indicator_column = "returns"
            elif indicator == "log_returns":
                df = self._calculate_log_returns(df)
                indicator_column = "log_returns"
            elif indicator == "momentum":
                df = self._calculate_momentum(df)
                indicator_column = "momentum_10"
            elif indicator == "roc":
                df = self._calculate_roc(df)
                indicator_column = "roc_10"
            elif indicator == "stochastic":
                df = self._calculate_stochastic(df)
                indicator_column = "stoch_k"
            elif indicator == "williams_r":
                df = self._calculate_williams_r(df)
                indicator_column = "williams_r_14"
            elif indicator == "adx":
                df = self._calculate_adx(df)
                indicator_column = "adx_14"
            elif indicator == "cci":
                df = self._calculate_cci(df)
                indicator_column = "cci_14"
            elif indicator == "aroon":
                df = self._calculate_aroon(df)
                indicator_column = "aroon_oscillator_14"
            elif indicator == "ichimoku":
                df = self._calculate_ichimoku(df)
                indicator_column = "tenkan_sen"
            else:
                raise ValidationError(f"Unsupported indicator: {indicator}")
            plt.figure(figsize=(12, 6))
            plt.plot(df[column], label=column)
            plt.plot(df[indicator_column], label=indicator_column)
            plt.title(f"{indicator} Plot")
            plt.xlabel("Time")
            plt.ylabel("Value")
            plt.legend()
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting technical indicator plot: {e}")
            raise ServiceError(f"Error getting technical indicator plot: {str(e)}")

    def get_feature_heatmap(self, df: pd.DataFrame) -> Any:
        """Get feature correlation heatmap

        Args:
            df: DataFrame with data
        """
        try:
            logger.info("Getting feature correlation heatmap")
            correlation_matrix = self.get_feature_correlation(df)
            plt.figure(figsize=(12, 10))
            sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", fmt=".2f")
            plt.title("Feature Correlation Heatmap")
            plt.show()
        except Exception as e:
            logger.error(f"Error getting feature correlation heatmap: {e}")
            raise ServiceError(f"Error getting feature correlation heatmap: {str(e)}")

    def get_scatter_plot(self, df: pd.DataFrame, x_column: str, y_column: str) -> Any:
        """Get scatter plot

        Args:
            df: DataFrame with data
            x_column: X-axis column
            y_column: Y-axis column
        """
        try:
            logger.info(f"Getting scatter plot for {x_column} vs {y_column}")
            plt.figure(figsize=(10, 6))
            sns.scatterplot(x=df[x_column], y=df[y_column])
            plt.title(f"Scatter Plot of {x_column} vs {y_column}")
            plt.xlabel(x_column)
            plt.ylabel(y_column)
            plt.show()
        except Exception as e:
            logger.error(f"Error getting scatter plot: {e}")
            raise ServiceError(f"Error getting scatter plot: {str(e)}")

    def get_box_plot(self, df: pd.DataFrame, column: str) -> Any:
        """Get box plot

        Args:
            df: DataFrame with data
            column: Column to plot box plot for
        """
        try:
            logger.info(f"Getting box plot for column: {column}")
            plt.figure(figsize=(8, 6))
            sns.boxplot(y=df[column])
            plt.title(f"Box Plot of {column}")
            plt.ylabel(column)
            plt.show()
        except Exception as e:
            logger.error(f"Error getting box plot: {e}")
            raise ServiceError(f"Error getting box plot: {str(e)}")

    def get_violin_plot(self, df: pd.DataFrame, column: str) -> Any:
        """Get violin plot

        Args:
            df: DataFrame with data
            column: Column to plot violin plot for
        """
        try:
            logger.info(f"Getting violin plot for column: {column}")
            plt.figure(figsize=(8, 6))
            sns.violinplot(y=df[column])
            plt.title(f"Violin Plot of {column}")
            plt.ylabel(column)
            plt.show()
        except Exception as e:
            logger.error(f"Error getting violin plot: {e}")
            raise ServiceError(f"Error getting violin plot: {str(e)}")

    def get_pair_plot(self, df: pd.DataFrame, columns: List[str]) -> Any:
        """Get pair plot

        Args:
            df: DataFrame with data
            columns: List of columns to include in the pair plot
        """
        try:
            logger.info(f"Getting pair plot for columns: {columns}")
            sns.pairplot(df[columns])
            plt.show()
        except Exception as e:
            logger.error(f"Error getting pair plot: {e}")
            raise ServiceError(f"Error getting pair plot: {str(e)}")

    def get_autocorrelation_plot(
        self, df: pd.DataFrame, column: str, lags: int = 20
    ) -> Any:
        """Get autocorrelation plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to plot autocorrelation for
            lags: Number of lags to include
        """
        try:
            logger.info(f"Getting autocorrelation plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for autocorrelation plot"
                )
            plt.figure(figsize=(12, 6))
            pd.plotting.autocorrelation_plot(df[column], ax=plt.gca())
            plt.title(f"Autocorrelation Plot of {column}")
            plt.xlim(0, lags)
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting autocorrelation plot: {e}")
            raise ServiceError(f"Error getting autocorrelation plot: {str(e)}")

    def get_partial_autocorrelation_plot(
        self, df: pd.DataFrame, column: str, lags: int = 20
    ) -> Any:
        """Get partial autocorrelation plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to plot partial autocorrelation for
            lags: Number of lags to include
        """
        try:
            logger.info(f"Getting partial autocorrelation plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for partial autocorrelation plot"
                )
            plt.figure(figsize=(12, 6))
            sm.graphics.tsa.plot_pacf(df[column].dropna(), lags=lags, ax=plt.gca())
            plt.title(f"Partial Autocorrelation Plot of {column}")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting partial autocorrelation plot: {e}")
            raise ServiceError(f"Error getting partial autocorrelation plot: {str(e)}")

    def get_seasonal_decompose_plot(self, df: pd.DataFrame, column: str) -> Any:
        """Get seasonal decompose plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to decompose
        """
        try:
            logger.info(f"Getting seasonal decompose plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for seasonal decompose plot"
                )
            decomposition = sm.tsa.seasonal_decompose(
                df[column].dropna(), model="additive"
            )
            fig = decomposition.plot()
            fig.set_size_inches(12, 8)
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting seasonal decompose plot: {e}")
            raise ServiceError(f"Error getting seasonal decompose plot: {str(e)}")

    def get_rolling_statistics_plot(
        self, df: pd.DataFrame, column: str, window: int = 20
    ) -> Any:
        """Get rolling statistics plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to calculate rolling statistics for
            window: Rolling window size
        """
        try:
            logger.info(f"Getting rolling statistics plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling statistics plot"
                )
            rolling_mean = df[column].rolling(window=window).mean()
            rolling_std = df[column].rolling(window=window).std()
            plt.figure(figsize=(12, 6))
            plt.plot(df[column], label="Original")
            plt.plot(rolling_mean, label="Rolling Mean")
            plt.plot(rolling_std, label="Rolling Std")
            plt.title(f"Rolling Statistics of {column}")
            plt.xlabel("Time")
            plt.ylabel(column)
            plt.legend()
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling statistics plot: {e}")
            raise ServiceError(f"Error getting rolling statistics plot: {str(e)}")

    def get_qq_plot(self, df: pd.DataFrame, column: str) -> Any:
        """Get Q-Q plot

        Args:
            df: DataFrame with data
            column: Column to plot Q-Q plot for
        """
        try:
            logger.info(f"Getting Q-Q plot for column: {column}")
            sm.qqplot(df[column].dropna(), line="s")
            plt.title(f"Q-Q Plot of {column}")
            plt.show()
        except Exception as e:
            logger.error(f"Error getting Q-Q plot: {e}")
            raise ServiceError(f"Error getting Q-Q plot: {str(e)}")

    def get_lag_plot(self, df: pd.DataFrame, column: str, lag: int = 1) -> Any:
        """Get lag plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to plot lag plot for
            lag: Lag period
        """
        try:
            logger.info(f"Getting lag plot for column: {column} with lag: {lag}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError("DataFrame index must be datetime for lag plot")
            pd.plotting.lag_plot(df[column], lag=lag)
            plt.title(f"Lag Plot of {column} (Lag {lag})")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting lag plot: {e}")
            raise ServiceError(f"Error getting lag plot: {str(e)}")

    def get_box_cox_transform(self, df: pd.DataFrame, column: str) -> Any:
        """Get Box-Cox transform

        Args:
            df: DataFrame with data
            column: Column to transform
        """
        try:
            logger.info(f"Getting Box-Cox transform for column: {column}")
            transformed_data, lambda_value = stats.boxcox(df[column].dropna())
            plt.figure(figsize=(12, 6))
            plt.plot(transformed_data)
            plt.title(f"Box-Cox Transform of {column} (Lambda: {lambda_value:.4f})")
            plt.xlabel("Time")
            plt.ylabel("Transformed Value")
            plt.show()
        except Exception as e:
            logger.error(f"Error getting Box-Cox transform: {e}")
            raise ServiceError(f"Error getting Box-Cox transform: {str(e)}")

    def get_yeo_johnson_transform(self, df: pd.DataFrame, column: str) -> Any:
        """Get Yeo-Johnson transform

        Args:
            df: DataFrame with data
            column: Column to transform
        """
        try:
            logger.info(f"Getting Yeo-Johnson transform for column: {column}")
            transformed_data, lambda_value = stats.yeojohnson(df[column].dropna())
            plt.figure(figsize=(12, 6))
            plt.plot(transformed_data)
            plt.title(f"Yeo-Johnson Transform of {column} (Lambda: {lambda_value:.4f})")
            plt.xlabel("Time")
            plt.ylabel("Transformed Value")
            plt.show()
        except Exception as e:
            logger.error(f"Error getting Yeo-Johnson transform: {e}")
            raise ServiceError(f"Error getting Yeo-Johnson transform: {str(e)}")

    def get_log_transform(self, df: pd.DataFrame, column: str) -> Any:
        """Get log transform

        Args:
            df: DataFrame with data
            column: Column to transform
        """
        try:
            logger.info(f"Getting log transform for column: {column}")
            transformed_data = np.log(df[column].dropna())
            plt.figure(figsize=(12, 6))
            plt.plot(transformed_data)
            plt.title(f"Log Transform of {column}")
            plt.xlabel("Time")
            plt.ylabel("Transformed Value")
            plt.show()
        except Exception as e:
            logger.error(f"Error getting log transform: {e}")
            raise ServiceError(f"Error getting log transform: {str(e)}")

    def get_square_root_transform(self, df: pd.DataFrame, column: str) -> Any:
        """Get square root transform

        Args:
            df: DataFrame with data
            column: Column to transform
        """
        try:
            logger.info(f"Getting square root transform for column: {column}")
            transformed_data = np.sqrt(df[column].dropna())
            plt.figure(figsize=(12, 6))
            plt.plot(transformed_data)
            plt.title(f"Square Root Transform of {column}")
            plt.xlabel("Time")
            plt.ylabel("Transformed Value")
            plt.show()
        except Exception as e:
            logger.error(f"Error getting square root transform: {e}")
            raise ServiceError(f"Error getting square root transform: {str(e)}")

    def get_inverse_transform(self, df: pd.DataFrame, column: str) -> Any:
        """Get inverse transform

        Args:
            df: DataFrame with data
            column: Column to transform
        """
        try:
            logger.info(f"Getting inverse transform for column: {column}")
            transformed_data = 1 / df[column].dropna()
            plt.figure(figsize=(12, 6))
            plt.plot(transformed_data)
            plt.title(f"Inverse Transform of {column}")
            plt.xlabel("Time")
            plt.ylabel("Transformed Value")
            plt.show()
        except Exception as e:
            logger.error(f"Error getting inverse transform: {e}")
            raise ServiceError(f"Error getting inverse transform: {str(e)}")

    def get_difference_transform(
        self, df: pd.DataFrame, column: str, periods: int = 1
    ) -> Any:
        """Get difference transform

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to transform
            periods: Number of periods to difference
        """
        try:
            logger.info(f"Getting difference transform for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for difference transform"
                )
            transformed_data = df[column].diff(periods=periods).dropna()
            plt.figure(figsize=(12, 6))
            plt.plot(transformed_data)
            plt.title(f"Difference Transform of {column} (Periods: {periods})")
            plt.xlabel("Time")
            plt.ylabel("Transformed Value")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting difference transform: {e}")
            raise ServiceError(f"Error getting difference transform: {str(e)}")

    def get_seasonal_difference_transform(
        self, df: pd.DataFrame, column: str, periods: int = 12
    ) -> Any:
        """Get seasonal difference transform

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to transform
            periods: Number of periods for seasonal difference
        """
        try:
            logger.info(f"Getting seasonal difference transform for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for seasonal difference transform"
                )
            transformed_data = df[column].diff(periods=periods).dropna()
            plt.figure(figsize=(12, 6))
            plt.plot(transformed_data)
            plt.title(f"Seasonal Difference Transform of {column} (Periods: {periods})")
            plt.xlabel("Time")
            plt.ylabel("Transformed Value")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting seasonal difference transform: {e}")
            raise ServiceError(f"Error getting seasonal difference transform: {str(e)}")

    def get_rolling_mean_transform(
        self, df: pd.DataFrame, column: str, window: int = 20
    ) -> Any:
        """Get rolling mean transform

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to transform
            window: Rolling window size
        """
        try:
            logger.info(f"Getting rolling mean transform for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling mean transform"
                )
            transformed_data = df[column].rolling(window=window).mean().dropna()
            plt.figure(figsize=(12, 6))
            plt.plot(transformed_data)
            plt.title(f"Rolling Mean Transform of {column} (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("Transformed Value")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling mean transform: {e}")
            raise ServiceError(f"Error getting rolling mean transform: {str(e)}")

    def get_rolling_std_transform(
        self, df: pd.DataFrame, column: str, window: int = 20
    ) -> Any:
        """Get rolling standard deviation transform

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to transform
            window: Rolling window size
        """
        try:
            logger.info(
                f"Getting rolling standard deviation transform for column: {column}"
            )
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling standard deviation transform"
                )
            transformed_data = df[column].rolling(window=window).std().dropna()
            plt.figure(figsize=(12, 6))
            plt.plot(transformed_data)
            plt.title(
                f"Rolling Standard Deviation Transform of {column} (Window: {window})"
            )
            plt.xlabel("Time")
            plt.ylabel("Transformed Value")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling standard deviation transform: {e}")
            raise ServiceError(
                f"Error getting rolling standard deviation transform: {str(e)}"
            )

    def get_exponential_smoothing_transform(
        self, df: pd.DataFrame, column: str, alpha: float = 0.5
    ) -> Any:
        """Get exponential smoothing transform

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to transform
            alpha: Smoothing factor
        """
        try:
            logger.info(f"Getting exponential smoothing transform for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for exponential smoothing transform"
                )
            transformed_data = df[column].ewm(alpha=alpha, adjust=False).mean().dropna()
            plt.figure(figsize=(12, 6))
            plt.plot(transformed_data)
            plt.title(
                f"Exponential Smoothing Transform of {column} (Alpha: {alpha:.2f})"
            )
            plt.xlabel("Time")
            plt.ylabel("Transformed Value")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting exponential smoothing transform: {e}")
            raise ServiceError(
                f"Error getting exponential smoothing transform: {str(e)}"
            )

    def get_double_exponential_smoothing_transform(
        self, df: pd.DataFrame, column: str, alpha: float = 0.5, beta: float = 0.5
    ) -> Any:
        """Get double exponential smoothing transform

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to transform
            alpha: Level smoothing factor
            beta: Trend smoothing factor
        """
        try:
            logger.info(
                f"Getting double exponential smoothing transform for column: {column}"
            )
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for double exponential smoothing transform"
                )
            transformed_data = (
                df[column]
                .ewm(alpha=alpha, adjust=False)
                .mean()
                .ewm(alpha=beta, adjust=False)
                .mean()
                .dropna()
            )
            plt.figure(figsize=(12, 6))
            plt.plot(transformed_data)
            plt.title(
                f"Double Exponential Smoothing Transform of {column} (Alpha: {alpha:.2f}, Beta: {beta:.2f})"
            )
            plt.xlabel("Time")
            plt.ylabel("Transformed Value")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting double exponential smoothing transform: {e}")
            raise ServiceError(
                f"Error getting double exponential smoothing transform: {str(e)}"
            )

    def get_triple_exponential_smoothing_transform(
        self,
        df: pd.DataFrame,
        column: str,
        alpha: float = 0.5,
        beta: float = 0.5,
        gamma: float = 0.5,
        seasonal_periods: int = 12,
    ) -> Any:
        """Get triple exponential smoothing transform

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to transform
            alpha: Level smoothing factor
            beta: Trend smoothing factor
            gamma: Seasonal smoothing factor
            seasonal_periods: Number of seasonal periods
        """
        try:
            logger.info(
                f"Getting triple exponential smoothing transform for column: {column}"
            )
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for triple exponential smoothing transform"
                )
            transformed_data = (
                df[column]
                .ewm(alpha=alpha, adjust=False)
                .mean()
                .ewm(alpha=beta, adjust=False)
                .mean()
                .ewm(alpha=gamma, adjust=False)
                .mean()
                .dropna()
            )
            plt.figure(figsize=(12, 6))
            plt.plot(transformed_data)
            plt.title(
                f"Triple Exponential Smoothing Transform of {column} (Alpha: {alpha:.2f}, Beta: {beta:.2f}, Gamma: {gamma:.2f})"
            )
            plt.xlabel("Time")
            plt.ylabel("Transformed Value")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting triple exponential smoothing transform: {e}")
            raise ServiceError(
                f"Error getting triple exponential smoothing transform: {str(e)}"
            )

    def get_adf_test(self, df: pd.DataFrame, column: str) -> Any:
        """Get Augmented Dickey-Fuller (ADF) test results

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to test
        """
        try:
            logger.info(f"Getting ADF test results for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError("DataFrame index must be datetime for ADF test")
            result = sm.tsa.adfuller(df[column].dropna())
            adf_results = {
                "Test Statistic": result[0],
                "p-value": result[1],
                "Lags Used": result[2],
                "Number of Observations Used": result[3],
                "Critical Values": result[4],
            }
            return adf_results
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting ADF test results: {e}")
            raise ServiceError(f"Error getting ADF test results: {str(e)}")

    def get_kpss_test(self, df: pd.DataFrame, column: str) -> Any:
        """Get Kwiatkowski-Phillips-Schmidt-Shin (KPSS) test results

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to test
        """
        try:
            logger.info(f"Getting KPSS test results for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError("DataFrame index must be datetime for KPSS test")
            result = sm.tsa.kpss(df[column].dropna())
            kpss_results = {
                "Test Statistic": result[0],
                "p-value": result[1],
                "Lags Used": result[2],
                "Critical Values": result[3],
            }
            return kpss_results
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting KPSS test results: {e}")
            raise ServiceError(f"Error getting KPSS test results: {str(e)}")

    def get_hurst_exponent(self, df: pd.DataFrame, column: str) -> Any:
        """Get Hurst exponent

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to calculate Hurst exponent for
        """
        try:
            logger.info(f"Getting Hurst exponent for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for Hurst exponent"
                )
            H, c, data = compute_Hc(df[column].dropna(), kind="price", simplified=True)
            return H
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting Hurst exponent: {e}")
            raise ServiceError(f"Error getting Hurst exponent: {str(e)}")

    def get_half_life(self, df: pd.DataFrame, column: str) -> Any:
        """Get half-life of mean reversion

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to calculate half-life for
        """
        try:
            logger.info(f"Getting half-life for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError("DataFrame index must be datetime for half-life")
            y = df[column].dropna()
            y_lag = y.shift(1).dropna()
            delta_y = y.diff().dropna()
            model = sm.OLS(delta_y, sm.add_constant(y_lag)).fit()
            half_life = -np.log(2) / model.params[1]
            return half_life
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting half-life: {e}")
            raise ServiceError(f"Error getting half-life: {str(e)}")

    def get_cointegration_test(self, df: pd.DataFrame, columns: List[str]) -> Any:
        """Get cointegration test results

        Args:
            df: DataFrame with data (index must be datetime)
            columns: List of columns to test for cointegration
        """
        try:
            logger.info(f"Getting cointegration test results for columns: {columns}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for cointegration test"
                )
            score, p_value, _ = coint(df[columns[0]].dropna(), df[columns[1]].dropna())
            coint_results = {"Test Statistic": score, "p-value": p_value}
            return coint_results
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting cointegration test results: {e}")
            raise ServiceError(f"Error getting cointegration test results: {str(e)}")

    def get_granger_causality_test(self, df: pd.DataFrame, columns: List[str]) -> Any:
        """Get Granger causality test results

        Args:
            df: DataFrame with data (index must be datetime)
            columns: List of columns to test for Granger causality
        """
        try:
            logger.info(
                f"Getting Granger causality test results for columns: {columns}"
            )
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for Granger causality test"
                )
            result = grangercausalitytests(
                df[columns].dropna(), maxlag=2, verbose=False
            )
            granger_results = {}
            for lag in result:
                granger_results[f"Lag {lag}"] = {
                    "F-statistic": result[lag][0]["ssr_ftest"][0],
                    "p-value": result[lag][0]["ssr_ftest"][1],
                }
            return granger_results
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting Granger causality test results: {e}")
            raise ServiceError(
                f"Error getting Granger causality test results: {str(e)}"
            )

    def get_kalman_filter(self, df: pd.DataFrame, column: str) -> Any:
        """Get Kalman filter results

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to apply Kalman filter to
        """
        try:
            logger.info(f"Getting Kalman filter results for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for Kalman filter"
                )
            kf = KalmanFilter(
                initial_state_mean=df[column].iloc[0],
                initial_state_covariance=1,
                observation_covariance=1,
                transition_covariance=0.01,
            )
            state_means, state_covs = kf.filter(df[column].dropna())
            plt.figure(figsize=(12, 6))
            plt.plot(df[column], label="Original")
            plt.plot(state_means, label="Kalman Filter")
            plt.title(f"Kalman Filter of {column}")
            plt.xlabel("Time")
            plt.ylabel(column)
            plt.legend()
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting Kalman filter results: {e}")
            raise ServiceError(f"Error getting Kalman filter results: {str(e)}")

    def get_wavelet_transform(self, df: pd.DataFrame, column: str) -> Any:
        """Get wavelet transform results

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to apply wavelet transform to
        """
        try:
            logger.info(f"Getting wavelet transform results for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for wavelet transform"
                )
            coeffs = pywt.wavedec(df[column].dropna(), "db1", level=5)
            plt.figure(figsize=(12, 6))
            plt.plot(coeffs[0], label="Approximation")
            plt.plot(coeffs[1], label="Detail 1")
            plt.plot(coeffs[2], label="Detail 2")
            plt.plot(coeffs[3], label="Detail 3")
            plt.plot(coeffs[4], label="Detail 4")
            plt.plot(coeffs[5], label="Detail 5")
            plt.title(f"Wavelet Transform of {column}")
            plt.xlabel("Time")
            plt.ylabel("Coefficient Value")
            plt.legend()
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting wavelet transform results: {e}")
            raise ServiceError(f"Error getting wavelet transform results: {str(e)}")

    def get_fourier_transform(self, df: pd.DataFrame, column: str) -> Any:
        """Get Fourier transform results

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to apply Fourier transform to
        """
        try:
            logger.info(f"Getting Fourier transform results for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for Fourier transform"
                )
            fft = np.fft.fft(df[column].dropna())
            freq = np.fft.fftfreq(len(df[column].dropna()))
            plt.figure(figsize=(12, 6))
            plt.plot(freq, np.abs(fft))
            plt.title(f"Fourier Transform of {column}")
            plt.xlabel("Frequency")
            plt.ylabel("Amplitude")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting Fourier transform results: {e}")
            raise ServiceError(f"Error getting Fourier transform results: {str(e)}")

    def get_spectral_density_plot(self, df: pd.DataFrame, column: str) -> Any:
        """Get spectral density plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Column to plot spectral density for
        """
        try:
            logger.info(f"Getting spectral density plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for spectral density plot"
                )
            plt.figure(figsize=(12, 6))
            plt.psd(df[column].dropna())
            plt.title(f"Spectral Density Plot of {column}")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting spectral density plot: {e}")
            raise ServiceError(f"Error getting spectral density plot: {str(e)}")

    def get_cross_correlation_plot(
        self, df: pd.DataFrame, column1: str, column2: str
    ) -> Any:
        """Get cross-correlation plot

        Args:
            df: DataFrame with data (index must be datetime)
            column1: First column
            column2: Second column
        """
        try:
            logger.info(f"Getting cross-correlation plot for {column1} and {column2}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for cross-correlation plot"
                )
            cross_correlation = pd.Series(
                np.correlate(
                    df[column1].dropna() - df[column1].dropna().mean(),
                    df[column2].dropna() - df[column2].dropna().mean(),
                    mode="full",
                )
            )
            plt.figure(figsize=(12, 6))
            plt.plot(cross_correlation)
            plt.title(f"Cross-Correlation Plot of {column1} and {column2}")
            plt.xlabel("Lag")
            plt.ylabel("Correlation")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting cross-correlation plot: {e}")
            raise ServiceError(f"Error getting cross-correlation plot: {str(e)}")

    def get_rolling_correlation_plot(
        self, df: pd.DataFrame, column1: str, column2: str, window: int = 20
    ) -> Any:
        """Get rolling correlation plot

        Args:
            df: DataFrame with data (index must be datetime)
            column1: First column
            column2: Second column
            window: Rolling window size
        """
        try:
            logger.info(f"Getting rolling correlation plot for {column1} and {column2}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling correlation plot"
                )
            rolling_correlation = (
                df[column1].rolling(window=window).corr(df[column2]).dropna()
            )
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_correlation)
            plt.title(
                f"Rolling Correlation Plot of {column1} and {column2} (Window: {window})"
            )
            plt.xlabel("Time")
            plt.ylabel("Correlation")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling correlation plot: {e}")
            raise ServiceError(f"Error getting rolling correlation plot: {str(e)}")

    def get_rolling_beta_plot(
        self, df: pd.DataFrame, market_column: str, asset_column: str, window: int = 20
    ) -> Any:
        """Get rolling beta plot

        Args:
            df: DataFrame with data (index must be datetime)
            market_column: Market return column
            asset_column: Asset return column
            window: Rolling window size
        """
        try:
            logger.info(
                f"Getting rolling beta plot for {asset_column} and {market_column}"
            )
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling beta plot"
                )
            rolling_covariance = (
                df[asset_column].rolling(window=window).cov(df[market_column]).dropna()
            )
            rolling_variance = df[market_column].rolling(window=window).var().dropna()
            rolling_beta = rolling_covariance / rolling_variance
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_beta)
            plt.title(
                f"Rolling Beta Plot of {asset_column} and {market_column} (Window: {window})"
            )
            plt.xlabel("Time")
            plt.ylabel("Beta")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling beta plot: {e}")
            raise ServiceError(f"Error getting rolling beta plot: {str(e)}")

    def get_rolling_sharpe_ratio_plot(
        self,
        df: pd.DataFrame,
        column: str,
        window: int = 20,
        risk_free_rate: float = 0.0,
    ) -> Any:
        """Get rolling Sharpe ratio plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            window: Rolling window size
            risk_free_rate: Risk-free rate
        """
        try:
            logger.info(f"Getting rolling Sharpe ratio plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling Sharpe ratio plot"
                )
            rolling_mean = df[column].rolling(window=window).mean()
            rolling_std = df[column].rolling(window=window).std()
            rolling_sharpe_ratio = (rolling_mean - risk_free_rate) / rolling_std
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_sharpe_ratio)
            plt.title(
                f"Rolling Sharpe Ratio Plot of {column} (Window: {window}, Risk-Free Rate: {risk_free_rate:.2f})"
            )
            plt.xlabel("Time")
            plt.ylabel("Sharpe Ratio")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling Sharpe ratio plot: {e}")
            raise ServiceError(f"Error getting rolling Sharpe ratio plot: {str(e)}")

    def get_rolling_sortino_ratio_plot(
        self,
        df: pd.DataFrame,
        column: str,
        window: int = 20,
        risk_free_rate: float = 0.0,
    ) -> Any:
        """Get rolling Sortino ratio plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            window: Rolling window size
            risk_free_rate: Risk-free rate
        """
        try:
            logger.info(f"Getting rolling Sortino ratio plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling Sortino ratio plot"
                )
            rolling_mean = df[column].rolling(window=window).mean()
            downside_returns = df[column][df[column] < risk_free_rate]
            rolling_downside_std = (
                downside_returns.rolling(window=window).std().dropna()
            )
            rolling_sortino_ratio = (
                rolling_mean - risk_free_rate
            ) / rolling_downside_std
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_sortino_ratio)
            plt.title(
                f"Rolling Sortino Ratio Plot of {column} (Window: {window}, Risk-Free Rate: {risk_free_rate:.2f})"
            )
            plt.xlabel("Time")
            plt.ylabel("Sortino Ratio")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling Sortino ratio plot: {e}")
            raise ServiceError(f"Error getting rolling Sortino ratio plot: {str(e)}")

    def get_rolling_max_drawdown_plot(
        self, df: pd.DataFrame, column: str, window: int = 20
    ) -> Any:
        """Get rolling maximum drawdown plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            window: Rolling window size
        """
        try:
            logger.info(f"Getting rolling maximum drawdown plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling maximum drawdown plot"
                )
            rolling_max_drawdown = (
                df[column]
                .rolling(window=window)
                .apply(lambda x: (x.max() - x.iloc[-1]) / x.max(), raw=True)
                .dropna()
            )
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_max_drawdown)
            plt.title(f"Rolling Maximum Drawdown Plot of {column} (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("Maximum Drawdown")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling maximum drawdown plot: {e}")
            raise ServiceError(f"Error getting rolling maximum drawdown plot: {str(e)}")

    def get_rolling_volatility_plot(
        self, df: pd.DataFrame, column: str, window: int = 20
    ) -> Any:
        """Get rolling volatility plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            window: Rolling window size
        """
        try:
            logger.info(f"Getting rolling volatility plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling volatility plot"
                )
            rolling_volatility = df[column].rolling(window=window).std().dropna()
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_volatility)
            plt.title(f"Rolling Volatility Plot of {column} (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("Volatility")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling volatility plot: {e}")
            raise ServiceError(f"Error getting rolling volatility plot: {str(e)}")

    def get_rolling_skewness_plot(
        self, df: pd.DataFrame, column: str, window: int = 20
    ) -> Any:
        """Get rolling skewness plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            window: Rolling window size
        """
        try:
            logger.info(f"Getting rolling skewness plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling skewness plot"
                )
            rolling_skewness = df[column].rolling(window=window).skew().dropna()
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_skewness)
            plt.title(f"Rolling Skewness Plot of {column} (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("Skewness")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling skewness plot: {e}")
            raise ServiceError(f"Error getting rolling skewness plot: {str(e)}")

    def get_rolling_kurtosis_plot(
        self, df: pd.DataFrame, column: str, window: int = 20
    ) -> Any:
        """Get rolling kurtosis plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            window: Rolling window size
        """
        try:
            logger.info(f"Getting rolling kurtosis plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling kurtosis plot"
                )
            rolling_kurtosis = df[column].rolling(window=window).kurt().dropna()
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_kurtosis)
            plt.title(f"Rolling Kurtosis Plot of {column} (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("Kurtosis")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling kurtosis plot: {e}")
            raise ServiceError(f"Error getting rolling kurtosis plot: {str(e)}")

    def get_rolling_quantile_plot(
        self, df: pd.DataFrame, column: str, window: int = 20, quantile: float = 0.5
    ) -> Any:
        """Get rolling quantile plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            window: Rolling window size
            quantile: Quantile to calculate
        """
        try:
            logger.info(f"Getting rolling quantile plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling quantile plot"
                )
            rolling_quantile = (
                df[column].rolling(window=window).quantile(quantile).dropna()
            )
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_quantile)
            plt.title(
                f"Rolling Quantile Plot of {column} (Window: {window}, Quantile: {quantile:.2f})"
            )
            plt.xlabel("Time")
            plt.ylabel("Quantile")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling quantile plot: {e}")
            raise ServiceError(f"Error getting rolling quantile plot: {str(e)}")

    def get_rolling_min_max_plot(
        self, df: pd.DataFrame, column: str, window: int = 20
    ) -> Any:
        """Get rolling min/max plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            window: Rolling window size
        """
        try:
            logger.info(f"Getting rolling min/max plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling min/max plot"
                )
            rolling_min = df[column].rolling(window=window).min().dropna()
            rolling_max = df[column].rolling(window=window).max().dropna()
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_min, label="Rolling Min")
            plt.plot(rolling_max, label="Rolling Max")
            plt.title(f"Rolling Min/Max Plot of {column} (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("Value")
            plt.legend()
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling min/max plot: {e}")
            raise ServiceError(f"Error getting rolling min/max plot: {str(e)}")

    def get_rolling_range_plot(
        self, df: pd.DataFrame, column: str, window: int = 20
    ) -> Any:
        """Get rolling range plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            window: Rolling window size
        """
        try:
            logger.info(f"Getting rolling range plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling range plot"
                )
            rolling_range = (
                df[column].rolling(window=window).max()
                - df[column].rolling(window=window).min()
            ).dropna()
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_range)
            plt.title(f"Rolling Range Plot of {column} (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("Range")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling range plot: {e}")
            raise ServiceError(f"Error getting rolling range plot: {str(e)}")

    def get_rolling_zscore_plot(
        self, df: pd.DataFrame, column: str, window: int = 20
    ) -> Any:
        """Get rolling Z-score plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            window: Rolling window size
        """
        try:
            logger.info(f"Getting rolling Z-score plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling Z-score plot"
                )
            rolling_mean = df[column].rolling(window=window).mean()
            rolling_std = df[column].rolling(window=window).std()
            rolling_zscore = (df[column] - rolling_mean) / rolling_std
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_zscore)
            plt.title(f"Rolling Z-Score Plot of {column} (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("Z-Score")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling Z-score plot: {e}")
            raise ServiceError(f"Error getting rolling Z-score plot: {str(e)}")

    def get_rolling_percent_change_plot(
        self, df: pd.DataFrame, column: str, window: int = 1
    ) -> Any:
        """Get rolling percent change plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            window: Rolling window size
        """
        try:
            logger.info(f"Getting rolling percent change plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling percent change plot"
                )
            rolling_percent_change = df[column].pct_change(periods=window)
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_percent_change)
            plt.title(f"Rolling Percent Change Plot of {column} (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("Percent Change")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling percent change plot: {e}")
            raise ServiceError(f"Error getting rolling percent change plot: {str(e)}")

    def get_rolling_log_return_plot(
        self, df: pd.DataFrame, column: str, window: int = 1
    ) -> Any:
        """Get rolling log return plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            window: Rolling window size
        """
        try:
            logger.info(f"Getting rolling log return plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling log return plot"
                )
            rolling_log_return = np.log(df[column] / df[column].shift(window))
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_log_return)
            plt.title(f"Rolling Log Return Plot of {column} (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("Log Return")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling log return plot: {e}")
            raise ServiceError(f"Error getting rolling log return plot: {str(e)}")

    def get_rolling_momentum_plot(
        self, df: pd.DataFrame, column: str, window: int = 10
    ) -> Any:
        """Get rolling momentum plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            window: Rolling window size
        """
        try:
            logger.info(f"Getting rolling momentum plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling momentum plot"
                )
            rolling_momentum = df[column] - df[column].shift(window)
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_momentum)
            plt.title(f"Rolling Momentum Plot of {column} (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("Momentum")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling momentum plot: {e}")
            raise ServiceError(f"Error getting rolling momentum plot: {str(e)}")

    def get_rolling_roc_plot(
        self, df: pd.DataFrame, column: str, window: int = 10
    ) -> Any:
        """Get rolling Rate of Change (ROC) plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            window: Rolling window size
        """
        try:
            logger.info(f"Getting rolling ROC plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling ROC plot"
                )
            rolling_roc = talib.ROC(df[column].values, timeperiod=window)
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_roc)
            plt.title(f"Rolling ROC Plot of {column} (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("ROC")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling ROC plot: {e}")
            raise ServiceError(f"Error getting rolling ROC plot: {str(e)}")

    def get_rolling_sma_plot(
        self, df: pd.DataFrame, column: str, window: int = 20
    ) -> Any:
        """Get rolling Simple Moving Average (SMA) plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            window: Rolling window size
        """
        try:
            logger.info(f"Getting rolling SMA plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling SMA plot"
                )
            rolling_sma = talib.SMA(df[column].values, timeperiod=window)
            plt.figure(figsize=(12, 6))
            plt.plot(df[column], label="Original")
            plt.plot(rolling_sma, label="SMA")
            plt.title(f"Rolling SMA Plot of {column} (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("Value")
            plt.legend()
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling SMA plot: {e}")
            raise ServiceError(f"Error getting rolling SMA plot: {str(e)}")

    def get_rolling_ema_plot(
        self, df: pd.DataFrame, column: str, window: int = 20
    ) -> Any:
        """Get rolling Exponential Moving Average (EMA) plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            window: Rolling window size
        """
        try:
            logger.info(f"Getting rolling EMA plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling EMA plot"
                )
            rolling_ema = talib.EMA(df[column].values, timeperiod=window)
            plt.figure(figsize=(12, 6))
            plt.plot(df[column], label="Original")
            plt.plot(rolling_ema, label="EMA")
            plt.title(f"Rolling EMA Plot of {column} (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("Value")
            plt.legend()
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling EMA plot: {e}")
            raise ServiceError(f"Error getting rolling EMA plot: {str(e)}")

    def get_rolling_rsi_plot(
        self, df: pd.DataFrame, column: str, window: int = 14
    ) -> Any:
        """Get rolling Relative Strength Index (RSI) plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            window: Rolling window size
        """
        try:
            logger.info(f"Getting rolling RSI plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling RSI plot"
                )
            rolling_rsi = talib.RSI(df[column].values, timeperiod=window)
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_rsi)
            plt.title(f"Rolling RSI Plot of {column} (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("RSI")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling RSI plot: {e}")
            raise ServiceError(f"Error getting rolling RSI plot: {str(e)}")

    def get_rolling_macd_plot(
        self,
        df: pd.DataFrame,
        column: str,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> Any:
        """Get rolling Moving Average Convergence Divergence (MACD) plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            fast_period: Fast period
            slow_period: Slow period
            signal_period: Signal period
        """
        try:
            logger.info(f"Getting rolling MACD plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling MACD plot"
                )
            macd, signal, hist = talib.MACD(
                df[column].values,
                fastperiod=fast_period,
                slowperiod=slow_period,
                signalperiod=signal_period,
            )
            plt.figure(figsize=(12, 6))
            plt.plot(macd, label="MACD")
            plt.plot(signal, label="Signal")
            plt.bar(df.index, hist, label="Histogram")
            plt.title(
                f"Rolling MACD Plot of {column} (Fast: {fast_period}, Slow: {slow_period}, Signal: {signal_period})"
            )
            plt.xlabel("Time")
            plt.ylabel("Value")
            plt.legend()
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling MACD plot: {e}")
            raise ServiceError(f"Error getting rolling MACD plot: {str(e)}")

    def get_rolling_bollinger_bands_plot(
        self, df: pd.DataFrame, column: str, window: int = 20, num_std: float = 2.0
    ) -> Any:
        """Get rolling Bollinger Bands plot

        Args:
            df: DataFrame with data (index must be datetime)
            column: Return column
            window: Rolling window size
            num_std: Number of standard deviations
        """
        try:
            logger.info(f"Getting rolling Bollinger Bands plot for column: {column}")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling Bollinger Bands plot"
                )
            upper, middle, lower = talib.BBANDS(
                df[column].values,
                timeperiod=window,
                nbdevup=num_std,
                nbdevdn=num_std,
                matype=0,
            )
            plt.figure(figsize=(12, 6))
            plt.plot(df[column], label="Original")
            plt.plot(upper, label="Upper Band")
            plt.plot(middle, label="Middle Band")
            plt.plot(lower, label="Lower Band")
            plt.title(
                f"Rolling Bollinger Bands Plot of {column} (Window: {window}, Std: {num_std:.2f})"
            )
            plt.xlabel("Time")
            plt.ylabel("Value")
            plt.legend()
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling Bollinger Bands plot: {e}")
            raise ServiceError(f"Error getting rolling Bollinger Bands plot: {str(e)}")

    def get_rolling_atr_plot(self, df: pd.DataFrame, window: int = 14) -> Any:
        """Get rolling Average True Range (ATR) plot

        Args:
            df: DataFrame with data (index must be datetime)
            window: Rolling window size
        """
        try:
            logger.info("Getting rolling ATR plot")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling ATR plot"
                )
            rolling_atr = talib.ATR(
                df["high"].values,
                df["low"].values,
                df["close"].values,
                timeperiod=window,
            )
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_atr)
            plt.title(f"Rolling ATR Plot (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("ATR")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling ATR plot: {e}")
            raise ServiceError(f"Error getting rolling ATR plot: {str(e)}")

    def get_rolling_obv_plot(self, df: pd.DataFrame) -> Any:
        """Get rolling On-Balance Volume (OBV) plot

        Args:
            df: DataFrame with data (index must be datetime)
        """
        try:
            logger.info("Getting rolling OBV plot")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling OBV plot"
                )
            rolling_obv = talib.OBV(df["close"].values, df["volume"].values)
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_obv)
            plt.title("Rolling OBV Plot")
            plt.xlabel("Time")
            plt.ylabel("OBV")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling OBV plot: {e}")
            raise ServiceError(f"Error getting rolling OBV plot: {str(e)}")

    def get_rolling_stochastic_plot(
        self,
        df: pd.DataFrame,
        fastk_period: int = 5,
        slowk_period: int = 3,
        slowd_period: int = 3,
    ) -> Any:
        """Get rolling Stochastic Oscillator plot

        Args:
            df: DataFrame with data (index must be datetime)
            fastk_period: Fast K period
            slowk_period: Slow K period
            slowd_period: Slow D period
        """
        try:
            logger.info("Getting rolling Stochastic Oscillator plot")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling Stochastic Oscillator plot"
                )
            slowk, slowd = talib.STOCH(
                df["high"].values,
                df["low"].values,
                df["close"].values,
                fastk_period=fastk_period,
                slowk_period=slowk_period,
                slowk_matype=0,
                slowd_period=slowd_period,
                slowd_matype=0,
            )
            plt.figure(figsize=(12, 6))
            plt.plot(slowk, label="%K")
            plt.plot(slowd, label="%D")
            plt.title(
                f"Rolling Stochastic Oscillator Plot (Fast K: {fastk_period}, Slow K: {slowk_period}, Slow D: {slowd_period})"
            )
            plt.xlabel("Time")
            plt.ylabel("Value")
            plt.legend()
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling Stochastic Oscillator plot: {e}")
            raise ServiceError(
                f"Error getting rolling Stochastic Oscillator plot: {str(e)}"
            )

    def get_rolling_williams_r_plot(self, df: pd.DataFrame, window: int = 14) -> Any:
        """Get rolling Williams %R plot

        Args:
            df: DataFrame with data (index must be datetime)
            window: Rolling window size
        """
        try:
            logger.info("Getting rolling Williams %R plot")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling Williams %R plot"
                )
            rolling_williams_r = talib.WILLR(
                df["high"].values,
                df["low"].values,
                df["close"].values,
                timeperiod=window,
            )
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_williams_r)
            plt.title(f"Rolling Williams %R Plot (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("Williams %R")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling Williams %R plot: {e}")
            raise ServiceError(f"Error getting rolling Williams %R plot: {str(e)}")

    def get_rolling_adx_plot(self, df: pd.DataFrame, window: int = 14) -> Any:
        """Get rolling Average Directional Index (ADX) plot

        Args:
            df: DataFrame with data (index must be datetime)
            window: Rolling window size
        """
        try:
            logger.info("Getting rolling ADX plot")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling ADX plot"
                )
            rolling_adx = talib.ADX(
                df["high"].values,
                df["low"].values,
                df["close"].values,
                timeperiod=window,
            )
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_adx)
            plt.title(f"Rolling ADX Plot (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("ADX")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling ADX plot: {e}")
            raise ServiceError(f"Error getting rolling ADX plot: {str(e)}")

    def get_rolling_cci_plot(self, df: pd.DataFrame, window: int = 14) -> Any:
        """Get rolling Commodity Channel Index (CCI) plot

        Args:
            df: DataFrame with data (index must be datetime)
            window: Rolling window size
        """
        try:
            logger.info("Getting rolling CCI plot")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling CCI plot"
                )
            rolling_cci = talib.CCI(
                df["high"].values,
                df["low"].values,
                df["close"].values,
                timeperiod=window,
            )
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_cci)
            plt.title(f"Rolling CCI Plot (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("CCI")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling CCI plot: {e}")
            raise ServiceError(f"Error getting rolling CCI plot: {str(e)}")

    def get_rolling_aroon_plot(self, df: pd.DataFrame, window: int = 14) -> Any:
        """Get rolling Aroon Oscillator plot

        Args:
            df: DataFrame with data (index must be datetime)
            window: Rolling window size
        """
        try:
            logger.info("Getting rolling Aroon Oscillator plot")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling Aroon Oscillator plot"
                )
            aroon_down, aroon_up = talib.AROON(
                df["high"].values, df["low"].values, timeperiod=window
            )
            rolling_aroon_oscillator = aroon_up - aroon_down
            plt.figure(figsize=(12, 6))
            plt.plot(rolling_aroon_oscillator)
            plt.title(f"Rolling Aroon Oscillator Plot (Window: {window})")
            plt.xlabel("Time")
            plt.ylabel("Aroon Oscillator")
            plt.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling Aroon Oscillator plot: {e}")
            raise ServiceError(f"Error getting rolling Aroon Oscillator plot: {str(e)}")

    def get_rolling_ichimoku_plot(self, df: pd.DataFrame) -> Any:
        """Get rolling Ichimoku Cloud plot

        Args:
            df: DataFrame with data (index must be datetime)
        """
        try:
            logger.info("Getting rolling Ichimoku Cloud plot")
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValidationError(
                    "DataFrame index must be datetime for rolling Ichimoku Cloud plot"
                )
            df = self._calculate_ichimoku(df)
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["tenkan_sen"],
                    name="Tenkan-sen",
                    line=dict(color="red"),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["kijun_sen"],
                    name="Kijun-sen",
                    line=dict(color="blue"),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["senkou_span_a"],
                    name="Senkou Span A",
                    line=dict(color="green"),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["senkou_span_b"],
                    name="Senkou Span B",
                    line=dict(color="red"),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["chikou_span"],
                    name="Chikou Span",
                    line=dict(color="purple"),
                )
            )
            fig.update_layout(
                title="Rolling Ichimoku Cloud Plot",
                xaxis_title="Time",
                yaxis_title="Value",
            )
            fig.show()
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting rolling Ichimoku Cloud plot: {e}")
            raise ServiceError(f"Error getting rolling Ichimoku Cloud plot: {str(e)}")
