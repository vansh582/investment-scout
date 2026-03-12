#!/usr/bin/env python3
"""
Test script for DataManager functionality

This script demonstrates the basic usage of DataManager with Redis and PostgreSQL.
Requires Redis and PostgreSQL to be running.

Usage:
    python scripts/test_data_manager.py
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.data_manager import DataManager
from src.models.data_models import Quote


def main():
    """Test DataManager functionality"""
    
    # Get database URLs from environment or use defaults
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    postgres_url = os.getenv('DATABASE_URL', 'postgresql://localhost/investment_scout')
    
    print("=" * 60)
    print("DataManager Test Script")
    print("=" * 60)
    print(f"\nRedis URL: {redis_url}")
    print(f"PostgreSQL URL: {postgres_url}")
    print()
    
    try:
        # Initialize DataManager
        print("Initializing DataManager...")
        with DataManager(redis_url, postgres_url) as manager:
            print("✓ DataManager initialized successfully\n")
            
            # Create a sample quote
            quote = Quote(
                symbol="AAPL",
                price=Decimal("150.25"),
                exchange_timestamp=datetime.now() - timedelta(seconds=5),
                received_timestamp=datetime.now(),
                bid=Decimal("150.20"),
                ask=Decimal("150.30"),
                volume=1000000
            )
            
            print(f"Sample Quote:")
            print(f"  Symbol: {quote.symbol}")
            print(f"  Price: ${quote.price}")
            print(f"  Volume: {quote.volume:,}")
            print(f"  Latency: {quote.latency.total_seconds():.2f}s")
            print(f"  Is Fresh: {quote.is_fresh}")
            print()
            
            # Test 1: Cache quote
            print("Test 1: Caching quote...")
            manager.cache_quote("AAPL", quote, is_active=True)
            print("✓ Quote cached successfully\n")
            
            # Test 2: Retrieve cached quote
            print("Test 2: Retrieving cached quote...")
            cached_quote = manager.get_cached_quote("AAPL")
            if cached_quote:
                print(f"✓ Retrieved cached quote:")
                print(f"  Symbol: {cached_quote.symbol}")
                print(f"  Price: ${cached_quote.price}")
                print(f"  Is Fresh: {cached_quote.is_fresh}")
            else:
                print("✗ Failed to retrieve cached quote")
            print()
            
            # Test 3: Check cache validity
            print("Test 3: Checking cache validity...")
            is_valid = manager.is_cache_valid("AAPL")
            print(f"✓ Cache is {'valid' if is_valid else 'invalid'}\n")
            
            # Test 4: Store quote history
            print("Test 4: Storing quote history...")
            manager.store_quote_history(quote)
            print("✓ Quote history stored successfully\n")
            
            # Test 5: Retrieve quote history
            print("Test 5: Retrieving quote history...")
            history = manager.get_quote_history("AAPL", days=1)
            print(f"✓ Retrieved {len(history)} historical quotes\n")
            
            # Test 6: Store historical data
            print("Test 6: Storing historical data...")
            historical_data = {
                'open': 149.50,
                'high': 152.00,
                'low': 148.75,
                'close': 150.25,
                'volume': 1000000
            }
            manager.store_historical_data("AAPL", "price_history", historical_data)
            print("✓ Historical data stored successfully\n")
            
            # Test 7: Retrieve historical data
            print("Test 7: Retrieving historical data...")
            data = manager.get_historical_data("AAPL", "price_history", days=1)
            print(f"✓ Retrieved {len(data)} historical data records\n")
            
            # Test 8: Test different TTLs
            print("Test 8: Testing different TTLs...")
            print(f"  Active stock TTL: {manager.active_cache_ttl}s")
            print(f"  Watchlist stock TTL: {manager.watchlist_cache_ttl}s")
            
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
            manager.cache_quote("GOOGL", watchlist_quote, is_active=False)
            print("✓ Cached watchlist stock with longer TTL\n")
            
            print("=" * 60)
            print("All tests completed successfully!")
            print("=" * 60)
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure Redis and PostgreSQL are running:")
        print("  Redis: redis-server")
        print("  PostgreSQL: Check your DATABASE_URL configuration")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
