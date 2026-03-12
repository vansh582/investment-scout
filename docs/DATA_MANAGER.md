# Data Manager Documentation

The Data Manager is a critical component of the Investment Scout system that provides caching and persistent storage capabilities using Redis and PostgreSQL.

## Overview

The `DataManager` class serves as the caching layer between market data clients and the rest of the system. It implements:

- **Redis caching** for real-time quote data with configurable TTL (15-60 seconds)
- **PostgreSQL storage** for historical data and audit logs
- **Automatic data freshness validation** (rejects data >30 seconds old)
- **Dual TTL strategy** for active vs watchlist stocks

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Data Manager                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │  Redis Cache     │         │  PostgreSQL DB   │          │
│  │                  │         │                  │          │
│  │  • Quotes        │         │  • Quote History │          │
│  │  • TTL: 15-60s   │         │  • Historical    │          │
│  │  • Fast access   │         │    Data          │          │
│  └──────────────────┘         │  • Audit Logs    │          │
│                                └──────────────────┘          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Dual-TTL Caching Strategy

The Data Manager implements different cache TTLs based on monitoring type:

- **Active stocks** (15 seconds): Stocks being actively monitored for opportunities
- **Watchlist stocks** (60 seconds): Stocks on the watchlist with less frequent updates

This strategy optimizes API usage while maintaining data freshness requirements (<30 seconds).

### 2. Data Freshness Validation

All quotes include both exchange timestamp and received timestamp, allowing the system to:

- Calculate data latency
- Reject stale data (>30 seconds old)
- Ensure recommendations are based on current market conditions

### 3. Historical Data Storage

The Data Manager stores:

- **Quote history**: Individual price quotes with full timestamp tracking
- **Historical data**: Aggregated data (financials, news, economic indicators)
- **Audit logs**: System operations for troubleshooting

## Usage

### Basic Usage

```python
from src.utils.data_manager import DataManager
from src.models.data_models import Quote
from datetime import datetime
from decimal import Decimal

# Initialize
manager = DataManager(
    redis_url="redis://localhost:6379",
    postgres_url="postgresql://localhost/investment_scout",
    active_cache_ttl=15,
    watchlist_cache_ttl=60
)

# Create a quote
quote = Quote(
    symbol="AAPL",
    price=Decimal("150.25"),
    exchange_timestamp=datetime.now(),
    received_timestamp=datetime.now(),
    bid=Decimal("150.20"),
    ask=Decimal("150.30"),
    volume=1000000
)

# Cache the quote
manager.cache_quote("AAPL", quote, is_active=True)

# Retrieve cached quote
cached_quote = manager.get_cached_quote("AAPL")

# Check cache validity
is_valid = manager.is_cache_valid("AAPL")

# Store quote history
manager.store_quote_history(quote)

# Retrieve quote history
history = manager.get_quote_history("AAPL", days=30)

# Close connections
manager.close()
```

### Context Manager Usage

```python
with DataManager(redis_url, postgres_url) as manager:
    manager.cache_quote("AAPL", quote)
    cached = manager.get_cached_quote("AAPL")
# Connections automatically closed
```

## API Reference

### Initialization

```python
DataManager(
    redis_url: str,
    postgres_url: str,
    active_cache_ttl: int = 15,
    watchlist_cache_ttl: int = 60
)
```

**Parameters:**
- `redis_url`: Redis connection URL (e.g., "redis://localhost:6379")
- `postgres_url`: PostgreSQL connection URL (e.g., "postgresql://user:pass@localhost/db")
- `active_cache_ttl`: Cache TTL for active stocks in seconds (default: 15)
- `watchlist_cache_ttl`: Cache TTL for watchlist stocks in seconds (default: 60)

### Methods

#### cache_quote()

Cache a quote in Redis with appropriate TTL.

```python
cache_quote(symbol: str, quote: Quote, is_active: bool = True) -> None
```

**Parameters:**
- `symbol`: Stock symbol
- `quote`: Quote object to cache
- `is_active`: Whether this is an actively monitored stock (affects TTL)

#### get_cached_quote()

Retrieve a cached quote from Redis.

```python
get_cached_quote(symbol: str) -> Optional[Quote]
```

**Returns:** Quote object if found and valid, None otherwise

#### is_cache_valid()

Check if cached data for a symbol is still valid.

```python
is_cache_valid(symbol: str) -> bool
```

**Returns:** True if cache exists and is valid, False otherwise

