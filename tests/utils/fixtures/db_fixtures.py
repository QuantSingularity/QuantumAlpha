"""
Database fixtures for testing.

This module provides utilities to create and manage test database fixtures.
"""

import os
import sqlite3
import tempfile
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import pytest


class TestDatabaseFixture:
    """SQLite database fixture for testing."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        """
        Initialize the test database fixture.

        Args:
            db_path: Path to the SQLite database file
        """
        if db_path is None:
            self.temp_dir = tempfile.TemporaryDirectory()
            self.db_path = os.path.join(self.temp_dir.name, "test_db.sqlite")
        else:
            self.temp_dir = None
            self.db_path = db_path
        self.conn = None

    def setup(self) -> Any:
        """Set up the test database."""
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()

    def teardown(self) -> Any:
        """Tear down the test database."""
        if self.conn:
            self.conn.close()
            self.conn = None
        if self.temp_dir:
            self.temp_dir.cleanup()

    def _create_tables(self) -> Any:
        """Create database tables."""
        cursor = self.conn.cursor()
        cursor.execute(
            "\n        CREATE TABLE IF NOT EXISTS users (\n            id TEXT PRIMARY KEY,\n            username TEXT UNIQUE NOT NULL,\n            email TEXT UNIQUE NOT NULL,\n            password_hash TEXT NOT NULL,\n            first_name TEXT,\n            last_name TEXT,\n            role TEXT NOT NULL,\n            created_at TEXT NOT NULL,\n            updated_at TEXT NOT NULL\n        )\n        "
        )
        cursor.execute(
            "\n        CREATE TABLE IF NOT EXISTS portfolios (\n            id TEXT PRIMARY KEY,\n            user_id TEXT NOT NULL,\n            name TEXT NOT NULL,\n            description TEXT,\n            created_at TEXT NOT NULL,\n            updated_at TEXT NOT NULL,\n            FOREIGN KEY (user_id) REFERENCES users (id)\n        )\n        "
        )
        cursor.execute(
            "\n        CREATE TABLE IF NOT EXISTS positions (\n            id TEXT PRIMARY KEY,\n            portfolio_id TEXT NOT NULL,\n            symbol TEXT NOT NULL,\n            quantity REAL NOT NULL,\n            average_entry_price REAL NOT NULL,\n            created_at TEXT NOT NULL,\n            updated_at TEXT NOT NULL,\n            FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)\n        )\n        "
        )
        cursor.execute(
            "\n        CREATE TABLE IF NOT EXISTS orders (\n            id TEXT PRIMARY KEY,\n            user_id TEXT NOT NULL,\n            portfolio_id TEXT NOT NULL,\n            symbol TEXT NOT NULL,\n            side TEXT NOT NULL,\n            type TEXT NOT NULL,\n            status TEXT NOT NULL,\n            quantity REAL NOT NULL,\n            price REAL,\n            filled_quantity REAL,\n            average_fill_price REAL,\n            broker_order_id TEXT,\n            created_at TEXT NOT NULL,\n            updated_at TEXT NOT NULL,\n            FOREIGN KEY (user_id) REFERENCES users (id),\n            FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)\n        )\n        "
        )
        cursor.execute(
            "\n        CREATE TABLE IF NOT EXISTS executions (\n            id TEXT PRIMARY KEY,\n            order_id TEXT NOT NULL,\n            price REAL NOT NULL,\n            quantity REAL NOT NULL,\n            timestamp TEXT NOT NULL,\n            broker_execution_id TEXT,\n            FOREIGN KEY (order_id) REFERENCES orders (id)\n        )\n        "
        )
        cursor.execute(
            "\n        CREATE TABLE IF NOT EXISTS market_data (\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n            symbol TEXT NOT NULL,\n            timestamp TEXT NOT NULL,\n            timeframe TEXT NOT NULL,\n            open REAL NOT NULL,\n            high REAL NOT NULL,\n            low REAL NOT NULL,\n            close REAL NOT NULL,\n            volume INTEGER NOT NULL,\n            UNIQUE(symbol, timestamp, timeframe)\n        )\n        "
        )
        cursor.execute(
            "\n        CREATE TABLE IF NOT EXISTS models (\n            id TEXT PRIMARY KEY,\n            name TEXT NOT NULL,\n            description TEXT,\n            model_type TEXT NOT NULL,\n            version TEXT NOT NULL,\n            status TEXT NOT NULL,\n            created_at TEXT NOT NULL,\n            updated_at TEXT NOT NULL\n        )\n        "
        )
        cursor.execute(
            "\n        CREATE TABLE IF NOT EXISTS predictions (\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n            model_id TEXT NOT NULL,\n            symbol TEXT NOT NULL,\n            timestamp TEXT NOT NULL,\n            prediction_timestamp TEXT NOT NULL,\n            value REAL NOT NULL,\n            confidence REAL NOT NULL,\n            FOREIGN KEY (model_id) REFERENCES models (id)\n        )\n        "
        )
        cursor.execute(
            "\n        CREATE TABLE IF NOT EXISTS risk_metrics (\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n            symbol TEXT,\n            portfolio_id TEXT,\n            timestamp TEXT NOT NULL,\n            var REAL NOT NULL,\n            cvar REAL NOT NULL,\n            sharpe_ratio REAL,\n            sortino_ratio REAL,\n            max_drawdown REAL,\n            risk_score INTEGER NOT NULL,\n            risk_level TEXT NOT NULL,\n            FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)\n        )\n        "
        )
        self.conn.commit()

    def insert_users(self, users: List[Dict[str, Any]]) -> Any:
        """
        Insert users into the database.

        Args:
            users: List of user data dictionaries
        """
        cursor = self.conn.cursor()
        for user in users:
            cursor.execute(
                "\n            INSERT INTO users (id, username, email, password_hash, first_name, last_name, role, created_at, updated_at)\n            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)\n            ",
                (
                    user["id"],
                    user["username"],
                    user["email"],
                    user["password_hash"],
                    user.get("first_name"),
                    user.get("last_name"),
                    user["role"],
                    user["created_at"],
                    user["updated_at"],
                ),
            )
        self.conn.commit()

    def insert_portfolios(self, portfolios: List[Dict[str, Any]]) -> Any:
        """
        Insert portfolios into the database.

        Args:
            portfolios: List of portfolio data dictionaries
        """
        cursor = self.conn.cursor()
        for portfolio in portfolios:
            cursor.execute(
                "\n            INSERT INTO portfolios (id, user_id, name, description, created_at, updated_at)\n            VALUES (?, ?, ?, ?, ?, ?)\n            ",
                (
                    portfolio["id"],
                    portfolio["user_id"],
                    portfolio["name"],
                    portfolio.get("description"),
                    portfolio["created_at"],
                    portfolio["updated_at"],
                ),
            )
        self.conn.commit()

    def insert_positions(self, positions: List[Dict[str, Any]]) -> Any:
        """
        Insert positions into the database.

        Args:
            positions: List of position data dictionaries
        """
        cursor = self.conn.cursor()
        for position in positions:
            cursor.execute(
                "\n            INSERT INTO positions (id, portfolio_id, symbol, quantity, average_entry_price, created_at, updated_at)\n            VALUES (?, ?, ?, ?, ?, ?, ?)\n            ",
                (
                    position["id"],
                    position["portfolio_id"],
                    position["symbol"],
                    position["quantity"],
                    position["average_entry_price"],
                    position["created_at"],
                    position["updated_at"],
                ),
            )
        self.conn.commit()

    def insert_orders(self, orders: List[Dict[str, Any]]) -> Any:
        """
        Insert orders into the database.

        Args:
            orders: List of order data dictionaries
        """
        cursor = self.conn.cursor()
        for order in orders:
            cursor.execute(
                "\n            INSERT INTO orders (id, user_id, portfolio_id, symbol, side, type, status, quantity, price, filled_quantity, average_fill_price, broker_order_id, created_at, updated_at)\n            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n            ",
                (
                    order["id"],
                    order["user_id"],
                    order["portfolio_id"],
                    order["symbol"],
                    order["side"],
                    order["type"],
                    order["status"],
                    order["quantity"],
                    order.get("price"),
                    order.get("filled_quantity"),
                    order.get("average_fill_price"),
                    order.get("broker_order_id"),
                    order["created_at"],
                    order["updated_at"],
                ),
            )
        self.conn.commit()

    def insert_executions(self, executions: List[Dict[str, Any]]) -> Any:
        """
        Insert executions into the database.

        Args:
            executions: List of execution data dictionaries
        """
        cursor = self.conn.cursor()
        for execution in executions:
            cursor.execute(
                "\n            INSERT INTO executions (id, order_id, price, quantity, timestamp, broker_execution_id)\n            VALUES (?, ?, ?, ?, ?, ?)\n            ",
                (
                    execution["id"],
                    execution["order_id"],
                    execution["price"],
                    execution["quantity"],
                    execution["timestamp"],
                    execution.get("broker_execution_id"),
                ),
            )
        self.conn.commit()

    def insert_market_data(self, market_data: pd.DataFrame) -> Any:
        """
        Insert market data into the database.

        Args:
            market_data: DataFrame with market data
        """
        market_data.to_sql("market_data", self.conn, if_exists="append", index=False)
        self.conn.commit()

    def insert_models(self, models: List[Dict[str, Any]]) -> Any:
        """
        Insert models into the database.

        Args:
            models: List of model data dictionaries
        """
        cursor = self.conn.cursor()
        for model in models:
            cursor.execute(
                "\n            INSERT INTO models (id, name, description, model_type, version, status, created_at, updated_at)\n            VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n            ",
                (
                    model["id"],
                    model["name"],
                    model.get("description"),
                    model["model_type"],
                    model["version"],
                    model["status"],
                    model["created_at"],
                    model["updated_at"],
                ),
            )
        self.conn.commit()

    def insert_predictions(self, predictions: List[Dict[str, Any]]) -> Any:
        """
        Insert predictions into the database.

        Args:
            predictions: List of prediction data dictionaries
        """
        cursor = self.conn.cursor()
        for prediction in predictions:
            cursor.execute(
                "\n            INSERT INTO predictions (model_id, symbol, timestamp, prediction_timestamp, value, confidence)\n            VALUES (?, ?, ?, ?, ?, ?)\n            ",
                (
                    prediction["model_id"],
                    prediction["symbol"],
                    prediction["timestamp"],
                    prediction["prediction_timestamp"],
                    prediction["value"],
                    prediction["confidence"],
                ),
            )
        self.conn.commit()

    def insert_risk_metrics(self, risk_metrics: List[Dict[str, Any]]) -> Any:
        """
        Insert risk metrics into the database.

        Args:
            risk_metrics: List of risk metric data dictionaries
        """
        cursor = self.conn.cursor()
        for metric in risk_metrics:
            cursor.execute(
                "\n            INSERT INTO risk_metrics (symbol, portfolio_id, timestamp, var, cvar, sharpe_ratio, sortino_ratio, max_drawdown, risk_score, risk_level)\n            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n            ",
                (
                    metric.get("symbol"),
                    metric.get("portfolio_id"),
                    metric["timestamp"],
                    metric["var"],
                    metric["cvar"],
                    metric.get("sharpe_ratio"),
                    metric.get("sortino_ratio"),
                    metric.get("max_drawdown"),
                    metric["risk_score"],
                    metric["risk_level"],
                ),
            )
        self.conn.commit()

    def query(self, sql: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """
        Execute a SQL query.

        Args:
            sql: SQL query
            params: Query parameters

        Returns:
            Query results
        """
        cursor = self.conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor.fetchall()

    def query_df(self, sql: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a DataFrame.

        Args:
            sql: SQL query
            params: Query parameters

        Returns:
            DataFrame with query results
        """
        if params:
            return pd.read_sql_query(sql, self.conn, params=params)
        else:
            return pd.read_sql_query(sql, self.conn)


