# CLI Reference

## Overview

QuantumAlpha provides command-line tools for deployment, testing, monitoring, and maintenance operations.

---

## Table of Contents

- [Setup Scripts](#setup-scripts)
- [Service Management](#service-management)
- [Testing Commands](#testing-commands)
- [Deployment Commands](#deployment-commands)
- [Database Operations](#database-operations)
- [Monitoring Scripts](#monitoring-scripts)

---

## Setup Scripts

### setup.sh

Install the backend (Python) and frontend (Node.js) dependencies in one step.

| Command    | Arguments | Description                                                    | Example              |
| ---------- | --------- | -------------------------------------------------------------- | -------------------- |
| `setup.sh` | None      | Install backend, web-frontend and mobile-frontend dependencies | `./scripts/setup.sh` |

```bash
./scripts/setup.sh

# What it does:
# - Installs Python dependencies with pip3 (or pip)
# - Installs web-frontend dependencies with pnpm (or npm)
# - Installs mobile-frontend dependencies with pnpm (or npm)
# - Skips any component whose directory or package manager is missing
```

---

### setup_env.sh

Initialize the development environment.

| Command        | Arguments         | Description                          | Example                            |
| -------------- | ----------------- | ------------------------------------ | ---------------------------------- |
| `setup_env.sh` | `-e, --env <ENV>` | Setup environment (dev/staging/prod) | `./scripts/setup_env.sh --env dev` |
|                | `-h, --help`      | Show help message                    | `./scripts/setup_env.sh --help`    |

**Full Example:**

```bash
# Setup development environment
./scripts/setup_env.sh --env dev

# What it does:
# - Checks Python 3.10+, Docker, Docker Compose
# - Creates Python virtual environment
# - Installs backend dependencies
# - Installs frontend dependencies (if Node.js available)
# - Creates .env file from template
# - Validates configuration
```

**Environment Options:**

- `dev` - Development environment with debug logging
- `staging` - Staging environment with test data
- `prod` - Production environment with strict security

---

## Service Management

### start.sh

Start all services in production mode.

| Command    | Arguments | Description                            | Example              |
| ---------- | --------- | -------------------------------------- | -------------------- |
| `start.sh` | None      | Start all services with Docker Compose | `./scripts/start.sh` |

```bash
./scripts/start.sh

# Starts:
# - PostgreSQL (TimescaleDB)
# - Redis
# - Kafka + Zookeeper
# - InfluxDB
# - MongoDB
# - All microservices
# - Web dashboard
```

### start_dev.sh

Start services in development mode with hot-reload.

| Command        | Arguments             | Description               | Example                                                  |
| -------------- | --------------------- | ------------------------- | -------------------------------------------------------- |
| `start_dev.sh` | None                  | Start development servers | `./scripts/start_dev.sh`                                 |
|                | `--service <SERVICE>` | Start specific service    | `./scripts/start_dev.sh --service ai_engine`             |
|                | `--port <PORT>`       | Override default port     | `./scripts/start_dev.sh --service ai_engine --port 9000` |

```bash
# Start all services in dev mode
./scripts/start_dev.sh

# Start specific service
./scripts/start_dev.sh --service ai_engine --port 8082

# What it does:
# - Starts services with debug mode enabled
# - Enables hot-reload for code changes
# - Verbose logging to console
# - Mock data for testing
```

### start_service.sh

Start individual services with custom configuration.

| Command            | Arguments          | Description             | Example                                             |
| ------------------ | ------------------ | ----------------------- | --------------------------------------------------- |
| `start_service.sh` | `--service <NAME>` | Service name (required) | `./scripts/start_service.sh --service data_service` |
|                    | `--port <PORT>`    | Port number             | `--port 8081`                                       |
|                    | `--env <ENV>`      | Environment             | `--env prod`                                        |
|                    | `--workers <N>`    | Number of workers       | `--workers 4`                                       |

```bash
# Start data service on custom port
./scripts/start_service.sh \
  --service data_service \
  --port 8081 \
  --env prod \
  --workers 4
```

### stop.sh / stop_services.sh

Stop running services.

| Command            | Arguments          | Description           | Example                                          |
| ------------------ | ------------------ | --------------------- | ------------------------------------------------ |
| `stop.sh`          | None               | Stop all services     | `./scripts/stop.sh`                              |
| `stop_services.sh` | `--service <NAME>` | Stop specific service | `./scripts/stop_services.sh --service ai_engine` |
|                    | `--all`            | Stop all services     | `./scripts/stop_services.sh --all`               |

```bash
# Stop all services
./scripts/stop.sh

# Stop specific service
./scripts/stop_services.sh --service data_service
```

---

## Testing Commands

### run_tests.sh

Execute test suites.

| Command        | Arguments       | Description              | Example                                |
| -------------- | --------------- | ------------------------ | -------------------------------------- |
| `run_tests.sh` | None            | Run all tests            | `./scripts/run_tests.sh`               |
|                | `--unit`        | Run unit tests only      | `./scripts/run_tests.sh --unit`        |
|                | `--integration` | Run integration tests    | `./scripts/run_tests.sh --integration` |
|                | `--system`      | Run system tests         | `./scripts/run_tests.sh --system`      |
|                | `--coverage`    | Generate coverage report | `./scripts/run_tests.sh --coverage`    |
|                | `--verbose`     | Verbose output           | `./scripts/run_tests.sh --verbose`     |

```bash
# Run all tests
./scripts/run_tests.sh

# Run specific test suite with coverage
./scripts/run_tests.sh --unit --coverage

# Run tests with verbose output
./scripts/run_tests.sh --integration --verbose
```

**Test Output:**

```text
Running unit tests...
============================= test session starts ==============================
collected 145 items

tests/unit/ai_engine/test_model_manager.py ........ [ 5%]
tests/unit/risk_service/test_risk_calculator.py ..... [ 8%]
...

========================= 145 passed in 45.23s ==========================
Coverage: 78%
```

### lint.sh

Run code quality checks.

| Command   | Arguments    | Description           | Example                        |
| --------- | ------------ | --------------------- | ------------------------------ |
| `lint.sh` | None         | Run all linters       | `./scripts/lint.sh`            |
|           | `--fix`      | Auto-fix issues       | `./scripts/lint.sh --fix`      |
|           | `--backend`  | Lint Python code only | `./scripts/lint.sh --backend`  |
|           | `--frontend` | Lint JS/TS code only  | `./scripts/lint.sh --frontend` |

```bash
# Run all linters
./scripts/lint.sh

# Auto-fix Python code
./scripts/lint.sh --backend --fix

# Lint tools used:
# - flake8 (Python)
# - black (Python formatter)
# - mypy (Python type checking)
# - ESLint (JavaScript/TypeScript)
# - Prettier (JS/TS formatter)
```

---

## Deployment Commands

### deploy.sh

Deploy to remote environments.

| Command     | Arguments         | Description                       | Example                             |
| ----------- | ----------------- | --------------------------------- | ----------------------------------- |
| `deploy.sh` | `--env <ENV>`     | Target environment (staging/prod) | `./scripts/deploy.sh --env staging` |
|             | `--version <TAG>` | Version tag to deploy             | `--version v1.2.0`                  |
|             | `--skip-tests`    | Skip pre-deployment tests         | `--skip-tests`                      |
|             | `--rollback`      | Rollback to previous version      | `--rollback`                        |

```bash
# Deploy to staging
./scripts/deploy.sh --env staging

# Deploy specific version to production
./scripts/deploy.sh --env prod --version v1.2.0

# Rollback production deployment
./scripts/deploy.sh --env prod --rollback
```

**Deployment Steps:**

1. Validate environment configuration
2. Run tests (unless `--skip-tests`)
3. Build Docker images
4. Push images to registry
5. Update infrastructure (Terraform)
6. Deploy new containers
7. Run smoke tests
8. Update monitoring alerts

### k8s_deploy.sh

Deploy to Kubernetes clusters.

| Command         | Arguments          | Description               | Example                                          |
| --------------- | ------------------ | ------------------------- | ------------------------------------------------ |
| `k8s_deploy.sh` | `--cluster <NAME>` | Kubernetes cluster name   | `./scripts/k8s_deploy.sh --cluster prod-cluster` |
|                 | `--namespace <NS>` | Kubernetes namespace      | `--namespace quantumalpha`                       |
|                 | `--context <CTX>`  | kubectl context           | `--context gke_project_us-central1_cluster`      |
|                 | `--dry-run`        | Validate without applying | `--dry-run`                                      |

```bash
# Deploy to production cluster
./scripts/k8s_deploy.sh \
  --cluster prod-cluster \
  --namespace quantumalpha \
  --context gke_quantumalpha_us-central1_prod

# Dry run deployment
./scripts/k8s_deploy.sh --cluster staging-cluster --dry-run
```

---

## Database Operations

### setup_db.py

Initialize database schema.

| Command              | Arguments     | Description          | Example                                |
| -------------------- | ------------- | -------------------- | -------------------------------------- |
| `python setup_db.py` | `--env <ENV>` | Environment          | `python scripts/setup_db.py --env dev` |
|                      | `--drop`      | Drop existing tables | `--drop`                               |
|                      | `--seed`      | Load seed data       | `--seed`                               |

```bash
# Initialize database
python scripts/setup_db.py --env dev

# Reset database with seed data
python scripts/setup_db.py --env dev --drop --seed
```

### backup.sh

Backup databases.

| Command     | Arguments         | Description              | Example               |
| ----------- | ----------------- | ------------------------ | --------------------- |
| `backup.sh` | None              | Backup all databases     | `./scripts/backup.sh` |
|             | `--db <NAME>`     | Backup specific database | `--db postgres`       |
|             | `--output <PATH>` | Output directory         | `--output /backups`   |
|             | `--compress`      | Compress backup          | `--compress`          |

```bash
# Backup all databases
./scripts/backup.sh

# Backup PostgreSQL with compression
./scripts/backup.sh --db postgres --compress --output /backups

# Creates:
# /backups/postgres_20231215_103000.sql.gz
# /backups/redis_20231215_103000.rdb
# /backups/influxdb_20231215_103000.tar.gz
```

### restore.sh

Restore database backups.

| Command      | Arguments         | Description            | Example                                       |
| ------------ | ----------------- | ---------------------- | --------------------------------------------- |
| `restore.sh` | `--backup <FILE>` | Backup file to restore | `./scripts/restore.sh --backup backup.sql.gz` |
|              | `--db <NAME>`     | Database name          | `--db postgres`                               |
|              | `--force`         | Skip confirmation      | `--force`                                     |

```bash
# Restore PostgreSQL backup
./scripts/restore.sh \
  --backup /backups/postgres_20231215_103000.sql.gz \
  --db postgres

# Force restore without confirmation
./scripts/restore.sh --backup backup.sql.gz --force
```

---

## Monitoring Scripts

### monitor_setup.sh

Setup monitoring infrastructure.

| Command            | Arguments           | Description                | Example                      |
| ------------------ | ------------------- | -------------------------- | ---------------------------- |
| `monitor_setup.sh` | None                | Setup Prometheus + Grafana | `./scripts/monitor_setup.sh` |
|                    | `--prometheus-only` | Setup Prometheus only      | `--prometheus-only`          |
|                    | `--grafana-only`    | Setup Grafana only         | `--grafana-only`             |
|                    | `--port <PORT>`     | Custom Prometheus port     | `--port 9090`                |

```bash
# Setup complete monitoring stack
./scripts/monitor_setup.sh

# Setup Prometheus only on custom port
./scripts/monitor_setup.sh --prometheus-only --port 9091
```

**What it does:**

1. Installs Prometheus
2. Configures service discovery
3. Sets up alerting rules
4. Installs Grafana
5. Imports pre-built dashboards
6. Configures data sources
7. Sets up alert notifications

---

## Docker Compose Commands

For direct Docker Compose usage:

```bash
# Start services
docker-compose up -d

# Start specific services
docker-compose up -d postgres redis kafka

# View logs
docker-compose logs -f
docker-compose logs -f ai_engine

# Restart service
docker-compose restart data_service

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild images
docker-compose build --no-cache

# Scale services
docker-compose up -d --scale ai_engine=3

# Check status
docker-compose ps

# Execute command in container
docker-compose exec ai_engine python manage.py shell
```

---

## Python Service Commands

For running services directly with Python:

```bash
# Activate virtual environment
source venv/bin/activate

# Start AI Engine
cd backend
python ai_engine/app.py

# Start with gunicorn (production)
gunicorn -w 4 -b 0.0.0.0:8082 ai_engine.app:app

# Start with custom config
FLASK_ENV=production python ai_engine/app.py

# Run with debugger
FLASK_DEBUG=1 python ai_engine/app.py
```

---

## Environment Variables

Common environment variables for CLI scripts:

```bash
# Override default ports
export DATA_SERVICE_PORT=8081
export AI_ENGINE_PORT=8082
export RISK_SERVICE_PORT=8083
export EXECUTION_SERVICE_PORT=8084

# Set environment
export FLASK_ENV=development
export LOG_LEVEL=DEBUG

# Database
export DB_HOST=localhost
export DB_PORT=5432

# Use in scripts
./scripts/start_dev.sh
```

---

## Troubleshooting CLI Issues

### Port Already in Use

```bash
# Find process using port
lsof -i :8080
sudo netstat -tulpn | grep 8080

# Kill process
kill -9 "$PID"  # PID from the output above

# Or start on different port
./scripts/start_service.sh --service ai_engine --port 9000
```

### Permission Denied

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run with sudo if needed
sudo ./scripts/setup_env.sh
```

### Docker Daemon Not Running

```bash
# Start Docker
sudo systemctl start docker   # Linux
open -a Docker               # macOS

# Check Docker status
docker info
```

---

## Quick Reference

| Task               | Command                             |
| ------------------ | ----------------------------------- |
| Setup environment  | `./scripts/setup_env.sh`            |
| Start all services | `./scripts/start.sh`                |
| Start dev mode     | `./scripts/start_dev.sh`            |
| Run tests          | `./scripts/run_tests.sh`            |
| Check code quality | `./scripts/lint.sh --fix`           |
| Backup database    | `./scripts/backup.sh`               |
| Deploy to staging  | `./scripts/deploy.sh --env staging` |
| View logs          | `docker-compose logs -f`            |
| Stop services      | `./scripts/stop.sh`                 |

---

**See Also:**

- [USAGE.md](./USAGE.md) - Python library usage
- [API.md](./API.md) - API endpoints
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues
