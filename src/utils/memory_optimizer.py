"""
Memory Optimization for Investment Scout

Implements aggressive memory management to operate within 512 MB RAM constraints:
- Aggressive cache eviction in Redis
- Lazy loading for historical data
- Streaming processing for large datasets
- Watchlist size limits (100-200 stocks)
- Memory monitoring with cleanup at 400 MB threshold
- Optimized data structures
"""

import gc
import logging
from typing import List, Dict, Optional, Iterator, Any
from datetime import datetime, timedelta
from decimal import Decimal
import psutil
import redis

from src.utils.logger import get_logger


logger = get_logger(__name__)


class MemoryOptimizer:
    """
    Central memory optimization manager for Investment Scout.
    
    Ensures system operates within 512 MB RAM constraint by:
    - Monitoring memory usage continuously
    - Triggering cleanup at 400 MB threshold
    - Managing cache eviction policies
    - Limiting active data structures
    """
    
    # Memory thresholds (in MB)
    WARNING_THRESHOLD = 400.0
    CRITICAL_THRESHOLD = 480.0
    MAX_MEMORY = 512.0
    
    # Watchlist limits
    MIN_WATCHLIST_SIZE = 100
    MAX_WATCHLIST_SIZE = 200
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize memory optimizer.
        
        Args:
            redis_client: Optional Redis client for cache management
        """
        self.redis_client = redis_client
        self.process = psutil.Process()
        self.logger = get_logger("MemoryOptimizer")
        self._last_cleanup = datetime.now()
        self._cleanup_interval = timedelta(minutes=5)
        
    def get_memory_usage_mb(self) -> float:
        """
        Get current memory usage in MB.
        
        Returns:
            Memory usage in megabytes
        """
        return self.process.memory_info().rss / (1024 * 1024)
    
    def check_and_optimize(self) -> Dict[str, Any]:
        """
        Check memory usage and optimize if needed.
        
        Returns:
            Dictionary with optimization results
        """
        current_mb = self.get_memory_usage_mb()
        
        result = {
            "current_mb": current_mb,
            "threshold": None,
            "action_taken": None,
            "cleanup_triggered": False
        }
        
        if current_mb >= self.CRITICAL_THRESHOLD:
            self.logger.warning(
                "memory_critical",
                f"Memory usage {current_mb:.1f} MB exceeds critical threshold {self.CRITICAL_THRESHOLD:.1f} MB",
                current_mb=current_mb,
                threshold_mb=self.CRITICAL_THRESHOLD
            )
            self._aggressive_cleanup()
            result["threshold"] = "critical"
            result["action_taken"] = "aggressive_cleanup"
            result["cleanup_triggered"] = True
            
        elif current_mb >= self.WARNING_THRESHOLD:
            self.logger.warning(
                "memory_warning",
                f"Memory usage {current_mb:.1f} MB exceeds warning threshold {self.WARNING_THRESHOLD:.1f} MB",
                current_mb=current_mb,
                threshold_mb=self.WARNING_THRESHOLD
            )
            self._standard_cleanup()
            result["threshold"] = "warning"
            result["action_taken"] = "standard_cleanup"
            result["cleanup_triggered"] = True
        
        return result
    
    def _standard_cleanup(self) -> None:
        """Perform standard memory cleanup"""
        self.logger.info("memory_cleanup", "Performing standard memory cleanup")
        
        # Garbage collection
        gc.collect()
        
        # Evict old cache entries if Redis available
        if self.redis_client:
            self._evict_expired_cache()
        
        after_mb = self.get_memory_usage_mb()
        self.logger.info(
            "memory_cleanup_complete",
            f"Standard cleanup complete: {after_mb:.1f} MB",
            memory_mb=after_mb
        )
        self._last_cleanup = datetime.now()
    
    def _aggressive_cleanup(self) -> None:
        """Perform aggressive memory cleanup"""
        self.logger.warning(
            "memory_cleanup_aggressive",
            "Performing aggressive memory cleanup"
        )
        
        # Full garbage collection
        gc.collect(generation=2)
        
        # Aggressive cache eviction if Redis available
        if self.redis_client:
            self._aggressive_cache_eviction()
        
        after_mb = self.get_memory_usage_mb()
        self.logger.info(
            "memory_cleanup_complete",
            f"Aggressive cleanup complete: {after_mb:.1f} MB",
            memory_mb=after_mb
        )
        self._last_cleanup = datetime.now()
    
    def _evict_expired_cache(self) -> None:
        """Evict expired cache entries from Redis"""
        if not self.redis_client:
            return
        
        try:
            # Redis automatically evicts expired keys, but we can help by
            # scanning for keys with very short TTL and deleting them
            cursor = 0
            evicted = 0
            
            while True:
                cursor, keys = self.redis_client.scan(cursor, match="quote:*", count=100)
                
                for key in keys:
                    ttl = self.redis_client.ttl(key)
                    # Evict keys with less than 5 seconds TTL
                    if 0 < ttl < 5:
                        self.redis_client.delete(key)
                        evicted += 1
                
                if cursor == 0:
                    break
            
            if evicted > 0:
                self.logger.debug(
                    "cache_eviction",
                    f"Evicted {evicted} near-expired cache entries",
                    evicted_count=evicted
                )
        except Exception as e:
            self.logger.error("cache_eviction_error", f"Error during cache eviction: {e}")
    
    def _aggressive_cache_eviction(self) -> None:
        """Aggressively evict cache entries to free memory"""
        if not self.redis_client:
            return
        
        try:
            # Delete all quote cache entries (they'll be refetched as needed)
            cursor = 0
            evicted = 0
            
            while True:
                cursor, keys = self.redis_client.scan(cursor, match="quote:*", count=100)
                
                if keys:
                    self.redis_client.delete(*keys)
                    evicted += len(keys)
                
                if cursor == 0:
                    break
            
            self.logger.warning(
                "aggressive_cache_eviction",
                f"Aggressively evicted {evicted} cache entries",
                evicted_count=evicted
            )
        except Exception as e:
            self.logger.error("aggressive_cache_eviction_error", f"Error during aggressive cache eviction: {e}")
    
    def should_cleanup(self) -> bool:
        """
        Check if cleanup should be performed based on time interval.
        
        Returns:
            True if cleanup interval has elapsed
        """
        return datetime.now() - self._last_cleanup >= self._cleanup_interval


class LazyDataLoader:
    """
    Lazy loading for historical data to minimize memory footprint.
    
    Loads data on-demand in chunks rather than loading entire datasets.
    """
    
    def __init__(self, data_manager):
        """
        Initialize lazy data loader.
        
        Args:
            data_manager: DataManager instance for database access
        """
        self.data_manager = data_manager
        self.logger = get_logger("LazyDataLoader")
    
    def load_historical_quotes_lazy(
        self,
        symbol: str,
        days: int = 30,
        chunk_size: int = 100
    ) -> Iterator[List[Dict]]:
        """
        Lazily load historical quotes in chunks.
        
        Args:
            symbol: Stock symbol
            days: Number of days of history
            chunk_size: Number of records per chunk
            
        Yields:
            Chunks of historical quote data
        """
        conn = self.data_manager.pg_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT symbol, price, bid, ask, volume, 
                           exchange_timestamp, received_timestamp
                    FROM historical_quotes
                    WHERE symbol = %s 
                    AND exchange_timestamp >= NOW() - INTERVAL '%s days'
                    ORDER BY exchange_timestamp DESC
                """, (symbol, days))
                
                while True:
                    chunk = cur.fetchmany(chunk_size)
                    if not chunk:
                        break
                    
                    # Convert to list of dicts
                    chunk_data = [
                        {
                            "symbol": row[0],
                            "price": row[1],
                            "bid": row[2],
                            "ask": row[3],
                            "volume": row[4],
                            "exchange_timestamp": row[5],
                            "received_timestamp": row[6]
                        }
                        for row in chunk
                    ]
                    
                    yield chunk_data
                    
        finally:
            self.data_manager.pg_pool.putconn(conn)
    
    def load_news_lazy(
        self,
        days: int = 7,
        symbols: Optional[List[str]] = None,
        chunk_size: int = 50
    ) -> Iterator[List[Dict]]:
        """
        Lazily load news articles in chunks.
        
        Args:
            days: Number of days of news
            symbols: Optional list of symbols to filter
            chunk_size: Number of articles per chunk
            
        Yields:
            Chunks of news article data
        """
        conn = self.data_manager.pg_pool.getconn()
        try:
            with conn.cursor() as cur:
                if symbols:
                    cur.execute("""
                        SELECT title, summary, source, published_at, url, sentiment, symbols
                        FROM news_articles
                        WHERE published_at >= NOW() - INTERVAL '%s days'
                        AND symbols && %s
                        ORDER BY published_at DESC
                    """, (days, symbols))
                else:
                    cur.execute("""
                        SELECT title, summary, source, published_at, url, sentiment, symbols
                        FROM news_articles
                        WHERE published_at >= NOW() - INTERVAL '%s days'
                        ORDER BY published_at DESC
                    """, (days,))
                
                while True:
                    chunk = cur.fetchmany(chunk_size)
                    if not chunk:
                        break
                    
                    chunk_data = [
                        {
                            "title": row[0],
                            "summary": row[1],
                            "source": row[2],
                            "published_at": row[3],
                            "url": row[4],
                            "sentiment": row[5],
                            "symbols": row[6]
                        }
                        for row in chunk
                    ]
                    
                    yield chunk_data
                    
        finally:
            self.data_manager.pg_pool.putconn(conn)


