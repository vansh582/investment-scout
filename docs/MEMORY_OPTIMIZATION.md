# Memory Optimization for Investment Scout

## Overview

The Memory Optimization module ensures Investment Scout operates within the 512 MB RAM constraint typical of free hosting platforms. It implements aggressive memory management strategies including cache eviction, lazy loading, streaming processing, and watchlist size limiting.

## Components

### 1. MemoryOptimizer

Central memory management component that monitors usage and triggers cleanup.

**Key Features:**
- Continuous memory monitoring
- Automatic cleanup at 400 MB threshold
- Aggressive cleanup at 480 MB critical threshold
- Redis cache eviction management
- Configurable cleanup intervals

**Usage:**

```python
from src.utils.memory_optimizer import get_memory_optimizer
import redis

# Initialize with Redis client
redis_client = redis.from_url("redis://localhost:6379")
optimizer = get_memory_optimizer(redis_client)

# Check memory and optimize if needed
result = optimizer.check_and_optimize()
print(f"Current memory: {result['current_mb']:.1f} MB")
print(f"Cleanup triggered: {result['cleanup_triggered']}")

# Manual memory check
current_mb = optimizer.get_memory_usage_mb()
print(f"Memory usage: {current_mb:.1f} MB")
```

**Memory Thresholds:**
- **Warning (400 MB)**: Standard cleanup (garbage collection + expired cache eviction)
- **Critical (480 MB)**: Aggressive cleanup (full GC + all quote cache eviction)
- **Maximum (512 MB)**: Platform limit

### 2. LazyDataLoader

Loads historical data on-demand in chunks to minimize memory footprint.

**Key Features:**
- Chunk-based data loading
- Iterator-based API (memory efficient)
- Configurable chunk sizes
- Support for quotes and news articles

**Usage:**

```python
from src.utils.memory_optimizer import LazyDataLoader
from src.utils.data_manager_scout import DataManager

# Initialize
data_manager = DataManager(redis_url, postgres_url)
loader = LazyDataLoader(data_manager)

# Load historical quotes in chunks
for chunk in loader.load_historical_quotes_lazy("AAPL", days=30, chunk_size=100):
    # Process chunk (max 100 quotes in memory at once)
    for quote in chunk:
        process_quote(quote)

# Load news articles in chunks
for chunk in loader.load_news_lazy(days=7, symbols=["AAPL", "MSFT"], chunk_size=50):
    # Process chunk (max 50 articles in memory at once)
    for article in chunk:
        analyze_sentiment(article)
```

**Benefits:**
- Processes large datasets without loading all into memory
- Reduces memory spikes during analysis
- Enables processing of unlimited historical data

### 3. StreamingProcessor

Processes data in streams to avoid loading entire datasets into memory.

**Key Features:**
- Stream-based processing
- Error handling for individual items
- Aggregation without full dataset in memory
- Composable processing pipelines

**Usage:**

```python
from src.utils.memory_optimizer import StreamingProcessor, LazyDataLoader

processor = StreamingProcessor()
loader = LazyDataLoader(data_manager)

# Stream processing with transformation
quote_iterator = loader.load_historical_quotes_lazy("AAPL", days=30)

def calculate_return(quote):
    return (quote["price"] - quote["bid"]) / quote["bid"]

returns = list(processor.process_quotes_stream(quote_iterator, calculate_return))

# Stream aggregation
quote_iterator = loader.load_historical_quotes_lazy("AAPL", days=30)

def sum_volumes(acc, quote):
    return (acc or 0) + quote["volume"]

total_volume = processor.aggregate_stream(quote_iterator, sum_volumes, initial_value=0)
```

**Benefits:**
- Process unlimited data with constant memory usage
- Graceful error handling (skip bad items, continue processing)
- Composable transformations

### 4. WatchlistManager

Manages watchlist size dynamically based on memory pressure.

**Key Features:**
- Dynamic size limiting (100-200 stocks)
- Priority-based symbol selection
- Memory-aware adjustments
- Real-time watchlist updates

**Usage:**

```python
from src.utils.memory_optimizer import WatchlistManager, get_memory_optimizer

optimizer = get_memory_optimizer(redis_client)
manager = WatchlistManager(optimizer)

# Update watchlist with priority scores
symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", ...]  # 300 symbols
priorities = {
    "AAPL": 0.95,
    "MSFT": 0.90,
    "GOOGL": 0.85,
    # ... priority scores for each symbol
}

# Manager will limit to 100-200 based on memory pressure
active_watchlist = manager.update_watchlist(symbols, priorities)
print(f"Active watchlist size: {len(active_watchlist)}")

# Check if symbol is being monitored
if manager.is_in_watchlist("AAPL"):
    print("AAPL is actively monitored")
```

