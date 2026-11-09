# Configuration Guide

## Overview

QuantumAlpha uses multiple configuration methods including environment variables, YAML files, and runtime configuration. This guide covers all configuration options.

---

## Table of Contents

- [Environment Variables](#environment-variables)
- [YAML Configuration Files](#yaml-configuration-files)
- [Service-Specific Configuration](#service-specific-configuration)
- [Database Configuration](#database-configuration)
- [Security Configuration](#security-configuration)

---

## Environment Variables

### Core Application Variables

| Option             | Type   | Default                 | Description                                      | Where to set (env/file) |
| ------------------ | ------ | ----------------------- | ------------------------------------------------ | ----------------------- |
| `FLASK_ENV`        | string | production              | Application environment (development/production) | `.env` file             |
| `LOG_LEVEL`        | string | INFO                    | Logging level (DEBUG/INFO/WARNING/ERROR)         | `.env` file             |
| `CORS_ORIGINS`     | string | <http://localhost:3000> | Allowed CORS origins (comma-separated)           | `.env` file             |
| `JWT_SECRET_KEY`   | string | (required)              | Secret key for JWT tokens                        | `.env` file (secure)    |
| `FLASK_SECRET_KEY` | string | (required)              | Flask session secret key                         | `.env` file (secure)    |

### Database Configuration

| Option            | Type    | Default           | Description          | Where to set (env/file) |
| ----------------- | ------- | ----------------- | -------------------- | ----------------------- |
| `DB_HOST`         | string  | localhost         | PostgreSQL host      | `.env` file             |
| `DB_PORT`         | integer | 5432              | PostgreSQL port      | `.env` file             |
| `DB_NAME`         | string  | quantumalpha_db   | Database name        | `.env` file             |
| `DB_USER`         | string  | quantumalpha_user | Database user        | `.env` file             |
| `DB_PASSWORD`     | string  | (required)        | Database password    | `.env` file (secure)    |
| `DB_POOL_SIZE`    | integer | 10                | Connection pool size | `.env` file             |
| `DB_MAX_OVERFLOW` | integer | 20                | Max pool overflow    | `.env` file             |

### Redis Configuration

| Option            | Type    | Default   | Description           | Where to set (env/file) |
| ----------------- | ------- | --------- | --------------------- | ----------------------- |
| `REDIS_HOST`      | string  | localhost | Redis host            | `.env` file             |
| `REDIS_PORT`      | integer | 6379      | Redis port            | `.env` file             |
| `REDIS_PASSWORD`  | string  | ""        | Redis password        | `.env` file (secure)    |
| `REDIS_DB`        | integer | 0         | Redis database number | `.env` file             |
| `REDIS_CACHE_TTL` | integer | 3600      | Cache TTL in seconds  | `.env` file             |

### Kafka Configuration

| Option                    | Type   | Default            | Description                           | Where to set (env/file) |
| ------------------------- | ------ | ------------------ | ------------------------------------- | ----------------------- |
| `KAFKA_BOOTSTRAP_SERVERS` | string | localhost:9092     | Kafka broker addresses                | `.env` file             |
| `KAFKA_TOPIC_PREFIX`      | string | quantumalpha       | Topic prefix for all topics           | `.env` file             |
| `KAFKA_CONSUMER_GROUP`    | string | quantumalpha-group | Consumer group ID                     | `.env` file             |
| `KAFKA_AUTO_OFFSET_RESET` | string | earliest           | Offset reset policy (earliest/latest) | `.env` file             |

### InfluxDB Configuration

| Option            | Type   | Default                 | Description          | Where to set (env/file) |
| ----------------- | ------ | ----------------------- | -------------------- | ----------------------- |
| `INFLUXDB_URL`    | string | <http://localhost:8086> | InfluxDB URL         | `.env` file             |
| `INFLUXDB_TOKEN`  | string | (required)              | Authentication token | `.env` file (secure)    |
| `INFLUXDB_ORG`    | string | quantumalpha            | Organization name    | `.env` file             |
| `INFLUXDB_BUCKET` | string | market_data             | Default bucket       | `.env` file             |

### API Keys (Data Providers)

| Option                  | Type   | Default    | Description           | Where to set (env/file) |
| ----------------------- | ------ | ---------- | --------------------- | ----------------------- |
| `ALPHA_VANTAGE_API_KEY` | string | (required) | Alpha Vantage API key | `.env` file (secure)    |
| `POLYGON_API_KEY`       | string | (optional) | Polygon.io API key    | `.env` file (secure)    |
| `FINNHUB_API_KEY`       | string | (optional) | Finnhub API key       | `.env` file (secure)    |
| `QUANDL_API_KEY`        | string | (optional) | Quandl API key        | `.env` file (secure)    |
| `IEX_API_KEY`           | string | (optional) | IEX Cloud API key     | `.env` file (secure)    |

### Broker Integration

| Option                     | Type    | Default                  | Description               | Where to set (env/file) |
| -------------------------- | ------- | ------------------------ | ------------------------- | ----------------------- |
| `ALPACA_API_KEY`           | string  | (required)               | Alpaca API key            | `.env` file (secure)    |
| `ALPACA_SECRET_KEY`        | string  | (required)               | Alpaca secret key         | `.env` file (secure)    |
| `ALPACA_BASE_URL`          | string  | paper-api.alpaca.markets | API base URL (paper/live) | `.env` file             |
| `INTERACTIVE_BROKERS_HOST` | string  | localhost                | IB Gateway host           | `.env` file             |
| `INTERACTIVE_BROKERS_PORT` | integer | 7496                     | IB Gateway port           | `.env` file             |

### AI/ML Configuration

| Option                          | Type    | Default                 | Description                | Where to set (env/file) |
| ------------------------------- | ------- | ----------------------- | -------------------------- | ----------------------- |
| `MODEL_REGISTRY_PATH`           | string  | ./backend/models        | Model storage path         | `.env` file             |
| `FEATURE_STORE_PATH`            | string  | ./backend/features      | Feature storage path       | `.env` file             |
| `EXPERIMENT_TRACKING_URI`       | string  | <http://localhost:5000> | MLflow tracking URI        | `.env` file             |
| `ENABLE_REINFORCEMENT_LEARNING` | boolean | false                   | Enable RL features         | `.env` file             |
| `GPU_ENABLED`                   | boolean | false                   | Enable GPU acceleration    | `.env` file             |
| `TENSORFLOW_MEMORY_LIMIT`       | integer | 4096                    | TensorFlow GPU memory (MB) | `.env` file             |

### Monitoring Configuration

| Option                  | Type    | Default | Description                     | Where to set (env/file) |
| ----------------------- | ------- | ------- | ------------------------------- | ----------------------- |
| `PROMETHEUS_PORT`       | integer | 9090    | Prometheus port                 | `.env` file             |
| `GRAFANA_PORT`          | integer | 3001    | Grafana port                    | `.env` file             |
| `METRICS_ENABLED`       | boolean | true    | Enable metrics export           | `.env` file             |
| `HEALTH_CHECK_INTERVAL` | integer | 30      | Health check interval (seconds) | `.env` file             |

---

## YAML Configuration Files

### Location

All YAML configuration files are located in `backend/config_files/`:

```text
backend/config_files/
├── database/
│   ├── postgres.yaml
│   └── influxdb.yaml
├── services/
│   ├── ai_engine.yaml
│   ├── data_service.yaml
│   ├── execution_service.yaml
│   └── risk_service.yaml
└── logging.yaml
```

### Loading Configuration

```python
from backend.common.config import get_config_manager

# Load all configurations
config = get_config_manager(env_file='.env')

# Access nested configuration
ai_config = config.get('ai_engine.models.price_prediction')
db_config = config.get('database.postgres')
```

---

## Service-Specific Configuration

### AI Engine Configuration

**File:** `backend/config_files/services/ai_engine.yaml`

#### Model Configuration

```yaml
models:
  price_prediction:
    - name: lstm_daily
      enabled: true
      algorithm: lstm
      hyperparameters:
        lstm_units: 128
        dropout_rate: 0.2
        learning_rate: 0.001
        batch_size: 64
        epochs: 100
```

**Parameters:**

| Parameter                       | Type    | Default    | Description                       |
| ------------------------------- | ------- | ---------- | --------------------------------- |
| `name`                          | string  | (required) | Model identifier                  |
| `enabled`                       | boolean | true       | Enable/disable model              |
| `algorithm`                     | string  | (required) | Algorithm type (lstm/xgboost/etc) |
| `hyperparameters.lstm_units`    | integer | 128        | LSTM layer units                  |
| `hyperparameters.dropout_rate`  | float   | 0.2        | Dropout rate (0-1)                |
| `hyperparameters.learning_rate` | float   | 0.001      | Learning rate                     |
| `hyperparameters.batch_size`    | integer | 64         | Batch size                        |
| `hyperparameters.epochs`        | integer | 100        | Training epochs                   |

#### Reinforcement Learning Configuration

```yaml
reinforcement_learning:
  enabled: true
  agents:
    - name: dqn_trader
      algorithm: dqn
      hyperparameters:
        learning_rate: 0.0001
        gamma: 0.99
        epsilon_start: 1.0
        epsilon_end: 0.01
        memory_size: 10000
```

**Parameters:**

| Parameter                       | Type    | Default    | Description                |
| ------------------------------- | ------- | ---------- | -------------------------- |
| `enabled`                       | boolean | false      | Enable RL features         |
| `agents[].name`                 | string  | (required) | Agent identifier           |
| `agents[].algorithm`            | string  | (required) | RL algorithm (dqn/ppo/a3c) |
| `hyperparameters.learning_rate` | float   | 0.0001     | Learning rate              |
| `hyperparameters.gamma`         | float   | 0.99       | Discount factor            |
| `hyperparameters.memory_size`   | integer | 10000      | Replay memory size         |

### Risk Service Configuration

**File:** `backend/config_files/services/risk_service.yaml`

```yaml
risk_metrics:
  var:
    confidence_level: 0.95
    lookback_period: 252
    method: historical # historical, parametric, monte_carlo

  position_sizing:
    method: kelly_criterion # kelly_criterion, fixed_fraction, volatility_based
    max_position_size: 0.20
    min_position_size: 0.01
    risk_per_trade: 0.02
```

**Parameters:**

| Parameter                           | Type    | Default         | Description                     |
| ----------------------------------- | ------- | --------------- | ------------------------------- |
| `var.confidence_level`              | float   | 0.95            | VaR confidence level            |
| `var.lookback_period`               | integer | 252             | Historical period (days)        |
| `var.method`                        | string  | historical      | VaR calculation method          |
| `position_sizing.method`            | string  | kelly_criterion | Position sizing method          |
| `position_sizing.max_position_size` | float   | 0.20            | Max % of portfolio per position |
| `position_sizing.risk_per_trade`    | float   | 0.02            | Max risk % per trade            |

### Execution Service Configuration

**File:** `backend/config_files/services/execution_service.yaml`

```yaml
execution_strategies:
  - name: vwap
    enabled: true
    parameters:
      time_window: 300 # seconds
      participation_rate: 0.10

  - name: twap
    enabled: true
    parameters:
      time_window: 600
      num_slices: 10

order_management:
  max_order_size: 10000
  min_order_size: 1
  default_time_in_force: day
```

**Parameters:**

| Parameter                         | Type    | Default    | Description                |
| --------------------------------- | ------- | ---------- | -------------------------- |
| `execution_strategies[].name`     | string  | (required) | Strategy name              |
| `execution_strategies[].enabled`  | boolean | true       | Enable strategy            |
| `vwap.time_window`                | integer | 300        | VWAP time window (seconds) |
| `vwap.participation_rate`         | float   | 0.10       | Market participation rate  |
| `twap.num_slices`                 | integer | 10         | Number of order slices     |
| `order_management.max_order_size` | integer | 10000      | Max order size             |

### Data Service Configuration

**File:** `backend/config_files/services/data_service.yaml`

```yaml
data_sources:
  market_data:
    primary: alpha_vantage
    fallback: [polygon, yfinance]
    update_frequency: 60 # seconds

  alternative_data:
    news_sentiment:
      enabled: true
      sources: [finnhub, newsapi]
    satellite_imagery:
      enabled: false

features:
  technical_indicators:
    - rsi_14
    - macd
    - bollinger_bands
    - moving_avg_5
    - moving_avg_20
```

**Parameters:**

| Parameter                                   | Type    | Default       | Description                     |
| ------------------------------------------- | ------- | ------------- | ------------------------------- |
| `data_sources.market_data.primary`          | string  | alpha_vantage | Primary data source             |
| `data_sources.market_data.update_frequency` | integer | 60            | Update interval (seconds)       |
| `alternative_data.news_sentiment.enabled`   | boolean | true          | Enable news sentiment           |
| `features.technical_indicators`             | array   | -             | List of indicators to calculate |

---

## Database Configuration

### PostgreSQL Configuration

**File:** `backend/config_files/database/postgres.yaml`

```yaml
connection:
  host: ${DB_HOST}
  port: ${DB_PORT}
  database: ${DB_NAME}
  user: ${DB_USER}
  password: ${DB_PASSWORD}

pool:
  size: 10
  max_overflow: 20
  timeout: 30
  recycle: 3600

performance:
  statement_timeout: 30000 # milliseconds
  idle_in_transaction_session_timeout: 60000
```

### InfluxDB Configuration

**File:** `backend/config_files/database/influxdb.yaml`

```yaml
connection:
  url: ${INFLUXDB_URL}
  token: ${INFLUXDB_TOKEN}
  org: ${INFLUXDB_ORG}
  bucket: ${INFLUXDB_BUCKET}

retention_policies:
  raw_data: 90d
  aggregated_1h: 1y
  aggregated_1d: 5y

batching:
  batch_size: 5000
  flush_interval: 10000 # milliseconds
```

---

## Security Configuration

### JWT Configuration

```yaml
jwt:
  secret_key: ${JWT_SECRET_KEY}
  algorithm: HS256
  access_token_expire: 3600 # seconds
  refresh_token_expire: 604800 # 7 days
```

### API Rate Limiting

```yaml
rate_limiting:
  enabled: true
  strategies:
    default:
      requests_per_minute: 100
      requests_per_hour: 1000

    authentication:
      requests_per_minute: 10

    model_training:
      requests_per_hour: 5
```

### CORS Configuration

```yaml
cors:
  origins:
    - http://localhost:3000
    - https://app.quantumalpha.ai
  methods:
    - GET
    - POST
    - PUT
    - DELETE
  allow_credentials: true
  max_age: 3600
```

---

## Example .env File

Complete `.env` file template:

```bash
# Application
FLASK_ENV=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Security
JWT_SECRET_KEY=your_jwt_secret_change_in_production
FLASK_SECRET_KEY=your_flask_secret_change_in_production

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=quantumalpha_db
DB_USER=quantumalpha_user
DB_PASSWORD=your_secure_password
DB_POOL_SIZE=10

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=quantumalpha

# InfluxDB
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_influxdb_token
INFLUXDB_ORG=quantumalpha
INFLUXDB_BUCKET=market_data

# API Keys
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
POLYGON_API_KEY=your_polygon_key
FINNHUB_API_KEY=your_finnhub_key

# Broker
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# AI/ML
MODEL_REGISTRY_PATH=./backend/models
FEATURE_STORE_PATH=./backend/features
EXPERIMENT_TRACKING_URI=http://localhost:5000
ENABLE_REINFORCEMENT_LEARNING=false

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
```

---

## Configuration Best Practices

### 1. Use Environment Variables for Secrets

```bash
# ✅ GOOD - Use environment variables
export DB_PASSWORD="secure_password"

# ❌ BAD - Hardcoded in config files
password: "secure_password"
```

### 2. Use Different Configs per Environment

```yaml
# config.dev.yaml
database:
  host: localhost
  debug: true

# config.prod.yaml
database:
  host: prod-db.example.com
  debug: false
  ssl: true
```

### 3. Validate Configuration on Startup

```python
from backend.common.validation import validate_config

# Validate all required configs are present
validate_config([
    'DB_HOST',
    'DB_PASSWORD',
    'JWT_SECRET_KEY',
    'ALPHA_VANTAGE_API_KEY'
])
```

### 4. Use Config Hierarchy

Priority order (highest to lowest):

1. Environment variables
2. `.env` file
3. YAML configuration files
4. Default values in code

---

## Troubleshooting Configuration

### Missing Environment Variables

```bash
# Check if variable is set
echo $DB_PASSWORD

# Set temporarily
export DB_PASSWORD="password"

# Set permanently (add to ~/.bashrc or ~/.zshrc)
echo 'export DB_PASSWORD="password"' >> ~/.bashrc
```

### Invalid YAML Syntax

```bash
# Validate YAML file
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Use online YAML validator
```

### Configuration Not Loading

```python
# Debug configuration loading
from backend.common.config import get_config_manager

config = get_config_manager(env_file='.env')
print(config.get_all())  # Print all loaded config
```

---

**See Also:**

- [INSTALLATION.md](./INSTALLATION.md) - Setup instructions
- [USAGE.md](./USAGE.md) - Usage examples
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues
