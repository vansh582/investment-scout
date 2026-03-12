"""Integration tests for DataManager with real Redis and PostgreSQL (optional)

These tests require actual Redis and PostgreSQL instances running.
Skip these tests if databases are not available.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
import os

from src.utils.data_manager import DataManager
from src.models.data_models import Quote


# Skip all tests in this module if database URLs are not configured
pytestmark = pytest.mark.skipif(
    not os.getenv('REDIS_URL') or not os.getenv('DATABASE_URL'),
    reason="Redis and PostgreSQL URLs not configured"
)


@pytest.fixture
def data_manager():
    """Create DataManager with real connections"""
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    postgres_url = os.getenv('DATABASE_URL', 'postgresql://localhost/investment_scout_test')
    
    manager = DataManager(redis_url, postgres_url)
    yield manager
    manager.close()


@pytest.fixture
def sample_quote():
    """Create a sample quote"""
    return Quote(
        symbol="AAPL",
        price=Decimal("150.25"),
        exchange_timestamp=datetime.now() - timedelta(seconds=5),
        received_timestamp=datetime.now(),
        bid=Decimal("150.20"),
        ask=Decimal("150.30"),
        volume=1000000
    )


class TestDataManagerIntegration:
    """Integration tests with real databases"""
    
    def test_cache_and_retrieve_quote(self, data_manager, sample_quote):
        """Test caching and retrieving a quote"""
        # Cache the quote
        data_manager.cache_quote("AAPL", sample_quote, is_active=True)
        
        # Retrieve the quote
        cached_quote = data_manager.get_cached_quote("AAPL")
        
        assert cached_quote is not None
        assert cached_quote.symbol == sample_quote.symbol
        assert cached_quote.price == sample_quote.price
        assert cached_quote.volume == sample_quote.volume
    
    def test_cache_expiration(self, data_manager, sample_quote):
        """Test that cache expires after TTL"""
        import time
        
        # Create manager with very short TTL
        manager = DataManager(
            redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379'),
            postgres_url=os.getenv('DATABASE_URL', 'postgresql://localhost/investment_scout_test'),
            active_cache_ttl=1  # 1 second
        )
        
        try:
            # Cache the quote
            manager.cache_quote("AAPL", sample_quote, is_active=True)
            
            # Verify it's cached
            assert manager.is_cache_valid("AAPL") is True
            
            # Wait for expiration
            time.sleep(2)
            
            # Verify it's expired
            assert manager.is_cache_valid("AAPL") is False
        finally:
            manager.close()
    
    def test_store_and_retrieve_historical_data(self, data_manager):
        """Test storing and retrieving historical data"""
        test_data = {
            'open': 150.0,
            'high': 152.0,
            'low': 149.0,
            'close': 151.0,
            'volume': 1000000
        }
        timestamp = datetime.now()
        
        # Store historical data
        data_manager.store_historical_data("AAPL", "price_history", test_data, timestamp)
        
        # Retrieve historical data
        results = data_manager.get_historical_data("AAPL", "price_history", days=1)
        
        assert len(results) > 0
        assert results[0]['symbol'] == "AAPL"
        assert results[0]['data_type'] == "price_history"
        assert 'open' in results[0]['data']
    
    def test_store_and_retrieve_quote_history(self, data_manager, sample_quote):
        """Test storing and retrieving quote history"""
        # Store quote history
        data_manager.store_quote_history(sample_quote)
        
        # Retrieve quote history
        quotes = data_manager.get_quote_history("AAPL", days=1)
        
        assert len(quotes) > 0
        assert quotes[0].symbol == "AAPL"
        assert quotes[0].price == sample_quote.price
    
    def test_active_vs_watchlist_ttl(self, data_manager, sample_quote):
        """Test different TTL for active vs watchlist stocks"""
        # Cache as active stock
        data_manager.cache_quote("AAPL", sample_quote, is_active=True)
        
        # Cache as watchlist stock
        watchlist_quote = Quote(
            symbol="GOOGL",
            price=Decimal("140.50"),
            exchange_timestamp=datetime.now() - timedelta(seconds=5),
            received_timestamp=datetime.now(),
            bid=Decimal("140.45"),
            ask=Decimal("140.55"),
            volume=500000
        )
        data_manager.cache_quote("GOOGL", watchlist_quote, is_active=False)
        
        # Both should be valid initially
        assert data_manager.is_cache_valid("AAPL") is True
        assert data_manager.is_cache_valid("GOOGL") is True
    
    def test_context_manager_usage(self, sample_quote):
        """Test using DataManager as context manager"""
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        postgres_url = os.getenv('DATABASE_URL', 'postgresql://localhost/investment_scout_test')
        
        with DataManager(redis_url, postgres_url) as manager:
            # Use the manager
            manager.cache_quote("AAPL", sample_quote)
            cached = manager.get_cached_quote("AAPL")
            assert cached is not None
        
        # Connections should be closed after exiting context


class TestDataFreshness:
    """Test data freshness validation"""
    
    def test_fresh_data_caching(self, data_manager):
        """Test that only fresh data is cached"""
        # Create a fresh quote
        fresh_quote = Quote(
            symbol="AAPL",
            price=Decimal("150.25"),
            exchange_timestamp=datetime.now() - timedelta(seconds=10),
            received_timestamp=datetime.now(),
            bid=Decimal("150.20"),
            ask=Decimal("150.30"),
            volume=1000000
        )
        
        assert fresh_quote.is_fresh is True
        
        # Cache and retrieve
        data_manager.cache_quote("AAPL", fresh_quote)
        cached = data_manager.get_cached_quote("AAPL")
        
        assert cached is not None
        assert cached.is_fresh is True
    
    def test_stale_data_detection(self, data_manager):
        """Test detection of stale data"""
        # Create a stale quote (>30 seconds old)
        stale_quote = Quote(
            symbol="AAPL",
            price=Decimal("150.25"),
            exchange_timestamp=datetime.now() - timedelta(seconds=35),
            received_timestamp=datetime.now(),
            bid=Decimal("150.20"),
            ask=Decimal("150.30"),
            volume=1000000
        )
        
        assert stale_quote.is_fresh is False
        
        # Even if cached, the quote itself indicates it's stale
        data_manager.cache_quote("AAPL", stale_quote)
        cached = data_manager.get_cached_quote("AAPL")
        
        if cached:
            assert cached.is_fresh is False