class StreamingProcessor:
    """
    Streaming processor for large datasets.
    
    Processes data in streams to avoid loading entire datasets into memory.
    """
    
    def __init__(self):
        self.logger = get_logger("StreamingProcessor")
    
    def process_quotes_stream(
        self,
        quote_iterator: Iterator[List[Dict]],
        processor_func: callable
    ) -> Iterator[Any]:
        """
        Process quotes in streaming fashion.
        
        Args:
            quote_iterator: Iterator yielding quote chunks
            processor_func: Function to process each quote
            
        Yields:
            Processed results
        """
        for chunk in quote_iterator:
            for quote in chunk:
                try:
                    result = processor_func(quote)
                    if result is not None:
                        yield result
                except Exception as e:
                    self.logger.error(
                        "stream_processing_error",
                        f"Error processing quote: {e}",
                        symbol=quote.get("symbol")
                    )
    
    def aggregate_stream(
        self,
        data_iterator: Iterator[List[Dict]],
        aggregator_func: callable,
        initial_value: Any = None
    ) -> Any:
        """
        Aggregate streaming data without loading all into memory.
        
        Args:
            data_iterator: Iterator yielding data chunks
            aggregator_func: Function to aggregate data (takes accumulator and item)
            initial_value: Initial accumulator value
            
        Returns:
            Aggregated result
        """
        accumulator = initial_value
        
        for chunk in data_iterator:
            for item in chunk:
                try:
                    accumulator = aggregator_func(accumulator, item)
                except Exception as e:
                    self.logger.error(
                        "stream_aggregation_error",
                        f"Error aggregating item: {e}"
                    )
        
        return accumulator


