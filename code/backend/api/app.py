"""
QuantumAlpha Backend API Service
Main API Gateway providing unified access to all backend services

"""

import logging
import os
import random
import traceback
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, g, jsonify, request
from flask_cors import CORS

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = Flask(__name__)

CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
CORS(app, origins=CORS_ORIGINS, supports_credentials=True)

# ---------------------------------------------------------------------------
# Mock data  (replace with real DB queries once postgres is healthy)
# ---------------------------------------------------------------------------
MOCK_MARKET_DATA: Dict[str, Dict[str, Any]] = {
    "AAPL": {
        "symbol": "AAPL",
        "price": 175.50,
        "change": 2.30,
        "change_percent": 1.33,
        "volume": 45_000_000,
        "market_cap": 2_800_000_000_000,
        "high": 178.00,
        "low": 173.50,
        "open": 174.00,
    },
    "GOOGL": {
        "symbol": "GOOGL",
        "price": 142.80,
        "change": -1.20,
        "change_percent": -0.83,
        "volume": 28_000_000,
        "market_cap": 1_800_000_000_000,
        "high": 145.00,
        "low": 141.50,
        "open": 144.00,
    },
    "MSFT": {
        "symbol": "MSFT",
        "price": 420.15,
        "change": 5.75,
        "change_percent": 1.39,
        "volume": 32_000_000,
        "market_cap": 3_100_000_000_000,
        "high": 425.00,
        "low": 418.00,
        "open": 419.00,
    },
    "AMZN": {
        "symbol": "AMZN",
        "price": 185.40,
        "change": 3.20,
        "change_percent": 1.76,
        "volume": 38_000_000,
        "market_cap": 1_900_000_000_000,
        "high": 188.00,
        "low": 183.00,
        "open": 184.00,
    },
    "TSLA": {
        "symbol": "TSLA",
        "price": 245.60,
        "change": -8.40,
        "change_percent": -3.31,
        "volume": 52_000_000,
        "market_cap": 780_000_000_000,
        "high": 255.00,
        "low": 242.00,
        "open": 252.00,
    },
}

MOCK_PORTFOLIO: Dict[str, Any] = {
    "total_value": 1_250_000.00,
    "daily_change": 15_750.00,
    "daily_change_percent": 1.28,
    "cash_balance": 250_000.00,
    "invested_amount": 1_000_000.00,
    "unrealized_pnl": 125_000.00,
    "realized_pnl": 45_000.00,
    "positions": [
        {
            "symbol": "AAPL",
            "shares": 1000,
            "avg_cost": 165.00,
            "current_price": 175.50,
            "market_value": 175_500.00,
            "unrealized_pnl": 10_500.00,
            "weight": 14.04,
            "sector": "Technology",
        },
        {
            "symbol": "GOOGL",
            "shares": 500,
            "avg_cost": 145.00,
            "current_price": 142.80,
            "market_value": 71_400.00,
            "unrealized_pnl": -1_100.00,
            "weight": 5.71,
            "sector": "Technology",
        },
        {
            "symbol": "MSFT",
            "shares": 800,
            "avg_cost": 410.00,
            "current_price": 420.15,
            "market_value": 336_120.00,
            "unrealized_pnl": 8_120.00,
            "weight": 26.89,
            "sector": "Technology",
        },
        {
            "symbol": "AMZN",
            "shares": 600,
            "avg_cost": 175.00,
            "current_price": 185.40,
            "market_value": 111_240.00,
            "unrealized_pnl": 6_240.00,
            "weight": 8.90,
            "sector": "Consumer Discretionary",
        },
        {
            "symbol": "TSLA",
            "shares": 400,
            "avg_cost": 250.00,
            "current_price": 245.60,
            "market_value": 98_240.00,
            "unrealized_pnl": -1_760.00,
            "weight": 7.86,
            "sector": "Consumer Discretionary",
        },
    ],
}

