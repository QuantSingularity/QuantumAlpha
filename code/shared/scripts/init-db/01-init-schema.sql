-- =============================================================================
-- QuantumAlpha Database Schema
-- TimescaleDB-compatible initialisation script (idempotent — safe to re-run)
--
-- TimescaleDB rule enforced here:
--   Every UNIQUE / PRIMARY KEY constraint on a hypertable MUST include the
--   partition column (timestamp).  Any unique index that omits it causes:
--     ERROR: cannot create a unique index without the column "timestamp"
--
-- Affected tables fixed below (all had a bare `id` primary key):
--   market_data.alternative_data
--   ai_models.prediction_history
--   ai_models.signals
--   risk_management.risk_metrics
--   execution.trades
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Extension
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ---------------------------------------------------------------------------
-- Schemas
-- ---------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS market_data;
CREATE SCHEMA IF NOT EXISTS ai_models;
CREATE SCHEMA IF NOT EXISTS risk_management;
CREATE SCHEMA IF NOT EXISTS execution;
CREATE SCHEMA IF NOT EXISTS auth;

-- ===========================================================================
-- MARKET DATA
-- ===========================================================================

CREATE TABLE IF NOT EXISTS market_data.symbols (
    id          SERIAL PRIMARY KEY,
    -- TEXT preferred over VARCHAR per TimescaleDB best-practice (avoids catalog
    -- warnings); semantics are identical.
    symbol      TEXT        NOT NULL UNIQUE,
    name        TEXT,
    exchange    TEXT,
    asset_class TEXT,
    is_active   BOOLEAN     DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- ohlcv — hypertable
-- PK already includes timestamp  ✓  (no change needed)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS market_data.ohlcv (
    symbol     TEXT        NOT NULL,
    timestamp  TIMESTAMPTZ NOT NULL,
    timeframe  TEXT        NOT NULL,
    open       NUMERIC(19,6) NOT NULL,
    high       NUMERIC(19,6) NOT NULL,
    low        NUMERIC(19,6) NOT NULL,
    close      NUMERIC(19,6) NOT NULL,
    volume     NUMERIC(19,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (symbol, timestamp, timeframe),
    FOREIGN KEY (symbol) REFERENCES market_data.symbols(symbol)
);

SELECT create_hypertable(
    'market_data.ohlcv', 'timestamp',
    if_not_exists => TRUE   -- safe on re-run
);

-- -----------------------------------------------------------------------------
-- alternative_data — hypertable
-- FIX: was `id SERIAL PRIMARY KEY` — unique index without timestamp → CRASH.
--      Changed to BIGINT GENERATED ALWAYS AS IDENTITY with composite PK
--      (id, timestamp) so TimescaleDB can partition without conflict.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS market_data.alternative_data (
    id          BIGINT      GENERATED ALWAYS AS IDENTITY,
    source      TEXT        NOT NULL,
    data_type   TEXT        NOT NULL,
    symbol      TEXT,
    timestamp   TIMESTAMPTZ NOT NULL,
    data        JSONB       NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, timestamp),            -- timestamp included  ✓
    FOREIGN KEY (symbol) REFERENCES market_data.symbols(symbol)
);

SELECT create_hypertable(
    'market_data.alternative_data', 'timestamp',
    if_not_exists => TRUE
);

-- -----------------------------------------------------------------------------
-- features — hypertable
-- PK already includes timestamp  ✓  (no change needed)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS market_data.features (
    symbol       TEXT        NOT NULL,
    timestamp    TIMESTAMPTZ NOT NULL,
    timeframe    TEXT        NOT NULL,
    feature_name TEXT        NOT NULL,
    value        NUMERIC(19,6) NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (symbol, timestamp, timeframe, feature_name),
    FOREIGN KEY (symbol) REFERENCES market_data.symbols(symbol)
);

SELECT create_hypertable(
    'market_data.features', 'timestamp',
    if_not_exists => TRUE
);

-- ===========================================================================
-- AI MODELS
-- ===========================================================================

CREATE TABLE IF NOT EXISTS ai_models.models (
    id          TEXT PRIMARY KEY,
    name        TEXT        NOT NULL,
    description TEXT,
    type        TEXT        NOT NULL,
    status      TEXT        NOT NULL,
    parameters  JSONB,
    metrics     JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_models.model_versions (
    id          SERIAL PRIMARY KEY,   -- NOT a hypertable → bare PK is fine
    model_id    TEXT        NOT NULL,
    version     TEXT        NOT NULL,
    file_path   TEXT        NOT NULL,
    parameters  JSONB,
    metrics     JSONB,
    is_active   BOOLEAN     DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (model_id) REFERENCES ai_models.models(id),
    UNIQUE (model_id, version)
);

-- -----------------------------------------------------------------------------
-- prediction_history — hypertable
-- FIX: was `id SERIAL PRIMARY KEY` → CRASH.
--      Composite PK (id, timestamp) applied.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_models.prediction_history (
    id          BIGINT      GENERATED ALWAYS AS IDENTITY,
    model_id    TEXT        NOT NULL,
    symbol      TEXT        NOT NULL,
    timestamp   TIMESTAMPTZ NOT NULL,
    prediction  NUMERIC(19,6) NOT NULL,
    actual      NUMERIC(19,6),
    error       NUMERIC(19,6),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, timestamp),            -- timestamp included  ✓
    FOREIGN KEY (model_id) REFERENCES ai_models.models(id),
    FOREIGN KEY (symbol)   REFERENCES market_data.symbols(symbol)
);

SELECT create_hypertable(
    'ai_models.prediction_history', 'timestamp',
    if_not_exists => TRUE
);

-- -----------------------------------------------------------------------------
-- signals — hypertable
-- FIX: was `id SERIAL PRIMARY KEY` → CRASH.
--      Composite PK (id, timestamp) applied.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_models.signals (
    id          BIGINT      GENERATED ALWAYS AS IDENTITY,
    model_id    TEXT,
    symbol      TEXT        NOT NULL,
    timestamp   TIMESTAMPTZ NOT NULL,
    signal_type TEXT        NOT NULL,
    strength    NUMERIC(5,2)  NOT NULL,
    price       NUMERIC(19,6),
    parameters  JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, timestamp),            -- timestamp included  ✓
    FOREIGN KEY (model_id) REFERENCES ai_models.models(id),
    FOREIGN KEY (symbol)   REFERENCES market_data.symbols(symbol)
);

