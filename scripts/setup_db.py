"""
QuantumAlpha Database Setup Script

This script initializes the database schema and seeds initial data for the QuantumAlpha platform.
It supports different environments (dev, staging, prod) and handles both PostgreSQL and InfluxDB.
"""

import argparse
import logging
import os
import sys

import influxdb_client
import psycopg2
import yaml
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
sys.path.insert(0, project_root)
RED = "\x1b[0;31m"
GREEN = "\x1b[0;32m"
YELLOW = "\x1b[0;33m"
BLUE = "\x1b[0;34m"
NC = "\x1b[0m"


def print_colored(message: Any, color: Any = NC) -> Any:
    """Print colored message to console."""
    logger.info(f"{color}{message}{NC}")


def load_config(env: Any) -> Any:
    """Load configuration for the specified environment."""
    env_file = os.path.join(project_root, "config", f".env.{env}")
    if not os.path.exists(env_file):
        print_colored(f"Error: Environment file not found: {env_file}", RED)
        sys.exit(1)
    load_dotenv(env_file)
    postgres_config_file = os.path.join(
        project_root, "config", "database", "postgres.yaml"
    )
    influxdb_config_file = os.path.join(
        project_root, "config", "database", "influxdb.yaml"
    )
    if not os.path.exists(postgres_config_file):
        print_colored(
            f"Error: PostgreSQL config file not found: {postgres_config_file}", RED
        )
        sys.exit(1)
    if not os.path.exists(influxdb_config_file):
        print_colored(
            f"Error: InfluxDB config file not found: {influxdb_config_file}", RED
        )
        sys.exit(1)
    with open(postgres_config_file, "r") as f:
        postgres_config = yaml.safe_load(f)
    with open(influxdb_config_file, "r") as f:
        influxdb_config = yaml.safe_load(f)
    postgres_config["connection"]["host"] = os.getenv(
        "DB_HOST", postgres_config["connection"].get("host", "localhost")
    )
    postgres_config["connection"]["port"] = int(
        os.getenv("DB_PORT", postgres_config["connection"].get("port", 5432))
    )
    postgres_config["connection"]["username"] = os.getenv(
        "DB_USERNAME", postgres_config["connection"].get("username", "postgres")
    )
    postgres_config["connection"]["password"] = os.getenv(
        "DB_PASSWORD", postgres_config["connection"].get("password", "postgres")
    )
    postgres_config["connection"]["database"] = os.getenv(
        "DB_NAME", postgres_config["connection"].get("database", "quantumalpha")
    )
    influxdb_config["connection"]["url"] = os.getenv(
        "INFLUXDB_URL",
        influxdb_config["connection"].get("url", "http://localhost:8086"),
    )
    influxdb_config["connection"]["org"] = os.getenv(
        "INFLUXDB_ORG", influxdb_config["connection"].get("org", "quantumalpha")
    )
    influxdb_config["connection"]["token"] = os.getenv(
        "INFLUXDB_TOKEN", influxdb_config["connection"].get("token", "")
    )
    return {"postgres": postgres_config, "influxdb": influxdb_config}


def setup_postgres(config: Any, args: Any) -> Any:
    """Set up PostgreSQL database."""
    print_colored("\nSetting up PostgreSQL database...", BLUE)
    conn_params = config["postgres"]["connection"]
    try:
        conn = psycopg2.connect(
            host=conn_params["host"],
            port=conn_params["port"],
            user=conn_params["username"],
            password=conn_params["password"],
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT 1 FROM pg_database WHERE datname = '{conn_params['database']}'"
        )
        exists = cursor.fetchone()
        if not exists:
            print_colored(f"Creating database: {conn_params['database']}", YELLOW)
            cursor.execute(f"CREATE DATABASE {conn_params['database']}")
            print_colored(f"Database created: {conn_params['database']}", GREEN)
        else:
            print_colored(f"Database already exists: {conn_params['database']}", GREEN)
        cursor.close()
        conn.close()
    except Exception as e:
        print_colored(f"Error connecting to PostgreSQL server: {e}", RED)
        return False
    try:
        conn = psycopg2.connect(
            host=conn_params["host"],
            port=conn_params["port"],
            user=conn_params["username"],
            password=conn_params["password"],
            database=conn_params["database"],
        )
        cursor = conn.cursor()
        schema_dir = os.path.join(project_root, "backend", "scripts", "init-db")
        if not os.path.exists(schema_dir):
            print_colored(f"Error: Schema directory not found: {schema_dir}", RED)
            return False
        schema_files = sorted([f for f in os.listdir(schema_dir) if f.endswith(".sql")])
        if not schema_files:
            print_colored("No schema files found", RED)
            return False
        for schema_file in schema_files:
            print_colored(f"Executing schema file: {schema_file}", YELLOW)
            with open(os.path.join(schema_dir, schema_file), "r") as f:
                sql = f.read()
                cursor.execute(sql)
            print_colored(f"Schema file executed: {schema_file}", GREEN)
        conn.commit()
        cursor.close()
        conn.close()
        print_colored("PostgreSQL database setup completed successfully", GREEN)
        return True
    except Exception as e:
        print_colored(f"Error setting up PostgreSQL database: {e}", RED)
        return False


