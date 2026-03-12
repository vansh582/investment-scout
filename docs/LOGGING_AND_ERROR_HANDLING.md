# Logging and Error Handling System

## Overview

The Investment Scout system includes comprehensive logging and error handling infrastructure to ensure reliable operation, easy debugging, and graceful degradation during failures.

## Components

### 1. Structured Logging System (`src/utils/logger.py`)

#### Features

- **JSON-formatted logs**: All logs output as structured JSON for easy parsing and analysis
- **Configurable log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Component-based logging**: Each component gets its own logger instance
- **Rich context**: Logs include timestamps, component names, event types, and custom fields
- **Convenience methods**: Pre-built methods for common events (API requests, failovers, etc.)

#### Usage

```python
from src.utils.logger import get_logger

# Create logger for your component
logger = get_logger("MyComponent", "INFO")

# Log component lifecycle
logger.log_startup(version="1.0.0")
logger.log_shutdown()

# Log API requests
logger.log_api_request(
    provider="yfinance",
    endpoint="/quote/AAPL",
    status="success",
    latency_ms=125.5
)

# Log data freshness violations
logger.log_data_freshness_violation(
    symbol="AAPL",
    latency_seconds=45.2,
    provider="finnhub"
)

# Log failover events
logger.log_failover(
    from_provider="yfinance",
    to_provider="finnhub",
    reason="timeout"
)

# Log errors with stack traces
try:
    risky_operation()
except Exception as e:
    logger.error("operation_failed", "Operation failed", error=e)
```

#### Log Format

All logs follow this JSON structure:

```json
{
    "timestamp": "2024-01-15T08:30:45.123Z",
    "level": "WARNING",
    "component": "MarketMonitor",
    "event": "stale_data_detected",
    "symbol": "AAPL",
    "latency_seconds": 45.2,
    "provider": "finnhub",
    "message": "Stale data detected for AAPL from finnhub"
}
```

#### Critical Events Logged

- Component startup/shutdown
- All API requests (provider, endpoint, status, latency)
- Data freshness violations (symbol, latency)
- Failover events (from/to providers, reason)
- Newsletter generation and delivery
- Trading alert generation and delivery
- Performance metric updates
- Database connection status changes
- Memory usage warnings
- All errors with full stack traces

### 2. Error Handling and Resilience (`src/utils/error_handler.py`)

#### Components

##### DatabaseConnectionManager

Manages database connections with automatic reconnection logic.

```python
from src.utils.error_handler import DatabaseConnectionManager

# Create manager
manager = DatabaseConnectionManager("redis", reconnect_interval=30)

# Connect
def create_connection():
    return redis.Redis(host='localhost', port=6379)

manager.connect(create_connection)

# Execute operations with automatic reconnection
result = manager.execute_with_reconnect(
    lambda: redis_client.get("key"),
    create_connection
)
```

**Features:**
- Automatic reconnection every 30 seconds
- Graceful handling of connection failures
- Separate managers for Redis and PostgreSQL

##### WriteQueue

Queues database writes during PostgreSQL outages.

```python
from src.utils.error_handler import write_queue

# Queue writes during outage
write_queue.enqueue(db.insert, "data")

# Flush when connection restored
write_queue.flush()
```

**Features:**
- Queues up to 1000 writes in memory
- Thread-safe operation
- Automatic flushing when connection restored

##### MemoryMonitor

Monitors memory usage and triggers cleanup.

```python
from src.utils.error_handler import memory_monitor

# Check and cleanup if needed
memory_monitor.check_and_cleanup()

# Get current usage
current_mb = memory_monitor.get_memory_usage_mb()
```

**Features:**
- Warning threshold: 400 MB (standard cleanup)
- Critical threshold: 480 MB (aggressive cleanup)
- Automatic garbage collection
- Helps stay within 512 MB free hosting limit

##### GracefulDegradation

Tracks component degradation status.

```python
from src.utils.error_handler import GracefulDegradation

degradation = GracefulDegradation()

# Mark component as degraded
degradation.mark_degraded("DataManager", "Redis unavailable")

# Check status
if degradation.is_degraded("DataManager"):
    # Use fallback behavior
    pass

# Mark as recovered
degradation.mark_recovered("DataManager")
```

##### ResilientOperation

Wraps operations with fallback support.

```python
from src.utils.error_handler import ResilientOperation

operation = ResilientOperation("MyComponent")

result = operation.execute_with_fallback(
    primary_operation=lambda: fetch_from_api(),
    fallback_operation=lambda: fetch_from_cache(),
    operation_name="fetch_data"
)
```

