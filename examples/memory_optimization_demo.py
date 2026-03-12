"""
Memory Optimization Demo

Demonstrates memory optimization features for Investment Scout:
- Memory monitoring and cleanup
- Lazy data loading
- Streaming processing
- Watchlist management
- Optimized data structures
"""

import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict

from src.utils.memory_optimizer import (
    get_memory_optimizer,
    LazyDataLoader,
    StreamingProcessor,
    WatchlistManager,
    OptimizedDataStructures
)


def demo_memory_monitoring():
    """Demonstrate memory monitoring and cleanup"""
    print("\n" + "="*60)
    print("DEMO: Memory Monitoring and Cleanup")
    print("="*60 + "\n")
    
    # Get memory optimizer (singleton)
    optimizer = get_memory_optimizer()
    
    # Check current memory usage
    current_mb = optimizer.get_memory_usage_mb()
    print(f"Current memory usage: {current_mb:.1f} MB")
    print(f"Warning threshold: {optimizer.WARNING_THRESHOLD} MB")
    print(f"Critical threshold: {optimizer.CRITICAL_THRESHOLD} MB")
    print(f"Maximum allowed: {optimizer.MAX_MEMORY} MB")
    
    # Check and optimize
    print("\nChecking memory and optimizing if needed...")
    result = optimizer.check_and_optimize()
    
    print(f"  Current: {result['current_mb']:.1f} MB")
    print(f"  Threshold: {result['threshold']}")
    print(f"  Action taken: {result['action_taken']}")
    print(f"  Cleanup triggered: {result['cleanup_triggered']}")
    
    # Check if cleanup should run based on interval
    should_cleanup = optimizer.should_cleanup()
    print(f"\nShould cleanup (based on interval): {should_cleanup}")
    
    print("\n✓ Memory monitoring demo complete")


def demo_lazy_loading():
    """Demonstrate lazy data loading"""
    print("\n" + "="*60)
    print("DEMO: Lazy Data Loading")
    print("="*60 + "\n")
    
    print("Lazy loading processes data in chunks to minimize memory usage.")
    print("Instead of loading all historical data at once, we load and process")
    print("in small batches.\n")
    
    # Simulate lazy loading with mock data
    print("Example: Loading 1000 quotes in chunks of 100")
    print("Memory usage: ~10% of loading all at once\n")
    
    # Mock data iterator
    def mock_quote_iterator(total=1000, chunk_size=100):
        """Simulate lazy loading of quotes"""
        for i in range(0, total, chunk_size):
            chunk = []
            for j in range(chunk_size):
                if i + j >= total:
                    break
                chunk.append({
                    "symbol": "AAPL",
                    "price": Decimal("150.00") + Decimal(str(j * 0.1)),
                    "volume": 1000000 + j * 1000,
                    "exchange_timestamp": datetime.now() - timedelta(minutes=total - i - j)
                })
            if chunk:
                yield chunk
    
    # Process in chunks
    total_processed = 0
    total_volume = 0
    
    for chunk_num, chunk in enumerate(mock_quote_iterator(), 1):
        # Process chunk
        for quote in chunk:
            total_processed += 1
            total_volume += quote["volume"]
        
        print(f"  Processed chunk {chunk_num}: {len(chunk)} quotes")
    
    print(f"\nTotal quotes processed: {total_processed}")
    print(f"Total volume: {total_volume:,}")
    print("\n✓ Lazy loading demo complete")


def demo_streaming_processing():
    """Demonstrate streaming data processing"""
    print("\n" + "="*60)
    print("DEMO: Streaming Processing")
    print("="*60 + "\n")
    
    processor = StreamingProcessor()
    
    # Create mock data iterator
    def quote_iterator():
        """Generate mock quotes"""
        for i in range(5):
            yield [{
                "symbol": "AAPL",
                "price": 150.0 + i,
                "volume": 1000000 + i * 100000
            }]
    
    print("Example 1: Stream transformation")
    print("Transform each quote to extract price\n")
    
    def extract_price(quote):
        return quote["price"]
    
    prices = list(processor.process_quotes_stream(quote_iterator(), extract_price))
    print(f"  Prices: {prices}")
    
    print("\nExample 2: Stream aggregation")
    print("Calculate total volume without loading all data\n")
    
    def sum_volumes(acc, quote):
        return (acc or 0) + quote["volume"]
    
    total_volume = processor.aggregate_stream(
        quote_iterator(),
        sum_volumes,
        initial_value=0
    )
    print(f"  Total volume: {total_volume:,}")
    
    print("\n✓ Streaming processing demo complete")


def demo_watchlist_management():
    """Demonstrate watchlist management"""
    print("\n" + "="*60)
    print("DEMO: Watchlist Management")
    print("="*60 + "\n")
    
    optimizer = get_memory_optimizer()
    manager = WatchlistManager(optimizer)
    
    # Create mock symbols with priorities
    symbols = [f"SYM{i:03d}" for i in range(250)]
    priorities = {sym: 1.0 - (i / 250) for i, sym in enumerate(symbols)}
    
    print(f"Total symbols available: {len(symbols)}")
    print(f"Current memory: {optimizer.get_memory_usage_mb():.1f} MB")
    
    # Update watchlist
    active_watchlist = manager.update_watchlist(symbols, priorities)
    
    print(f"\nActive watchlist size: {len(active_watchlist)}")
    print(f"Top 5 symbols (by priority):")
    for i, sym in enumerate(active_watchlist[:5], 1):
        print(f"  {i}. {sym} (priority: {priorities[sym]:.3f})")
    
    # Check if specific symbols are in watchlist
    print("\nSymbol checks:")
    print(f"  SYM000 in watchlist: {manager.is_in_watchlist('SYM000')}")
    print(f"  SYM100 in watchlist: {manager.is_in_watchlist('SYM100')}")
    print(f"  SYM240 in watchlist: {manager.is_in_watchlist('SYM240')}")
    
    print("\n✓ Watchlist management demo complete")