# Mutable mock stores — use list copies so appends don't bleed across tests
_BASE_STRATEGIES: List[Dict[str, Any]] = [
    {
        "id": "1",
        "name": "Momentum Strategy",
        "description": "Trend-following strategy based on price momentum and moving averages",
        "status": "active",
        "return_ytd": 12.5,
        "sharpe_ratio": 1.8,
        "max_drawdown": -5.2,
        "positions": 15,
        "type": "momentum",
        "created_at": "2024-01-15T00:00:00Z",
    },
    {
        "id": "2",
        "name": "Mean Reversion",
        "description": "Contrarian strategy exploiting price reversals from statistical extremes",
        "status": "active",
        "return_ytd": 8.3,
        "sharpe_ratio": 1.4,
        "max_drawdown": -3.8,
        "positions": 8,
        "type": "mean_reversion",
        "created_at": "2024-02-01T00:00:00Z",
    },
    {
        "id": "3",
        "name": "Pairs Trading",
        "description": "Market-neutral strategy trading correlated pairs with cointegration analysis",
        "status": "paused",
        "return_ytd": 6.7,
        "sharpe_ratio": 2.1,
        "max_drawdown": -2.1,
        "positions": 12,
        "type": "pairs_trading",
        "created_at": "2024-01-20T00:00:00Z",
    },
    {
        "id": "4",
        "name": "Value Investing",
        "description": "Fundamental analysis-based strategy targeting undervalued securities",
        "status": "active",
        "return_ytd": 15.2,
        "sharpe_ratio": 1.6,
        "max_drawdown": -7.5,
        "positions": 20,
        "type": "value",
        "created_at": "2024-01-10T00:00:00Z",
    },
]

_BASE_TRADES: List[Dict[str, Any]] = [
    {
        "id": "1",
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 100,
        "price": 175.50,
        "status": "filled",
        "timestamp": datetime.now().isoformat(),
        "total_value": 17_550.00,
    },
    {
        "id": "2",
        "symbol": "MSFT",
        "side": "buy",
        "quantity": 50,
        "price": 420.15,
        "status": "filled",
        "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
        "total_value": 21_007.50,
    },
    {
        "id": "3",
        "symbol": "TSLA",
        "side": "sell",
        "quantity": 25,
        "price": 245.60,
        "status": "filled",
        "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
        "total_value": 6_140.00,
    },
]

# Runtime-mutable copies (avoids mutating module-level constants)
MOCK_STRATEGIES: List[Dict[str, Any]] = list(_BASE_STRATEGIES)
MOCK_TRADES: List[Dict[str, Any]] = list(_BASE_TRADES)

MOCK_RISK_METRICS: Dict[str, Any] = {
    "portfolio_var_95": 25_000.00,
    "portfolio_var_99": 45_000.00,
    "beta": 1.15,
    "sharpe_ratio": 1.72,
    "sortino_ratio": 2.1,
    "max_drawdown": -8.5,
    "volatility": 18.3,
    "correlation_matrix": {
        "AAPL": {"AAPL": 1.00, "GOOGL": 0.75, "MSFT": 0.82, "AMZN": 0.68, "TSLA": 0.55},
        "GOOGL": {
            "AAPL": 0.75,
            "GOOGL": 1.00,
            "MSFT": 0.78,
            "AMZN": 0.72,
            "TSLA": 0.48,
        },
        "MSFT": {"AAPL": 0.82, "GOOGL": 0.78, "MSFT": 1.00, "AMZN": 0.70, "TSLA": 0.52},
        "AMZN": {"AAPL": 0.68, "GOOGL": 0.72, "MSFT": 0.70, "AMZN": 1.00, "TSLA": 0.45},
        "TSLA": {"AAPL": 0.55, "GOOGL": 0.48, "MSFT": 0.52, "AMZN": 0.45, "TSLA": 1.00},
    },
    "alerts": [
        {
            "type": "warning",
            "message": "TSLA position approaching stop-loss",
            "symbol": "TSLA",
        },
        {"type": "info", "message": "Portfolio beta above target", "value": 1.15},
    ],
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_TIMEFRAME_DAYS: Dict[str, int] = {
    "1W": 7,
    "1M": 30,
    "3M": 90,
    "6M": 180,
    "1Y": 365,
}


def generate_historical_data(symbol: str, days: int = 30) -> List[Dict[str, Any]]:
    """Generate deterministic-ish mock historical OHLCV data."""
    base_price: float = MOCK_MARKET_DATA.get(symbol, {}).get("price", 100.0)
    data: List[Dict[str, Any]] = []
    current_price = base_price

    for i in range(days):
        date = datetime.now() - timedelta(days=days - i)
        change = (random.random() - 0.5) * 10
        current_price = max(current_price + change, 0.01)  # prevent negative price

        data.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "open": round(current_price - (random.random() - 0.5) * 2, 2),
                "high": round(current_price + random.random() * 5, 2),
                "low": round(max(current_price - random.random() * 5, 0.01), 2),
                "close": round(current_price, 2),
                "volume": int(random.random() * 40_000_000) + 10_000_000,
            }
        )

    return data