**Features:**
- Automatic fallback on primary failure
- Tracks degradation status
- Comprehensive error logging

##### Network Error Handling

Handles network errors with retry and exponential backoff.

```python
from src.utils.error_handler import handle_network_error

result = handle_network_error(
    network_operation,
    max_retries=3,
    backoff_base=1.0  # 1s, 3s, 9s delays
)
```

##### Rate Limit Handling

Handles API rate limits by waiting for reset.

```python
from src.utils.error_handler import handle_rate_limit_error

# Wait until rate limit resets
handle_rate_limit_error(reset_time=datetime.now() + timedelta(seconds=60))
```

## Error Handling Patterns

### 1. Circuit Breaker Pattern

Already implemented in `BaseAPIClient` (see `src/clients/base_api_client.py`):

- **CLOSED**: Normal operation
- **OPEN**: Too many failures, reject requests
- **HALF_OPEN**: Testing recovery

### 2. Retry with Exponential Backoff

All network operations retry 3 times with delays: 1s, 3s, 9s

### 3. Graceful Degradation

System continues operating with reduced functionality:

- **Redis outage**: Continue without caching, use direct API calls
- **PostgreSQL outage**: Queue writes in memory (max 1000)
- **API failures**: Failover to alternative providers
- **Email failures**: Log for manual review

### 4. Failover Chains

Data sources have automatic failover:

```
yfinance → Finnhub → Twelve Data → Redis cache
```

## Requirements Validated

### Task 19: Logging System

✓ Structured logging with JSON format  
✓ Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL  
✓ Component startup/shutdown events  
✓ API requests with provider, endpoint, status, latency  
✓ Data freshness violations with symbol and latency  
✓ Failover events  
✓ Newsletter and alert generation/delivery  
✓ Performance metric updates  
✓ Database connection status changes  
✓ Memory usage warnings  
✓ All errors with full stack traces  

**Requirements: 10.5, 10.6, 11.1-11.7**

### Task 20: Error Handling

✓ CircuitBreaker pattern for API clients  
✓ Graceful degradation for component failures  
✓ Network errors with retry and failover  
✓ Rate limit errors with wait and retry  
✓ Database connection errors with reconnection attempts  
✓ Memory pressure with aggressive cleanup  
✓ Queue writes in memory (max 1000) during PostgreSQL outage  
✓ Continue with degraded service during Redis outage  

**Requirements: 10.1-10.6, 11.1-11.7**

## Testing

### Unit Tests

- **Logging**: `tests/test_logger.py` (24 tests)
- **Error Handling**: `tests/test_error_handler.py` (30 tests)

Run tests:

```bash
pytest tests/test_logger.py -v
pytest tests/test_error_handler.py -v
```

### Demo

See `examples/logging_error_handling_demo.py` for comprehensive examples.

Run demo:

```bash
PYTHONPATH=. python3 examples/logging_error_handling_demo.py
```

## Integration with Existing Components

All existing components should integrate these systems:

```python
from src.utils.logger import get_logger
from src.utils.error_handler import ResilientOperation, memory_monitor

class MyComponent:
    def __init__(self):
        self.logger = get_logger("MyComponent")
        self.resilient = ResilientOperation("MyComponent")
        
    def start(self):
        self.logger.log_startup()
        
        # Check memory periodically
        memory_monitor.check_and_cleanup()
        
    def fetch_data(self):
        return self.resilient.execute_with_fallback(
            primary_operation=self._fetch_from_api,
            fallback_operation=self._fetch_from_cache,
            operation_name="fetch_data"
        )
```

## Best Practices

1. **Always use structured logging**: Use the provided logger, not print statements
2. **Log at appropriate levels**: DEBUG for detailed flow, INFO for normal operations, WARNING for recoverable issues, ERROR for failures
3. **Include context**: Add relevant fields (symbol, provider, latency, etc.)
4. **Use resilient operations**: Wrap critical operations with fallback support
5. **Monitor memory**: Check memory usage in long-running operations
6. **Handle failures gracefully**: Continue operating with degraded functionality
7. **Log all errors**: Include full stack traces for debugging

## Performance Considerations

- **Structured logging**: Minimal overhead, JSON serialization is fast
- **Memory monitoring**: Uses psutil, very lightweight
- **Write queue**: Thread-safe, minimal memory overhead
- **Circuit breaker**: Prevents cascading failures, improves overall performance

## Future Enhancements

- Log aggregation to external service (e.g., Papertrail, Loggly)
- Metrics collection (e.g., Prometheus)
- Alerting on critical errors (e.g., PagerDuty)
- Distributed tracing (e.g., OpenTelemetry)
