"""Unit tests for DataManager"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch, call
import json

from src.utils.data_manager import DataManager
from src.models.data_models import Quote


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch('src.utils.data_manager.redis') as mock:
        redis_client = MagicMock()
        redis_client.ping.return_value = True
        redis_client.get.return_value = None
        redis_client.setex.return_value = True
        redis_client.ttl.return_value = 10
        mock.from_url.return_value = redis_client
        yield redis_client


@pytest.fixture
def mock_postgres():
    """Mock PostgreSQL connection"""
    with patch('src.utils.data_manager.psycopg2') as mock:
        pg_conn = MagicMock()
        cursor = MagicMock()
        pg_conn.cursor.return_value.__enter__.return_value = cursor
        pg_conn.cursor.return_value.__exit__.return_value = None
        mock.connect.return_value = pg_conn
        yield pg_conn


@pytest.fixture
def data_manager(mock_redis, mock_postgres):
    """Create DataManager instance with mocked connections"""
    manager = DataManager(
        redis_url="redis://localhost:6379",
        postgres_url="postgresql://localhost/test",
        active_cache_ttl=15,
        watchlist_cache_ttl=60
    )
    return manager


@pytest.fixture
def sample_quote():
    """Create a sample quote for testing"""
    return Quote(
        symbol="AAPL",
        price=Decimal("150.25"),
        exchange_timestamp=datetime(2024, 1, 15, 10, 30, 0),
        received_timestamp=datetime(2024, 1, 15, 10, 30, 10),
        bid=Decimal("150.20"),
        ask=Decimal("150.30"),
        volume=1000000
    )


class TestDataManagerInitialization:
    """Test DataManager initialization"""
    
    def test_initialization_success(self, mock_redis, mock_postgres):
        """Test successful initialization"""
        manager = DataManager(
            redis_url="redis://localhost:6379",
            postgres_url="postgresql://localhost/test"
        )
        
        assert manager.active_cache_ttl == 15
        assert manager.watchlist_cache_ttl == 60
        mock_redis.ping.assert_called_once()
    
    def test_initialization_with_custom_ttl(self, mock_redis, mock_postgres):
        """Test initialization with custom TTL values"""
        manager = DataManager(
            redis_url="redis://localhost:6379",
            postgres_url="postgresql://localhost/test",
            active_cache_ttl=20,
            watchlist_cache_ttl=90
        )
        
        assert manager.active_cache_ttl == 20
        assert manager.watchlist_cache_ttl == 90
    
    def test_redis_connection_failure(self, mock_postgres):
        """Test handling of Redis connection failure"""
        with patch('src.utils.data_manager.redis') as mock:
            redis_client = MagicMock()
            redis_client.ping.side_effect = Exception("Connection failed")
            mock.from_url.return_value = redis_client
            
            with pytest.raises(Exception, match="Connection failed"):
                DataManager(
                    redis_url="redis://localhost:6379",
                    postgres_url="postgresql://localhost/test"
                )
    
    def test_postgres_connection_failure(self, mock_redis):
        """Test handling of PostgreSQL connection failure"""
        with patch('src.utils.data_manager.psycopg2') as mock:
            mock.connect.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception, match="Connection failed"):
                DataManager(
                    redis_url="redis://localhost:6379",
                    postgres_url="postgresql://localhost/test"
                )


class TestCacheQuote:
    """Test cache_quote method"""
    
    def test_cache_active_stock(self, data_manager, sample_quote, mock_redis):
        """Test caching an actively monitored stock"""
        data_manager.cache_quote("AAPL", sample_quote, is_active=True)
        
        # Verify setex was called with correct TTL
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "quote:AAPL"
        assert call_args[0][1] == 15  # active_cache_ttl
        
        # Verify quote data was serialized correctly
        cached_data = json.loads(call_args[0][2])
        assert cached_data['symbol'] == "AAPL"
        assert cached_data['price'] == "150.25"
        assert cached_data['volume'] == 1000000
    
    def test_cache_watchlist_stock(self, data_manager, sample_quote, mock_redis):
        """Test caching a watchlist stock"""
        data_manager.cache_quote("AAPL", sample_quote, is_active=False)
        
        # Verify setex was called with watchlist TTL
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 60  # watchlist_cache_ttl
    
    def test_cache_quote_error_handling(self, data_manager, sample_quote, mock_redis):
        """Test error handling when caching fails"""
        mock_redis.setex.side_effect = Exception("Redis error")
        
        # Should not raise exception, just log error
        data_manager.cache_quote("AAPL", sample_quote)


class TestGetCachedQuote:
    """Test get_cached_quote method"""
    
    def test_get_cached_quote_success(self, data_manager, sample_quote, mock_redis):
        """Test retrieving a cached quote"""
        # Setup mock to return cached data
        cached_data = {
            'symbol': 'AAPL',
            'price': '150.25',
            'exchange_timestamp': '2024-01-15T10:30:00',
            'received_timestamp': '2024-01-15T10:30:10',
            'bid': '150.20',
            'ask': '150.30',
            'volume': 1000000
        }
        mock_redis.get.return_value = json.dumps(cached_data)
        
        quote = data_manager.get_cached_quote("AAPL")
        
        assert quote is not None
        assert quote.symbol == "AAPL"
        assert quote.price == Decimal("150.25")
        assert quote.volume == 1000000
        mock_redis.get.assert_called_once_with("quote:AAPL")
    
    def test_get_cached_quote_not_found(self, data_manager, mock_redis):
        """Test retrieving a quote that doesn't exist in cache"""
        mock_redis.get.return_value = None
        
        quote = data_manager.get_cached_quote("AAPL")
        
        assert quote is None
    
    def test_get_cached_quote_error_handling(self, data_manager, mock_redis):
        """Test error handling when retrieval fails"""
        mock_redis.get.side_effect = Exception("Redis error")
        
        quote = data_manager.get_cached_quote("AAPL")
        
        assert quote is None


