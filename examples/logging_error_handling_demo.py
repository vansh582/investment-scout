"""
Demo: Logging System and Error Handling

Demonstrates the structured logging and error handling capabilities
of the Investment Scout system.
"""

import time
from datetime import datetime, timedelta

from src.utils.logger import get_logger
from src.utils.error_handler import (
    DatabaseConnectionManager,
    WriteQueue,
    MemoryMonitor,
    GracefulDegradation,
    ResilientOperation,
    handle_network_error
)


def demo_structured_logging():
    """Demonstrate structured logging capabilities"""
    print("\n" + "="*60)
    print("DEMO: Structured Logging")
    print("="*60 + "\n")
    
    # Create logger for a component
    logger = get_logger("DemoComponent", "INFO")
    
    # Log component startup
    logger.log_startup(version="1.0.0", environment="demo")
    
    # Log API request
    logger.log_api_request(
        provider="yfinance",
        endpoint="/quote/AAPL",
        status="success",
        latency_ms=125.5
    )
    
    # Log data freshness violation
    logger.log_data_freshness_violation(
        symbol="TSLA",
        latency_seconds=45.2,
        provider="finnhub"
    )
    
    # Log failover event
    logger.log_failover(
        from_provider="yfinance",
        to_provider="finnhub",
        reason="timeout"
    )
    
    # Log newsletter generation
    logger.log_newsletter_generation(
        opportunity_count=3,
        generation_time_ms=1250.0
    )
    
    # Log alert generation
    logger.log_alert_generation(
        symbol="AAPL",
        signal_type="BUY",
        generation_time_ms=85.0
    )
    
    # Log performance update
    logger.log_performance_update(
        total_return=12.5,
        sp500_return=8.3,
        relative_performance=4.2
    )
    
    # Log database connection change
    logger.log_db_connection_change(
        database="redis",
        status="connected"
    )
    
    # Log memory warning
    logger.log_memory_warning(
        current_mb=425.5,
        threshold_mb=400.0
    )
    
    # Log error with exception
    try:
        raise ValueError("Demo error")
    except ValueError as e:
        logger.error("demo_error", "An error occurred during demo", error=e)
    
    # Log component shutdown
    logger.log_shutdown()
    
    print("\n✓ Structured logging demo complete")


def demo_database_connection_manager():
    """Demonstrate database connection management with reconnection"""
    print("\n" + "="*60)
    print("DEMO: Database Connection Manager")
    print("="*60 + "\n")
    
    # Create connection manager
    manager = DatabaseConnectionManager("redis", reconnect_interval=2)
    
    # Simulate successful connection
    def mock_connect_success():
        print("  → Connecting to Redis...")
        return {"connection": "mock_redis"}
    
    print("1. Initial connection:")
    success = manager.connect(mock_connect_success)
    print(f"   Connected: {success}")
    
    # Simulate disconnection
    print("\n2. Simulating disconnection:")
    manager.disconnect()
    print(f"   Connected: {manager.is_connected}")
    
    # Attempt reconnection too soon
    print("\n3. Attempting reconnection (too soon):")
    success = manager.reconnect_if_needed(mock_connect_success)
    print(f"   Reconnected: {success}")
    
    # Wait and reconnect
    print("\n4. Waiting 2 seconds and reconnecting:")
    time.sleep(2)
    success = manager.reconnect_if_needed(mock_connect_success)
    print(f"   Reconnected: {success}")
    
    print("\n✓ Database connection manager demo complete")


def demo_write_queue():
    """Demonstrate write queue for PostgreSQL outage handling"""
    print("\n" + "="*60)
    print("DEMO: Write Queue")
    print("="*60 + "\n")
    
    # Create write queue
    queue = WriteQueue(max_size=5)
    
    # Simulate queuing writes during outage
    print("1. Queuing writes during PostgreSQL outage:")
    
    executed_writes = []
    
    def mock_write(data):
        executed_writes.append(data)
        print(f"   → Executed write: {data}")
    
    for i in range(3):
        queue.enqueue(mock_write, f"data_{i}")
        print(f"   Queued write {i+1} (queue size: {queue.size()})")
    
    # Flush queue when connection restored
    print("\n2. Flushing queue after connection restored:")
    count = queue.flush()
    print(f"   Flushed {count} writes")
    print(f"   Queue size: {queue.size()}")
    
    print("\n✓ Write queue demo complete")


