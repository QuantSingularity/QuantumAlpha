"""
QuantumAlpha Backend API Service
Main API Gateway providing unified access to all backend services
"""

import logging
import os
import random
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Configure CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS(app, origins=CORS_ORIGINS, supports_credentials=True)

# Mock data for demonstration
MOCK_MARKET_DATA = {
    "AAPL": {
        "symbol": "AAPL",
        "price": 175.50,
        "change": 2.30,
        "change_percent": 1.33,
        "volume": 45000000,
        "market_cap": 2800000000000,
        "high": 178.00,
        "low": 173.50,
        "open": 174.00,
    },
    "GOOGL": {
        "symbol": "GOOGL",
        "price": 142.80,
        "change": -1.20,
        "change_percent": -0.83,
        "volume": 28000000,
        "market_cap": 1800000000000,
        "high": 145.00,
        "low": 141.50,
        "open": 144.00,
    },
    "MSFT": {
        "symbol": "MSFT",
        "price": 420.15,
        "change": 5.75,
        "change_percent": 1.39,
        "volume": 32000000,
        "market_cap": 3100000000000,
        "high": 425.00,
        "low": 418.00,
        "open": 419.00,
    },
    "AMZN": {
        "symbol": "AMZN",
        "price": 185.40,
        "change": 3.20,
        "change_percent": 1.76,
        "volume": 38000000,
        "market_cap": 1900000000000,
        "high": 188.00,
        "low": 183.00,
        "open": 184.00,
    },
    "TSLA": {
        "symbol": "TSLA",
        "price": 245.60,
        "change": -8.40,
        "change_percent": -3.31,
        "volume": 52000000,
        "market_cap": 780000000000,
        "high": 255.00,
        "low": 242.00,
        "open": 252.00,
    },
}

MOCK_PORTFOLIO = {
    "total_value": 1250000.00,
    "daily_change": 15750.00,
    "daily_change_percent": 1.28,
    "cash_balance": 250000.00,
    "invested_amount": 1000000.00,
    "unrealized_pnl": 125000.00,
    "realized_pnl": 45000.00,
    "positions": [
        {
            "symbol": "AAPL",
            "shares": 1000,
            "avg_cost": 165.00,
            "current_price": 175.50,
            "market_value": 175500.00,
            "unrealized_pnl": 10500.00,
            "weight": 14.04,
            "sector": "Technology",
        },
        {
            "symbol": "GOOGL",
            "shares": 500,
            "avg_cost": 145.00,
            "current_price": 142.80,
            "market_value": 71400.00,
            "unrealized_pnl": -1100.00,
            "weight": 5.71,
            "sector": "Technology",
        },
        {
            "symbol": "MSFT",
            "shares": 800,
            "avg_cost": 410.00,
            "current_price": 420.15,
            "market_value": 336120.00,
            "unrealized_pnl": 8120.00,
            "weight": 26.89,
            "sector": "Technology",
        },
        {
            "symbol": "AMZN",
            "shares": 600,
            "avg_cost": 175.00,
            "current_price": 185.40,
            "market_value": 111240.00,
            "unrealized_pnl": 6240.00,
            "weight": 8.90,
            "sector": "Consumer Discretionary",
        },
        {
            "symbol": "TSLA",
            "shares": 400,
            "avg_cost": 250.00,
            "current_price": 245.60,
            "market_value": 98240.00,
            "unrealized_pnl": -1760.00,
            "weight": 7.86,
            "sector": "Consumer Discretionary",
        },
    ],
}

