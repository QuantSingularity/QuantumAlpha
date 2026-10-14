# QuantumAlpha

This is the source tree for the QuantumAlpha platform.

## Directory Structure

```
code/
├── backend/                        # Core backend services (Flask API + business logic)
│   ├── api/                        # API gateway entry points
│   │   ├── app.py                  # Lightweight Flask app (mock/deployment version)
│   │   ├── main.py                 # Full QuantumAlphaApp with JWT, blueprints, routes
│   │   ├── config.py               # Flask Config class
│   │   └── wsgi.py                 # Gunicorn WSGI entry point
│   ├── common/                     # Shared utilities used by all backend services
│   │   ├── audit.py                # Audit logging
│   │   ├── auth.py                 # JWT auth, decorators
│   │   ├── config.py               # ConfigManager (env + YAML)
│   │   ├── database.py             # DB session management (Postgres, Redis, InfluxDB)
│   │   ├── logging_config.py       # Logging setup
│   │   ├── logging_utils.py        # ServiceError, ValidationError, setup_logger
│   │   ├── messaging.py            # Async messaging utilities
│   │   ├── models.py               # SQLAlchemy ORM models
│   │   ├── monitoring.py           # Prometheus/health monitoring blueprints
│   │   ├── utils.py                # RateLimiter, SimpleCache, parse_period
│   │   └── validation.py           # Marshmallow schemas, FinancialValidator
│   ├── analytics_service/          # Portfolio analytics
│   │   ├── factor_analysis.py      # PCA, factor decomposition
│   │   └── performance_attribution.py  # Brinson-Hood-Beebower attribution
│   ├── compliance_service/         # Regulatory compliance
│   │   ├── compliance_monitoring.py    # Real-time violation detection
│   │   └── regulatory_reporting.py     # Report generation
│   ├── data_service/               # Market & alternative data ingestion
│   │   ├── app.py                  # Flask app for data_service microservice
│   │   ├── alternative_data.py     # Alternative data sources
│   │   ├── data_processor.py       # Data cleaning & normalisation
│   │   ├── feature_engineering.py  # Feature computation pipeline
│   │   └── market_data.py          # Market data fetching & storage
│   ├── execution_service/          # Order execution microservice
│   │   ├── app.py                  # Flask app for execution_service
│   │   ├── broker_integration.py   # Broker API adapters
│   │   ├── execution_strategy.py   # TWAP, VWAP, etc.
│   │   ├── order_manager.py        # Order CRUD & lifecycle
│   │   └── trading_service.py      # Trading coordination
│   ├── portfolio_service/          # Portfolio management service
│   │   └── portfolio_service.py    # Portfolio metrics & position tracking
│   ├── risk_service/               # Risk management microservice
│   │   ├── app.py                  # Flask app for risk_service
│   │   ├── online_learning.py      # Adaptive risk models
│   │   ├── position_sizing.py      # Kelly, fixed-fraction sizing
│   │   ├── real_time_updater.py    # Live risk feed consumer
│   │   ├── risk_calculator.py      # VaR, CVaR, Greeks
│   │   └── stress_testing.py       # Scenario & stress tests
│   ├── trading_engine/             # Trade execution engine service
│   │   └── trading_engine.py       # Order lifecycle & execution logic
│   ├── config/                     # Service & database configuration
│   │   ├── logging.yaml
│   │   ├── database/
│   │   │   ├── influxdb.yaml
│   │   │   └── postgres.yaml
│   │   └── services/
│   │       ├── ai_engine.yaml
│   │       ├── data_service.yaml
│   │       ├── execution_service.yaml
│   │       └── risk_service.yaml
│   ├── scripts/
│   │   └── init-db/
│   │       ├── 01-init-schema.sql  # Schema initialisation
│   │       └── 02-sample-data.sql  # Seed data
│   ├── tests/                      # Backend unit & integration tests
│   │   ├── conftest.py
│   │   ├── test_analytics_service.py
│   │   ├── test_compliance_service.py
│   │   ├── test_data_service.py
│   │   ├── test_execution_service.py
│   │   ├── test_integration.py
│   │   └── test_risk_service.py
│   ├── Dockerfile                  # Production image build
│   ├── docker-compose.yml          # Full local stack (Postgres, Redis, app)
│   ├── pytest.ini                  # Test discovery for backend/tests/
│   └── requirements.txt            # Python dependencies
│
├── ai_models/                      # AI engine service (see ai_models/README.md)
│   ├── api/                        # Flask app factory, routes, auth, error handling
│   ├── core/                       # Settings, exceptions, logging, cache, job manager
│   ├── data/                       # Data service client, features, windowing, scaling
│   ├── models/                     # Deep and classical forecasters, factory
│   ├── training/                   # Trainer, walk-forward validation, tuning
│   ├── evaluation/                 # Metrics, backtesting, bundle evaluation
│   ├── inference/                  # Predictions, ensembles, signals, explainability
│   ├── registry/                   # Versioned model registry and artifact bundles
│   ├── rl/                         # Trading environment, agents, RL service
│   ├── monitoring/                 # Drift detection, performance tracking, metrics
│   ├── persistence/                # Prediction and signal store
│   ├── engine/                     # Compatibility shim for ai_models.engine.app
│   ├── configs/                    # Reference configuration
│   ├── tests/                      # Unit and integration tests
│   ├── Dockerfile
│   └── requirements*.txt
│
└── README.md
```

## Running Tests

Each package has its own `pytest.ini` scoped to its `tests/` directory.

```bash
# Backend tests
cd backend/
pytest

# AI model tests
cd ai_models/
pytest

# With coverage (run from code/ root)
pytest backend/tests/ --cov=backend
pytest ai_models/tests/ --cov=ai_models
```

## Running Services

Each microservice has its own Flask `app.py`. Run from the `code/` root so package imports resolve correctly:

```bash
# Individual microservices
python -m backend.data_service.app
python -m backend.execution_service.app
python -m backend.risk_service.app
python -m ai_models

# Main API gateway (production via Gunicorn)
gunicorn backend.api.wsgi:application
```

## Local Docker Stack

The `backend/docker-compose.yml` spins up Postgres, Redis, and the backend service:

```bash
cd backend/
docker compose up
```

The database is seeded automatically on first run using the SQL scripts in `backend/scripts/init-db/`.

## Configuration

YAML configs live in `backend/config/` and are loaded at runtime by `backend/common/config.py` via `ConfigManager`. Environment variables take precedence over YAML values.

| Path                                             | Purpose                        |
| ------------------------------------------------ | ------------------------------ |
| `backend/config/logging.yaml`                    | Structured logging setup       |
| `backend/config/database/postgres.yaml`          | PostgreSQL connection settings |
| `backend/config/database/influxdb.yaml`          | InfluxDB time-series settings  |
| `backend/config/services/ai_engine.yaml`         | AI engine service config       |
| `backend/config/services/data_service.yaml`      | Data service config            |
| `backend/config/services/execution_service.yaml` | Execution service config       |
| `backend/config/services/risk_service.yaml`      | Risk service config            |