**Size Limits:**
- **Normal memory (<400 MB)**: Up to 200 stocks
- **Warning memory (400-480 MB)**: Up to 150 stocks
- **Critical memory (>480 MB)**: Up to 100 stocks

### 5. OptimizedDataStructures

Memory-efficient data representations.

**Key Features:**
- Compact tuple representation for quotes
- Batch conversion utilities
- Round-trip conversion (dict ↔ tuple)
- Reduced memory footprint

**Usage:**

```python
from src.utils.memory_optimizer import OptimizedDataStructures

# Compact single quote
quote_dict = {
    "symbol": "AAPL",
    "price": Decimal("150.00"),
    "volume": 1000000,
    "exchange_timestamp": datetime.now()
}

compact = OptimizedDataStructures.compact_quote(quote_dict)
# compact is a tuple: ("AAPL", 150.0, 1000000, timestamp)

# Expand back to dict
expanded = OptimizedDataStructures.expand_quote(compact)

# Batch operations
quotes = [quote_dict1, quote_dict2, quote_dict3]
compact_list = OptimizedDataStructures.batch_compact_quotes(quotes)
```

**Memory Savings:**
- Tuples use ~30% less memory than dicts
- Useful for storing large collections of quotes
- Trade-off: Less readable, but more efficient

## Integration Examples

### Example 1: Memory-Aware Market Monitoring

```python
from src.utils.memory_optimizer import (
    get_memory_optimizer,
    WatchlistManager,
    LazyDataLoader
)

# Initialize components
optimizer = get_memory_optimizer(redis_client)
watchlist_mgr = WatchlistManager(optimizer)
loader = LazyDataLoader(data_manager)

# Update watchlist based on memory
all_symbols = get_all_tradeable_symbols()  # 1000+ symbols
priorities = calculate_priorities(all_symbols)
active_watchlist = watchlist_mgr.update_watchlist(all_symbols, priorities)

# Monitor memory periodically
while True:
    # Check and optimize memory
    result = optimizer.check_and_optimize()
    
    if result["cleanup_triggered"]:
        # Reduce watchlist if memory pressure
        active_watchlist = watchlist_mgr.update_watchlist(all_symbols, priorities)
    
    # Monitor active watchlist
    for symbol in active_watchlist:
        quote = fetch_quote(symbol)
        process_quote(quote)
    
    time.sleep(15)  # 15-second polling
```

### Example 2: Memory-Efficient Historical Analysis

```python
from src.utils.memory_optimizer import LazyDataLoader, StreamingProcessor

loader = LazyDataLoader(data_manager)
processor = StreamingProcessor()

# Analyze 90 days of data without loading all into memory
quote_iterator = loader.load_historical_quotes_lazy("AAPL", days=90, chunk_size=100)

# Calculate moving average in streaming fashion
def calculate_moving_avg(acc, quote):
    if acc is None:
        acc = {"prices": [], "sum": 0}
    
    acc["prices"].append(quote["price"])
    acc["sum"] += quote["price"]
    
    # Keep only last 20 prices for moving average
    if len(acc["prices"]) > 20:
        removed = acc["prices"].pop(0)
        acc["sum"] -= removed
    
    return acc

result = processor.aggregate_stream(quote_iterator, calculate_moving_avg)
moving_avg = result["sum"] / len(result["prices"])
```

### Example 3: Automatic Memory Management

```python
from src.utils.memory_optimizer import get_memory_optimizer

optimizer = get_memory_optimizer(redis_client)

# In main application loop
def main_loop():
    while True:
        # Perform work
        opportunities = analyze_market()
        
        # Periodic memory check (every 5 minutes)
        if optimizer.should_cleanup():
            result = optimizer.check_and_optimize()
            
            if result["threshold"] == "critical":
                # Reduce workload under critical memory
                reduce_active_monitoring()
        
        time.sleep(60)
```

## Best Practices

### 1. Always Use Lazy Loading for Historical Data

❌ **Bad:**
```python
# Loads all 90 days into memory at once
quotes = data_manager.get_historical_quotes("AAPL", days=90)
for quote in quotes:
    process(quote)
```

✅ **Good:**
```python
# Loads in chunks, processes incrementally
loader = LazyDataLoader(data_manager)
for chunk in loader.load_historical_quotes_lazy("AAPL", days=90, chunk_size=100):
    for quote in chunk:
        process(quote)
```

### 2. Monitor Memory Regularly

```python
# Check memory every 5 minutes
optimizer = get_memory_optimizer(redis_client)

if optimizer.should_cleanup():
    optimizer.check_and_optimize()
```

### 3. Use Streaming for Large Aggregations

❌ **Bad:**
```python
# Loads all data, then aggregates
all_quotes = fetch_all_quotes()
total = sum(q["volume"] for q in all_quotes)
```