SELECT create_hypertable(
    'ai_models.signals', 'timestamp',
    if_not_exists => TRUE
);

-- ===========================================================================
-- RISK MANAGEMENT
-- ===========================================================================

CREATE TABLE IF NOT EXISTS risk_management.portfolios (
    id          TEXT PRIMARY KEY,
    name        TEXT        NOT NULL,
    description TEXT,
    owner_id    TEXT        NOT NULL,
    parameters  JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS risk_management.positions (
    id            SERIAL PRIMARY KEY,   -- NOT a hypertable → bare PK is fine
    portfolio_id  TEXT        NOT NULL,
    symbol        TEXT        NOT NULL,
    quantity      NUMERIC(19,6) NOT NULL,
    entry_price   NUMERIC(19,6) NOT NULL,
    current_price NUMERIC(19,6) NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (portfolio_id) REFERENCES risk_management.portfolios(id),
    FOREIGN KEY (symbol)       REFERENCES market_data.symbols(symbol),
    UNIQUE (portfolio_id, symbol)
);

-- -----------------------------------------------------------------------------
-- risk_metrics — hypertable
-- FIX: was `id SERIAL PRIMARY KEY` → CRASH.
--      Composite PK (id, timestamp) applied.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS risk_management.risk_metrics (
    id                 BIGINT      GENERATED ALWAYS AS IDENTITY,
    portfolio_id       TEXT        NOT NULL,
    timestamp          TIMESTAMPTZ NOT NULL,
    var_95             NUMERIC(19,6),
    var_99             NUMERIC(19,6),
    expected_shortfall NUMERIC(19,6),
    sharpe_ratio       NUMERIC(10,4),
    sortino_ratio      NUMERIC(10,4),
    max_drawdown       NUMERIC(10,4),
    beta               NUMERIC(10,4),
    alpha              NUMERIC(10,4),
    volatility         NUMERIC(10,4),
    created_at         TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, timestamp),            -- timestamp included  ✓
    FOREIGN KEY (portfolio_id) REFERENCES risk_management.portfolios(id)
);

SELECT create_hypertable(
    'risk_management.risk_metrics', 'timestamp',
    if_not_exists => TRUE
);

CREATE TABLE IF NOT EXISTS risk_management.stress_tests (
    id            SERIAL PRIMARY KEY,   -- NOT a hypertable → bare PK is fine
    portfolio_id  TEXT        NOT NULL,
    scenario_name TEXT        NOT NULL,
    parameters    JSONB,
    results       JSONB,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (portfolio_id) REFERENCES risk_management.portfolios(id)
);

-- ===========================================================================
-- EXECUTION
-- ===========================================================================

CREATE TABLE IF NOT EXISTS execution.orders (
    id              TEXT PRIMARY KEY,   -- NOT a hypertable → bare PK is fine
    portfolio_id    TEXT        NOT NULL,
    symbol          TEXT        NOT NULL,
    order_type      TEXT        NOT NULL,
    side            TEXT        NOT NULL,
    quantity        NUMERIC(19,6) NOT NULL,
    price           NUMERIC(19,6),
    time_in_force   TEXT        NOT NULL,
    status          TEXT        NOT NULL,
    broker_order_id TEXT,
    parameters      JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (portfolio_id) REFERENCES risk_management.portfolios(id),
    FOREIGN KEY (symbol)       REFERENCES market_data.symbols(symbol)
);

