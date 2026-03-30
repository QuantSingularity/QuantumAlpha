import os
import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

import redis
import structlog
from influxdb_client import InfluxDBClient
from pymongo import MongoClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool

logger = structlog.get_logger(__name__)


class DatabaseConfig:
    """Database configuration management"""

    def __init__(self) -> None:
        self.postgres_url = self._build_postgres_url()
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_password = os.getenv("REDIS_PASSWORD")
        self.influx_url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        self.influx_token = os.getenv("INFLUXDB_TOKEN")
        self.influx_org = os.getenv("INFLUXDB_ORG", "quantumalpha")
        self.influx_bucket = os.getenv("INFLUXDB_BUCKET", "market_data")
        self.mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.mongo_db = os.getenv("MONGODB_DATABASE", "quantumalpha")
        self.pool_size = int(os.getenv("DB_POOL_SIZE", 20))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", 30))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", 30))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", 3600))

    def _build_postgres_url(self) -> str:
        """Build PostgreSQL connection URL"""
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DB", "quantumalpha")
        username = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "password")
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"


class DatabaseManager:

    def __init__(self, config: DatabaseConfig) -> None:
        self.config = config
        self._engine = None
        self._session_factory = None
        self._scoped_session = None
        self._redis_client = None
        self._influx_client = None
        self._mongo_client = None
        self._connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "last_connection_time": None,
        }
        self._lock = threading.Lock()

    def initialize(self) -> None:
        """Initialize all database connections"""
        try:
            self._setup_postgresql()
            self._setup_redis()
            self._setup_influxdb()
            self._setup_mongodb()
            logger.info("Database connections initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise

    def _setup_postgresql(self) -> None:
        """Setup PostgreSQL connection with optimizations"""
        try:
            self._engine = create_engine(
                self.config.postgres_url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=True,
                echo=os.getenv("SQL_ECHO", "false").lower() == "true",
                connect_args={
                    "application_name": "QuantumAlpha",
                    "connect_timeout": 10,
                    "options": "-c timezone=UTC",
                },
            )
            self._session_factory = sessionmaker(bind=self._engine)
            self._scoped_session = scoped_session(self._session_factory)
            self._register_postgresql_events()
            with self._engine.connect() as conn:
                conn.execute("SELECT 1")
            logger.info("PostgreSQL connection established")
        except Exception as e:
            logger.error(f"Failed to setup PostgreSQL: {e}")
            raise

    def _register_postgresql_events(self) -> None:
        """Register SQLAlchemy event listeners for monitoring"""

        @event.listens_for(self._engine, "connect")
        def receive_connect(dbapi_connection: Any, connection_record: Any) -> None:
            with self._lock:
                self._connection_stats["total_connections"] += 1
                self._connection_stats["active_connections"] += 1
                self._connection_stats["last_connection_time"] = time.time()

        @event.listens_for(self._engine, "close")
        def receive_close(dbapi_connection: Any, connection_record: Any) -> None:
            with self._lock:
                self._connection_stats["active_connections"] -= 1

        @event.listens_for(self._engine, "handle_error")
        def receive_error(exception_context: Any) -> None:
            with self._lock:
                self._connection_stats["failed_connections"] += 1
            logger.error(f"Database error: {exception_context.original_exception}")

    def _setup_redis(self) -> None:
        """Setup Redis connection with retry logic"""
        try:
            self._redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                password=self.config.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            self._redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to setup Redis: {e}")

    def _setup_influxdb(self) -> None:
        """Setup InfluxDB connection for time-series data"""
        try:
            if self.config.influx_token:
                self._influx_client = InfluxDBClient(
                    url=self.config.influx_url,
                    token=self.config.influx_token,
                    org=self.config.influx_org,
                    timeout=10000,
                )
                health = self._influx_client.health()
                if health.status == "pass":
                    logger.info("InfluxDB connection established")
                else:
                    logger.warning("InfluxDB health check failed")
            else:
                logger.info("InfluxDB token not provided, skipping connection")
        except Exception as e:
            logger.error(f"Failed to setup InfluxDB: {e}")

    def _setup_mongodb(self) -> None:
        """Setup MongoDB connection for document storage"""
        try:
            self._mongo_client = MongoClient(
                self.config.mongo_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
            )
            self._mongo_client.admin.command("ping")
            logger.info("MongoDB connection established")
        except Exception as e:
            logger.error(f"Failed to setup MongoDB: {e}")

    @property
    def engine(self) -> Engine:
        """Get PostgreSQL engine"""
        if not self._engine:
            raise RuntimeError("Database not initialized")
        return self._engine

    @property
    def session_factory(self) -> sessionmaker:
        """Get session factory"""
        if not self._session_factory:
            raise RuntimeError("Database not initialized")
        return self._session_factory

    @property
    def redis(self) -> Optional[redis.Redis]:
        """Get Redis client"""
        return self._redis_client

    @property
    def influx(self) -> Optional[InfluxDBClient]:
        """Get InfluxDB client"""
        return self._influx_client

    @property
    def mongo(self) -> Optional[MongoClient]:
        """Get MongoDB client"""
        return self._mongo_client

    def get_session(self) -> Any:
        """Get a new database session"""
        if not self._scoped_session:
            raise RuntimeError("Database not initialized")
        return self._scoped_session()

    @contextmanager
    def session_scope(self) -> Generator[Any, None, None]:
        """Provide a transactional scope around a series of operations"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        with self._lock:
            stats = self._connection_stats.copy()
        if self._engine and hasattr(self._engine.pool, "size"):
            stats.update(
                {
                    "pool_size": self._engine.pool.size(),
                    "checked_in": self._engine.pool.checkedin(),
                    "checked_out": self._engine.pool.checkedout(),
                    "overflow": self._engine.pool.overflow(),
                    "invalid": self._engine.pool.invalid(),
                }
            )
        return stats

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all database connections"""
        health_status = {
            "postgresql": {"status": "unknown", "error": None},
            "redis": {"status": "unknown", "error": None},
            "influxdb": {"status": "unknown", "error": None},
            "mongodb": {"status": "unknown", "error": None},
        }
        try:
            with self._engine.connect() as conn:
                conn.execute("SELECT 1")
            health_status["postgresql"]["status"] = "healthy"
        except Exception as e:
            health_status["postgresql"]["status"] = "unhealthy"
            health_status["postgresql"]["error"] = str(e)
        if self._redis_client:
            try:
                self._redis_client.ping()
                health_status["redis"]["status"] = "healthy"
            except Exception as e:
                health_status["redis"]["status"] = "unhealthy"
                health_status["redis"]["error"] = str(e)
        else:
            health_status["redis"]["status"] = "not_configured"
        if self._influx_client:
            try:
                health = self._influx_client.health()
                health_status["influxdb"]["status"] = (
                    "healthy" if health.status == "pass" else "unhealthy"
                )
            except Exception as e:
                health_status["influxdb"]["status"] = "unhealthy"
                health_status["influxdb"]["error"] = str(e)
        else:
            health_status["influxdb"]["status"] = "not_configured"
        if self._mongo_client:
            try:
                self._mongo_client.admin.command("ping")
                health_status["mongodb"]["status"] = "healthy"
            except Exception as e:
                health_status["mongodb"]["status"] = "unhealthy"
                health_status["mongodb"]["error"] = str(e)
        else:
            health_status["mongodb"]["status"] = "not_configured"
        return health_status

    def close_all_connections(self) -> None:
        """Close all database connections"""
        try:
            if self._scoped_session:
                self._scoped_session.remove()
            if self._engine:
                self._engine.dispose()
            if self._redis_client:
                self._redis_client.close()
            if self._influx_client:
                self._influx_client.close()
            if self._mongo_client:
                self._mongo_client.close()
            logger.info("All database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")


class DatabaseMigrationManager:
    """Database migration management"""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def create_tables(self) -> Any:
        """Create all database tables"""
        try:
            from .models import create_tables, init_database

            create_tables(self.db_manager.engine)
            init_database(self.db_manager.engine)
            logger.info("Database tables created and initialized")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    def check_migration_status(self) -> Dict[str, Any]:
        """Check database migration status"""
        try:
            with self.db_manager.session_scope():
                inspector = self.db_manager.engine.dialect.get_table_names(
                    self.db_manager.engine.connect()
                )
                required_tables = [
                    "users",
                    "user_sessions",
                    "audit_logs",
                    "portfolios",
                    "positions",
                    "orders",
                    "order_executions",
                    "strategies",
                    "risk_limits",
                    "compliance_rules",
                    "market_data",
                ]
                missing_tables = [
                    table for table in required_tables if table not in inspector
                ]
                return {
                    "tables_exist": len(missing_tables) == 0,
                    "missing_tables": missing_tables,
                    "total_tables": len(inspector),
                }
        except Exception as e:
            logger.error(f"Failed to check migration status: {e}")
            return {"error": str(e)}


db_config = DatabaseConfig()
db_manager = DatabaseManager(db_config)
migration_manager = DatabaseMigrationManager(db_manager)


def get_db_session() -> Any:
    """Get a database session"""
    return db_manager.get_session()


def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client"""
    return db_manager.redis


def get_influx_client() -> Optional[InfluxDBClient]:
    """Get InfluxDB client"""
    return db_manager.influx


def get_mongo_client() -> Optional[MongoClient]:
    """Get MongoDB client"""
    return db_manager.mongo


@contextmanager
def db_session_scope() -> Generator[Any, None, None]:
    """Database session context manager"""
    with db_manager.session_scope() as session:
        yield session


def initialize_database() -> None:
    """Initialize all database connections"""
    try:
        db_manager.initialize()
        migration_status = migration_manager.check_migration_status()
        if not migration_status.get("tables_exist", False):
            logger.info("Creating database tables...")
            migration_manager.create_tables()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def cleanup_database() -> None:
    """Cleanup database connections"""
    db_manager.close_all_connections()


__all__ = [
    "DatabaseConfig",
    "DatabaseManager",
    "DatabaseMigrationManager",
    "db_manager",
    "migration_manager",
    "get_db_session",
    "get_redis_client",
    "get_influx_client",
    "get_mongo_client",
    "db_session_scope",
    "initialize_database",
    "cleanup_database",
]