class WatchlistManager:
    """
    Manages watchlist size to stay within memory constraints.
    
    Limits active watchlist to 100-200 stocks based on memory pressure.
    """
    
    MIN_SIZE = 100
    MAX_SIZE = 200
    
    def __init__(self, memory_optimizer: MemoryOptimizer):
        """
        Initialize watchlist manager.
        
        Args:
            memory_optimizer: MemoryOptimizer instance
        """
        self.memory_optimizer = memory_optimizer
        self.logger = get_logger("WatchlistManager")
        self._active_watchlist: List[str] = []
    
    def update_watchlist(self, symbols: List[str], priorities: Optional[Dict[str, float]] = None) -> List[str]:
        """
        Update watchlist with memory-aware size limiting.
        
        Args:
            symbols: List of symbols to monitor
            priorities: Optional priority scores for each symbol
            
        Returns:
            Final watchlist (may be truncated)
        """
        current_memory = self.memory_optimizer.get_memory_usage_mb()
        
        # Determine target size based on memory pressure
        if current_memory >= self.memory_optimizer.CRITICAL_THRESHOLD:
            target_size = self.MIN_SIZE
            self.logger.warning(
                "watchlist_reduced",
                f"Reducing watchlist to {target_size} due to critical memory pressure",
                current_memory_mb=current_memory
            )
        elif current_memory >= self.memory_optimizer.WARNING_THRESHOLD:
            target_size = int((self.MIN_SIZE + self.MAX_SIZE) / 2)
            self.logger.info(
                "watchlist_limited",
                f"Limiting watchlist to {target_size} due to memory warning",
                current_memory_mb=current_memory
            )
        else:
            target_size = self.MAX_SIZE
        
        # Sort by priority if provided
        if priorities:
            sorted_symbols = sorted(
                symbols,
                key=lambda s: priorities.get(s, 0.0),
                reverse=True
            )
        else:
            sorted_symbols = symbols
        
        # Truncate to target size
        self._active_watchlist = sorted_symbols[:target_size]
        
        if len(symbols) > target_size:
            self.logger.info(
                "watchlist_truncated",
                f"Watchlist truncated from {len(symbols)} to {target_size} symbols",
                original_size=len(symbols),
                final_size=target_size
            )
        
        return self._active_watchlist
    
    def get_active_watchlist(self) -> List[str]:
        """
        Get current active watchlist.
        
        Returns:
            List of active symbols
        """
        return self._active_watchlist.copy()
    
    def is_in_watchlist(self, symbol: str) -> bool:
        """
        Check if symbol is in active watchlist.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if in watchlist
        """
        return symbol in self._active_watchlist


