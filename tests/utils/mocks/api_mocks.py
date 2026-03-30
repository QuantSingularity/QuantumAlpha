"""
API response mocks for testing.

This module provides utilities to mock API responses for testing purposes.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
import requests


class MockResponse:
    """Mock response for requests library."""

    def __init__(
        self,
        status_code: int = 200,
        json_data: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        content: Optional[bytes] = None,
        reason: str = "OK",
    ) -> None:
        """
        Initialize the mock response.

        Args:
            status_code: HTTP status code
            json_data: JSON response data
            text: Text response
            headers: Response headers
            content: Response content
            reason: Response reason
        """
        self.status_code = status_code
        self._json_data = json_data
        self._text = text
        self.headers = headers or {}
        self._content = content
        self.reason = reason
        self.url = "https://mock.api/endpoint"

    def json(self) -> Any:
        """
        Get JSON response data.

        Returns:
            JSON response data
        """
        return self._json_data

    @property
    def text(self) -> Any:
        """
        Get text response.

        Returns:
            Text response
        """
        if self._text is not None:
            return self._text
        elif self._json_data is not None:
            return json.dumps(self._json_data)
        else:
            return ""

    @property
    def content(self) -> Any:
        """
        Get response content.

        Returns:
            Response content
        """
        if self._content is not None:
            return self._content
        else:
            return self.text.encode("utf-8")

    def raise_for_status(self) -> Any:
        """Raise an exception if the status code indicates an error."""
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(
                f"Mock HTTP Error: {self.status_code} {self.reason}"
            )


class APIMockFactory:
    """Factory for creating API response mocks."""

    @staticmethod
    def create_market_data_response(
        symbol: str,
        timeframe: str = "1d",
        periods: int = 100,
        start_date: Optional[Union[str, datetime]] = None,
    ) -> MockResponse:
        """
        Create a mock market data API response.

        Args:
            symbol: Stock symbol
            timeframe: Timeframe
            periods: Number of periods
            start_date: Start date

        Returns:
            Mock response
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=periods)
        elif isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        timestamps = pd.date_range(
            start=start_date,
            periods=periods,
            freq=timeframe.replace("1d", "D").replace("1h", "H"),
        )
        base_price = 100.0
        volatility = 0.02
        trend = 0.0001
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
        volumes = np.random.normal(1000000, 100000, periods)
        volumes = np.maximum(volumes, 0).astype(int)
        data = []
        for i in range(periods):
            data.append(
                {
                    "timestamp": timestamps[i].isoformat(),
                    "open": open_prices[i],
                    "high": high_prices[i],
                    "low": low_prices[i],
                    "close": close_prices[i],
                    "volume": int(volumes[i]),
                    "symbol": symbol,
                }
            )
        json_data = {"symbol": symbol, "timeframe": timeframe, "data": data}
        return MockResponse(status_code=200, json_data=json_data)

    @staticmethod
    def create_technical_indicators_response(
        symbol: str,
        timeframe: str = "1d",
        periods: int = 100,
        start_date: Optional[Union[str, datetime]] = None,
    ) -> MockResponse:
        """
        Create a mock technical indicators API response.

        Args:
            symbol: Stock symbol
            timeframe: Timeframe
            periods: Number of periods
            start_date: Start date

        Returns:
            Mock response
        """
        market_data_response = APIMockFactory.create_market_data_response(
            symbol=symbol, timeframe=timeframe, periods=periods, start_date=start_date
        )
        market_data = market_data_response.json()["data"]
        for i in range(len(market_data)):
            if i >= 20:
                sma_20 = sum((item["close"] for item in market_data[i - 20 : i])) / 20
                market_data[i]["sma_20"] = sma_20
            else:
                market_data[i]["sma_20"] = None
            if i >= 50:
                sma_50 = sum((item["close"] for item in market_data[i - 50 : i])) / 50
                market_data[i]["sma_50"] = sma_50
            else:
                market_data[i]["sma_50"] = None
            if i >= 14:
                gains = []
                losses = []
                for j in range(i - 14, i):
                    change = market_data[j + 1]["close"] - market_data[j]["close"]
                    if change > 0:
                        gains.append(change)
                        losses.append(0)
                    else:
                        gains.append(0)
                        losses.append(abs(change))
                avg_gain = sum(gains) / 14
                avg_loss = sum(losses) / 14
                if avg_loss == 0:
                    rsi = 100
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - 100 / (1 + rs)
                market_data[i]["rsi_14"] = rsi
            else:
                market_data[i]["rsi_14"] = None
            if i >= 26:
                ema_12 = market_data[i]["close"]
                ema_26 = market_data[i]["close"]
                for j in range(12):
                    ema_12 = 0.85 * ema_12 + 0.15 * market_data[i - j]["close"]
                for j in range(26):
                    ema_26 = 0.93 * ema_26 + 0.07 * market_data[i - j]["close"]
                macd = ema_12 - ema_26
                market_data[i]["macd"] = macd
            else:
                market_data[i]["macd"] = None
        json_data = {"symbol": symbol, "timeframe": timeframe, "data": market_data}
        return MockResponse(status_code=200, json_data=json_data)

    @staticmethod
    def create_prediction_response(
        symbol: str,
        model_id: str = "model_1234567890",
        latest_price: Optional[float] = None,
        days: int = 5,
        trend: float = 0.01,
        volatility: float = 0.02,
    ) -> MockResponse:
        """
        Create a mock prediction API response.

        Args:
            symbol: Stock symbol
            model_id: Model ID
            latest_price: Latest price
            days: Number of days to predict
            trend: Price trend
            volatility: Price volatility

        Returns:
            Mock response
        """
        if latest_price is None:
            latest_price = 100.0
        predicted_prices = []
        current_price = latest_price
        for i in range(days):
            price_change = current_price * (trend + np.random.normal(0, volatility))
            current_price += price_change
            confidence = 0.9 - i * 0.05
            predicted_prices.append(
                {
                    "timestamp": (datetime.now() + timedelta(days=i + 1)).isoformat(),
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
        json_data = {
            "model_id": model_id,
            "symbol": symbol,
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
        return MockResponse(status_code=200, json_data=json_data)

    @staticmethod
    def create_risk_metrics_response(
        symbol: Optional[str] = None,
        portfolio_id: Optional[str] = None,
        var_value: Optional[float] = None,
        cvar_value: Optional[float] = None,
        sharpe_ratio: Optional[float] = None,
        sortino_ratio: Optional[float] = None,
        max_drawdown: Optional[float] = None,
    ) -> MockResponse:
        """
        Create a mock risk metrics API response.

        Args:
            symbol: Stock symbol
            portfolio_id: Portfolio ID
            var_value: Value at Risk
            cvar_value: Conditional Value at Risk
            sharpe_ratio: Sharpe ratio
            sortino_ratio: Sortino ratio
            max_drawdown: Maximum drawdown

        Returns:
            Mock response
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
        json_data = {
            "var": var_value,
            "cvar": cvar_value,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "max_drawdown": max_drawdown,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "timestamp": datetime.now().isoformat(),
        }
        if symbol is not None:
            json_data["symbol"] = symbol
        if portfolio_id is not None:
            json_data["portfolio_id"] = portfolio_id
        return MockResponse(status_code=200, json_data=json_data)

    @staticmethod
    def create_order_response(
        order_id: str,
        user_id: str,
        portfolio_id: str,
        symbol: str,
        side: str,
        order_type: str,
        quantity: int,
        price: Optional[float] = None,
        status: str = "created",
    ) -> MockResponse:
        """
        Create a mock order API response.

        Args:
            order_id: Order ID
            user_id: User ID
            portfolio_id: Portfolio ID
            symbol: Stock symbol
            side: Order side
            order_type: Order type
            quantity: Order quantity
            price: Order price
            status: Order status

        Returns:
            Mock response
        """
        now = datetime.now()
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
        json_data = order
        return MockResponse(status_code=200, json_data=json_data)

    @staticmethod
    def create_portfolio_response(
        portfolio_id: str,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        positions: Optional[List[Dict[str, Any]]] = None,
    ) -> MockResponse:
        """
        Create a mock portfolio API response.

        Args:
            portfolio_id: Portfolio ID
            user_id: User ID
            name: Portfolio name
            description: Portfolio description
            positions: Portfolio positions

        Returns:
            Mock response
        """
        now = datetime.now()
        portfolio = {
            "id": portfolio_id,
            "user_id": user_id,
            "name": name,
            "description": description,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        if positions is not None:
            portfolio["positions"] = positions
            total_value = sum((position["market_value"] for position in positions))
            total_cost = sum((position["cost_basis"] for position in positions))
            total_pl = sum((position["unrealized_pl"] for position in positions))
            total_pl_percent = total_pl / total_cost * 100 if total_cost != 0 else 0
            portfolio.update(
                {
                    "total_value": total_value,
                    "total_cost": total_cost,
                    "total_pl": total_pl,
                    "total_pl_percent": total_pl_percent,
                }
            )
        json_data = portfolio
        return MockResponse(status_code=200, json_data=json_data)

    @staticmethod
    def create_user_response(
        user_id: str,
        username: str,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: str = "user",
    ) -> MockResponse:
        """
        Create a mock user API response.

        Args:
            user_id: User ID
            username: Username
            email: Email
            first_name: First name
            last_name: Last name
            role: User role

        Returns:
            Mock response
        """
        now = datetime.now()
        user = {
            "id": user_id,
            "username": username,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "role": role,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        json_data = user
        return MockResponse(status_code=200, json_data=json_data)

    @staticmethod
    def create_auth_response(
        user_id: str,
        username: str,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: str = "user",
    ) -> MockResponse:
        """
        Create a mock authentication API response.

        Args:
            user_id: User ID
            username: Username
            email: Email
            first_name: First name
            last_name: Last name
            role: User role

        Returns:
            Mock response
        """
        user = {
            "id": user_id,
            "username": username,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "role": role,
        }
        access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl8xMjM0NTY3ODkwIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MTY5MjMwMDB9.6J6vEwrKqZUF9aQQIkxHhOLvK6XnJJEj6xn2d-0g5Yk"
        refresh_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl8xMjM0NTY3ODkwIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MTcwMDk0MDB9.8J8vEwrKqZUF9aQQIkxHhOLvK6XnJJEj6xn2d-0g5Yk"
        json_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user,
        }
        return MockResponse(status_code=200, json_data=json_data)

    @staticmethod
    def create_error_response(
        status_code: int, error: str, message: str
    ) -> MockResponse:
        """
        Create a mock error API response.

        Args:
            status_code: HTTP status code
            error: Error type
            message: Error message

        Returns:
            Mock response
        """
        json_data = {"error": error, "message": message}
        return MockResponse(status_code=status_code, json_data=json_data, reason=error)


class MockAPIClient:
    """Mock API client for testing."""

    def __init__(self, base_url: str = "https://api.example.com") -> None:
        """
        Initialize the mock API client.

        Args:
            base_url: Base URL for the API
        """
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.auth_token = None

    def set_auth_token(self, token: str) -> Any:
        """
        Set the authentication token.

        Args:
            token: Authentication token
        """
        self.auth_token = token
        self.headers["Authorization"] = f"Bearer {token}"

    def get_headers(self) -> Dict[str, str]:
        """
        Get the request headers.

        Returns:
            Request headers
        """
        return self.headers

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> MockResponse:
        """
        Mock GET request.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Mock response
        """
        f"{self.base_url}/{endpoint}"
        if endpoint.startswith("market-data"):
            parts = endpoint.split("/")
            if len(parts) >= 2:
                symbol = parts[1]
                timeframe = params.get("timeframe", "1d") if params else "1d"
                periods = int(params.get("periods", 100)) if params else 100
                return APIMockFactory.create_market_data_response(
                    symbol=symbol, timeframe=timeframe, periods=periods
                )
        elif endpoint.startswith("technical-indicators"):
            parts = endpoint.split("/")
            if len(parts) >= 2:
                symbol = parts[1]
                timeframe = params.get("timeframe", "1d") if params else "1d"
                periods = int(params.get("periods", 100)) if params else 100
                return APIMockFactory.create_technical_indicators_response(
                    symbol=symbol, timeframe=timeframe, periods=periods
                )
        elif endpoint.startswith("predictions"):
            parts = endpoint.split("/")
            if len(parts) >= 3:
                model_id = parts[1]
                symbol = parts[2]
                return APIMockFactory.create_prediction_response(
                    symbol=symbol, model_id=model_id
                )
        elif endpoint.startswith("risk"):
            if "symbol" in params:
                return APIMockFactory.create_risk_metrics_response(
                    symbol=params["symbol"]
                )
            elif "portfolio_id" in params:
                return APIMockFactory.create_risk_metrics_response(
                    portfolio_id=params["portfolio_id"]
                )
        elif endpoint.startswith("orders"):
            parts = endpoint.split("/")
            if len(parts) >= 2:
                order_id = parts[1]
                return APIMockFactory.create_order_response(
                    order_id=order_id,
                    user_id="user_1234567890",
                    portfolio_id="portfolio_1234567890",
                    symbol="AAPL",
                    side="buy",
                    order_type="market",
                    quantity=100,
                    status="created",
                )
        elif endpoint.startswith("portfolios"):
            parts = endpoint.split("/")
            if len(parts) >= 2:
                portfolio_id = parts[1]
                return APIMockFactory.create_portfolio_response(
                    portfolio_id=portfolio_id,
                    user_id="user_1234567890",
                    name="Test Portfolio",
                )
        elif endpoint.startswith("users"):
            parts = endpoint.split("/")
            if len(parts) >= 2:
                user_id = parts[1]
                return APIMockFactory.create_user_response(
                    user_id=user_id,
                    username="testuser",
                    email="test@example.com",
                    first_name="Test",
                    last_name="User",
                )
        return MockResponse(
            status_code=404,
            json_data={"error": "Not Found", "message": "Endpoint not found"},
            reason="Not Found",
        )

    def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> MockResponse:
        """
        Mock POST request.

        Args:
            endpoint: API endpoint
            data: Request data

        Returns:
            Mock response
        """
        f"{self.base_url}/{endpoint}"
        if endpoint == "auth/login":
            if data and "username" in data and ("password" in data):
                return APIMockFactory.create_auth_response(
                    user_id="user_1234567890",
                    username=data["username"],
                    email="test@example.com",
                    first_name="Test",
                    last_name="User",
                )
            else:
                return APIMockFactory.create_error_response(
                    status_code=400,
                    error="Bad Request",
                    message="Username and password are required",
                )
        elif endpoint == "auth/register":
            if (
                data
                and "username" in data
                and ("email" in data)
                and ("password" in data)
            ):
                return APIMockFactory.create_user_response(
                    user_id="user_1234567890",
                    username=data["username"],
                    email=data["email"],
                    first_name=data.get("first_name"),
                    last_name=data.get("last_name"),
                )
            else:
                return APIMockFactory.create_error_response(
                    status_code=400,
                    error="Bad Request",
                    message="Username, email, and password are required",
                )
        elif endpoint.startswith("predict"):
            if data and "model_id" in data and ("symbol" in data):
                return APIMockFactory.create_prediction_response(
                    symbol=data["symbol"], model_id=data["model_id"]
                )
            else:
                return APIMockFactory.create_error_response(
                    status_code=400,
                    error="Bad Request",
                    message="Model ID and symbol are required",
                )
        elif endpoint.startswith("risk"):
            if "symbol" in data:
                return APIMockFactory.create_risk_metrics_response(
                    symbol=data["symbol"]
                )
            elif "portfolio_id" in data:
                return APIMockFactory.create_risk_metrics_response(
                    portfolio_id=data["portfolio_id"]
                )
            else:
                return APIMockFactory.create_error_response(
                    status_code=400,
                    error="Bad Request",
                    message="Symbol or portfolio ID is required",
                )
        elif endpoint == "orders":
            if data and "symbol" in data and ("side" in data) and ("quantity" in data):
                return APIMockFactory.create_order_response(
                    order_id="order_1234567890",
                    user_id="user_1234567890",
                    portfolio_id=data.get("portfolio_id", "portfolio_1234567890"),
                    symbol=data["symbol"],
                    side=data["side"],
                    order_type=data.get("type", "market"),
                    quantity=data["quantity"],
                    price=data.get("price"),
                    status="created",
                )
            else:
                return APIMockFactory.create_error_response(
                    status_code=400,
                    error="Bad Request",
                    message="Symbol, side, and quantity are required",
                )
        elif endpoint == "portfolios":
            if data and "name" in data:
                return APIMockFactory.create_portfolio_response(
                    portfolio_id="portfolio_1234567890",
                    user_id="user_1234567890",
                    name=data["name"],
                    description=data.get("description"),
                )
            else:
                return APIMockFactory.create_error_response(
                    status_code=400,
                    error="Bad Request",
                    message="Portfolio name is required",
                )
        return MockResponse(
            status_code=404,
            json_data={"error": "Not Found", "message": "Endpoint not found"},
            reason="Not Found",
        )

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> MockResponse:
        """
        Mock PUT request.

        Args:
            endpoint: API endpoint
            data: Request data

        Returns:
            Mock response
        """
        f"{self.base_url}/{endpoint}"
        if endpoint.startswith("orders"):
            parts = endpoint.split("/")
            if len(parts) >= 2:
                order_id = parts[1]
                return APIMockFactory.create_order_response(
                    order_id=order_id,
                    user_id="user_1234567890",
                    portfolio_id="portfolio_1234567890",
                    symbol="AAPL",
                    side="buy",
                    order_type="market",
                    quantity=100,
                    status=data.get("status", "created") if data else "created",
                )
        elif endpoint.startswith("portfolios"):
            parts = endpoint.split("/")
            if len(parts) >= 2:
                portfolio_id = parts[1]
                return APIMockFactory.create_portfolio_response(
                    portfolio_id=portfolio_id,
                    user_id="user_1234567890",
                    name=(
                        data.get("name", "Test Portfolio") if data else "Test Portfolio"
                    ),
                    description=data.get("description") if data else None,
                )
        elif endpoint.startswith("users"):
            parts = endpoint.split("/")
            if len(parts) >= 2:
                user_id = parts[1]
                return APIMockFactory.create_user_response(
                    user_id=user_id,
                    username=data.get("username", "testuser") if data else "testuser",
                    email=(
                        data.get("email", "test@example.com")
                        if data
                        else "test@example.com"
                    ),
                    first_name=data.get("first_name") if data else None,
                    last_name=data.get("last_name") if data else None,
                )
        return MockResponse(
            status_code=404,
            json_data={"error": "Not Found", "message": "Endpoint not found"},
            reason="Not Found",
        )

    def delete(self, endpoint: str) -> MockResponse:
        """
        Mock DELETE request.

        Args:
            endpoint: API endpoint

        Returns:
            Mock response
        """
        f"{self.base_url}/{endpoint}"
        if endpoint.startswith("orders"):
            return MockResponse(status_code=204)
        elif endpoint.startswith("portfolios"):
            return MockResponse(status_code=204)
        return MockResponse(
            status_code=404,
            json_data={"error": "Not Found", "message": "Endpoint not found"},
            reason="Not Found",
        )
