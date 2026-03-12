-- Investment Scout Database Initialization Script
-- This script creates all necessary tables for the application

-- Financial data table
CREATE TABLE IF NOT EXISTS financial_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    revenue NUMERIC(20, 2),
    earnings NUMERIC(20, 2),
    pe_ratio NUMERIC(10, 2),
    debt_to_equity NUMERIC(10, 2),
    free_cash_flow NUMERIC(20, 2),
    roe NUMERIC(10, 4),
    updated_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_symbol_financial UNIQUE (symbol, updated_at)
);

CREATE INDEX IF NOT EXISTS idx_financial_symbol ON financial_data(symbol);
CREATE INDEX IF NOT EXISTS idx_financial_updated ON financial_data(updated_at DESC);

-- News articles table
CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT,
    source VARCHAR(100),
    published_at TIMESTAMP NOT NULL,
    url TEXT,
    sentiment NUMERIC(3, 2),  -- -1.0 to 1.0
    symbols TEXT[],  -- Array of related symbols
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_article_url UNIQUE (url)
);

CREATE INDEX IF NOT EXISTS idx_news_published ON news_articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_symbols ON news_articles USING GIN(symbols);
CREATE INDEX IF NOT EXISTS idx_news_sentiment ON news_articles(sentiment);

-- Geopolitical events table
CREATE TABLE IF NOT EXISTS geopolitical_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,  -- 'election', 'policy', 'conflict', 'trade', 'sanction'
    title TEXT NOT NULL,
    description TEXT,
    affected_regions TEXT[],
    affected_sectors TEXT[],
    impact_score NUMERIC(3, 2),  -- -1.0 to 1.0
    event_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_geo_event_date ON geopolitical_events(event_date DESC);
CREATE INDEX IF NOT EXISTS idx_geo_event_type ON geopolitical_events(event_type);
CREATE INDEX IF NOT EXISTS idx_geo_impact ON geopolitical_events(impact_score);

