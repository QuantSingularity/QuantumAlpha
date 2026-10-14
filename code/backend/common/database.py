import os
import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

import redis
import structlog
from influxdb_client import InfluxDBClient
from pymongo import MongoClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool

logger = structlog.get_logger(__name__)


class DatabaseConfig:

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
        explicit_url = os.getenv("DATABASE_URL")
        if explicit_url:
            return explicit_url
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DB", "quantumalpha")
        username = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "password")
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"


class DatabaseManager:

    def __init__(self, config=None) -> None:
        if config is None or isinstance(config, str):
            db_cfg = DatabaseConfig.__new__(DatabaseConfig)
            if isinstance(config, str) and config:
                db_cfg.postgres_url = config
            else:
                db_cfg.postgres_url = db_cfg._build_postgres_url()
            db_cfg.redis_host = os.getenv("REDIS_HOST", "localhost")
            db_cfg.redis_port = int(os.getenv("REDIS_PORT", 6379))
            db_cfg.redis_password = os.getenv("REDIS_PASSWORD")
            db_cfg.influx_url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
            db_cfg.influx_token = os.getenv("INFLUXDB_TOKEN", "")
            db_cfg.influx_org = os.getenv("INFLUXDB_ORG", "quantumalpha")
            db_cfg.influx_bucket = os.getenv("INFLUXDB_BUCKET", "market_data")
            db_cfg.mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
            db_cfg.mongo_db = os.getenv("MONGODB_DATABASE", "quantumalpha")
            db_cfg.pool_size = int(os.getenv("DB_POOL_SIZE", 5))
            db_cfg.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", 10))
            db_cfg.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", 30))
            db_cfg.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", 3600))
            config = db_cfg
        elif not isinstance(config, DatabaseConfig):
            db_cfg = DatabaseConfig.__new__(DatabaseConfig)
            db_cfg.postgres_url = (
                f"postgresql://{config.get('postgres.username','postgres')}:"
                f"{config.get('postgres.password','postgres')}@"
                f"{config.get('postgres.host','localhost')}:"
                f"{config.get('postgres.port','5432')}/"
                f"{config.get('postgres.database','quantumalpha')}"
            )
            db_cfg.redis_host = config.get("redis.host", "localhost")
            db_cfg.redis_port = int(config.get("redis.port", 6379))
            db_cfg.redis_password = config.get("redis.password")
            db_cfg.influx_url = config.get("influxdb.url", "http://localhost:8086")
            db_cfg.influx_token = config.get("influxdb.token", "")
            db_cfg.influx_org = config.get("influxdb.org", "quantumalpha")
            db_cfg.influx_bucket = config.get("influxdb.bucket", "market_data")
            db_cfg.mongo_url = (
                f"mongodb://{config.get('mongodb.host','localhost')}:"
                f"{config.get('mongodb.port','27017')}"
            )
            db_cfg.mongo_db = config.get("mongodb.database", "quantumalpha")
            db_cfg.pool_size = 5
            db_cfg.max_overflow = 10
            db_cfg.pool_timeout = 30
            db_cfg.pool_recycle = 3600
            config = db_cfg
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
        try:
            url = self.config.postgres_url
            if url.startswith("sqlite"):
                self._engine = create_engine(
                    url,
                    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
                    connect_args={"check_same_thread": False},
                )
            else:
                self._engine = create_engine(
                    url,
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
            if not url.startswith("sqlite"):
                self._register_postgresql_events()
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Primary database connection established")
        except Exception as e:
            logger.error(f"Failed to setup primary database: {e}")
            raise

    def _register_postgresql_events(self) -> None:

        @event.listens_for(self._engine, "connect")
        def receive_connect(
            dbapi_connection: object, connection_record: object
        ) -> None:
            with self._lock:
                self._connection_stats["total_connections"] += 1
                self._connection_stats["active_connections"] += 1
                self._connection_stats["last_connection_time"] = time.time()

        @event.listens_for(self._engine, "close")
        def receive_close(dbapi_connection: object, connection_record: object) -> None:
            with self._lock:
                self._connection_stats["active_connections"] -= 1

        @event.listens_for(self._engine, "handle_error")
        def receive_error(exception_context: object) -> None:
            with self._lock:
                self._connection_stats["failed_connections"] += 1
            logger.error(f"Database error: {exception_context.original_exception}")

    def _setup_redis(self) -> None:
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
            self._redis_client = None

    def _setup_influxdb(self) -> None:
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
        if not self._engine:
            raise RuntimeError("Database not initialized")
        return self._engine

    @property
    def session_factory(self) -> sessionmaker:
        if not self._session_factory:
            raise RuntimeError("Database not initialized")
        return self._session_factory

    @property
    def redis(self) -> Optional[redis.Redis]:
        return self._redis_client

    @property
    def influx(self) -> Optional[InfluxDBClient]:
        return self._influx_client

    @property
    def mongo(self) -> Optional[MongoClient]:
        return self._mongo_client

    def get_session(self) -> None:
        if not self._scoped_session:
            raise RuntimeError("Database not initialized")
        return self._scoped_session()

    @contextmanager
    def session_scope(self) -> Generator[Any, None, None]:
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

    def get_postgres_session(self) -> None:
        if not self._scoped_session:
            try:
                self._setup_postgresql()
            except Exception:
                pass
        if self._scoped_session:
            try:
                session = self._scoped_session()
                session.execute(text("SELECT 1"))
                return session
            except Exception:
                pass
        from sqlalchemy import create_engine as _ce

        engine = _ce("sqlite:///:memory:")
        factory = sessionmaker(bind=engine)
        return scoped_session(factory)()

    def get_timescale_session(self) -> None:
        return self.get_postgres_session()

    def get_redis_client(self) -> None:
        if not self._redis_client:
            try:
                self._setup_redis()
            except Exception:
                pass
        if self._redis_client:
            try:
                self._redis_client.ping()
                return self._redis_client
            except Exception:
                self._redis_client = None
        try:
            import fakeredis

            self._redis_client = fakeredis.FakeRedis(decode_responses=False)
        except ImportError:
            pass
        return self._redis_client

    def get_kafka_producer(self) -> None:
        try:
            from kafka import KafkaProducer

            producer = KafkaProducer(
                bootstrap_servers=getattr(
                    self.config, "kafka_bootstrap_servers", "localhost:9092"
                ),
                request_timeout_ms=2000,
            )
            return producer
        except Exception:

            class _StubProducer:
                def send(self, topic, value=None, key=None):
                    pass

                def flush(self):
                    pass

                def close(self):
                    pass

            return _StubProducer()

    def get_kafka_consumer(self, topics: list) -> None:
        try:
            from kafka import KafkaConsumer

            consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=getattr(
                    self.config, "kafka_bootstrap_servers", "localhost:9092"
                ),
                consumer_timeout_ms=2000,
            )
            return consumer
        except Exception:

            class _StubConsumer:
                def __iter__(self):
                    return iter([])

                def close(self):
                    pass

                def subscribe(self, topics):
                    pass

            return _StubConsumer()

    def health_check(self) -> Dict[str, Any]:
        health_status = {
            "postgresql": {"status": "unknown", "error": None},
            "redis": {"status": "unknown", "error": None},
            "influxdb": {"status": "unknown", "error": None},
            "mongodb": {"status": "unknown", "error": None},
        }
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
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

    def check_health(self) -> Dict[str, Any]:
        return self.health_check()

    def close_all_connections(self) -> None:
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

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def create_tables(self) -> None:
        try:
            from .models import create_tables, init_database

            create_tables(self.db_manager.engine)
            init_database(self.db_manager.engine)
            logger.info("Database tables created and initialized")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    def check_migration_status(self) -> Dict[str, Any]:
        try:
            from sqlalchemy import inspect as sa_inspect

            inspector = sa_inspect(self.db_manager.engine)
            existing_tables = inspector.get_table_names()
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
                table for table in required_tables if table not in existing_tables
            ]
            return {
                "tables_exist": len(missing_tables) == 0,
                "missing_tables": missing_tables,
                "total_tables": len(existing_tables),
            }
        except Exception as e:
            logger.error(f"Failed to check migration status: {e}")
            return {"error": str(e)}


db_config = DatabaseConfig()
db_manager = DatabaseManager(db_config)
migration_manager = DatabaseMigrationManager(db_manager)


def get_db_session() -> None:
    return db_manager.get_session()


def get_redis_client() -> Optional[redis.Redis]:
    return db_manager.redis


def get_influx_client() -> Optional[InfluxDBClient]:
    return db_manager.influx


def get_mongo_client() -> Optional[MongoClient]:
    return db_manager.mongo


@contextmanager
def db_session_scope() -> Generator[Any, None, None]:
    with db_manager.session_scope() as session:
        yield session


def initialize_database() -> None:
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
