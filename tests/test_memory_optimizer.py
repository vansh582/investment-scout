"""
Tests for Memory Optimizer

Tests memory optimization features including:
- Memory monitoring and cleanup
- Lazy data loading
- Streaming processing
- Watchlist management
- Optimized data structures
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from src.utils.memory_optimizer import (
    MemoryOptimizer,
    LazyDataLoader,
    StreamingProcessor,
    WatchlistManager,
    OptimizedDataStructures,
    get_memory_optimizer
)


class TestMemoryOptimizer:
    """Test MemoryOptimizer class"""
    
    def test_initialization(self):
        """Test memory optimizer initialization"""
        optimizer = MemoryOptimizer()
        
        assert optimizer.WARNING_THRESHOLD == 400.0
        assert optimizer.CRITICAL_THRESHOLD == 480.0
        assert optimizer.MAX_MEMORY == 512.0
        assert optimizer.MIN_WATCHLIST_SIZE == 100
        assert optimizer.MAX_WATCHLIST_SIZE == 200
    
    def test_get_memory_usage(self):
        """Test memory usage retrieval"""
        optimizer = MemoryOptimizer()
        
        memory_mb = optimizer.get_memory_usage_mb()
        
        assert isinstance(memory_mb, float)
        assert memory_mb > 0
    
    @patch('src.utils.memory_optimizer.MemoryOptimizer.get_memory_usage_mb')
    def test_check_and_optimize_below_threshold(self, mock_memory):
        """Test optimization when memory is below threshold"""
        mock_memory.return_value = 300.0
        optimizer = MemoryOptimizer()
        
        result = optimizer.check_and_optimize()
        
        assert result["current_mb"] == 300.0
        assert result["threshold"] is None
        assert result["action_taken"] is None
        assert result["cleanup_triggered"] is False
    
    @patch('src.utils.memory_optimizer.MemoryOptimizer.get_memory_usage_mb')
    @patch('src.utils.memory_optimizer.gc.collect')
    def test_check_and_optimize_warning_threshold(self, mock_gc, mock_memory):
        """Test optimization at warning threshold"""
        mock_memory.return_value = 420.0
        optimizer = MemoryOptimizer()
        
        result = optimizer.check_and_optimize()
        
        assert result["current_mb"] == 420.0
        assert result["threshold"] == "warning"
        assert result["action_taken"] == "standard_cleanup"
        assert result["cleanup_triggered"] is True
        mock_gc.assert_called_once()
    
    @patch('src.utils.memory_optimizer.MemoryOptimizer.get_memory_usage_mb')
    @patch('src.utils.memory_optimizer.gc.collect')
    def test_check_and_optimize_critical_threshold(self, mock_gc, mock_memory):
        """Test optimization at critical threshold"""
        mock_memory.return_value = 490.0
        optimizer = MemoryOptimizer()
        
        result = optimizer.check_and_optimize()
        
        assert result["current_mb"] == 490.0
        assert result["threshold"] == "critical"
        assert result["action_taken"] == "aggressive_cleanup"
        assert result["cleanup_triggered"] is True
        mock_gc.assert_called_once_with(generation=2)
    
    def test_evict_expired_cache(self):
        """Test cache eviction for near-expired entries"""
        mock_redis = Mock()
        mock_redis.scan.side_effect = [
            (0, [b"quote:AAPL", b"quote:MSFT", b"quote:GOOGL"])
        ]
        mock_redis.ttl.side_effect = [3, 10, 2]  # AAPL and GOOGL should be evicted
        
        optimizer = MemoryOptimizer(redis_client=mock_redis)
        optimizer._evict_expired_cache()
        
        # Should delete keys with TTL < 5
        assert mock_redis.delete.call_count == 2
    
    def test_aggressive_cache_eviction(self):
        """Test aggressive cache eviction"""
        mock_redis = Mock()
        mock_redis.scan.side_effect = [
            (0, [b"quote:AAPL", b"quote:MSFT"])
        ]
        
        optimizer = MemoryOptimizer(redis_client=mock_redis)
        optimizer._aggressive_cache_eviction()
        
        # Should delete all quote keys
        mock_redis.delete.assert_called_once()
    
    def test_should_cleanup_interval(self):
        """Test cleanup interval checking"""
        optimizer = MemoryOptimizer()
        
        # Just cleaned up
        assert not optimizer.should_cleanup()
        
        # Simulate time passing
        optimizer._last_cleanup = datetime.now() - timedelta(minutes=6)
        assert optimizer.should_cleanup()


class TestLazyDataLoader:
    """Test LazyDataLoader class"""
    
    def test_initialization(self):
        """Test lazy data loader initialization"""
        mock_dm = Mock()
        loader = LazyDataLoader(mock_dm)
        
        assert loader.data_manager == mock_dm
    
    def test_load_historical_quotes_lazy(self):
        """Test lazy loading of historical quotes"""
        mock_dm = Mock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Mock database responses
        mock_cursor.fetchmany.side_effect = [
            [
                ("AAPL", Decimal("150.00"), Decimal("149.90"), Decimal("150.10"), 1000000,
                 datetime(2024, 1, 1, 10, 0), datetime(2024, 1, 1, 10, 0, 5))
            ],
            [
                ("AAPL", Decimal("151.00"), Decimal("150.90"), Decimal("151.10"), 1100000,
                 datetime(2024, 1, 1, 11, 0), datetime(2024, 1, 1, 11, 0, 5))
            ],
            []  # End of data
        ]
        
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_dm.pg_pool.getconn.return_value = mock_conn
        
        loader = LazyDataLoader(mock_dm)
        chunks = list(loader.load_historical_quotes_lazy("AAPL", days=30, chunk_size=1))
        
        assert len(chunks) == 2
        assert chunks[0][0]["symbol"] == "AAPL"
        assert chunks[0][0]["price"] == Decimal("150.00")
        assert chunks[1][0]["price"] == Decimal("151.00")
    
    def test_load_news_lazy(self):
        """Test lazy loading of news articles"""
        mock_dm = Mock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Mock database responses
        mock_cursor.fetchmany.side_effect = [
            [
                ("Title 1", "Summary 1", "Source 1", datetime(2024, 1, 1),
                 "http://example.com/1", 0.5, ["AAPL"])
            ],
            [
                ("Title 2", "Summary 2", "Source 2", datetime(2024, 1, 2),
                 "http://example.com/2", -0.3, ["MSFT"])
            ],
            []  # End of data
        ]
        
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_dm.pg_pool.getconn.return_value = mock_conn
        
        loader = LazyDataLoader(mock_dm)
        chunks = list(loader.load_news_lazy(days=7, chunk_size=1))
        
        assert len(chunks) == 2
        assert chunks[0][0]["title"] == "Title 1"
        assert chunks[0][0]["sentiment"] == 0.5
        assert chunks[1][0]["sentiment"] == -0.3


class TestStreamingProcessor:
    """Test StreamingProcessor class"""
    
    def test_process_quotes_stream(self):
        """Test streaming quote processing"""
        processor = StreamingProcessor()
        
        # Create mock iterator
        def quote_iterator():
            yield [{"symbol": "AAPL", "price": 150.0}]
            yield [{"symbol": "MSFT", "price": 300.0}]
        
        # Process with simple function
        def double_price(quote):
            return quote["price"] * 2
        
        results = list(processor.process_quotes_stream(quote_iterator(), double_price))
        
        assert len(results) == 2
        assert results[0] == 300.0
        assert results[1] == 600.0
    
    def test_process_quotes_stream_with_error(self):
        """Test streaming processing handles errors gracefully"""
        processor = StreamingProcessor()
        
        def quote_iterator():
            yield [{"symbol": "AAPL", "price": 150.0}]
            yield [{"symbol": "INVALID"}]  # Missing price
            yield [{"symbol": "MSFT", "price": 300.0}]
        
        def get_price(quote):
            return quote["price"]
        
        results = list(processor.process_quotes_stream(quote_iterator(), get_price))
        
        # Should skip the invalid quote
        assert len(results) == 2
        assert results[0] == 150.0
        assert results[1] == 300.0
    
    def test_aggregate_stream(self):
        """Test streaming aggregation"""
        processor = StreamingProcessor()
        
        def data_iterator():
            yield [{"value": 10}, {"value": 20}]
            yield [{"value": 30}, {"value": 40}]
        
        def sum_values(acc, item):
            return (acc or 0) + item["value"]
        
        result = processor.aggregate_stream(data_iterator(), sum_values, initial_value=0)
        
        assert result == 100
    
    def test_aggregate_stream_with_error(self):
        """Test streaming aggregation handles errors"""
        processor = StreamingProcessor()
        
        def data_iterator():
            yield [{"value": 10}]
            yield [{"invalid": "data"}]  # Missing value
            yield [{"value": 20}]
        
        def sum_values(acc, item):
            return acc + item["value"]
        
        result = processor.aggregate_stream(data_iterator(), sum_values, initial_value=0)
        
        # Should skip invalid item
        assert result == 30


class TestWatchlistManager:
    """Test WatchlistManager class"""
    
    @patch('src.utils.memory_optimizer.MemoryOptimizer.get_memory_usage_mb')
    def test_update_watchlist_normal_memory(self, mock_memory):
        """Test watchlist update with normal memory usage"""
        mock_memory.return_value = 300.0
        optimizer = MemoryOptimizer()
        manager = WatchlistManager(optimizer)
        
        symbols = [f"SYM{i}" for i in range(250)]
        watchlist = manager.update_watchlist(symbols)
        
        # Should allow max size
        assert len(watchlist) == 200
    
    @patch('src.utils.memory_optimizer.MemoryOptimizer.get_memory_usage_mb')
    def test_update_watchlist_warning_memory(self, mock_memory):
        """Test watchlist update with warning memory usage"""
        mock_memory.return_value = 420.0
        optimizer = MemoryOptimizer()
        manager = WatchlistManager(optimizer)
        
        symbols = [f"SYM{i}" for i in range(250)]
        watchlist = manager.update_watchlist(symbols)
        
        # Should limit to middle size
        assert len(watchlist) == 150
    
    @patch('src.utils.memory_optimizer.MemoryOptimizer.get_memory_usage_mb')
    def test_update_watchlist_critical_memory(self, mock_memory):
        """Test watchlist update with critical memory usage"""
        mock_memory.return_value = 490.0
        optimizer = MemoryOptimizer()
        manager = WatchlistManager(optimizer)
        
        symbols = [f"SYM{i}" for i in range(250)]
        watchlist = manager.update_watchlist(symbols)
        
        # Should limit to minimum size
        assert len(watchlist) == 100
    
    @patch('src.utils.memory_optimizer.MemoryOptimizer.get_memory_usage_mb')
    def test_update_watchlist_with_priorities(self, mock_memory):
        """Test watchlist update with priority sorting"""
        mock_memory.return_value = 300.0
        optimizer = MemoryOptimizer()
        manager = WatchlistManager(optimizer)
        
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
        priorities = {"AAPL": 0.9, "MSFT": 0.5, "GOOGL": 0.8, "TSLA": 0.7}
        
        watchlist = manager.update_watchlist(symbols, priorities)
        
        # Should be sorted by priority
        assert watchlist[0] == "AAPL"  # Highest priority
        assert watchlist[1] == "GOOGL"
        assert watchlist[2] == "TSLA"
        assert watchlist[3] == "MSFT"  # Lowest priority
    
    @patch('src.utils.memory_optimizer.MemoryOptimizer.get_memory_usage_mb')
    def test_get_active_watchlist(self, mock_memory):
        """Test getting active watchlist"""
        mock_memory.return_value = 300.0
        optimizer = MemoryOptimizer()
        manager = WatchlistManager(optimizer)
        
        symbols = ["AAPL", "MSFT", "GOOGL"]
        manager.update_watchlist(symbols)
        
        watchlist = manager.get_active_watchlist()
        
        assert len(watchlist) == 3
        assert "AAPL" in watchlist
    
    @patch('src.utils.memory_optimizer.MemoryOptimizer.get_memory_usage_mb')
    def test_is_in_watchlist(self, mock_memory):
        """Test checking if symbol is in watchlist"""
        mock_memory.return_value = 300.0
        optimizer = MemoryOptimizer()
        manager = WatchlistManager(optimizer)
        
        symbols = ["AAPL", "MSFT", "GOOGL"]
        manager.update_watchlist(symbols)
        
        assert manager.is_in_watchlist("AAPL")
        assert manager.is_in_watchlist("MSFT")
        assert not manager.is_in_watchlist("TSLA")


class TestOptimizedDataStructures:
    """Test OptimizedDataStructures class"""
    
    def test_compact_quote(self):
        """Test quote compaction"""
        quote_dict = {
            "symbol": "AAPL",
            "price": Decimal("150.00"),
            "volume": 1000000,
            "exchange_timestamp": datetime(2024, 1, 1, 10, 0)
        }
        
        compact = OptimizedDataStructures.compact_quote(quote_dict)
        
        assert compact[0] == "AAPL"
        assert compact[1] == 150.0
        assert compact[2] == 1000000
        assert compact[3] == datetime(2024, 1, 1, 10, 0)
    
    def test_expand_quote(self):
        """Test quote expansion"""
        compact = (
            "AAPL",
            150.0,
            1000000,
            datetime(2024, 1, 1, 10, 0)
        )
        
        quote_dict = OptimizedDataStructures.expand_quote(compact)
        
        assert quote_dict["symbol"] == "AAPL"
        assert quote_dict["price"] == Decimal("150.0")
        assert quote_dict["volume"] == 1000000
        assert quote_dict["exchange_timestamp"] == datetime(2024, 1, 1, 10, 0)
    
    def test_batch_compact_quotes(self):
        """Test batch quote compaction"""
        quotes = [
            {
                "symbol": "AAPL",
                "price": Decimal("150.00"),
                "volume": 1000000,
                "exchange_timestamp": datetime(2024, 1, 1, 10, 0)
            },
            {
                "symbol": "MSFT",
                "price": Decimal("300.00"),
                "volume": 2000000,
                "exchange_timestamp": datetime(2024, 1, 1, 10, 0)
            }
        ]
        
        compact_list = OptimizedDataStructures.batch_compact_quotes(quotes)
        
        assert len(compact_list) == 2
        assert compact_list[0][0] == "AAPL"
        assert compact_list[1][0] == "MSFT"
    
    def test_round_trip_conversion(self):
        """Test compact and expand round trip"""
        original = {
            "symbol": "AAPL",
            "price": Decimal("150.00"),
            "volume": 1000000,
            "exchange_timestamp": datetime(2024, 1, 1, 10, 0)
        }
        
        compact = OptimizedDataStructures.compact_quote(original)
        expanded = OptimizedDataStructures.expand_quote(compact)
        
        assert expanded["symbol"] == original["symbol"]
        assert expanded["price"] == original["price"]
        assert expanded["volume"] == original["volume"]
        assert expanded["exchange_timestamp"] == original["exchange_timestamp"]


class TestGlobalMemoryOptimizer:
    """Test global memory optimizer instance"""
    
    def test_get_memory_optimizer_singleton(self):
        """Test that get_memory_optimizer returns singleton"""
        # Reset global instance for test
        import src.utils.memory_optimizer as mem_opt
        mem_opt._global_memory_optimizer = None
        
        optimizer1 = get_memory_optimizer()
        optimizer2 = get_memory_optimizer()
        
        assert optimizer1 is optimizer2
    
    def test_get_memory_optimizer_with_redis(self):
        """Test memory optimizer with Redis client"""
        # Reset global instance for test
        import src.utils.memory_optimizer as mem_opt
        mem_opt._global_memory_optimizer = None
        
        mock_redis = Mock()
        optimizer = get_memory_optimizer(redis_client=mock_redis)
        
        assert optimizer.redis_client == mock_redis