MOCK_STRATEGIES = [
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

MOCK_TRADES = [
    {
        "id": "1",
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 100,
        "price": 175.50,
        "status": "filled",
        "timestamp": datetime.now().isoformat(),
        "total_value": 17550.00,
    },
    {
        "id": "2",
        "symbol": "MSFT",
        "side": "buy",
        "quantity": 50,
        "price": 420.15,
        "status": "filled",
        "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
        "total_value": 21007.50,
    },
    {
        "id": "3",
        "symbol": "TSLA",
        "side": "sell",
        "quantity": 25,
        "price": 245.60,
        "status": "filled",
        "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
        "total_value": 6140.00,
    },
]

MOCK_RISK_METRICS = {
    "portfolio_var_95": 25000.00,
    "portfolio_var_99": 45000.00,
    "beta": 1.15,
    "sharpe_ratio": 1.72,
    "sortino_ratio": 2.1,
    "max_drawdown": -8.5,
    "volatility": 18.3,
    "correlation_matrix": {
        "AAPL": {"AAPL": 1.0, "GOOGL": 0.75, "MSFT": 0.82, "AMZN": 0.68, "TSLA": 0.55},
        "GOOGL": {"AAPL": 0.75, "GOOGL": 1.0, "MSFT": 0.78, "AMZN": 0.72, "TSLA": 0.48},
        "MSFT": {"AAPL": 0.82, "GOOGL": 0.78, "MSFT": 1.0, "AMZN": 0.70, "TSLA": 0.52},
        "AMZN": {"AAPL": 0.68, "GOOGL": 0.72, "MSFT": 0.70, "AMZN": 1.0, "TSLA": 0.45},
        "TSLA": {"AAPL": 0.55, "GOOGL": 0.48, "MSFT": 0.52, "AMZN": 0.45, "TSLA": 1.0},
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


def generate_historical_data(symbol: str, days: int = 30) -> List[Dict[str, Any]]:
    """Generate mock historical price data"""
    base_price = MOCK_MARKET_DATA.get(symbol, {}).get("price", 100)
    data = []
    current_price = base_price

    for i in range(days):
        date = datetime.now() - timedelta(days=days - i)
        change = (random.random() - 0.5) * 10
        current_price += change

        data.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "open": round(current_price - (random.random() - 0.5) * 2, 2),
                "high": round(current_price + random.random() * 5, 2),
                "low": round(current_price - random.random() * 5, 2),
                "close": round(current_price, 2),
                "volume": int(random.random() * 40000000) + 10000000,
            }
        )

    return data


# Error handlers
@app.errorhandler(Exception)
def handle_error(error: Any) -> Any:
    """Handle all unhandled errors"""
    logger.error(f"Unhandled error: {error}")
    logger.error(traceback.format_exc())
    return (
        jsonify(
            {
                "success": False,
                "error": "Internal server error",
                "message": str(error),
            }
        ),
        500,
    )


# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check() -> Any:
    """Health check endpoint"""
    return jsonify(
        {
            "status": "ok",
            "service": "quantumalpha-api-gateway",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
        }
    )


# =================================================================
# Authentication Endpoints
# =================================================================


@app.route("/api/auth/login", methods=["POST"])
def login() -> Any:
    """User login endpoint"""
    try:
        data = request.json or {}
        email = data.get("email", data.get("username"))
        password = data.get("password")

        if not email or not password:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Email/username and password are required",
                    }
                ),
                400,
            )

        # Mock authentication - accept any credentials for demo
        return jsonify(
            {
                "success": True,
                "data": {
                    "token": "mock_jwt_token_12345",
                    "refresh_token": "mock_refresh_token_67890",
                    "user": {
                        "id": "1",
                        "email": email,
                        "name": "Demo User",
                        "role": "trader",
                    },
                },
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/auth/register", methods=["POST"])
def register() -> Any:
    """User registration endpoint"""
    try:
        data = request.json or {}
        email = data.get("email")
        password = data.get("password")
        name = data.get("name")

        if not email or not password:
            return (
                jsonify({"success": False, "error": "Email and password are required"}),
                400,
            )

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "user": {
                            "id": "2",
                            "email": email,
                            "name": name or "New User",
                            "role": "trader",
                        },
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            201,
        )
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/auth/user", methods=["GET"])
def get_user() -> Any:
    """Get current user info"""
    try:
        return jsonify(
            {
                "success": True,
                "data": {
                    "id": "1",
                    "email": "demo@quantumalpha.com",
                    "name": "Demo User",
                    "role": "trader",
                },
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/auth/logout", methods=["POST"])
def logout() -> Any:
    """User logout endpoint"""
    return jsonify(
        {
            "success": True,
            "message": "Logout successful",
            "timestamp": datetime.now().isoformat(),
        }
    )


# =================================================================
# Portfolio Endpoints
# =================================================================


@app.route("/api/portfolio", methods=["GET"])
def get_portfolio() -> Any:
    """Get portfolio data"""
    try:
        return jsonify(
            {
                "success": True,
                "data": MOCK_PORTFOLIO,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/portfolio/positions", methods=["GET"])
def get_portfolio_positions() -> Any:
    """Get portfolio positions"""
    try:
        return jsonify(
            {
                "success": True,
                "data": MOCK_PORTFOLIO["positions"],
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error getting portfolio positions: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/portfolio/history", methods=["GET"])
def get_portfolio_history() -> Any:
    """Get portfolio history"""
    try:
        timeframe = request.args.get("timeframe", "1M")
        days = {"1W": 7, "1M": 30, "3M": 90, "6M": 180, "1Y": 365}.get(timeframe, 30)

        history = []
        base_value = 1100000
        for i in range(days):
            date = datetime.now() - timedelta(days=days - i)
            change = (random.random() - 0.48) * 5000  # Slight upward bias
            base_value += change
            history.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "value": round(base_value, 2),
                    "change": round(change, 2),
                }
            )

        return jsonify(
            {
                "success": True,
                "data": history,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error getting portfolio history: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =================================================================
# Market Data Endpoints
# =================================================================


@app.route("/api/market-data/<symbol>", methods=["GET"])
def get_market_data(symbol: str) -> Any:
    """Get market data for a symbol"""
    try:
        symbol = symbol.upper()
        timeframe = request.args.get("timeframe", "1d")
        period = request.args.get("period", "30d")

        if symbol in MOCK_MARKET_DATA:
            data = MOCK_MARKET_DATA[symbol].copy()
            days = int(period.replace("d", "")) if "d" in period else 30
            data["historical"] = generate_historical_data(symbol, days)

            return jsonify(
                {
                    "success": True,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        else:
            # Return mock data for unknown symbols
            return jsonify(
                {
                    "success": True,
                    "data": {
                        "symbol": symbol,
                        "price": round(100 + random.random() * 200, 2),
                        "change": round((random.random() - 0.5) * 10, 2),
                        "change_percent": round((random.random() - 0.5) * 5, 2),
                        "volume": int(random.random() * 50000000),
                        "market_cap": int(random.random() * 2000000000000),
                        "historical": generate_historical_data(symbol, 30),
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            )
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/market-data", methods=["GET"])
def get_all_market_data() -> Any:
    """Get all market data"""
    try:
        return jsonify(
            {
                "success": True,
                "data": list(MOCK_MARKET_DATA.values()),
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error getting all market data: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =================================================================
# Strategy Endpoints
# =================================================================


@app.route("/api/strategies", methods=["GET"])
def get_strategies() -> Any:
    """Get all trading strategies"""
    try:
        return jsonify(
            {
                "success": True,
                "data": MOCK_STRATEGIES,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/strategies/<strategy_id>", methods=["GET"])
def get_strategy(strategy_id: str) -> Any:
    """Get a specific strategy"""
    try:
        strategy = next((s for s in MOCK_STRATEGIES if s["id"] == strategy_id), None)
        if strategy:
            return jsonify(
                {
                    "success": True,
                    "data": strategy,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        else:
            return (
                jsonify(
                    {"success": False, "error": f"Strategy {strategy_id} not found"}
                ),
                404,
            )
    except Exception as e:
        logger.error(f"Error getting strategy: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/strategies", methods=["POST"])
def create_strategy() -> Any:
    """Create a new strategy"""
    try:
        data = request.json or {}
        new_strategy = {
            "id": str(len(MOCK_STRATEGIES) + 1),
            "name": data.get("name", "New Strategy"),
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

        return (
            jsonify(
                {
                    "success": True,
                    "data": new_strategy,
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            201,
        )
    except Exception as e:
        logger.error(f"Error creating strategy: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/strategies/<strategy_id>", methods=["PATCH"])
def update_strategy(strategy_id: str) -> Any:
    """Update a strategy"""
    try:
        data = request.json or {}
        strategy = next((s for s in MOCK_STRATEGIES if s["id"] == strategy_id), None)

        if strategy:
            strategy.update(data)
            return jsonify(
                {
                    "success": True,
                    "data": strategy,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        else:
            return (
                jsonify(
                    {"success": False, "error": f"Strategy {strategy_id} not found"}
                ),
                404,
            )
    except Exception as e:
        logger.error(f"Error updating strategy: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/strategies/<strategy_id>", methods=["DELETE"])
def delete_strategy(strategy_id: str) -> Any:
    """Delete a strategy"""
    try:
        global MOCK_STRATEGIES
        MOCK_STRATEGIES = [s for s in MOCK_STRATEGIES if s["id"] != strategy_id]

        return jsonify(
            {
                "success": True,
                "message": f"Strategy {strategy_id} deleted",
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error deleting strategy: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =================================================================
# Trade Endpoints
# =================================================================


@app.route("/api/trades", methods=["GET"])
def get_trades() -> Any:
    """Get all trades"""
    try:
        params = request.args
        trades = MOCK_TRADES

        if params.get("symbol"):
            trades = [t for t in trades if t["symbol"] == params.get("symbol").upper()]
        if params.get("status"):
            trades = [t for t in trades if t["status"] == params.get("status")]

        return jsonify(
            {
                "success": True,
                "data": trades,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/trade/order", methods=["POST"])
def place_order() -> Any:
    """Place a new order"""
    try:
        data = request.json or {}

        new_trade = {
            "id": str(len(MOCK_TRADES) + 1),
            "symbol": data.get("symbol", "UNKNOWN").upper(),
            "side": data.get("side", "buy"),
            "quantity": data.get("quantity", 0),
            "price": data.get("price", 100.0),
            "status": "filled",
            "timestamp": datetime.now().isoformat(),
            "total_value": data.get("quantity", 0) * data.get("price", 100.0),
        }
        MOCK_TRADES.append(new_trade)

        return (
            jsonify(
                {
                    "success": True,
                    "data": new_trade,
                    "message": "Order placed successfully",
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            201,
        )
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =================================================================
# Risk Endpoints
# =================================================================


@app.route("/api/risk/metrics/<strategy_id>", methods=["GET"])
def get_risk_metrics(strategy_id: str = None) -> Any:
    """Get risk metrics"""
    try:
        return jsonify(
            {
                "success": True,
                "data": MOCK_RISK_METRICS,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/risk/metrics", methods=["GET"])
def get_portfolio_risk_metrics() -> Any:
    """Get portfolio risk metrics"""
    try:
        return jsonify(
            {
                "success": True,
                "data": MOCK_RISK_METRICS,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error getting portfolio risk metrics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =================================================================
# Watchlist Endpoints
# =================================================================


@app.route("/api/watchlist", methods=["GET"])
def get_watchlist() -> Any:
    """Get user's watchlist"""
    try:
        watchlist = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META"]
        data = [
            MOCK_MARKET_DATA.get(s, {"symbol": s, "price": 100.0}) for s in watchlist
        ]

        return jsonify(
            {
                "success": True,
                "data": data,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error getting watchlist: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =================================================================
# News Endpoints
# =================================================================


@app.route("/api/news", methods=["GET"])
def get_news() -> Any:
    """Get financial news"""
    try:
        news = [
            {
                "id": "1",
                "title": "Tech Stocks Rally as AI Adoption Accelerates",
                "summary": "Major technology companies see gains as artificial intelligence integration drives growth expectations.",
                "source": "Financial Times",
                "published_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "symbols": ["AAPL", "MSFT", "GOOGL"],
            },
            {
                "id": "2",
                "title": "Federal Reserve Signals Potential Rate Cuts",
                "summary": "Markets react positively to hints of monetary policy easing in the coming months.",
                "source": "Reuters",
                "published_at": (datetime.now() - timedelta(hours=5)).isoformat(),
                "symbols": ["SPY", "QQQ"],
            },
            {
                "id": "3",
                "title": "Tesla Announces New Manufacturing Facility",
                "summary": "Electric vehicle maker expands production capacity with new plant announcement.",
                "source": "Bloomberg",
                "published_at": (datetime.now() - timedelta(hours=8)).isoformat(),
                "symbols": ["TSLA"],
            },
        ]

        return jsonify(
            {
                "success": True,
                "data": news,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error getting news: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =================================================================
# Analytics Endpoints
# =================================================================


@app.route("/api/analytics/performance", methods=["GET"])
def get_performance_analytics() -> Any:
    """Get performance analytics"""
    try:
        return jsonify(
            {
                "success": True,
                "data": {
                    "total_return": 15.7,
                    "annualized_return": 18.3,
                    "volatility": 16.2,
                    "sharpe_ratio": 1.72,
                    "sortino_ratio": 2.1,
                    "max_drawdown": -8.5,
                    "calmar_ratio": 2.15,
                    "win_rate": 62.5,
                    "profit_factor": 1.85,
                },
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error getting performance analytics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =================================================================
# Main Entry Point
# =================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    logger.info(f"Starting QuantumAlpha API Gateway on port {port}")
    logger.info(f"Debug mode: {debug}")

    app.run(host="0.0.0.0", port=port, debug=debug)