@pytest.fixture
def test_db() -> Any:
    """Pytest fixture for test database."""
    db = TestDatabaseFixture()
    db.setup()
    yield db
    db.teardown()


class MockDatabaseManager:
    """Mock database manager for testing."""

    def __init__(self, db_fixture: TestDatabaseFixture) -> None:
        """
        Initialize the mock database manager.

        Args:
            db_fixture: Test database fixture
        """
        self.db = db_fixture

    def execute_query(self, sql: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """
        Execute a SQL query.

        Args:
            sql: SQL query
            params: Query parameters

        Returns:
            Query results
        """
        return self.db.query(sql, params)

    def execute_query_df(
        self, sql: str, params: Optional[Tuple] = None
    ) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a DataFrame.

        Args:
            sql: SQL query
            params: Query parameters

        Returns:
            DataFrame with query results
        """
        return self.db.query_df(sql, params)

    def insert_user(self, user: Dict[str, Any]) -> str:
        """
        Insert a user into the database.

        Args:
            user: User data dictionary

        Returns:
            User ID
        """
        self.db.insert_users([user])
        return user["id"]

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by ID.

        Args:
            user_id: User ID

        Returns:
            User data dictionary
        """
        result = self.db.query("SELECT * FROM users WHERE id = ?", (user_id,))
        if not result:
            return None
        user = result[0]
        return {
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "password_hash": user[3],
            "first_name": user[4],
            "last_name": user[5],
            "role": user[6],
            "created_at": user[7],
            "updated_at": user[8],
        }

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by username.

        Args:
            username: Username

        Returns:
            User data dictionary
        """
        result = self.db.query("SELECT * FROM users WHERE username = ?", (username,))
        if not result:
            return None
        user = result[0]
        return {
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "password_hash": user[3],
            "first_name": user[4],
            "last_name": user[5],
            "role": user[6],
            "created_at": user[7],
            "updated_at": user[8],
        }

    def insert_portfolio(self, portfolio: Dict[str, Any]) -> str:
        """
        Insert a portfolio into the database.

        Args:
            portfolio: Portfolio data dictionary

        Returns:
            Portfolio ID
        """
        self.db.insert_portfolios([portfolio])
        return portfolio["id"]

    def get_portfolio_by_id(self, portfolio_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a portfolio by ID.

        Args:
            portfolio_id: Portfolio ID

        Returns:
            Portfolio data dictionary
        """
        result = self.db.query("SELECT * FROM portfolios WHERE id = ?", (portfolio_id,))
        if not result:
            return None
        portfolio = result[0]
        return {
            "id": portfolio[0],
            "user_id": portfolio[1],
            "name": portfolio[2],
            "description": portfolio[3],
            "created_at": portfolio[4],
            "updated_at": portfolio[5],
        }

    def get_portfolios_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get portfolios by user ID.

        Args:
            user_id: User ID

        Returns:
            List of portfolio data dictionaries
        """
        results = self.db.query(
            "SELECT * FROM portfolios WHERE user_id = ?", (user_id,)
        )
        portfolios = []
        for result in results:
            portfolios.append(
                {
                    "id": result[0],
                    "user_id": result[1],
                    "name": result[2],
                    "description": result[3],
                    "created_at": result[4],
                    "updated_at": result[5],
                }
            )
        return portfolios

    def insert_position(self, position: Dict[str, Any]) -> str:
        """
        Insert a position into the database.

        Args:
            position: Position data dictionary

        Returns:
            Position ID
        """
        self.db.insert_positions([position])
        return position["id"]

    def get_position_by_id(self, position_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a position by ID.

        Args:
            position_id: Position ID

        Returns:
            Position data dictionary
        """
        result = self.db.query("SELECT * FROM positions WHERE id = ?", (position_id,))
        if not result:
            return None
        position = result[0]
        return {
            "id": position[0],
            "portfolio_id": position[1],
            "symbol": position[2],
            "quantity": position[3],
            "average_entry_price": position[4],
            "created_at": position[5],
            "updated_at": position[6],
        }

    def get_positions_by_portfolio_id(self, portfolio_id: str) -> List[Dict[str, Any]]:
        """
        Get positions by portfolio ID.

        Args:
            portfolio_id: Portfolio ID

        Returns:
            List of position data dictionaries
        """
        results = self.db.query(
            "SELECT * FROM positions WHERE portfolio_id = ?", (portfolio_id,)
        )
        positions = []
        for result in results:
            positions.append(
                {
                    "id": result[0],
                    "portfolio_id": result[1],
                    "symbol": result[2],
                    "quantity": result[3],
                    "average_entry_price": result[4],
                    "created_at": result[5],
                    "updated_at": result[6],
                }
            )
        return positions

    def insert_order(self, order: Dict[str, Any]) -> str:
        """
        Insert an order into the database.

        Args:
            order: Order data dictionary

        Returns:
            Order ID
        """
        self.db.insert_orders([order])
        return order["id"]

    def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an order by ID.

        Args:
            order_id: Order ID

        Returns:
            Order data dictionary
        """
        result = self.db.query("SELECT * FROM orders WHERE id = ?", (order_id,))
        if not result:
            return None
        order = result[0]
        return {
            "id": order[0],
            "user_id": order[1],
            "portfolio_id": order[2],
            "symbol": order[3],
            "side": order[4],
            "type": order[5],
            "status": order[6],
            "quantity": order[7],
            "price": order[8],
            "filled_quantity": order[9],
            "average_fill_price": order[10],
            "broker_order_id": order[11],
            "created_at": order[12],
            "updated_at": order[13],
        }

    def get_orders_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get orders by user ID.

        Args:
            user_id: User ID

        Returns:
            List of order data dictionaries
        """
        results = self.db.query("SELECT * FROM orders WHERE user_id = ?", (user_id,))
        orders = []
        for result in results:
            orders.append(
                {
                    "id": result[0],
                    "user_id": result[1],
                    "portfolio_id": result[2],
                    "symbol": result[3],
                    "side": result[4],
                    "type": result[5],
                    "status": result[6],
                    "quantity": result[7],
                    "price": result[8],
                    "filled_quantity": result[9],
                    "average_fill_price": result[10],
                    "broker_order_id": result[11],
                    "created_at": result[12],
                    "updated_at": result[13],
                }
            )
        return orders

    def insert_execution(self, execution: Dict[str, Any]) -> str:
        """
        Insert an execution into the database.

        Args:
            execution: Execution data dictionary

        Returns:
            Execution ID
        """
        self.db.insert_executions([execution])
        return execution["id"]

    def get_executions_by_order_id(self, order_id: str) -> List[Dict[str, Any]]:
        """
        Get executions by order ID.

        Args:
            order_id: Order ID

        Returns:
            List of execution data dictionaries
        """
        results = self.db.query(
            "SELECT * FROM executions WHERE order_id = ?", (order_id,)
        )
        executions = []
        for result in results:
            executions.append(
                {
                    "id": result[0],
                    "order_id": result[1],
                    "price": result[2],
                    "quantity": result[3],
                    "timestamp": result[4],
                    "broker_execution_id": result[5],
                }
            )
        return executions

    def insert_market_data(self, market_data: pd.DataFrame) -> bool:
        """
        Insert market data into the database.

        Args:
            market_data: DataFrame with market data

        Returns:
            Success flag
        """
        try:
            self.db.insert_market_data(market_data)
            return True
        except Exception:
            return False

    def get_market_data(
        self, symbol: str, timeframe: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Get market data from the database.

        Args:
            symbol: Stock symbol
            timeframe: Timeframe
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with market data
        """
        sql = "\n        SELECT * FROM market_data\n        WHERE symbol = ? AND timeframe = ? AND timestamp BETWEEN ? AND ?\n        ORDER BY timestamp\n        "
        return self.db.query_df(sql, (symbol, timeframe, start_date, end_date))

    def insert_model(self, model: Dict[str, Any]) -> str:
        """
        Insert a model into the database.

        Args:
            model: Model data dictionary

        Returns:
            Model ID
        """
        self.db.insert_models([model])
        return model["id"]

    def get_model_by_id(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a model by ID.

        Args:
            model_id: Model ID

        Returns:
            Model data dictionary
        """
        result = self.db.query("SELECT * FROM models WHERE id = ?", (model_id,))
        if not result:
            return None
        model = result[0]
        return {
            "id": model[0],
            "name": model[1],
            "description": model[2],
            "model_type": model[3],
            "version": model[4],
            "status": model[5],
            "created_at": model[6],
            "updated_at": model[7],
        }

    def insert_predictions(self, predictions: List[Dict[str, Any]]) -> bool:
        """
        Insert predictions into the database.

        Args:
            predictions: List of prediction data dictionaries

        Returns:
            Success flag
        """
        try:
            self.db.insert_predictions(predictions)
            return True
        except Exception:
            return False

    def get_predictions(self, model_id: str, symbol: str) -> List[Dict[str, Any]]:
        """
        Get predictions from the database.

        Args:
            model_id: Model ID
            symbol: Stock symbol

        Returns:
            List of prediction data dictionaries
        """
        results = self.db.query(
            "\n        SELECT * FROM predictions\n        WHERE model_id = ? AND symbol = ?\n        ORDER BY prediction_timestamp\n        ",
            (model_id, symbol),
        )
        predictions = []
        for result in results:
            predictions.append(
                {
                    "id": result[0],
                    "model_id": result[1],
                    "symbol": result[2],
                    "timestamp": result[3],
                    "prediction_timestamp": result[4],
                    "value": result[5],
                    "confidence": result[6],
                }
            )
        return predictions

    def insert_risk_metrics(self, risk_metrics: List[Dict[str, Any]]) -> bool:
        """
        Insert risk metrics into the database.

        Args:
            risk_metrics: List of risk metric data dictionaries

        Returns:
            Success flag
        """
        try:
            self.db.insert_risk_metrics(risk_metrics)
            return True
        except Exception:
            return False

    def get_risk_metrics_by_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get risk metrics by symbol.

        Args:
            symbol: Stock symbol

        Returns:
            List of risk metric data dictionaries
        """
        results = self.db.query(
            "\n        SELECT * FROM risk_metrics\n        WHERE symbol = ?\n        ORDER BY timestamp DESC\n        ",
            (symbol,),
        )
        risk_metrics = []
        for result in results:
            risk_metrics.append(
                {
                    "id": result[0],
                    "symbol": result[1],
                    "portfolio_id": result[2],
                    "timestamp": result[3],
                    "var": result[4],
                    "cvar": result[5],
                    "sharpe_ratio": result[6],
                    "sortino_ratio": result[7],
                    "max_drawdown": result[8],
                    "risk_score": result[9],
                    "risk_level": result[10],
                }
            )
        return risk_metrics

    def get_risk_metrics_by_portfolio_id(
        self, portfolio_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get risk metrics by portfolio ID.

        Args:
            portfolio_id: Portfolio ID

        Returns:
            List of risk metric data dictionaries
        """
        results = self.db.query(
            "\n        SELECT * FROM risk_metrics\n        WHERE portfolio_id = ?\n        ORDER BY timestamp DESC\n        ",
            (portfolio_id,),
        )
        risk_metrics = []
        for result in results:
            risk_metrics.append(
                {
                    "id": result[0],
                    "symbol": result[1],
                    "portfolio_id": result[2],
                    "timestamp": result[3],
                    "var": result[4],
                    "cvar": result[5],
                    "sharpe_ratio": result[6],
                    "sortino_ratio": result[7],
                    "max_drawdown": result[8],
                    "risk_score": result[9],
                    "risk_level": result[10],
                }
            )
        return risk_metrics


@pytest.fixture
def mock_db_manager(test_db: Any) -> Any:
    """Pytest fixture for mock database manager."""
    return MockDatabaseManager(test_db)