def demo_memory_monitor():
    """Demonstrate memory monitoring and cleanup"""
    print("\n" + "="*60)
    print("DEMO: Memory Monitor")
    print("="*60 + "\n")
    
    # Create memory monitor with low thresholds for demo
    monitor = MemoryMonitor(warning_threshold_mb=1.0, critical_threshold_mb=2.0)
    
    # Check current memory usage
    current_mb = monitor.get_memory_usage_mb()
    print(f"Current memory usage: {current_mb:.1f} MB")
    
    # Check and cleanup if needed
    print("\nChecking memory and triggering cleanup if needed:")
    cleanup_triggered = monitor.check_and_cleanup()
    
    if cleanup_triggered:
        print("  → Cleanup was triggered")
    else:
        print("  → No cleanup needed (below threshold)")
    
    print("\n✓ Memory monitor demo complete")


def demo_graceful_degradation():
    """Demonstrate graceful degradation management"""
    print("\n" + "="*60)
    print("DEMO: Graceful Degradation")
    print("="*60 + "\n")
    
    degradation = GracefulDegradation()
    
    # Mark component as degraded
    print("1. Marking DataManager as degraded:")
    degradation.mark_degraded("DataManager", "Redis unavailable")
    print(f"   Is degraded: {degradation.is_degraded('DataManager')}")
    
    # Mark another component as degraded
    print("\n2. Marking EmailService as degraded:")
    degradation.mark_degraded("EmailService", "SendGrid rate limit")
    print(f"   Degraded components: {degradation.get_degraded_components()}")
    
    # Recover a component
    print("\n3. Recovering DataManager:")
    degradation.mark_recovered("DataManager")
    print(f"   Is degraded: {degradation.is_degraded('DataManager')}")
    print(f"   Degraded components: {degradation.get_degraded_components()}")
    
    print("\n✓ Graceful degradation demo complete")


def demo_resilient_operation():
    """Demonstrate resilient operation with fallback"""
    print("\n" + "="*60)
    print("DEMO: Resilient Operation")
    print("="*60 + "\n")
    
    operation = ResilientOperation("DemoComponent")
    
    # Successful primary operation
    print("1. Successful primary operation:")
    def primary_success():
        print("   → Primary operation executed")
        return "primary_result"
    
    result = operation.execute_with_fallback(primary_success, None, "test_op")
    print(f"   Result: {result}")
    
    # Primary fails, fallback succeeds
    print("\n2. Primary fails, using fallback:")
    def primary_fail():
        print("   → Primary operation failed")
        raise RuntimeError("Primary failed")
    
    def fallback_success():
        print("   → Fallback operation executed")
        return "fallback_result"
    
    result = operation.execute_with_fallback(primary_fail, fallback_success, "test_op")
    print(f"   Result: {result}")
    print(f"   Component degraded: {operation.degradation.is_degraded('DemoComponent')}")
    
    print("\n✓ Resilient operation demo complete")


def demo_network_error_handling():
    """Demonstrate network error handling with retry"""
    print("\n" + "="*60)
    print("DEMO: Network Error Handling")
    print("="*60 + "\n")
    
    # Simulate network operation that succeeds after retry
    print("1. Network operation with retry:")
    
    attempts = [0]
    
    def network_operation():
        attempts[0] += 1
        print(f"   → Attempt {attempts[0]}")
        if attempts[0] < 2:
            raise ConnectionError("Network error")
        return "success"
    
    result = handle_network_error(network_operation, max_retries=3, backoff_base=0.1)
    print(f"   Result: {result}")
    print(f"   Total attempts: {attempts[0]}")
    
    print("\n✓ Network error handling demo complete")


def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("Investment Scout - Logging & Error Handling Demo")
    print("="*60)
    
    demo_structured_logging()
    demo_database_connection_manager()
    demo_write_queue()
    demo_memory_monitor()
    demo_graceful_degradation()
    demo_resilient_operation()
    demo_network_error_handling()
    
    print("\n" + "="*60)
    print("All demos complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