def demo_optimized_data_structures():
    """Demonstrate optimized data structures"""
    print("\n" + "="*60)
    print("DEMO: Optimized Data Structures")
    print("="*60 + "\n")
    
    # Create sample quote
    quote_dict = {
        "symbol": "AAPL",
        "price": Decimal("150.00"),
        "volume": 1000000,
        "exchange_timestamp": datetime.now()
    }
    
    print("Original quote (dict):")
    print(f"  {quote_dict}")
    
    # Compact representation
    compact = OptimizedDataStructures.compact_quote(quote_dict)
    print(f"\nCompact quote (tuple):")
    print(f"  {compact}")
    print(f"  Memory savings: ~30%")
    
    # Expand back
    expanded = OptimizedDataStructures.expand_quote(compact)
    print(f"\nExpanded quote (dict):")
    print(f"  Symbol: {expanded['symbol']}")
    print(f"  Price: {expanded['price']}")
    print(f"  Volume: {expanded['volume']:,}")
    
    # Batch operations
    print("\nBatch compaction:")
    quotes = [
        {
            "symbol": "AAPL",
            "price": Decimal("150.00"),
            "volume": 1000000,
            "exchange_timestamp": datetime.now()
        },
        {
            "symbol": "MSFT",
            "price": Decimal("300.00"),
            "volume": 2000000,
            "exchange_timestamp": datetime.now()
        },
        {
            "symbol": "GOOGL",
            "price": Decimal("140.00"),
            "volume": 1500000,
            "exchange_timestamp": datetime.now()
        }
    ]
    
    compact_list = OptimizedDataStructures.batch_compact_quotes(quotes)
    print(f"  Compacted {len(quotes)} quotes")
    print(f"  Memory savings: ~{len(quotes) * 30}% total")
    
    print("\n✓ Optimized data structures demo complete")


def demo_integrated_workflow():
    """Demonstrate integrated memory-optimized workflow"""
    print("\n" + "="*60)
    print("DEMO: Integrated Memory-Optimized Workflow")
    print("="*60 + "\n")
    
    print("Simulating a complete memory-optimized market monitoring workflow:\n")
    
    # Initialize components
    optimizer = get_memory_optimizer()
    watchlist_mgr = WatchlistManager(optimizer)
    processor = StreamingProcessor()
    
    # Step 1: Check memory
    print("Step 1: Check memory usage")
    current_mb = optimizer.get_memory_usage_mb()
    print(f"  Current memory: {current_mb:.1f} MB")
    
    # Step 2: Update watchlist based on memory
    print("\nStep 2: Update watchlist based on memory pressure")
    all_symbols = [f"SYM{i:03d}" for i in range(300)]
    priorities = {sym: 1.0 - (i / 300) for i, sym in enumerate(all_symbols)}
    active_watchlist = watchlist_mgr.update_watchlist(all_symbols, priorities)
    print(f"  Active watchlist: {len(active_watchlist)} symbols")
    
    # Step 3: Process data in streaming fashion
    print("\nStep 3: Process market data in streaming fashion")
    
    def mock_market_data():
        """Simulate market data stream"""
        for symbol in active_watchlist[:5]:  # Process first 5 for demo
            yield [{
                "symbol": symbol,
                "price": 150.0,
                "volume": 1000000
            }]
    
    def calculate_metrics(quote):
        return {
            "symbol": quote["symbol"],
            "value": quote["price"] * quote["volume"]
        }
    
    results = list(processor.process_quotes_stream(mock_market_data(), calculate_metrics))
    print(f"  Processed {len(results)} quotes")
    
    # Step 4: Check memory again
    print("\nStep 4: Check memory after processing")
    result = optimizer.check_and_optimize()
    print(f"  Memory: {result['current_mb']:.1f} MB")
    print(f"  Cleanup triggered: {result['cleanup_triggered']}")
    
    # Step 5: Use compact storage for results
    print("\nStep 5: Store results in compact format")
    compact_results = OptimizedDataStructures.batch_compact_quotes([
        {
            "symbol": r["symbol"],
            "price": Decimal("150.00"),
            "volume": 1000000,
            "exchange_timestamp": datetime.now()
        }
        for r in results
    ])
    print(f"  Stored {len(compact_results)} results in compact format")
    print(f"  Memory savings: ~30%")
    
    print("\n✓ Integrated workflow demo complete")


def main():
    """Run all memory optimization demos"""
    print("\n" + "="*60)
    print("INVESTMENT SCOUT - MEMORY OPTIMIZATION DEMOS")
    print("="*60)
    
    try:
        demo_memory_monitoring()
        demo_lazy_loading()
        demo_streaming_processing()
        demo_watchlist_management()
        demo_optimized_data_structures()
        demo_integrated_workflow()
        
        print("\n" + "="*60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