✅ **Good:**
```python
# Streams data, aggregates incrementally
processor = StreamingProcessor()
quote_iterator = loader.load_historical_quotes_lazy("AAPL", days=90)
total = processor.aggregate_stream(
    quote_iterator,
    lambda acc, q: (acc or 0) + q["volume"],
    initial_value=0
)
```

### 4. Limit Active Watchlist Dynamically

```python
# Adjust watchlist based on memory pressure
watchlist_mgr = WatchlistManager(optimizer)
active = watchlist_mgr.update_watchlist(all_symbols, priorities)

# Watchlist automatically shrinks under memory pressure
```

### 5. Use Compact Data Structures for Large Collections

```python
# When storing many quotes in memory
quotes = fetch_recent_quotes()
compact_quotes = OptimizedDataStructures.batch_compact_quotes(quotes)

# Use compact representation for storage
# Expand only when needed for processing
```

## Memory Budget Allocation

For 512 MB total RAM:

| Component | Budget | Purpose |
|-----------|--------|---------|
| Python Runtime | ~50 MB | Base Python + libraries |
| Redis Cache | ~100 MB | Hot quote data (15s/60s TTL) |
| Active Watchlist | ~50 MB | 100-200 stocks being monitored |
| Analysis Buffers | ~100 MB | Temporary data during analysis |
| Database Connections | ~50 MB | PostgreSQL connection pool |
| Working Set | ~100 MB | Application logic and processing |
| **Reserve** | ~62 MB | Safety margin for spikes |

**Total: 512 MB**

## Monitoring and Alerts

### Memory Usage Logging

The memory optimizer logs all significant events:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "WARNING",
  "component": "MemoryOptimizer",
  "event": "memory_warning",
  "current_mb": 420.5,
  "threshold_mb": 400.0,
  "message": "Memory usage 420.5 MB exceeds warning threshold 400.0 MB"
}
```

### Cleanup Events

```json
{
  "timestamp": "2024-01-15T10:30:01Z",
  "level": "INFO",
  "component": "MemoryOptimizer",
  "event": "memory_cleanup_complete",
  "memory_mb": 380.2,
  "message": "Standard cleanup complete: 380.2 MB"
}
```

## Performance Impact

### Memory Optimization Overhead

- **Memory monitoring**: <1ms per check
- **Standard cleanup**: 10-50ms (garbage collection)
- **Aggressive cleanup**: 50-200ms (full GC + cache eviction)
- **Lazy loading**: Minimal overhead, iterator-based
- **Streaming processing**: Constant memory, slight CPU increase

### Trade-offs

| Strategy | Memory Savings | Performance Impact |
|----------|----------------|-------------------|
| Lazy Loading | 70-90% | Minimal (iterator overhead) |
| Streaming | 80-95% | Slight (incremental processing) |
| Cache Eviction | 50-100 MB | None (Redis handles TTL) |
| Watchlist Limiting | 20-50 MB | None (fewer API calls) |
| Compact Structures | 30% | Minimal (conversion overhead) |

## Troubleshooting

### Issue: Memory Still Exceeds 512 MB

**Diagnosis:**
```python
optimizer = get_memory_optimizer()
current = optimizer.get_memory_usage_mb()
print(f"Current: {current} MB")
```

**Solutions:**
1. Reduce watchlist size manually
2. Increase cleanup frequency
3. Reduce chunk sizes in lazy loading
4. Clear Redis cache completely

### Issue: Frequent Cleanup Cycles

**Diagnosis:** Check cleanup frequency in logs

**Solutions:**
1. Increase cleanup interval
2. Reduce active watchlist size
3. Use more aggressive cache TTLs
4. Optimize data structures

### Issue: Out of Memory Errors

**Emergency Actions:**
```python
# Force aggressive cleanup
optimizer._aggressive_cleanup()

# Clear all Redis cache
if optimizer.redis_client:
    optimizer.redis_client.flushdb()

# Reduce watchlist to minimum
watchlist_mgr.update_watchlist(symbols[:100])
```

## Testing

Run memory optimization tests:

```bash
python3 -m pytest tests/test_memory_optimizer.py -v
```

All 27 tests should pass, covering:
- Memory monitoring and thresholds
- Cache eviction strategies
- Lazy loading functionality
- Streaming processing
- Watchlist management
- Data structure optimization

## Summary

The Memory Optimization module ensures Investment Scout operates reliably within 512 MB RAM constraints through:

1. **Continuous Monitoring**: Track memory usage and trigger cleanup at 400 MB
2. **Lazy Loading**: Load historical data in chunks, not all at once
3. **Streaming Processing**: Process unlimited data with constant memory
4. **Dynamic Watchlist**: Adjust monitoring scope based on memory pressure
5. **Efficient Structures**: Use compact representations for large collections

These strategies enable the system to handle large-scale market monitoring and analysis on free hosting platforms with strict memory limits.