class TestIsCacheValid:
    """Test is_cache_valid method"""
    
    def test_cache_valid(self, data_manager, mock_redis):
        """Test checking valid cache"""
        mock_redis.ttl.return_value = 10  # 10 seconds remaining
        
        is_valid = data_manager.is_cache_valid("AAPL")
        
        assert is_valid is True
        mock_redis.ttl.assert_called_once_with("quote:AAPL")
    
    def test_cache_expired(self, data_manager, mock_redis):
        """Test checking expired cache"""
        mock_redis.ttl.return_value = -2  # Key doesn't exist
        
        is_valid = data_manager.is_cache_valid("AAPL")
        
        assert is_valid is False
    
    def test_cache_no_expiry(self, data_manager, mock_redis):
        """Test checking cache with no expiry"""
        mock_redis.ttl.return_value = -1  # No expiry set
        
        is_valid = data_manager.is_cache_valid("AAPL")
        
        assert is_valid is False
    
    def test_cache_validity_error_handling(self, data_manager, mock_redis):
        """Test error handling when checking cache validity"""
        mock_redis.ttl.side_effect = Exception("Redis error")
        
        is_valid = data_manager.is_cache_valid("AAPL")
        
        assert is_valid is False


class TestStoreHistoricalData:
    """Test store_historical_data method"""
    
    def test_store_historical_data_success(self, data_manager, mock_postgres):
        """Test storing historical data"""
        test_data = {
            'open': 150.0,
            'high': 152.0,
            'low': 149.0,
            'close': 151.0
        }
        timestamp = datetime(2024, 1, 15, 10, 0, 0)
        
        data_manager.store_historical_data("AAPL", "price_history", test_data, timestamp)
        
        # Verify INSERT was called
        cursor = mock_postgres.cursor.return_value.__enter__.return_value
        cursor.execute.assert_called_once()
        call_args = cursor.execute.call_args[0]
        assert "INSERT INTO historical_data" in call_args[0]
        assert call_args[1][0] == "AAPL"
        assert call_args[1][1] == "price_history"
        
        mock_postgres.commit.assert_called_once()
    
    def test_store_historical_data_default_timestamp(self, data_manager, mock_postgres):
        """Test storing historical data with default timestamp"""
        test_data = {'key': 'value'}
        
        data_manager.store_historical_data("AAPL", "test_type", test_data)
        
        cursor = mock_postgres.cursor.return_value.__enter__.return_value
        cursor.execute.assert_called_once()
    
    def test_store_historical_data_error_handling(self, data_manager, mock_postgres):
        """Test error handling when storing fails"""
        cursor = mock_postgres.cursor.return_value.__enter__.return_value
        cursor.execute.side_effect = Exception("Database error")
        
        # Should not raise exception, just log error
        data_manager.store_historical_data("AAPL", "test_type", {})
        
        mock_postgres.rollback.assert_called_once()


class TestGetHistoricalData:
    """Test get_historical_data method"""
    
    def test_get_historical_data_success(self, data_manager, mock_postgres):
        """Test retrieving historical data"""
        # Setup mock cursor to return data
        cursor = mock_postgres.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            {
                'symbol': 'AAPL',
                'data_type': 'price_history',
                'data': {'close': 150.0},
                'timestamp': datetime(2024, 1, 15),
                'created_at': datetime(2024, 1, 15)
            }
        ]
        
        results = data_manager.get_historical_data("AAPL", "price_history", days=30)
        
        assert len(results) == 1
        assert results[0]['symbol'] == 'AAPL'
        assert results[0]['data_type'] == 'price_history'
        cursor.execute.assert_called_once()
    
    def test_get_historical_data_empty(self, data_manager, mock_postgres):
        """Test retrieving historical data when none exists"""
        cursor = mock_postgres.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = []
        
        results = data_manager.get_historical_data("AAPL", "price_history")
        
        assert len(results) == 0
    
    def test_get_historical_data_error_handling(self, data_manager, mock_postgres):
        """Test error handling when retrieval fails"""
        cursor = mock_postgres.cursor.return_value.__enter__.return_value
        cursor.execute.side_effect = Exception("Database error")
        
        results = data_manager.get_historical_data("AAPL", "price_history")
        
        assert len(results) == 0