def _ok(data: object, status: int = 200) -> Tuple[object, int]:
    """Wrap a successful payload in the standard envelope."""
    return (
        jsonify(
            {"success": True, "data": data, "timestamp": datetime.now().isoformat()}
        ),
        status,
    )


def _err(message: str, status: int = 400) -> Tuple[Any, int]:
    """Wrap an error message in the standard envelope."""
    return (
        jsonify(
            {
                "success": False,
                "error": message,
                "timestamp": datetime.now().isoformat(),
            }
        ),
        status,
    )


def _parse_period_days(period: Optional[str], default: int = 30) -> int:
    """Parse a period string like '30d', '7d' into an integer day count."""
    if not period:
        return default
    try:
        return int(period.rstrip("d"))
    except ValueError:
        return default


# ---------------------------------------------------------------------------
# Request lifecycle hooks
# ---------------------------------------------------------------------------


@app.before_request
def attach_request_id() -> None:
    """Attach a unique request ID to g for structured logging."""
    g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))


@app.after_request
def set_request_id_header(response: object) -> None:
    """Echo the request ID back in the response headers."""
    response.headers["X-Request-ID"] = getattr(g, "request_id", "")
    return response


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------


@app.errorhandler(404)
def not_found(_error: Exception) -> Tuple[object, int]:
    return _err("Endpoint not found", 404)


@app.errorhandler(405)
def method_not_allowed(_error: Exception) -> Tuple[object, int]:
    return _err("Method not allowed", 405)


@app.errorhandler(Exception)
def handle_error(error: Exception) -> Tuple[Any, int]:
    """Catch-all for unhandled exceptions — never leak tracebacks to clients."""
    logger.error(
        "Unhandled error | request_id=%s | %s",
        getattr(g, "request_id", "?"),
        traceback.format_exc(),
    )
    return _err("Internal server error", 500)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.route("/health", methods=["GET"])
def health_check() -> Tuple[Any, int]:
    return _ok(
        {
            "service": "quantumalpha-api-gateway",
            "version": "2.0.0",
            "status": "ok",
        }
    )


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


@app.route("/api/auth/login", methods=["POST"])
def login() -> Tuple[Any, int]:
    data = request.get_json(silent=True) or {}
    email = data.get("email") or data.get("username")
    password = data.get("password")

    if not email or not password:
        return _err("Email/username and password are required", 400)

    # TODO: replace with real credential check against postgres users table
    return _ok(
        {
            "token": "mock_jwt_token_12345",
            "refresh_token": "mock_refresh_token_67890",
            "user": {
                "id": "1",
                "email": email,
                "name": "Demo User",
                "role": "trader",
            },
        }
    )


@app.route("/api/auth/register", methods=["POST"])
def register() -> Tuple[Any, int]:
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")
    name = data.get("name", "New User")

    if not email or not password:
        return _err("Email and password are required", 400)

    # TODO: persist to postgres users table
    return _ok(
        {
            "user": {
                "id": str(uuid.uuid4()),
                "email": email,
                "name": name,
                "role": "trader",
            }
        },
        201,
    )


@app.route("/api/auth/user", methods=["GET"])
def get_user() -> Tuple[Any, int]:
    # TODO: decode JWT and look up real user record
    return _ok(
        {
            "id": "1",
            "email": "demo@quantumalpha.com",
            "name": "Demo User",
            "role": "trader",
        }
    )


@app.route("/api/auth/logout", methods=["POST"])
def logout() -> Tuple[Any, int]:
    # TODO: invalidate token in Redis/postgres session store
    return _ok({"message": "Logout successful"})


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------


@app.route("/api/portfolio", methods=["GET"])
def get_portfolio() -> Tuple[Any, int]:
    # TODO: query postgres portfolio schema
    return _ok(MOCK_PORTFOLIO)