-- -----------------------------------------------------------------------------
-- trades — hypertable
-- FIX: was `id VARCHAR(50) PRIMARY KEY` → CRASH.
--      id kept as TEXT (explicitly supplied by callers, not auto-generated).
--      Composite PK (id, timestamp) applied.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS execution.trades (
    id          TEXT        NOT NULL,
    order_id    TEXT        NOT NULL,
    symbol      TEXT        NOT NULL,
    side        TEXT        NOT NULL,
    quantity    NUMERIC(19,6) NOT NULL,
    price       NUMERIC(19,6) NOT NULL,
    commission  NUMERIC(19,6) NOT NULL,
    timestamp   TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, timestamp),            -- timestamp included  ✓
    FOREIGN KEY (order_id) REFERENCES execution.orders(id),
    FOREIGN KEY (symbol)   REFERENCES market_data.symbols(symbol)
);

SELECT create_hypertable(
    'execution.trades', 'timestamp',
    if_not_exists => TRUE
);

CREATE TABLE IF NOT EXISTS execution.broker_accounts (
    id             TEXT PRIMARY KEY,
    broker_name    TEXT        NOT NULL,
    account_number TEXT        NOT NULL,
    api_key        TEXT,
    api_secret     TEXT,
    parameters     JSONB,
    is_active      BOOLEAN     DEFAULT TRUE,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ===========================================================================
-- AUTHENTICATION
-- ===========================================================================

CREATE TABLE IF NOT EXISTS auth.users (
    id            TEXT PRIMARY KEY,
    username      TEXT        NOT NULL UNIQUE,
    email         TEXT        NOT NULL UNIQUE,
    password_hash TEXT        NOT NULL,
    first_name    TEXT,
    last_name     TEXT,
    is_active     BOOLEAN     DEFAULT TRUE,
    is_admin      BOOLEAN     DEFAULT FALSE,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS auth.api_keys (
    id          TEXT PRIMARY KEY,
    user_id     TEXT        NOT NULL,
    key_name    TEXT        NOT NULL,
    api_key     TEXT        NOT NULL UNIQUE,
    permissions JSONB,
    expires_at  TIMESTAMPTZ,
    is_active   BOOLEAN     DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES auth.users(id)
);

-- ===========================================================================
-- INDEXES
-- IF NOT EXISTS prevents "already exists" errors on container restart
-- ===========================================================================
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol
    ON market_data.ohlcv(symbol);

CREATE INDEX IF NOT EXISTS idx_alternative_data_symbol
    ON market_data.alternative_data(symbol);

CREATE INDEX IF NOT EXISTS idx_features_symbol
    ON market_data.features(symbol);

CREATE INDEX IF NOT EXISTS idx_prediction_history_model_id
    ON ai_models.prediction_history(model_id);

CREATE INDEX IF NOT EXISTS idx_prediction_history_symbol
    ON ai_models.prediction_history(symbol);

CREATE INDEX IF NOT EXISTS idx_signals_model_id
    ON ai_models.signals(model_id);

CREATE INDEX IF NOT EXISTS idx_signals_symbol
    ON ai_models.signals(symbol);

CREATE INDEX IF NOT EXISTS idx_positions_portfolio_id
    ON risk_management.positions(portfolio_id);

CREATE INDEX IF NOT EXISTS idx_risk_metrics_portfolio_id
    ON risk_management.risk_metrics(portfolio_id);

CREATE INDEX IF NOT EXISTS idx_orders_portfolio_id
    ON execution.orders(portfolio_id);

CREATE INDEX IF NOT EXISTS idx_orders_symbol
    ON execution.orders(symbol);

CREATE INDEX IF NOT EXISTS idx_trades_order_id
    ON execution.trades(order_id);

CREATE INDEX IF NOT EXISTS idx_trades_symbol
    ON execution.trades(symbol);

-- ===========================================================================
-- UPDATED_AT trigger function
-- ===========================================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ===========================================================================
-- TRIGGERS
-- OR REPLACE (PostgreSQL 14+) prevents "already exists" errors on re-run.
-- Running on PostgreSQL 15.6 — confirmed safe.
-- ===========================================================================
CREATE OR REPLACE TRIGGER update_market_data_symbols_updated_at
    BEFORE UPDATE ON market_data.symbols
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE TRIGGER update_ai_models_models_updated_at
    BEFORE UPDATE ON ai_models.models
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE TRIGGER update_risk_management_portfolios_updated_at
    BEFORE UPDATE ON risk_management.portfolios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE TRIGGER update_risk_management_positions_updated_at
    BEFORE UPDATE ON risk_management.positions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE TRIGGER update_execution_orders_updated_at
    BEFORE UPDATE ON execution.orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE TRIGGER update_execution_broker_accounts_updated_at
    BEFORE UPDATE ON execution.broker_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE TRIGGER update_auth_users_updated_at
    BEFORE UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE TRIGGER update_auth_api_keys_updated_at
    BEFORE UPDATE ON auth.api_keys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