class TestStoreQuoteHistory:
    """Test store_quote_history method"""
    
    def test_store_quote_history_success(self, data_manager, sample_quote, mock_postgres):
        """Test storing quote history"""
        data_manager.store_quote_history(sample_quote)
        
        cursor = mock_postgres.cursor.return_value.__enter__.return_value
        cursor.execute.assert_called_once()
        call_args = cursor.execute.call_args[0]
        assert "INSERT INTO quotes" in call_args[0]
        assert call_args[1][0] == "AAPL"
        
        mock_postgres.commit.assert_called_once()
    
    def test_store_quote_history_error_handling(self, data_manager, sample_quote, mock_postgres):
        """Test error handling when storing fails"""
        cursor = mock_postgres.cursor.return_value.__enter__.return_value
        cursor.execute.side_effect = Exception("Database error")
        
        # Should not raise exception, just log error
        data_manager.store_quote_history(sample_quote)
        
        mock_postgres.rollback.assert_called_once()


class TestGetQuoteHistory:
    """Test get_quote_history method"""
    
    def test_get_quote_history_success(self, data_manager, mock_postgres):
        """Test retrieving quote history"""
        cursor = mock_postgres.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            {
                'symbol': 'AAPL',
                'price': Decimal('150.25'),
                'exchange_timestamp': datetime(2024, 1, 15, 10, 30, 0),
                'received_timestamp': datetime(2024, 1, 15, 10, 30, 10),
                'bid': Decimal('150.20'),
                'ask': Decimal('150.30'),
                'volume': 1000000
            }
        ]
        
        quotes = data_manager.get_quote_history("AAPL", days=30)
        
        assert len(quotes) == 1
        assert quotes[0].symbol == "AAPL"
        assert quotes[0].price == Decimal("150.25")
        assert quotes[0].volume == 1000000
    
    def test_get_quote_history_empty(self, data_manager, mock_postgres):
        """Test retrieving quote history when none exists"""
        cursor = mock_postgres.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = []
        
        quotes = data_manager.get_quote_history("AAPL")
        
        assert len(quotes) == 0
    
    def test_get_quote_history_error_handling(self, data_manager, mock_postgres):
        """Test error handling when retrieval fails"""
        cursor = mock_postgres.cursor.return_value.__enter__.return_value
        cursor.execute.side_effect = Exception("Database error")
        
        quotes = data_manager.get_quote_history("AAPL")
        
        assert len(quotes) == 0


class TestContextManager:
    """Test context manager functionality"""
    
    def test_context_manager(self, mock_redis, mock_postgres):
        """Test using DataManager as context manager"""
        with DataManager(
            redis_url="redis://localhost:6379",
            postgres_url="postgresql://localhost/test"
        ) as manager:
            assert manager is not None
        
        # Verify connections were closed
        mock_redis.close.assert_called_once()
        mock_postgres.close.assert_called_once()
    
    def test_close_method(self, data_manager, mock_redis, mock_postgres):
        """Test explicit close method"""
        data_manager.close()
        
        mock_redis.close.assert_called_once()
        mock_postgres.close.assert_called_once()


class TestCacheTTLBehavior:
    """Test cache TTL behavior"""
    
    def test_active_stock_ttl(self, data_manager, sample_quote, mock_redis):
        """Test that active stocks use shorter TTL"""
        data_manager.cache_quote("AAPL", sample_quote, is_active=True)
        
        call_args = mock_redis.setex.call_args[0]
        assert call_args[1] == 15  # active_cache_ttl
    
    def test_watchlist_stock_ttl(self, data_manager, sample_quote, mock_redis):
        """Test that watchlist stocks use longer TTL"""
        data_manager.cache_quote("AAPL", sample_quote, is_active=False)
        
        call_args = mock_redis.setex.call_args[0]
        assert call_args[1] == 60  # watchlist_cache_ttl
    
    def test_ttl_range_validation(self, mock_redis, mock_postgres):
        """Test that TTL values are within expected range (15-60 seconds)"""
        manager = DataManager(
            redis_url="redis://localhost:6379",
            postgres_url="postgresql://localhost/test",
            active_cache_ttl=15,
            watchlist_cache_ttl=60
        )
        
        assert 15 <= manager.active_cache_ttl <= 60
        assert 15 <= manager.watchlist_cache_ttl <= 60
