"""
Market data generator for testing.

This module provides utilities to generate synthetic market data for testing purposes.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd


class MarketDataGenerator:
    """Generator for synthetic market data."""

    def __init__(self, seed: Optional[int] = None) -> None:
        """
        Initialize the market data generator.

        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            np.random.seed(seed)

    def generate_ohlcv_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        periods: int,
        freq: str = "D",
        base_price: float = 100.0,
        volatility: float = 0.02,
        trend: float = 0.0001,
        volume_mean: float = 1000000,
        volume_std: float = 100000,
    ) -> pd.DataFrame:
        """
        Generate synthetic OHLCV (Open, High, Low, Close, Volume) data.

        Args:
            symbol: Stock symbol
            start_date: Start date for the data
            periods: Number of periods to generate
            freq: Frequency of the data (D=daily, H=hourly, etc.)
            base_price: Starting price
            volatility: Price volatility
            trend: Price trend (positive for uptrend, negative for downtrend)
            volume_mean: Mean trading volume
            volume_std: Standard deviation of trading volume

        Returns:
            DataFrame with OHLCV data
        """
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        timestamps = pd.date_range(start=start_date, periods=periods, freq=freq)
        close_prices = np.zeros(periods)
        close_prices[0] = base_price
        for i in range(1, periods):
            price_change = np.random.normal(trend, volatility) * close_prices[i - 1]
            close_prices[i] = close_prices[i - 1] + price_change
        open_prices = np.zeros(periods)
        high_prices = np.zeros(periods)
        low_prices = np.zeros(periods)
        open_prices[0] = base_price
        for i in range(1, periods):
            open_prices[i] = close_prices[i - 1] * (
                1 + np.random.normal(0, volatility / 2)
            )
        for i in range(periods):
            max_price = max(open_prices[i], close_prices[i])
            high_prices[i] = max_price * (1 + abs(np.random.normal(0, volatility)))
            min_price = min(open_prices[i], close_prices[i])
            low_prices[i] = min_price * (1 - abs(np.random.normal(0, volatility)))
            high_prices[i] = max(high_prices[i], open_prices[i], close_prices[i])
            low_prices[i] = min(low_prices[i], open_prices[i], close_prices[i])
        volumes = np.random.normal(volume_mean, volume_std, periods)
        volumes = np.maximum(volumes, 0)
        df = pd.DataFrame(
            {
                "timestamp": timestamps,
                "open": open_prices,
                "high": high_prices,
                "low": low_prices,
                "close": close_prices,
                "volume": volumes.astype(int),
                "symbol": symbol,
            }
        )
        return df

    def generate_multiple_symbols(
        self,
        symbols: List[str],
        start_date: Union[str, datetime],
        periods: int,
        freq: str = "D",
        base_prices: Optional[Dict[str, float]] = None,
        correlation_matrix: Optional[np.ndarray] = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Generate synthetic OHLCV data for multiple symbols with correlation.

        Args:
            symbols: List of stock symbols
            start_date: Start date for the data
            periods: Number of periods to generate
            freq: Frequency of the data (D=daily, H=hourly, etc.)
            base_prices: Dictionary mapping symbols to their base prices
            correlation_matrix: Correlation matrix for price movements

        Returns:
            Dictionary mapping symbols to their OHLCV DataFrames
        """
        n_symbols = len(symbols)
        if base_prices is None:
            base_prices = {symbol: 100.0 for symbol in symbols}
        if correlation_matrix is None:
            correlation_matrix = np.ones((n_symbols, n_symbols)) * 0.5
            np.fill_diagonal(correlation_matrix, 1.0)
        L = np.linalg.cholesky(correlation_matrix)
        uncorrelated_changes = np.random.normal(0.0001, 0.02, (periods, n_symbols))
        correlated_changes = uncorrelated_changes @ L.T
        result = {}
        for i, symbol in enumerate(symbols):
            close_prices = np.zeros(periods)
            close_prices[0] = base_prices[symbol]
            for j in range(1, periods):
                close_prices[j] = close_prices[j - 1] * (1 + correlated_changes[j, i])
            open_prices = np.zeros(periods)
            high_prices = np.zeros(periods)
            low_prices = np.zeros(periods)
            open_prices[0] = base_prices[symbol]
            for j in range(1, periods):
                open_prices[j] = close_prices[j - 1] * (1 + np.random.normal(0, 0.01))
            for j in range(periods):
                max_price = max(open_prices[j], close_prices[j])
                high_prices[j] = max_price * (1 + abs(np.random.normal(0, 0.01)))
                min_price = min(open_prices[j], close_prices[j])
                low_prices[j] = min_price * (1 - abs(np.random.normal(0, 0.01)))
                high_prices[j] = max(high_prices[j], open_prices[j], close_prices[j])
                low_prices[j] = min(low_prices[j], open_prices[j], close_prices[j])
            volumes = np.random.normal(1000000, 100000, periods)
            volumes = np.maximum(volumes, 0)
            timestamps = pd.date_range(start=start_date, periods=periods, freq=freq)
            df = pd.DataFrame(
                {
                    "timestamp": timestamps,
                    "open": open_prices,
                    "high": high_prices,
                    "low": low_prices,
                    "close": close_prices,
                    "volume": volumes.astype(int),
                    "symbol": symbol,
                }
            )
            result[symbol] = df
        return result

    def generate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate technical indicators for the given OHLCV data.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added technical indicators
        """
        result = df.copy()
        result["sma_20"] = result["close"].rolling(window=20).mean()
        result["sma_50"] = result["close"].rolling(window=50).mean()
        result["ema_20"] = result["close"].ewm(span=20, adjust=False).mean()
        delta = result["close"].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        result["rsi_14"] = 100 - 100 / (1 + rs)
        ema_12 = result["close"].ewm(span=12, adjust=False).mean()
        ema_26 = result["close"].ewm(span=26, adjust=False).mean()
        result["macd"] = ema_12 - ema_26
        result["macd_signal"] = result["macd"].ewm(span=9, adjust=False).mean()
        result["macd_hist"] = result["macd"] - result["macd_signal"]
        result["bb_middle"] = result["close"].rolling(window=20).mean()
        std_dev = result["close"].rolling(window=20).std()
        result["bb_upper"] = result["bb_middle"] + std_dev * 2
        result["bb_lower"] = result["bb_middle"] - std_dev * 2
        return result

    def generate_signals(
        self, df: pd.DataFrame, strategy: str = "sma_crossover"
    ) -> pd.DataFrame:
        """
        Generate trading signals based on technical indicators.

        Args:
            df: DataFrame with technical indicators
            strategy: Signal generation strategy

        Returns:
            DataFrame with added signals
        """
        result = df.copy()
        if strategy == "sma_crossover":
            result["signal"] = 0
            result.loc[result["sma_20"] > result["sma_50"], "signal"] = 1
            result.loc[result["sma_20"] < result["sma_50"], "signal"] = -1
        elif strategy == "macd":
            result["signal"] = 0
            result.loc[result["macd"] > result["macd_signal"], "signal"] = 1
            result.loc[result["macd"] < result["macd_signal"], "signal"] = -1
        elif strategy == "rsi":
            result["signal"] = 0
            result.loc[result["rsi_14"] > 30, "signal"] = 1
            result.loc[result["rsi_14"] < 70, "signal"] = -1
        elif strategy == "bollinger_bands":
            result["signal"] = 0
            result.loc[result["close"] < result["bb_lower"], "signal"] = 1
            result.loc[result["close"] > result["bb_upper"], "signal"] = -1
        return result

    def generate_portfolio(
        self,
        symbols: List[str],
        quantities: List[int],
        entry_prices: List[float],
        current_prices: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate portfolio data for testing.

        Args:
            symbols: List of stock symbols
            quantities: List of quantities for each symbol
            entry_prices: List of entry prices for each symbol
            current_prices: List of current prices for each symbol

        Returns:
            List of portfolio positions
        """
        if current_prices is None:
            current_prices = [
                price * (1 + np.random.normal(0, 0.05)) for price in entry_prices
            ]
        portfolio = []
        for i, symbol in enumerate(symbols):
            quantity = quantities[i]
            entry_price = entry_prices[i]
            current_price = current_prices[i]
            market_value = quantity * current_price
            cost_basis = quantity * entry_price
            unrealized_pl = market_value - cost_basis
            unrealized_pl_percent = (
                unrealized_pl / cost_basis * 100 if cost_basis != 0 else 0
            )
            position = {
                "symbol": symbol,
                "quantity": quantity,
                "entry_price": entry_price,
                "current_price": current_price,
                "market_value": market_value,
                "cost_basis": cost_basis,
                "unrealized_pl": unrealized_pl,
                "unrealized_pl_percent": unrealized_pl_percent,
            }
            portfolio.append(position)
        return portfolio

    def generate_order(
        self,
        order_id: str,
        user_id: str,
        portfolio_id: str,
        symbol: str,
        side: str,
        order_type: str,
        quantity: int,
        price: Optional[float] = None,
        status: str = "created",
    ) -> Dict[str, Any]:
        """
        Generate order data for testing.

        Args:
            order_id: Order ID
            user_id: User ID
            portfolio_id: Portfolio ID
            symbol: Stock symbol
            side: Order side (buy or sell)
            order_type: Order type (market or limit)
            quantity: Order quantity
            price: Order price (required for limit orders)
            status: Order status

        Returns:
            Order data
        """
        now = datetime.utcnow()
        order = {
            "id": order_id,
            "user_id": user_id,
            "portfolio_id": portfolio_id,
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "status": status,
            "quantity": quantity,
            "price": price,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        if status in ["filled", "partially_filled"]:
            fill_price = price if price is not None else np.random.normal(100, 2)
            filled_quantity = (
                quantity
                if status == "filled"
                else int(quantity * np.random.uniform(0.1, 0.9))
            )
            order.update(
                {
                    "filled_quantity": filled_quantity,
                    "average_fill_price": fill_price,
                    "executed_at": (now + timedelta(seconds=5)).isoformat(),
                }
            )
        return order

    def generate_execution(
        self,
        execution_id: str,
        order_id: str,
        price: float,
        quantity: int,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Generate execution data for testing.

        Args:
            execution_id: Execution ID
            order_id: Order ID
            price: Execution price
            quantity: Execution quantity
            timestamp: Execution timestamp

        Returns:
            Execution data
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        execution = {
            "id": execution_id,
            "order_id": order_id,
            "price": price,
            "quantity": quantity,
            "timestamp": timestamp.isoformat(),
            "broker_execution_id": f"broker_{execution_id}",
        }
        return execution

    def generate_prediction(
        self,
        symbol: str,
        model_id: str,
        latest_price: float,
        days: int = 5,
        trend: float = 0.01,
        volatility: float = 0.02,
    ) -> Dict[str, Any]:
        """
        Generate prediction data for testing.

        Args:
            symbol: Stock symbol
            model_id: Model ID
            latest_price: Latest price
            days: Number of days to predict
            trend: Price trend (positive for uptrend, negative for downtrend)
            volatility: Price volatility

        Returns:
            Prediction data
        """
        predicted_prices = []
        current_price = latest_price
        for i in range(days):
            price_change = current_price * (trend + np.random.normal(0, volatility))
            current_price += price_change
            confidence = 0.9 - i * 0.05
            predicted_prices.append(
                {
                    "timestamp": (
                        datetime.utcnow() + timedelta(days=i + 1)
                    ).isoformat(),
                    "value": current_price,
                    "confidence": confidence,
                }
            )
        values = [p["value"] for p in predicted_prices]
        average = sum(values) / len(values)
        minimum = min(values)
        maximum = max(values)
        change = average - latest_price
        change_percent = change / latest_price * 100
        direction = "up" if change > 0 else "down" if change < 0 else "sideways"
        prediction = {
            "symbol": symbol,
            "model_id": model_id,
            "latest_price": latest_price,
            "prediction": {
                "average": average,
                "minimum": minimum,
                "maximum": maximum,
                "change": change,
                "change_percent": change_percent,
                "direction": direction,
            },
            "predictions": predicted_prices,
        }
        return prediction

    def generate_risk_metrics(
        self,
        symbol: Optional[str] = None,
        portfolio_id: Optional[str] = None,
        var_value: Optional[float] = None,
        cvar_value: Optional[float] = None,
        sharpe_ratio: Optional[float] = None,
        sortino_ratio: Optional[float] = None,
        max_drawdown: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Generate risk metrics data for testing.

        Args:
            symbol: Stock symbol (for position risk)
            portfolio_id: Portfolio ID (for portfolio risk)
            var_value: Value at Risk
            cvar_value: Conditional Value at Risk
            sharpe_ratio: Sharpe ratio
            sortino_ratio: Sortino ratio
            max_drawdown: Maximum drawdown

        Returns:
            Risk metrics data
        """
        if var_value is None:
            var_value = np.random.uniform(0.02, 0.08)
        if cvar_value is None:
            cvar_value = var_value * np.random.uniform(1.2, 1.5)
        if sharpe_ratio is None:
            sharpe_ratio = np.random.uniform(0.5, 2.0)
        if sortino_ratio is None:
            sortino_ratio = sharpe_ratio * np.random.uniform(1.0, 1.5)
        if max_drawdown is None:
            max_drawdown = np.random.uniform(0.1, 0.3)
        risk_score = int(var_value * 1000)
        if risk_score < 40:
            risk_level = "low"
        elif risk_score < 70:
            risk_level = "medium"
        else:
            risk_level = "high"
        risk_metrics = {
            "var": var_value,
            "cvar": cvar_value,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "max_drawdown": max_drawdown,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if symbol is not None:
            risk_metrics["symbol"] = symbol
        if portfolio_id is not None:
            risk_metrics["portfolio_id"] = portfolio_id
        return risk_metrics
