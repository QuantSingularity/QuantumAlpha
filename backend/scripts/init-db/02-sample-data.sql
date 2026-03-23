-- =============================================================================
-- QuantumAlpha Sample / Seed Data  (idempotent — safe to re-run)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Symbols
-- ---------------------------------------------------------------------------
INSERT INTO market_data.symbols (symbol, name, exchange, asset_class, is_active)
VALUES
    ('AAPL',    'Apple Inc.',                    'NASDAQ', 'equity', TRUE),
    ('MSFT',    'Microsoft Corporation',         'NASDAQ', 'equity', TRUE),
    ('GOOGL',   'Alphabet Inc.',                 'NASDAQ', 'equity', TRUE),
    ('AMZN',    'Amazon.com Inc.',               'NASDAQ', 'equity', TRUE),
    ('TSLA',    'Tesla Inc.',                    'NASDAQ', 'equity', TRUE),
    ('BTC-USD', 'Bitcoin USD',                   'CRYPTO', 'crypto', TRUE),
    ('ETH-USD', 'Ethereum USD',                  'CRYPTO', 'crypto', TRUE),
    ('EUR-USD', 'Euro US Dollar',                'FOREX',  'forex',  TRUE),
    ('GBP-USD', 'British Pound US Dollar',       'FOREX',  'forex',  TRUE),
    ('JPY-USD', 'Japanese Yen US Dollar',        'FOREX',  'forex',  TRUE)
ON CONFLICT (symbol) DO NOTHING;

-- ---------------------------------------------------------------------------
-- AI models
-- ---------------------------------------------------------------------------
INSERT INTO ai_models.models (id, name, description, type, status, parameters, metrics)
VALUES
    (
        'lstm_model_001',
        'LSTM Price Predictor',
        'LSTM model for price prediction',
        'lstm', 'trained',
        '{"layers": 2, "units": 64, "dropout": 0.2, "optimizer": "adam"}',
        '{"mse": 0.0023, "mae": 0.0345, "r2": 0.87}'
    ),
    (
        'cnn_model_001',
        'CNN Pattern Detector',
        'CNN model for pattern detection',
        'cnn', 'trained',
        '{"filters": 32, "kernel_size": 3, "pool_size": 2, "optimizer": "adam"}',
        '{"accuracy": 0.92, "precision": 0.89, "recall": 0.91}'
    ),
    (
        'rl_model_001',
        'RL Trading Agent',
        'Reinforcement learning model for trading',
        'reinforcement', 'trained',
        '{"algorithm": "ppo", "gamma": 0.99, "learning_rate": 0.0003}',
        '{"avg_reward": 245.6, "max_reward": 512.3, "win_rate": 0.68}'
    )
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Portfolios
-- ---------------------------------------------------------------------------
INSERT INTO risk_management.portfolios (id, name, description, owner_id, parameters)
VALUES
    (
        'portfolio_001',
        'Tech Growth Portfolio',
        'Portfolio focused on tech growth stocks',
        'user_001',
        '{"risk_tolerance": "high", "investment_horizon": "long_term", "rebalance_frequency": "quarterly"}'
    ),
    (
        'portfolio_002',
        'Balanced Portfolio',
        'Balanced portfolio with mixed assets',
        'user_001',
        '{"risk_tolerance": "medium", "investment_horizon": "medium_term", "rebalance_frequency": "monthly"}'
    ),
    (
        'portfolio_003',
        'Crypto Portfolio',
        'Portfolio focused on cryptocurrencies',
        'user_002',
        '{"risk_tolerance": "very_high", "investment_horizon": "short_term", "rebalance_frequency": "weekly"}'
    )
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Positions
-- ---------------------------------------------------------------------------
INSERT INTO risk_management.positions
    (portfolio_id, symbol, quantity, entry_price, current_price)
VALUES
    ('portfolio_001', 'AAPL',    100,  150.0,    160.0),
    ('portfolio_001', 'MSFT',     50,  250.0,    260.0),
    ('portfolio_001', 'GOOGL',    20, 2800.0,   2900.0),
    ('portfolio_002', 'AAPL',     50,  155.0,    160.0),
    ('portfolio_002', 'AMZN',     10, 3200.0,   3300.0),
    ('portfolio_003', 'BTC-USD',   2.5, 40000.0, 42000.0),
    ('portfolio_003', 'ETH-USD',  10,  3000.0,   3200.0)
ON CONFLICT (portfolio_id, symbol) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Users
-- NOTE: password_hash values below are placeholder bcrypt hashes for
-- development only.  Replace with real hashes before any production use.
-- ---------------------------------------------------------------------------
INSERT INTO auth.users
    (id, username, email, password_hash, first_name, last_name, is_active, is_admin)