-- Industry trends table
CREATE TABLE IF NOT EXISTS industry_trends (
    id SERIAL PRIMARY KEY,
    sector VARCHAR(100) NOT NULL,
    industry VARCHAR(100) NOT NULL,
    trend_type VARCHAR(50),  -- 'regulatory', 'technological', 'competitive', 'supply_chain'
    description TEXT,
    impact_score NUMERIC(3, 2),
    affected_companies TEXT[],
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_industry_sector ON industry_trends(sector);
CREATE INDEX IF NOT EXISTS idx_industry_timestamp ON industry_trends(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_industry_type ON industry_trends(trend_type);

-- Real-time projections table
CREATE TABLE IF NOT EXISTS projections (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    projection_type VARCHAR(50),  -- 'revenue', 'earnings', 'price_target'
    projected_value NUMERIC(20, 2),
    confidence_lower NUMERIC(20, 2),
    confidence_upper NUMERIC(20, 2),
    confidence_level NUMERIC(3, 2),  -- 0.0 to 1.0
    projection_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_projection_symbol ON projections(symbol);
CREATE INDEX IF NOT EXISTS idx_projection_type ON projections(projection_type);
CREATE INDEX IF NOT EXISTS idx_projection_date ON projections(projection_date DESC);

-- Recommendations tracking table
CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    recommendation_type VARCHAR(20),  -- 'investment' or 'trading'
    entry_price NUMERIC(20, 6),
    entry_date TIMESTAMP NOT NULL,
    position_size_percent NUMERIC(5, 2),
    target_price NUMERIC(20, 6),
    stop_loss NUMERIC(20, 6),
    exit_price NUMERIC(20, 6),
    exit_date TIMESTAMP,
    status VARCHAR(20),  -- 'open', 'closed', 'stopped'
    return_percent NUMERIC(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rec_symbol ON recommendations(symbol);
CREATE INDEX IF NOT EXISTS idx_rec_status ON recommendations(status);
CREATE INDEX IF NOT EXISTS idx_rec_entry_date ON recommendations(entry_date DESC);
CREATE INDEX IF NOT EXISTS idx_rec_type ON recommendations(recommendation_type);

-- Performance snapshots table
CREATE TABLE IF NOT EXISTS performance_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL UNIQUE,
    portfolio_value NUMERIC(20, 2),
    total_return_percent NUMERIC(10, 4),
    sp500_return_percent NUMERIC(10, 4),
    relative_performance NUMERIC(10, 4),
    sharpe_ratio NUMERIC(10, 4),
    max_drawdown NUMERIC(10, 4),
    win_rate NUMERIC(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_perf_date ON performance_snapshots(snapshot_date DESC);

-- Historical quotes table (for backtesting and analysis)
CREATE TABLE IF NOT EXISTS historical_quotes (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    price NUMERIC(20, 6),
    bid NUMERIC(20, 6),
    ask NUMERIC(20, 6),
    volume BIGINT,
    exchange_timestamp TIMESTAMP NOT NULL,
    received_timestamp TIMESTAMP NOT NULL,
    latency_seconds NUMERIC(10, 3),
    is_fresh BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_quote UNIQUE (symbol, exchange_timestamp)
);

CREATE INDEX IF NOT EXISTS idx_quote_symbol ON historical_quotes(symbol);
CREATE INDEX IF NOT EXISTS idx_quote_timestamp ON historical_quotes(exchange_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_quote_fresh ON historical_quotes(is_fresh);

-- System logs table (for monitoring and debugging)
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20) NOT NULL,
    component VARCHAR(100),
    event VARCHAR(100),
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_log_timestamp ON system_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_log_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_log_component ON system_logs(component);
CREATE INDEX IF NOT EXISTS idx_log_metadata ON system_logs USING GIN(metadata);

-- Email delivery tracking table
CREATE TABLE IF NOT EXISTS email_deliveries (
    id SERIAL PRIMARY KEY,
    email_type VARCHAR(20) NOT NULL,  -- 'newsletter' or 'alert'
    recipient VARCHAR(255) NOT NULL,
    subject TEXT,
    sent_at TIMESTAMP,
    delivery_status VARCHAR(20),  -- 'pending', 'sent', 'failed'
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_email_type ON email_deliveries(email_type);
CREATE INDEX IF NOT EXISTS idx_email_status ON email_deliveries(delivery_status);
CREATE INDEX IF NOT EXISTS idx_email_sent ON email_deliveries(sent_at DESC);

-- Create a view for open recommendations
CREATE OR REPLACE VIEW open_recommendations AS
SELECT 
    r.*,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - r.entry_date)) / 86400 AS days_held
FROM recommendations r
WHERE r.status = 'open'
ORDER BY r.entry_date DESC;

-- Create a view for performance summary
CREATE OR REPLACE VIEW performance_summary AS
SELECT 
    COUNT(*) FILTER (WHERE status = 'closed') AS total_closed,
    COUNT(*) FILTER (WHERE status = 'open') AS total_open,
    COUNT(*) FILTER (WHERE status = 'closed' AND return_percent > 0) AS winners,
    COUNT(*) FILTER (WHERE status = 'closed' AND return_percent <= 0) AS losers,
    ROUND(AVG(return_percent) FILTER (WHERE status = 'closed'), 2) AS avg_return,
    ROUND(AVG(return_percent) FILTER (WHERE status = 'closed' AND return_percent > 0), 2) AS avg_winner,
    ROUND(AVG(return_percent) FILTER (WHERE status = 'closed' AND return_percent <= 0), 2) AS avg_loser,
    ROUND(
        (COUNT(*) FILTER (WHERE status = 'closed' AND return_percent > 0)::NUMERIC / 
         NULLIF(COUNT(*) FILTER (WHERE status = 'closed'), 0) * 100), 
        2
    ) AS win_rate_percent
FROM recommendations;

-- Grant permissions (adjust as needed for your deployment)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;

-- Insert initial data (optional)
-- You can add seed data here if needed

-- Vacuum and analyze for optimal performance
VACUUM ANALYZE;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Investment Scout database initialized successfully!';
END $$;
