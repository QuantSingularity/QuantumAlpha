# QuantumAlpha AI Models

Standalone AI engine service for forecasting, signal generation, reinforcement learning, model lifecycle management and monitoring. It talks to the data service over HTTP, persists predictions and signals to PostgreSQL (or memory when no database is configured), and is exposed to the web and mobile clients through the backend gateway at `/api/ai/*`.

## Layout

```
ai_models/
  api/            Flask app factory, auth, error handling, routes, service container
  core/           settings, exceptions, logging, TTL cache, background job manager
  data/           data service client, feature engineering, windowing and scaling
  models/         ForecastModel interface, deep (LSTM, GRU, CNN, Transformer), classical (Ridge, RandomForest, GradientBoosting), factory
  training/       trainer, request parsing, walk-forward validation, hyperparameter search
  evaluation/     regression and directional metrics, backtesting, bundle evaluator
  inference/      prediction service, ensemble, signal generator, permutation importance
  registry/       versioned file-backed model registry, artifact bundles
  rl/             trading environment, agents (tabular Q-learning, PPO, A2C, DQN, SAC), service
  monitoring/     drift detection (PSI), performance tracker, Prometheus style metrics
  persistence/    prediction and signal store (PostgreSQL or in-memory)
  engine/         compatibility shim for the legacy ai_models.engine.app:app entry point
  configs/        reference configuration
  tests/          unit and integration tests
```

## Running

```
pip install -r requirements.txt
pip install -r requirements-ml.txt
PORT=8082 DATA_SERVICE_URL=http://localhost:8081 gunicorn --workers 1 --threads 8 --timeout 300 ai_models.api.wsgi:app
```

Use a single worker with threads. The job manager, bundle cache and metrics are process local. The registry itself is safe across processes through file locking.

The deep learning models need TensorFlow and the stable-baselines3 agents need PyTorch (`requirements-ml.txt`). Without them, classical models and the tabular `q_learning` agent still work and deep or SB3 requests return a clear 502 dependency error.

## Configuration

| Variable                  | Default               | Purpose                                                     |
| ------------------------- | --------------------- | ----------------------------------------------------------- |
| `PORT` / `AI_ENGINE_PORT` | 8082                  | listen port                                                 |
| `AI_MODEL_DIR`            | models                | registry and artifact directory                             |
| `AI_RL_MODEL_DIR`         | models/rl             | RL registry directory                                       |
| `DATA_SERVICE_URL`        | http://localhost:8081 | market data source                                          |
| `DATABASE_URL`            | unset                 | PostgreSQL URL, memory store when unset                     |
| `AI_ENGINE_API_KEY`       | unset                 | when set, `/api/*` requires `X-Internal-Key` or `X-API-Key` |
| `AI_REQUEST_TIMEOUT`      | 30                    | data service timeout in seconds                             |
| `AI_MAX_WORKERS`          | 2                     | concurrent background jobs                                  |
| `AI_MAX_EPOCHS`           | 500                   | upper bound for epochs                                      |
| `CORS_ORIGINS`            | *                     | comma separated origins                                     |

## API

Model lifecycle

| Method           | Path                                                                     | Description                                             |
| ---------------- | ------------------------------------------------------------------------ | ------------------------------------------------------- |
| GET              | `/api/catalog`                                                           | model types, defaults, search spaces, features          |
| GET, POST        | `/api/models`                                                            | list, create                                            |
| GET, PUT, DELETE | `/api/models/<id>`                                                       | read, update, delete                                    |
| POST             | `/api/train-model`, `/api/models/<id>/train`                             | train, `async: true` returns a job                      |
| POST             | `/api/models/<id>/evaluate`                                              | evaluate the active version on fresh data               |
| POST             | `/api/models/<id>/validate`                                              | walk-forward cross validation                           |
| POST             | `/api/models/<id>/tune`                                                  | random search, `apply: true` stores the best parameters |
| GET              | `/api/models/<id>/versions`                                              | version history                                         |
| POST, DELETE     | `/api/models/<id>/versions/<v>/promote`, `/api/models/<id>/versions/<v>` | promote or remove a version                             |
| GET              | `/api/models/<id>/explain`                                               | permutation feature importance                          |
| GET              | `/api/jobs`, `/api/jobs/<id>`                                            | background jobs                                         |

Inference

| Method | Path                               | Description                                      |
| ------ | ---------------------------------- | ------------------------------------------------ |
| POST   | `/api/predict`                     | multi step forecast with intervals               |
| GET    | `/api/predict/<model_id>/<symbol>` | same, query parameters                           |
| POST   | `/api/predict/batch`               | many symbols, partial failures reported          |
| POST   | `/api/predict/ensemble`            | weighted ensemble across models                  |
| POST   | `/api/generate-signals`            | `prediction`, `technical` or `ensemble` strategy |
| GET    | `/api/signals`                     | persisted signals                                |

Tracking and monitoring

| Method    | Path                                                | Description                          |
| --------- | --------------------------------------------------- | ------------------------------------ |
| GET, POST | `/api/models/<id>/predictions[/<symbol>]`           | prediction history, manual save      |
| PUT       | `/api/predictions/<id>`                             | record the actual value              |
| GET       | `/api/models/<id>/performance`                      | live error statistics                |
| POST      | `/api/models/<id>/reconcile`                        | fill actuals from market data        |
| GET       | `/api/models/<id>/drift`, `/api/models/<id>/health` | feature drift, retraining advice     |
| GET       | `/health`, `/ready`, `/metrics`                     | liveness, readiness, Prometheus text |

Reinforcement learning lives under `/api/rl` (`algorithms`, `models`, `train`, `act`).

## Modelling notes

- The target is the forward return for steps 1 to `horizon`, predicted directly by a multi output model. Forecast prices are `last_close * (1 + return)`, with 95 percent intervals from validation residuals.
- Features are dimensionless (ratios, oscillators, returns), so a model trained on one symbol can be applied to another and scaling is stable.
- Splits are chronological with an embargo of `horizon` samples, and the scaler is fitted on the training period only.
- Metrics include directional accuracy, information coefficient, skill against a zero return baseline and a cost aware long or flat backtest.
- Drift uses a bias corrected population stability index over the latest 250 rows against training deciles. Thresholds are 0.25 (moderate) and 0.5 (significant) because market features are strongly autocorrelated.
- Periods are normalised to the data service format (`30d`, `365d`) before every request.
- RL environments execute on the next bar, so an action never sees the return it earns. SAC uses a continuous exposure action, the other algorithms a discrete hold, buy, sell action.

## Backend integration

The backend gateway proxies `/api/ai/*` to this service with an allowlist, JWT authentication and role checks (training and model changes need `admin`, `trader` or `analyst`). The trading and risk services call `/api/predict` with timeouts and the internal key.

## Tests

```
python -m pytest ai_models/tests
```

Deep learning tests are skipped when TensorFlow is not installed.