#### store_quote_history()

Store a quote in PostgreSQL for historical tracking.

```python
store_quote_history(quote: Quote) -> None
```

#### get_quote_history()

Retrieve quote history from PostgreSQL.

```python
get_quote_history(symbol: str, days: int = 30) -> List[Quote]
```

**Returns:** List of Quote objects

#### store_historical_data()

Store historical data in PostgreSQL.

```python
store_historical_data(
    symbol: str,
    data_type: str,
    data: Dict[str, Any],
    timestamp: Optional[datetime] = None
) -> None
```

**Parameters:**
- `symbol`: Stock symbol
- `data_type`: Type of data (e.g., 'price_history', 'financials', 'news')
- `data`: Data to store as dictionary
- `timestamp`: Timestamp for the data (defaults to now)

#### get_historical_data()

Retrieve historical data from PostgreSQL.

```python
get_historical_data(
    symbol: str,
    data_type: str,
    days: int = 30
) -> List[Dict[str, Any]]
```

**Returns:** List of historical data records

#### close()

Close database connections.

```python
close() -> None
```

## Database Schema

### quotes Table

Stores individual quote history:

```sql
CREATE TABLE quotes (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    price NUMERIC(20, 6) NOT NULL,
    exchange_timestamp TIMESTAMP NOT NULL,
    received_timestamp TIMESTAMP NOT NULL,
    bid NUMERIC(20, 6),
    ask NUMERIC(20, 6),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_symbol_timestamp ON quotes (symbol, exchange_timestamp DESC);
```

### historical_data Table

Stores aggregated historical data:

```sql
CREATE TABLE historical_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_symbol_type_timestamp ON historical_data (symbol, data_type, timestamp DESC);
```

## Configuration

### Environment Variables

```bash
# Redis configuration
REDIS_URL=redis://localhost:6379

# PostgreSQL configuration
DATABASE_URL=postgresql://user:password@localhost:5432/investment_scout

# Optional: Custom TTL values (in seconds)
ACTIVE_CACHE_TTL=15
WATCHLIST_CACHE_TTL=60
```

### Docker Compose Example

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: investment_scout
      POSTGRES_USER: scout
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  redis_data:
  postgres_data:
```

## Testing

### Unit Tests

Run unit tests with mocked connections:

```bash
pytest tests/test_data_manager.py -v
```

### Integration Tests

Run integration tests with real databases:

```bash
# Set environment variables
export REDIS_URL=redis://localhost:6379
export DATABASE_URL=postgresql://localhost/investment_scout_test

# Run tests
pytest tests/test_data_manager_integration.py -v
```

### Manual Testing

Use the test script:

```bash
python scripts/test_data_manager.py
```

## Performance Considerations

### Redis Performance

- **Memory usage**: Each cached quote uses ~200 bytes
- **Throughput**: Redis can handle 100K+ operations/second
- **TTL cleanup**: Automatic expiration frees memory

### PostgreSQL Performance

- **Indexes**: Optimized for time-series queries
- **JSONB**: Efficient storage for flexible data structures
- **Partitioning**: Consider partitioning by date for large datasets

### Optimization Tips

1. **Batch operations**: Use transactions for multiple inserts
2. **Connection pooling**: Reuse connections for better performance
3. **Query optimization**: Use indexes for common query patterns
4. **Data retention**: Implement cleanup for old historical data

## Error Handling

The Data Manager implements graceful error handling:

- **Connection failures**: Logged and raised during initialization
- **Cache failures**: Logged but don't stop execution
- **Database failures**: Transactions rolled back, errors logged
- **Serialization errors**: Caught and logged

## Monitoring

Key metrics to monitor:

- **Cache hit rate**: Percentage of successful cache retrievals
- **Cache TTL distribution**: Verify TTL values are appropriate
- **Database query latency**: Monitor slow queries
- **Connection pool usage**: Ensure sufficient connections
- **Error rates**: Track failures by operation type

## Requirements Validation

The Data Manager satisfies the following requirements:

- **Requirement 3.2**: Data latency <30 seconds (validated via Quote.is_fresh)
- **Requirement 3.3**: Reject stale data >30 seconds
- **Requirement 3.9**: Flag stale data and exclude from recommendations

## See Also

- [Market Monitor Documentation](MARKET_MONITOR.md)
- [API Clients Documentation](API_CLIENTS.md)
- [Deployment Guide](../DEPLOYMENT.md)