def setup_influxdb(config: Any, args: Any) -> Any:
    """Set up InfluxDB database."""
    print_colored("\nSetting up InfluxDB...", BLUE)
    conn_params = config["influxdb"]["connection"]
    try:
        client = influxdb_client.InfluxDBClient(
            url=conn_params["url"], token=conn_params["token"], org=conn_params["org"]
        )
        health = client.health()
        if health.status != "pass":
            print_colored(f"Error: InfluxDB health check failed: {health.message}", RED)
            return False
        print_colored("Connected to InfluxDB", GREEN)
        buckets_api = client.buckets_api()
        for bucket_config in config["influxdb"]["buckets"]:
            bucket_name = bucket_config["name"]
            retention = bucket_config["retention_period"]
            retention_seconds = 0
            if retention.endswith("d"):
                retention_seconds = int(retention[:-1]) * 86400
            elif retention.endswith("h"):
                retention_seconds = int(retention[:-1]) * 3600
            elif retention.endswith("m"):
                retention_seconds = int(retention[:-1]) * 60
            elif retention.endswith("s"):
                retention_seconds = int(retention[:-1])
            buckets = buckets_api.find_buckets().buckets
            bucket_exists = any((bucket.name == bucket_name for bucket in buckets))
            if not bucket_exists:
                print_colored(f"Creating bucket: {bucket_name}", YELLOW)
                buckets_api.create_bucket(
                    bucket_name=bucket_name,
                    org=conn_params["org"],
                    retention_rules=[
                        influxdb_client.BucketRetentionRules(
                            type="expire", every_seconds=retention_seconds
                        )
                    ],
                )
                print_colored(f"Bucket created: {bucket_name}", GREEN)
            else:
                print_colored(f"Bucket already exists: {bucket_name}", GREEN)
        print_colored("InfluxDB setup completed successfully", GREEN)
        return True
    except Exception as e:
        print_colored(f"Error setting up InfluxDB: {e}", RED)
        return False


def main() -> Any:
    """Main function."""
    parser = argparse.ArgumentParser(description="QuantumAlpha Database Setup Script")
    parser.add_argument(
        "--env",
        choices=["dev", "staging", "prod"],
        default="dev",
        help="Environment (dev, staging, prod). Default: dev",
    )
    parser.add_argument(
        "--postgres-only", action="store_true", help="Set up PostgreSQL only"
    )
    parser.add_argument(
        "--influxdb-only", action="store_true", help="Set up InfluxDB only"
    )
    parser.add_argument(
        "--no-seed", action="store_true", help="Skip seeding initial data"
    )
    args = parser.parse_args()
    print_colored(f"QuantumAlpha Database Setup - Environment: {args.env}", BLUE)
    config = load_config(args.env)
    success = True
    if not args.influxdb_only:
        postgres_success = setup_postgres(config, args)
        success = success and postgres_success
    if not args.postgres_only:
        influxdb_success = setup_influxdb(config, args)
        success = success and influxdb_success
    if success:
        print_colored("\nDatabase setup completed successfully!", GREEN)
        return 0
    else:
        print_colored("\nDatabase setup failed!", RED)
        return 1


if __name__ == "__main__":
    sys.exit(main())