VALUES
    (
        'user_001', 'johndoe', 'john.doe@example.com',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5/Qe2',
        'John', 'Doe', TRUE, FALSE
    ),
    (
        'user_002', 'janedoe', 'jane.doe@example.com',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5/Qe2',
        'Jane', 'Doe', TRUE, FALSE
    ),
    (
        'admin_001', 'admin', 'admin@example.com',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5/Qe2',
        'Admin', 'User', TRUE, TRUE
    )
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- API keys
-- NOTE: api_key values here are plaintext seeds for development only.
-- In production, store only the hashed form and never the raw secret.
-- ---------------------------------------------------------------------------
INSERT INTO auth.api_keys
    (id, user_id, key_name, api_key, permissions, expires_at, is_active)
VALUES
    (
        'apikey_001', 'user_001', 'Trading API Key',
        '1234567890abcdef1234567890abcdef',
        '{"read": true, "write": true, "trade": true}',
        '2025-12-31 23:59:59+00', TRUE
    ),
    (
        'apikey_002', 'user_002', 'Read-Only API Key',
        'abcdef1234567890abcdef1234567890',
        '{"read": true, "write": false, "trade": false}',
        '2025-12-31 23:59:59+00', TRUE
    )
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Orders  (plain text PK, not a hypertable — ON CONFLICT (id) unchanged)
-- ---------------------------------------------------------------------------
INSERT INTO execution.orders
    (id, portfolio_id, symbol, order_type, side, quantity, price,
     time_in_force, status, broker_order_id, parameters)
VALUES
    ('order_001', 'portfolio_001', 'AAPL',    'market', 'buy',  100,   NULL,   'day', 'filled', 'broker_order_001', NULL),
    ('order_002', 'portfolio_001', 'MSFT',    'limit',  'buy',   50,  250.0,   'day', 'filled', 'broker_order_002', NULL),
    ('order_003', 'portfolio_001', 'GOOGL',   'market', 'buy',   20,   NULL,   'day', 'filled', 'broker_order_003', NULL),
    ('order_004', 'portfolio_002', 'AAPL',    'market', 'buy',   50,   NULL,   'day', 'filled', 'broker_order_004', NULL),
    ('order_005', 'portfolio_002', 'AMZN',    'limit',  'buy',   10, 3200.0,   'day', 'filled', 'broker_order_005', NULL),
    ('order_006', 'portfolio_003', 'BTC-USD', 'market', 'buy',  2.5,   NULL,   'day', 'filled', 'broker_order_006', NULL),
    ('order_007', 'portfolio_003', 'ETH-USD', 'limit',  'buy',   10, 3000.0,   'day', 'filled', 'broker_order_007', NULL)
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Trades  (hypertable — PK is now composite (id, timestamp))
--
-- FIX: ON CONFLICT must reference all columns of the PRIMARY KEY.
--      Was: ON CONFLICT (id)
--      Now: ON CONFLICT (id, timestamp)
-- ---------------------------------------------------------------------------
INSERT INTO execution.trades
    (id, order_id, symbol, side, quantity, price, commission, timestamp)
VALUES
    ('trade_001', 'order_001', 'AAPL',    'buy', 100,  150.0, 1.0, '2023-01-01 10:00:00+00'),
    ('trade_002', 'order_002', 'MSFT',    'buy',  50,  250.0, 1.0, '2023-01-02 11:00:00+00'),
    ('trade_003', 'order_003', 'GOOGL',   'buy',  20, 2800.0, 1.0, '2023-01-03 12:00:00+00'),
    ('trade_004', 'order_004', 'AAPL',    'buy',  50,  155.0, 1.0, '2023-01-04 13:00:00+00'),
    ('trade_005', 'order_005', 'AMZN',    'buy',  10, 3200.0, 1.0, '2023-01-05 14:00:00+00'),
    ('trade_006', 'order_006', 'BTC-USD', 'buy',  2.5, 40000.0, 1.0, '2023-01-06 15:00:00+00'),
    ('trade_007', 'order_007', 'ETH-USD', 'buy',  10, 3000.0, 1.0, '2023-01-07 16:00:00+00')
ON CONFLICT (id, timestamp) DO NOTHING;    -- composite PK  ✓

-- ---------------------------------------------------------------------------
-- Broker accounts
-- ---------------------------------------------------------------------------
INSERT INTO execution.broker_accounts
    (id, broker_name, account_number, api_key, api_secret, parameters, is_active)
VALUES
    ('broker_account_001', 'Interactive Brokers', 'U1234567',
     'api_key_1', 'api_secret_1', '{"paper_trading": true}', TRUE),
    ('broker_account_002', 'Alpaca',              'A1234567',
     'api_key_2', 'api_secret_2', '{"paper_trading": true}', TRUE),
    ('broker_account_003', 'Binance',             'B1234567',
     'api_key_3', 'api_secret_3', '{"paper_trading": true}', TRUE)
ON CONFLICT (id) DO NOTHING;
