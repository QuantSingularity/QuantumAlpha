# QuantumAlpha — `code/` Directory

This is the restructured source tree for the QuantumAlpha platform.

## Directory Structure

```
code/
├── backend/                    # Core backend services (Flask API + business logic)
│   ├── api/                    # API gateway entry points
│   │   ├── app.py              # Lightweight Flask app (mock/deployment version)
│   │   ├── main.py             # Full QuantumAlphaApp with JWT, blueprints, routes
│   │   ├── config.py           # Flask Config class
│   │   └── wsgi.py             # Gunicorn WSGI entry point
│   ├── common/                 # Shared utilities used by all backend services
│   │   ├── audit.py            # Audit logging
│   │   ├── auth.py             # JWT auth, decorators
│   │   ├── config.py           # ConfigManager (env + YAML)
│   │   ├── database.py         # DB session management (Postgres, Redis, InfluxDB)
│   │   ├── logging_config.py   # Logging setup
│   │   ├── logging_utils.py    # ServiceError, ValidationError, setup_logger
│   │   ├── messaging.py        # Async messaging utilities
│   │   ├── models.py           # SQLAlchemy ORM models
│   │   ├── monitoring.py       # Prometheus/health monitoring blueprints
│   │   ├── utils.py            # RateLimiter, SimpleCache, parse_period
│   │   └── validation.py       # Marshmallow schemas, FinancialValidator
│   ├── portfolio_service/      # Portfolio management service
│   │   ├── __init__.py
│   │   └── portfolio_service.py  # Portfolio metrics & position tracking
│   ├── trading_engine/            # Trade execution engine service
│   │   ├── __init__.py
│   │   └── trading_engine.py     # Order lifecycle & execution logic
│   ├── data_service/           # Market & alternative data ingestion
│   │   ├── app.py              # Flask app for data_service microservice
│   │   ├── market_data.py      # Market data fetching & storage
│   │   ├── alternative_data.py # Alternative data sources
│   │   ├── data_processor.py   # Data cleaning & normalisation
│   │   └── feature_engineering.py  # Feature computation pipeline
│   ├── execution_service/      # Order execution microservice
│   │   ├── app.py              # Flask app for execution_service
│   │   ├── order_manager.py    # Order CRUD & lifecycle
│   │   ├── broker_integration.py  # Broker API adapters
│   │   ├── execution_strategy.py  # TWAP, VWAP, etc.
│   │   └── trading_service.py  # Trading coordination
│   ├── risk_service/           # Risk management microservice
│   │   ├── app.py              # Flask app for risk_service
│   │   ├── risk_calculator.py  # VaR, CVaR, Greeks
│   │   ├── stress_testing.py   # Scenario & stress tests
│   │   ├── position_sizing.py  # Kelly, fixed-fraction sizing
│   │   ├── real_time_updater.py  # Live risk feed consumer
│   │   └── online_learning.py  # Adaptive risk models
│   ├── analytics_service/      # Portfolio analytics
│   │   ├── factor_analysis.py  # PCA, factor decomposition
│   │   └── performance_attribution.py  # Brinson-Hood-Beebower attribution
│   ├── compliance_service/     # Regulatory compliance
│   │   ├── compliance_monitoring.py  # Real-time violation detection
│   │   └── regulatory_reporting.py   # Report generation
│   └── tests/                  # Backend unit & integration tests
│       ├── conftest.py
│       ├── test_data_service.py
│       ├── test_execution_service.py
│       ├── test_risk_service.py
│       └── test_integration.py
│
├── ai_models/                  # AI/ML models and training infrastructure
│   ├── engine/                 # Core AI engine
│   │   ├── app.py              # Flask app for ai_models microservice
│   │   ├── model_manager.py    # Model registry, training, serialisation
│   │   ├── prediction_service.py  # Signal generation & inference
│   │   └── reinforcement_learning.py  # RL agents (Gymnasium-based)
│   └── tests/                  # AI model unit tests
│       ├── conftest.py
│       └── test_ai_engine.py
│
├── shared/                     # Infrastructure, config files, DB scripts
│   ├── config/                 # Service & DB configuration YAML files
│   │   ├── logging.yaml
│   │   ├── .env.example
│   │   ├── database/
│   │   │   ├── postgres.yaml
│   │   │   └── influxdb.yaml
│   │   └── services/
│   │       ├── ai_engine.yaml
│   │       ├── data_service.yaml
│   │       ├── execution_service.yaml
│   │       └── risk_service.yaml
│   ├── scripts/
│   │   └── init-db/
│   │       ├── 01-init-schema.sql
│   │       └── 02-sample-data.sql
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   ├── requirements.txt
│   ├── .env
│   ├── .env.example
│   └── .dockerignore
│
├── conftest.py                 # Root pytest config (adds code/ to sys.path)
├── pytest.ini                  # Test discovery settings
└── README.md
```

## Import Conventions

All imports use fully-qualified package paths from the `code/` root:

```python
# Common utilities
from backend.common import ServiceError, ValidationError, setup_logger
from backend.common.database import get_db_session
from backend.common.models import Portfolio, Order

# Business services
from backend.portfolio_service.portfolio_service import portfolio_service
from backend.trading_engine.trading_engine import trading_engine, OrderRequest

# Domain services
from backend.data_service.market_data import MarketDataService
from backend.risk_service.risk_calculator import RiskCalculator

# AI models
from ai_models.engine.model_manager import ModelManager
from ai_models.engine.prediction_service import PredictionService
```

## Running Tests

From the `code/` directory:

```bash
# All tests
pytest

# Backend tests only
pytest backend/tests/

# AI model tests only
pytest ai_models/tests/

# With coverage
pytest --cov=backend --cov=ai_models
```

## Running Services

Each microservice has its own Flask `app.py`:

```bash
# From the code/ root
python -m backend.data_service.app
python -m backend.execution_service.app
python -m backend.risk_service.app
python -m ai_models.engine.app

# Main API gateway (production)
gunicorn backend.api.wsgi:application
```