class OptimizedDataStructures:
    """
    Memory-optimized data structures for Investment Scout.
    
    Uses efficient data representations to minimize memory footprint.
    """
    
    @staticmethod
    def compact_quote(quote_dict: Dict) -> tuple:
        """
        Convert quote dict to compact tuple representation.
        
        Args:
            quote_dict: Quote as dictionary
            
        Returns:
            Compact tuple (symbol, price, volume, timestamp)
        """
        return (
            quote_dict["symbol"],
            float(quote_dict["price"]),
            quote_dict["volume"],
            quote_dict["exchange_timestamp"]
        )
    
    @staticmethod
    def expand_quote(compact: tuple) -> Dict:
        """
        Expand compact quote tuple back to dictionary.
        
        Args:
            compact: Compact tuple representation
            
        Returns:
            Quote dictionary
        """
        return {
            "symbol": compact[0],
            "price": Decimal(str(compact[1])),
            "volume": compact[2],
            "exchange_timestamp": compact[3]
        }
    
    @staticmethod
    def batch_compact_quotes(quotes: List[Dict]) -> List[tuple]:
        """
        Batch convert quotes to compact representation.
        
        Args:
            quotes: List of quote dictionaries
            
        Returns:
            List of compact tuples
        """
        return [OptimizedDataStructures.compact_quote(q) for q in quotes]


# Global memory optimizer instance
_global_memory_optimizer: Optional[MemoryOptimizer] = None


def get_memory_optimizer(redis_client: Optional[redis.Redis] = None) -> MemoryOptimizer:
    """
    Get or create global memory optimizer instance.
    
    Args:
        redis_client: Optional Redis client
        
    Returns:
        MemoryOptimizer instance
    """
    global _global_memory_optimizer
    
    if _global_memory_optimizer is None:
        _global_memory_optimizer = MemoryOptimizer(redis_client)
    
    return _global_memory_optimizer