@app.route("/api/portfolio/positions", methods=["GET"])
def get_portfolio_positions() -> Tuple[Any, int]:
    return _ok(MOCK_PORTFOLIO["positions"])


@app.route("/api/portfolio/history", methods=["GET"])
def get_portfolio_history() -> Tuple[Any, int]:
    timeframe = request.args.get("timeframe", "1M")
    days = _TIMEFRAME_DAYS.get(timeframe, 30)

    history: List[Dict[str, Any]] = []
    base_value = 1_100_000.0

    for i in range(days):
        date = datetime.now() - timedelta(days=days - i)
        change = (random.random() - 0.48) * 5_000  # slight upward bias
        base_value += change
        history.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "value": round(base_value, 2),
                "change": round(change, 2),
            }
        )

    return _ok(history)


# ---------------------------------------------------------------------------
# Market data
# ---------------------------------------------------------------------------


@app.route("/api/market-data", methods=["GET"])
def get_all_market_data() -> Tuple[Any, int]:
    return _ok(list(MOCK_MARKET_DATA.values()))


@app.route("/api/market-data/<symbol>", methods=["GET"])
def get_market_data(symbol: str) -> Tuple[Any, int]:
    symbol = symbol.upper()
    period = request.args.get("period", "30d")
    days = _parse_period_days(period)

    base = MOCK_MARKET_DATA.get(symbol)
    if base:
        data = {**base, "historical": generate_historical_data(symbol, days)}
    else:
        # Return a plausible stub for unknown symbols rather than an error,
        # matching the original intent.
        price = round(100 + random.random() * 200, 2)
        data = {
            "symbol": symbol,
            "price": price,
            "change": round((random.random() - 0.5) * 10, 2),
            "change_percent": round((random.random() - 0.5) * 5, 2),
            "volume": int(random.random() * 50_000_000),
            "market_cap": int(random.random() * 2_000_000_000_000),
            "historical": generate_historical_data(symbol, days),
        }

    return _ok(data)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


@app.route("/api/strategies", methods=["GET"])
def get_strategies() -> Tuple[Any, int]:
    return _ok(MOCK_STRATEGIES)


@app.route("/api/strategies/<strategy_id>", methods=["GET"])
def get_strategy(strategy_id: str) -> Tuple[Any, int]:
    strategy = next((s for s in MOCK_STRATEGIES if s["id"] == strategy_id), None)
    if not strategy:
        return _err(f"Strategy '{strategy_id}' not found", 404)
    return _ok(strategy)


@app.route("/api/strategies", methods=["POST"])
def create_strategy() -> Tuple[Any, int]:
    data = request.get_json(silent=True) or {}

    if not data.get("name"):
        return _err("'name' is required to create a strategy", 400)

    new_strategy: Dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "name": data["name"],
        "description": data.get("description", ""),
        "status": data.get("status", "paused"),
        "return_ytd": 0.0,
        "sharpe_ratio": 0.0,
        "max_drawdown": 0.0,
        "positions": 0,
        "type": data.get("type", "custom"),
        "created_at": datetime.now().isoformat(),
    }
    MOCK_STRATEGIES.append(new_strategy)
    return _ok(new_strategy, 201)


@app.route("/api/strategies/<strategy_id>", methods=["PATCH"])
def update_strategy(strategy_id: str) -> Tuple[Any, int]:
    data = request.get_json(silent=True) or {}
    strategy = next((s for s in MOCK_STRATEGIES if s["id"] == strategy_id), None)

    if not strategy:
        return _err(f"Strategy '{strategy_id}' not found", 404)

    # Prevent clients from overwriting the immutable id
    data.pop("id", None)
    strategy.update(data)
    return _ok(strategy)


@app.route("/api/strategies/<strategy_id>", methods=["DELETE"])
def delete_strategy(strategy_id: str) -> Tuple[Any, int]:

    before = len(MOCK_STRATEGIES)
    MOCK_STRATEGIES[:] = [s for s in MOCK_STRATEGIES if s["id"] != strategy_id]

    if len(MOCK_STRATEGIES) == before:
        return _err(f"Strategy '{strategy_id}' not found", 404)

    return _ok({"message": f"Strategy '{strategy_id}' deleted"})


# ---------------------------------------------------------------------------
# Trades
# ---------------------------------------------------------------------------


