# API Reference

## Overview

QuantumAlpha provides a comprehensive REST API for interacting with all platform services. This document covers all public API endpoints, parameters, and response formats.

---

## Table of Contents

- [Authentication](#authentication)
- [Data Service API](#data-service-api)
- [AI Engine API](#ai-engine-api)
- [Risk Service API](#risk-service-api)
- [Execution Service API](#execution-service-api)
- [Common Responses](#common-responses)
- [Rate Limiting](#rate-limiting)

---

## Authentication

### Overview

All API endpoints (except `/health` and `/auth/*`) require JWT-based authentication.

### Login

```http
POST /api/v1/auth/login
```

| Name     | Type   | Required? | Default | Description        | Example          |
| -------- | ------ | --------- | ------- | ------------------ | ---------------- |
| username | string | Yes       | -       | User email address | user@example.com |
| password | string | Yes       | -       | User password      | mypassword123    |

**Example Request:**

```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "mypassword123"
  }'
```

**Example Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Using Access Token

Include the access token in the `Authorization` header:

```bash
curl -X GET http://localhost:8080/api/v1/models \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Data Service API

**Base URL:** `http://localhost:8081/api` or via API Gateway: `http://localhost:8080/api/v1/data`

### Endpoints

| Method | Path                               | Description                | Query/Body params                    | Auth required | Example request                                                                                                     |
| ------ | ---------------------------------- | -------------------------- | ------------------------------------ | ------------- | ------------------------------------------------------------------------------------------------------------------- |
| GET    | `/health`                          | Health check               | None                                 | No            | `curl http://localhost:8081/health`                                                                                 |
| GET    | `/market-data/{symbol}`            | Get market data for symbol | `period`, `interval`                 | Yes           | `curl -H "Authorization: Bearer TOKEN" http://localhost:8081/api/market-data/AAPL?period=1d`                        |
| GET    | `/market-data/{symbol}/historical` | Get historical data        | `start_date`, `end_date`, `interval` | Yes           | `curl -H "Authorization: Bearer TOKEN" http://localhost:8081/api/market-data/AAPL/historical?start_date=2023-01-01` |
| GET    | `/alternative-data/{symbol}`       | Get alternative data       | `data_types`                         | Yes           | `curl -H "Authorization: Bearer TOKEN" http://localhost:8081/api/alternative-data/AAPL?data_types=sentiment,news`   |
| POST   | `/features/generate`               | Generate features          | Body: `symbol`, `data`, `features`   | Yes           | See example below                                                                                                   |

### Get Market Data

```http
GET /api/market-data/{symbol}
```

**Parameters:**

| Name     | Type   | Required? | Default | Description                         | Example |
| -------- | ------ | --------- | ------- | ----------------------------------- | ------- |
| symbol   | string | Yes       | -       | Stock ticker symbol                 | AAPL    |
| period   | string | No        | 1d      | Time period (1d, 5d, 1mo, 3mo, 1y)  | 1d      |
| interval | string | No        | 1h      | Data interval (1m, 5m, 15m, 1h, 1d) | 1h      |

**Example Request:**

```bash
curl -X GET "http://localhost:8081/api/market-data/AAPL?period=1d&interval=1h" \
  -H "Authorization: Bearer TOKEN"
```

**Example Response:**

```json
{
  "symbol": "AAPL",
  "period": "1d",
  "interval": "1h",
  "data": [
    {
      "timestamp": "2023-12-15T09:00:00Z",
      "open": 175.2,
      "high": 176.5,
      "low": 175.0,
      "close": 176.3,
      "volume": 1250000
    }
  ],
  "current_price": 176.3,
  "change": 2.3,
  "change_percent": 1.32
}
```

### Generate Features

```http
POST /api/features/generate
```

**Request Body:**

| Name     | Type   | Required? | Default | Description           | Example                         |
| -------- | ------ | --------- | ------- | --------------------- | ------------------------------- |
| symbol   | string | Yes       | -       | Stock ticker          | AAPL                            |
| data     | array  | Yes       | -       | Historical price data | See below                       |
| features | array  | Yes       | -       | Features to generate  | ["rsi_14", "macd", "bollinger"] |

**Example Request:**

```bash
curl -X POST http://localhost:8081/api/features/generate \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "data": [
      {"date": "2023-12-01", "close": 175.0, "volume": 1000000},
      {"date": "2023-12-02", "close": 176.0, "volume": 1200000}
    ],
    "features": ["rsi_14", "macd", "bollinger_bands"]
  }'
```

**Example Response:**

```json
{
  "symbol": "AAPL",
  "features": {
    "rsi_14": [45.2, 48.3, 52.1],
    "macd": [0.5, 0.7, 0.9],
    "bollinger_bands": {
      "upper": [180.0, 181.0],
      "middle": [175.0, 176.0],
      "lower": [170.0, 171.0]
    }
  }
}
```

---

## AI Engine API

**Base URL:** `http://localhost:8082/api` or via API Gateway: `http://localhost:8080/api/v1/ai`

### Endpoints

| Method | Path                                      | Description                              | Body/query params                                                                            | Auth required | Example request                                                                       |
| ------ | ----------------------------------------- | ---------------------------------------- | -------------------------------------------------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------- |
| GET    | `/health`                                 | Health check                             | None                                                                                         | No            | `curl http://localhost:8082/health`                                                   |
| GET    | `/models`                                 | List all models                          | None                                                                                         | Yes           | `curl -H "Authorization: Bearer TOKEN" http://localhost:8082/api/models`              |
| POST   | `/models`                                 | Create a new (untrained) model           | `name`, `type`, `description?`, `parameters?`, `features?`                                   | Yes           | See example below                                                                     |
| GET    | `/models/{model_id}`                      | Get model details                        | None                                                                                         | Yes           | `curl -H "Authorization: Bearer TOKEN" http://localhost:8082/api/models/model_abc123` |
| PUT    | `/models/{model_id}`                      | Update a model's metadata                | Any of `name`, `description`, `parameters`, `features`                                       | Yes           | -                                                                                     |
| DELETE | `/models/{model_id}`                      | Delete a model and its artifacts         | None                                                                                         | Yes           | -                                                                                     |
| POST   | `/models/{model_id}/evaluate`             | Evaluate a trained model                 | `symbol`, `timeframe`, `period`                                                              | Yes           | -                                                                                     |
| GET    | `/models/{model_id}/predictions/{symbol}` | Saved prediction history                 | Query: `start_date?`, `end_date?`                                                            | Yes           | -                                                                                     |
| POST   | `/models/{model_id}/predictions`          | Persist a prediction                     | `symbol`, `timestamp`, `prediction`, `actual?`                                               | Yes           | -                                                                                     |
| PUT    | `/predictions/{prediction_id}`            | Attach a realised actual value           | `actual`                                                                                     | Yes           | -                                                                                     |
| GET    | `/models/{model_id}/performance`          | Accuracy/error metrics for a model       | Query: `symbol?`, `start_date?`, `end_date?`                                                 | Yes           | -                                                                                     |
| POST   | `/train-model`                            | Create (if needed) and train a model     | `model_id?` (else `name`+`type` to create first), `symbol`, `timeframe`, `period`            | Yes           | See example below                                                                     |
| POST   | `/predict`                                | Generate a prediction                    | `model_id`, `symbol`, `timeframe?`, `period?`, `horizon?`                                    | Yes           | See example below                                                                     |
| GET    | `/predict/{model_id}/{symbol}`            | Convenience GET form of `/predict`       | Query: `timeframe?`, `period?`, `horizon?`                                                   | Yes           | -                                                                                     |
| POST   | `/generate-signals`                       | Generate trading signals                 | `symbols` (list), `model_id?`, `timeframe?`, `period?`, `strategy?`                          | Yes           | See example below                                                                     |
| GET    | `/rl/models`                              | List all RL models                       | None                                                                                         | Yes           | -                                                                                     |
| POST   | `/rl/models`                              | Create a new (untrained) RL model        | `name`, `algorithm` (`ppo`\|`a2c`\|`dqn`\|`sac`), `description?`, `parameters?`, `features?` | Yes           | -                                                                                     |
| GET    | `/rl/models/{model_id}`                   | Get RL model details                     | None                                                                                         | Yes           | -                                                                                     |
| PUT    | `/rl/models/{model_id}`                   | Update an RL model's metadata            | Any of `name`, `description`, `parameters`, `features`                                       | Yes           | -                                                                                     |
| DELETE | `/rl/models/{model_id}`                   | Delete an RL model and its artifacts     | None                                                                                         | Yes           | -                                                                                     |
| POST   | `/rl/train`                               | Create (if needed) and train an RL agent | `model_id?` (else `name`+`algorithm` to create first), `symbol`, `timeframe`, `period`       | Yes           | See example below                                                                     |
| POST   | `/rl/act`                                 | Run a trained agent over recent history  | `model_id`, `symbol`, `timeframe`, `period`                                                  | Yes           | See example below                                                                     |

### Create and Train a Model

`/api/train-model` creates a new model first when no `model_id` is given, then trains it in the same call - so a first-time request needs both the model-definition fields (`name`, `type`, `parameters`, `features`) and the training fields (`symbol`, `timeframe`, `period`). To retrain an existing model, pass just `model_id` plus the training fields.

```http
POST /api/train-model
```

**Request Body:**

| Name        | Type   | Required?                             | Default | Description                                              | Example                    |
| ----------- | ------ | ------------------------------------- | ------- | -------------------------------------------------------- | -------------------------- |
| model_id    | string | No (creates a new model when omitted) | -       | Existing model to retrain                                | model_abc123               |
| name        | string | Yes, when `model_id` is omitted       | -       | Model name                                               | lstm_aapl_predictor        |
| type        | string | Yes, when `model_id` is omitted       | -       | `lstm`, `cnn`, or `transformer`                          | lstm                       |
| description | string | No                                    | ""      | Model description                                        | Price prediction for AAPL  |
| parameters  | object | No                                    | {}      | Model hyperparameters (e.g. `epochs`, `sequence_length`) | See below                  |
| features    | array  | No                                    | []      | Feature column names                                     | ["close", "volume", "rsi"] |
| symbol      | string | Yes                                   | -       | Ticker to train on                                       | AAPL                       |
| timeframe   | string | Yes                                   | -       | Bar size                                                 | "1d"                       |
| period      | string | Yes                                   | -       | Historical lookback window                               | "2y"                       |

**Example Request:**

```bash
curl -X POST http://localhost:8082/api/train-model   -H "Authorization: Bearer TOKEN"   -H "Content-Type: application/json"   -d '{
    "name": "lstm_aapl_predictor",
    "type": "lstm",
    "description": "LSTM model for AAPL price prediction",
    "parameters": {
      "sequence_length": 60,
      "epochs": 100,
      "batch_size": 64
    },
    "features": ["close", "volume", "rsi_14", "macd"],
    "symbol": "AAPL",
    "timeframe": "1d",
    "period": "2y"
  }'
```

**Example Response:**

```json
{
  "id": "model_abc123",
  "name": "lstm_aapl_predictor",
  "type": "lstm",
  "status": "trained",
  "created_at": "2023-12-15T10:00:00Z",
  "updated_at": "2023-12-15T10:30:00Z",
  "metrics": { "mse": 4.12, "rmse": 2.03, "mae": 1.55, "r2": 0.87 }
}
```

### Generate a Prediction

```http
POST /api/predict
```

**Request Body:**

| Name      | Type   | Required? | Default | Description                | Example      |
| --------- | ------ | --------- | ------- | -------------------------- | ------------ |
| model_id  | string | Yes       | -       | A trained model's ID       | model_abc123 |
| symbol    | string | Yes       | -       | Ticker to predict          | AAPL         |
| timeframe | string | No        | "1d"    | Bar size                   | "1d"         |
| period    | string | No        | "1mo"   | Historical window to fetch | "1mo"        |
| horizon   | int    | No        | 5       | Bars ahead to predict      | 5            |

**Example Request:**

```bash
curl -X POST http://localhost:8082/api/predict   -H "Authorization: Bearer TOKEN"   -H "Content-Type: application/json"   -d '{
    "model_id": "model_abc123",
    "symbol": "AAPL",
    "timeframe": "1d",
    "period": "1mo",
    "horizon": 5
  }'
```

**Example Response:**

```json
{
  "symbol": "AAPL",
  "model_id": "model_abc123",
  "prediction": {
    "average": 177.5,
    "minimum": 176.0,
    "maximum": 179.1,
    "change": 2.5,
    "change_percent": 1.43,
    "direction": "bullish"
  },
  "generated_at": "2023-12-15T10:30:00Z"
}
```

There's also a `GET /api/predict/{model_id}/{symbol}` convenience form (query params `timeframe`, `period`, `horizon`), used by the risk service's `/api/portfolio-value-prediction` (see the Risk Service API section).

### Generate Trading Signals

```http
POST /api/generate-signals
```

**Request Body:**

| Name      | Type   | Required?                              | Default      | Description                                    | Example          |
| --------- | ------ | -------------------------------------- | ------------ | ---------------------------------------------- | ---------------- |
| symbols   | array  | Yes                                    | -            | Tickers to generate signals for                | ["AAPL", "MSFT"] |
| model_id  | string | Yes, when `strategy` is `"prediction"` | -            | Model to use                                   | model_abc123     |
| timeframe | string | No                                     | "1d"         | Bar size                                       | "1d"             |
| period    | string | No                                     | "1mo"        | Historical window                              | "1mo"            |
| strategy  | string | No                                     | "prediction" | `"prediction"`, `"technical"`, or `"ensemble"` | "prediction"     |

**Example Request:**

```bash
curl -X POST http://localhost:8082/api/generate-signals   -H "Authorization: Bearer TOKEN"   -H "Content-Type: application/json"   -d '{
    "symbols": ["AAPL"],
    "model_id": "model_abc123",
    "strategy": "prediction"
  }'
```

**Example Response:**

```json
{
  "signals": [
    {
      "symbol": "AAPL",
      "signal": "buy",
      "confidence": 0.85,
      "predicted_price": 177.5,
      "model_id": "model_abc123",
      "strategy": "prediction",
      "generated_at": "2023-12-15T10:30:00Z"
    }
  ],
  "count": 1,
  "strategy": "prediction",
  "model_id": "model_abc123",
  "generated_at": "2023-12-15T10:30:00Z"
}
```

### Train a Reinforcement Learning Agent

Same create-or-retrain pattern as `/api/train-model`.

```http
POST /api/rl/train
```

**Request Body:**

| Name       | Type   | Required?                             | Default | Description                              | Example             |
| ---------- | ------ | ------------------------------------- | ------- | ---------------------------------------- | ------------------- |
| model_id   | string | No (creates a new agent when omitted) | -       | Existing agent to retrain                | rl_xyz789           |
| name       | string | Yes, when `model_id` is omitted       | -       | Agent name                               | dqn_trader          |
| algorithm  | string | Yes, when `model_id` is omitted       | -       | `ppo`, `a2c`, `dqn`, or `sac`            | dqn                 |
| parameters | object | No                                    | {}      | Hyperparameters (e.g. `total_timesteps`) | See below           |
| features   | array  | No                                    | []      | Feature column names                     | ["close", "volume"] |
| symbol     | string | Yes                                   | -       | Ticker to train on                       | AAPL                |
| timeframe  | string | Yes                                   | -       | Bar size                                 | "1d"                |
| period     | string | Yes                                   | -       | Historical lookback window               | "6mo"               |

**Example Request:**

```bash
curl -X POST http://localhost:8082/api/rl/train   -H "Authorization: Bearer TOKEN"   -H "Content-Type: application/json"   -d '{
    "name": "dqn_trader",
    "algorithm": "dqn",
    "parameters": {
      "total_timesteps": 50000
    },
    "symbol": "AAPL",
    "timeframe": "1d",
    "period": "6mo"
  }'
```

**Example Response:**

```json
{
  "id": "rl_xyz789",
  "name": "dqn_trader",
  "algorithm": "dqn",
  "status": "trained",
  "created_at": "2023-12-15T10:00:00Z",
  "updated_at": "2023-12-15T10:45:00Z",
  "metrics": { "mean_reward": 12.5, "std_reward": 1.2 }
}
```

### Get an RL Agent's Action

```http
POST /api/rl/act
```

**Request Body:**

| Name      | Type   | Required? | Default | Description          | Example   |
| --------- | ------ | --------- | ------- | -------------------- | --------- |
| model_id  | string | Yes       | -       | A trained agent's ID | rl_xyz789 |
| symbol    | string | Yes       | -       | Ticker               | AAPL      |
| timeframe | string | Yes       | -       | Bar size             | "1d"      |
| period    | string | Yes       | -       | Historical window    | "1mo"     |

**Example Response:**

```json
{
  "model_id": "rl_xyz789",
  "symbol": "AAPL",
  "actions": [1, 1, 0, 2, 1],
  "generated_at": "2023-12-15T10:30:00Z"
}
```

---

## Risk Service API

**Base URL:** `http://localhost:8083/api` or via API Gateway: `http://localhost:8080/api/v1/risk`

All the POST endpoints below take a `portfolio` object in the request body - the risk service has no way to look up a portfolio by ID on its own, so callers must supply its current state:

```json
{
  "id": "portfolio_123",
  "cash": 10000.0,
  "positions": [
    {
      "symbol": "AAPL",
      "quantity": 100,
      "current_price": 175.0,
      "entry_price": 160.0
    }
  ]
}
```

### Endpoints

| Method | Path                          | Description                               | Body params                                                                                    | Auth required | Example request                     |
| ------ | ----------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------- | ----------------------------------- |
| GET    | `/health`                     | Health check                              | None                                                                                           | No            | `curl http://localhost:8083/health` |
| POST   | `/risk-metrics`               | VaR, Expected Shortfall, and Sharpe ratio | `portfolio`, `confidence_levels?`, `timeframe?`, `include_positions?`                          | Yes           | See example below                   |
| POST   | `/stress-test`                | Run a named or custom stress scenario     | `portfolio`, `scenario_name`, `shocks?` (required for `"custom"`), `parameters?`               | Yes           | See example below                   |
| POST   | `/calculate-position`         | Risk-based position sizing                | `portfolio`, `symbol`, `entry_price`, `stop_price`, `risk_amount?` or `risk_percent?`, `side?` | Yes           | See example below                   |
| POST   | `/portfolio-risk`             | Risk-metrics snapshot for a portfolio     | `portfolio`                                                                                    | Yes           | See example below                   |
| POST   | `/risk-alerts`                | Threshold-based risk alerts               | `portfolio`, `var_threshold_percent?`, `concentration_threshold_percent?`                      | Yes           | See example below                   |
| POST   | `/portfolio-value-prediction` | Current vs. AI-model-predicted value      | `portfolio`, `model_id` (calls the AI engine's `/api/predict`)                                 | Yes           | See example below                   |

### Calculate Risk Metrics

```http
POST /api/risk-metrics
```

**Request Body:**

| Name              | Type    | Required? | Default      | Description                               | Example      |
| ----------------- | ------- | --------- | ------------ | ----------------------------------------- | ------------ |
| portfolio         | object  | Yes       | -            | Portfolio state (see above)               | See above    |
| confidence_levels | array   | No        | [0.95, 0.99] | VaR/Expected Shortfall confidence levels  | [0.95, 0.99] |
| timeframe         | string  | No        | "1m"         | One of 1d, 1w, 1m, 3m, 6m, 1y, ytd        | "1m"         |
| include_positions | boolean | No        | true         | Include the position list in the response | true         |

**Example Request:**

```bash
curl -X POST http://localhost:8083/api/risk-metrics \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio": {
      "id": "portfolio_123",
      "cash": 5000.0,
      "positions": [
        {"symbol": "AAPL", "quantity": 100, "current_price": 175.0, "entry_price": 160.0},
        {"symbol": "GOOGL", "quantity": 50, "current_price": 145.0, "entry_price": 140.0}
      ]
    },
    "confidence_levels": [0.95, 0.99]
  }'
```

**Example Response:**

```json
{
  "portfolio_id": "portfolio_123",
  "timeframe": "1m",
  "total_value": 29750.0,
  "var": {
    "0.95": {
      "var": 1250.5,
      "var_percent": 4.2,
      "confidence_level": 0.95,
      "time_horizon": 1
    },
    "0.99": {
      "var": 1800.3,
      "var_percent": 6.05,
      "confidence_level": 0.99,
      "time_horizon": 1
    }
  },
  "expected_shortfall": {
    "0.95": {
      "es": 1600.1,
      "es_percent": 5.38,
      "confidence_level": 0.95,
      "time_horizon": 1
    },
    "0.99": {
      "es": 2100.7,
      "es_percent": 7.06,
      "confidence_level": 0.99,
      "time_horizon": 1
    }
  },
  "sharpe_ratio": 1.45,
  "annualized_return": 0.18,
  "annualized_volatility": 0.22,
  "positions": [/* the request's position list, echoed back */]
}
```

### Run Stress Tests

```http
POST /api/stress-test
```

**Request Body:**

| Name          | Type   | Required?                                   | Description                                                                                            | Example                        |
| ------------- | ------ | ------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------ |
| portfolio     | object | Yes                                         | Portfolio state (see above)                                                                            | See above                      |
| scenario_name | string | Yes                                         | One of `2008_financial_crisis`, `covid_crash_2020`, `dot_com_bubble`, `black_monday_1987`, or `custom` | "covid_crash_2020"             |
| shocks        | object | Required when `scenario_name` is `"custom"` | Per-symbol price shocks, as **fractions** (`-0.3` = -30%, `2.0` = +200%)                               | `{"AAPL": -0.3}`               |
| parameters    | object | No                                          | For a named historical scenario, overrides its default `start_date`/`end_date`                         | `{"start_date": "2020-02-15"}` |

**Example Request (custom scenario):**

```bash
curl -X POST http://localhost:8083/api/stress-test \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio": {
      "id": "portfolio_123",
      "cash": 0,
      "positions": [{"symbol": "AAPL", "quantity": 100, "current_price": 175.0}]
    },
    "scenario_name": "custom",
    "shocks": {"AAPL": -0.20}
  }'
```

**Example Response:**

```json
{
  "portfolio_id": "portfolio_123",
  "scenario_name": "custom",
  "initial_value": 17500.0,
  "final_value": 14000.0,
  "change": -3500.0,
  "change_percent": -20.0,
  "positions": [
    {
      "symbol": "AAPL",
      "quantity": 100,
      "initial_price": 175.0,
      "final_price": 140.0,
      "initial_value": 17500.0,
      "final_value": 14000.0,
      "change": -3500.0,
      "change_percent": -20.0
    }
  ]
}
```

### Calculate Position Size

```http
POST /api/calculate-position
```

Sizes a position so that being stopped out at `stop_price` loses no more than the requested risk (either a fixed `risk_amount` or a `risk_percent` of portfolio value).

**Request Body:**

| Name         | Type   | Required?                                    | Description                                               | Example   |
| ------------ | ------ | -------------------------------------------- | --------------------------------------------------------- | --------- |
| portfolio    | object | Yes                                          | Portfolio state (see above)                               | See above |
| symbol       | string | Yes                                          | Stock ticker                                              | "AAPL"    |
| entry_price  | float  | Yes                                          | Intended entry price                                      | 175.0     |
| stop_price   | float  | Yes                                          | Stop-loss price (below entry for `buy`, above for `sell`) | 168.0     |
| risk_amount  | float  | One of `risk_amount`/`risk_percent` required | Fixed dollar amount to risk                               | 500.0     |
| risk_percent | float  | One of `risk_amount`/`risk_percent` required | Fraction of portfolio value to risk (0.0001-1.0)          | 0.02      |
| side         | string | No, default `"buy"`                          | `"buy"` or `"sell"`                                       | "buy"     |

**Example Request:**

```bash
curl -X POST http://localhost:8083/api/calculate-position \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio": {"id": "portfolio_123", "cash": 100000.0, "positions": []},
    "symbol": "AAPL",
    "entry_price": 175.0,
    "stop_price": 168.5,
    "risk_percent": 0.02,
    "side": "buy"
  }'
```

**Example Response:**

```json
{
  "symbol": "AAPL",
  "price": 175.0,
  "method": "risk",
  "quantity": 307.69,
  "value": 53846.15,
  "stop_loss": 168.5,
  "side": "buy",
  "entry_price": 175.0,
  "stop_price": 168.5
}
```

### Get Portfolio Risk

```http
POST /api/portfolio-risk
```

A convenience wrapper around `/api/risk-metrics` using the default confidence levels and a 1-month timeframe. Takes `{"portfolio": {...}}` and returns the same shape as `/api/risk-metrics`.

### Get Risk Alerts

```http
POST /api/risk-alerts
```

**Request Body:**

| Name                            | Type   | Required? | Default | Description                                              |
| ------------------------------- | ------ | --------- | ------- | -------------------------------------------------------- |
| portfolio                       | object | Yes       | -       | Portfolio state (see above)                              |
| var_threshold_percent           | float  | No        | 5.0     | Alert if 1-day 95% VaR exceeds this % of portfolio value |
| concentration_threshold_percent | float  | No        | 25.0    | Alert if any position exceeds this % of portfolio value  |

**Example Response:**

```json
{
  "alerts": [
    {
      "type": "concentration",
      "severity": "high",
      "message": "AAPL is 41.03% of portfolio, exceeding threshold (25.0%)",
      "symbol": "AAPL",
      "value": 41.03,
      "threshold": 25.0
    }
  ]
}
```

### Portfolio Value Prediction

```http
POST /api/portfolio-value-prediction
```

Calls the AI engine (`GET /api/predict/{model_id}/{symbol}`, see the AI Engine API section) for each position and compares the resulting predicted portfolio value to its current value.

**Request Body:** `portfolio` (see above), `model_id` (a trained AI engine model ID).

**Example Response:**

```json
{
  "portfolio_id": "portfolio_123",
  "current_value": 25000.0,
  "predicted_value": 25500.0,
  "change": 500.0,
  "change_percent": 2.0
}
```

---

## Execution Service API

**Base URL:** `http://localhost:8084/api` or via API Gateway: `http://localhost:8080/api/v1/execution`

### Endpoints

| Method | Path                             | Description          | Query/Body params                         | Auth required | Example request                                                                                   |
| ------ | -------------------------------- | -------------------- | ----------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------- |
| GET    | `/health`                        | Health check         | None                                      | No            | `curl http://localhost:8084/health`                                                               |
| GET    | `/orders`                        | List orders          | Query: `portfolio_id`, `status`, `symbol` | Yes           | `curl -H "Authorization: Bearer TOKEN" "http://localhost:8084/api/orders?status=pending"`         |
| GET    | `/orders/{order_id}`             | Get order details    | None                                      | Yes           | `curl -H "Authorization: Bearer TOKEN" http://localhost:8084/api/orders/order_123`                |
| POST   | `/orders`                        | Create new order     | Body: order details                       | Yes           | See example below                                                                                 |
| POST   | `/orders/{order_id}/cancel`      | Cancel order         | None                                      | Yes           | `curl -X POST -H "Authorization: Bearer TOKEN" http://localhost:8084/api/orders/order_123/cancel` |
| GET    | `/execution-strategies`          | List strategies      | None                                      | Yes           | `curl -H "Authorization: Bearer TOKEN" http://localhost:8084/api/execution-strategies`            |
| GET    | `/brokers`                       | List brokers         | None                                      | Yes           | `curl -H "Authorization: Bearer TOKEN" http://localhost:8084/api/brokers`                         |
| GET    | `/brokers/{broker_id}/positions` | Get broker positions | Query: `account_id`                       | Yes           | See example below                                                                                 |

### Create Order

```http
POST /api/orders
```

**Request Body:**

| Name               | Type   | Required? | Default | Description                        | Example       |
| ------------------ | ------ | --------- | ------- | ---------------------------------- | ------------- |
| portfolio_id       | string | Yes       | -       | Portfolio identifier               | portfolio_123 |
| symbol             | string | Yes       | -       | Stock ticker                       | AAPL          |
| side               | string | Yes       | -       | Order side (buy, sell)             | buy           |
| quantity           | int    | Yes       | -       | Number of shares                   | 100           |
| order_type         | string | Yes       | -       | Order type (market, limit, stop)   | market        |
| limit_price        | float  | No        | -       | Limit price (for limit orders)     | 175.50        |
| stop_price         | float  | No        | -       | Stop price (for stop orders)       | 170.00        |
| execution_strategy | string | No        | default | Execution algorithm                | vwap          |
| time_in_force      | string | No        | day     | Time in force (day, gtc, ioc, fok) | day           |

**Example Request:**

```bash
curl -X POST http://localhost:8084/api/orders \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": "portfolio_123",
    "symbol": "AAPL",
    "side": "buy",
    "quantity": 100,
    "order_type": "limit",
    "limit_price": 175.50,
    "execution_strategy": "vwap",
    "time_in_force": "day"
  }'
```

**Example Response:**

```json
{
  "order_id": "order_abc123",
  "portfolio_id": "portfolio_123",
  "symbol": "AAPL",
  "side": "buy",
  "quantity": 100,
  "filled_quantity": 0,
  "order_type": "limit",
  "limit_price": 175.5,
  "status": "pending",
  "execution_strategy": "vwap",
  "created_at": "2023-12-15T10:00:00Z",
  "updated_at": "2023-12-15T10:00:00Z"
}
```

---

## Common Responses

### Error Response Format

```json
{
  "error": "ValidationError",
  "message": "Symbol is required",
  "status_code": 400,
  "timestamp": "2023-12-15T10:30:00Z"
}
```

### HTTP Status Codes

| Code | Meaning               | Description                       |
| ---- | --------------------- | --------------------------------- |
| 200  | OK                    | Request succeeded                 |
| 201  | Created               | Resource created successfully     |
| 400  | Bad Request           | Invalid input parameters          |
| 401  | Unauthorized          | Missing or invalid authentication |
| 403  | Forbidden             | Insufficient permissions          |
| 404  | Not Found             | Resource not found                |
| 429  | Too Many Requests     | Rate limit exceeded               |
| 500  | Internal Server Error | Server error                      |

---

## Rate Limiting

API endpoints are rate-limited to ensure fair usage:

| Endpoint Type   | Rate Limit   | Window     |
| --------------- | ------------ | ---------- |
| Authentication  | 10 requests  | per minute |
| Data fetching   | 100 requests | per minute |
| Model training  | 5 requests   | per hour   |
| Order placement | 50 requests  | per minute |

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1702641600
```

---

## SDK Libraries

Official SDK libraries are available for:

- **Python**: `pip install quantumalpha-sdk`
- **JavaScript/Node.js**: `npm install quantumalpha-sdk`
- **TypeScript**: Full type definitions included

Example using Python SDK:

```python
from quantumalpha import QuantumAlphaClient

client = QuantumAlphaClient(
    api_key='your_api_key',
    base_url='http://localhost:8080'
)

# Get market data
data = client.data.get_market_data('AAPL', period='1d')

# Create order
order = client.execution.create_order(
    symbol='AAPL',
    side='buy',
    quantity=100,
    order_type='market'
)
```