@app.route("/api/trades", methods=["GET"])
def get_trades() -> Tuple[Any, int]:
    symbol = (request.args.get("symbol") or "").upper() or None
    status = request.args.get("status")

    trades = MOCK_TRADES
    if symbol:
        trades = [t for t in trades if t["symbol"] == symbol]
    if status:
        trades = [t for t in trades if t["status"] == status]

    return _ok(trades)


@app.route("/api/trade/order", methods=["POST"])
def place_order() -> Tuple[Any, int]:
    data = request.get_json(silent=True) or {}

    symbol = (data.get("symbol") or "").strip().upper()
    side = data.get("side", "buy")
    quantity = data.get("quantity", 0)
    price = data.get("price", 100.0)

    if not symbol:
        return _err("'symbol' is required", 400)
    if side not in {"buy", "sell"}:
        return _err("'side' must be 'buy' or 'sell'", 400)
    if not isinstance(quantity, (int, float)) or quantity <= 0:
        return _err("'quantity' must be a positive number", 400)
    if not isinstance(price, (int, float)) or price <= 0:
        return _err("'price' must be a positive number", 400)

    new_trade: Dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "price": price,
        "status": "filled",
        "timestamp": datetime.now().isoformat(),
        "total_value": round(quantity * price, 4),
    }
    MOCK_TRADES.append(new_trade)
    return _ok(new_trade, 201)


# ---------------------------------------------------------------------------
# Risk
# ---------------------------------------------------------------------------


@app.route("/api/risk/metrics", methods=["GET"])
def get_portfolio_risk_metrics() -> Tuple[Any, int]:
    # TODO: query risk_service via internal HTTP or postgres risk schema
    return _ok(MOCK_RISK_METRICS)


@app.route("/api/risk/metrics/<strategy_id>", methods=["GET"])
def get_risk_metrics(strategy_id: str) -> Tuple[Any, int]:
    # visible when wiring up the real risk service.
    logger.debug("Risk metrics requested for strategy_id=%s", strategy_id)
    return _ok(MOCK_RISK_METRICS)


# ---------------------------------------------------------------------------
# Watchlist
# ---------------------------------------------------------------------------


@app.route("/api/watchlist", methods=["GET"])
def get_watchlist() -> Tuple[Any, int]:
    watchlist = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META"]
    data = [MOCK_MARKET_DATA.get(s, {"symbol": s, "price": 100.0}) for s in watchlist]
    return _ok(data)


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------


@app.route("/api/news", methods=["GET"])
def get_news() -> Tuple[Any, int]:
    now = datetime.now()
    news = [
        {
            "id": "1",
            "title": "Tech Stocks Rally as AI Adoption Accelerates",
            "summary": "Major technology companies see gains as artificial intelligence integration drives growth expectations.",
            "source": "Financial Times",
            "published_at": (now - timedelta(hours=2)).isoformat(),
            "symbols": ["AAPL", "MSFT", "GOOGL"],
        },
        {
            "id": "2",
            "title": "Federal Reserve Signals Potential Rate Cuts",
            "summary": "Markets react positively to hints of monetary policy easing in the coming months.",
            "source": "Reuters",
            "published_at": (now - timedelta(hours=5)).isoformat(),
            "symbols": ["SPY", "QQQ"],
        },
        {
            "id": "3",
            "title": "Tesla Announces New Manufacturing Facility",
            "summary": "Electric vehicle maker expands production capacity with new plant announcement.",
            "source": "Bloomberg",
            "published_at": (now - timedelta(hours=8)).isoformat(),
            "symbols": ["TSLA"],
        },
    ]
    return _ok(news)


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


@app.route("/api/analytics/performance", methods=["GET"])
def get_performance_analytics() -> Tuple[Any, int]:
    # TODO: compute from postgres trades / portfolio schema
    return _ok(
        {
            "total_return": 15.7,
            "annualized_return": 18.3,
            "volatility": 16.2,
            "sharpe_ratio": 1.72,
            "sortino_ratio": 2.1,
            "max_drawdown": -8.5,
            "calmar_ratio": 2.15,
            "win_rate": 62.5,
            "profit_factor": 1.85,
        }
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    logger.info("Starting QuantumAlpha API Gateway on port %d", port)
    logger.info("Debug mode: %s", debug)

    app.run(host="0.0.0.0", port=port, debug=debug)
