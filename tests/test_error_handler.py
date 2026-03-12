"""
Unit tests for Error Handling and Resilience
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.utils.error_handler import (
    DatabaseConnectionManager,
    WriteQueue,
    MemoryMonitor,
    GracefulDegradation,
    ResilientOperation,
    handle_network_error,
    handle_rate_limit_error
)


class TestDatabaseConnectionManager:
    """Test database connection management with reconnection logic"""
    
    def test_successful_connection(self):
        """Test successful database connection"""
        manager = DatabaseConnectionManager("redis")
        
        def mock_connect():
            return Mock()
        
        result = manager.connect(mock_connect)
        
        assert result is True
        assert manager.is_connected is True
        assert manager.connection is not None
    
    def test_failed_connection(self):
        """Test failed database connection"""
        manager = DatabaseConnectionManager("postgresql")
        
        def mock_connect():
            raise ConnectionError("Connection failed")
        
        result = manager.connect(mock_connect)
        
        assert result is False
        assert manager.is_connected is False
    
    def test_reconnect_if_needed_when_connected(self):
        """Test reconnect skips when already connected"""
        manager = DatabaseConnectionManager("redis")
        manager.is_connected = True
        
        def mock_connect():
            return Mock()
        
        result = manager.reconnect_if_needed(mock_connect)
        
        assert result is True
    
    def test_reconnect_if_needed_respects_interval(self):
        """Test reconnect respects reconnection interval"""
        manager = DatabaseConnectionManager("redis", reconnect_interval=30)
        manager.is_connected = False
        manager.last_reconnect_attempt = datetime.now()
        
        def mock_connect():
            return Mock()
        
        # Should not attempt reconnect (too soon)
        result = manager.reconnect_if_needed(mock_connect)
        
        assert result is False
    
    def test_reconnect_if_needed_after_interval(self):
        """Test reconnect attempts after interval passes"""
        manager = DatabaseConnectionManager("redis", reconnect_interval=1)
        manager.is_connected = False
        manager.last_reconnect_attempt = datetime.now() - timedelta(seconds=2)
        
        def mock_connect():
            return Mock()
        
        # Should attempt reconnect (interval passed)
        result = manager.reconnect_if_needed(mock_connect)
        
        assert result is True
        assert manager.is_connected is True
    
    def test_disconnect(self):
        """Test disconnect marks connection as disconnected"""
        manager = DatabaseConnectionManager("redis")
        manager.is_connected = True
        
        manager.disconnect()
        
        assert manager.is_connected is False
    
    def test_execute_with_reconnect_when_connected(self):
        """Test execute operation when connected"""
        manager = DatabaseConnectionManager("redis")
        manager.is_connected = True
        
        def mock_operation():
            return "success"
        
        def mock_connect():
            return Mock()
        
        result = manager.execute_with_reconnect(mock_operation, mock_connect)
        
        assert result == "success"
    
    def test_execute_with_reconnect_when_disconnected(self):
        """Test execute operation attempts reconnect when disconnected"""
        manager = DatabaseConnectionManager("redis", reconnect_interval=0)
        manager.is_connected = False
        
        def mock_operation():
            return "success"
        
        def mock_connect():
            return Mock()
        
        result = manager.execute_with_reconnect(mock_operation, mock_connect)
        
        # Should reconnect and execute
        assert result == "success"
        assert manager.is_connected is True
    
    def test_execute_with_reconnect_handles_operation_failure(self):
        """Test execute handles operation failure and disconnects"""
        manager = DatabaseConnectionManager("redis")
        manager.is_connected = True
        
        def mock_operation():
            raise RuntimeError("Operation failed")
        
        def mock_connect():
            return Mock()
        
        result = manager.execute_with_reconnect(mock_operation, mock_connect)
        
        assert result is None
        assert manager.is_connected is False


class TestWriteQueue:
    """Test write queue for PostgreSQL outage handling"""
    
    def test_enqueue_write(self):
        """Test enqueueing write operation"""
        queue = WriteQueue(max_size=10)
        
        def mock_write():
            pass
        
        queue.enqueue(mock_write)
        
        assert queue.size() == 1
    
    def test_enqueue_respects_max_size(self):
        """Test queue respects maximum size"""
        queue = WriteQueue(max_size=3)
        
        def mock_write():
            pass
        
        # Add 5 items (should only keep 3)
        for i in range(5):
            queue.enqueue(mock_write, i)
        
        assert queue.size() == 3
    
    def test_flush_executes_all_writes(self):
        """Test flush executes all queued writes"""
        queue = WriteQueue()
        
        executed = []
        
        def mock_write(value):
            executed.append(value)
        
        # Queue 3 writes
        for i in range(3):
            queue.enqueue(mock_write, i)
        
        # Flush
        count = queue.flush()
        
        assert count == 3
        assert executed == [0, 1, 2]
        assert queue.size() == 0
    
    def test_flush_handles_failures(self):
        """Test flush handles write failures gracefully"""
        queue = WriteQueue()
        
        executed = []
        
        def mock_write_success(value):
            executed.append(value)
        
        def mock_write_failure(value):
            raise RuntimeError("Write failed")
        
        # Queue mix of successful and failing writes
        queue.enqueue(mock_write_success, 1)
        queue.enqueue(mock_write_failure, 2)
        queue.enqueue(mock_write_success, 3)
        
        # Flush (should continue despite failure)
        count = queue.flush()
        
        assert count == 2  # 2 successful
        assert executed == [1, 3]
    
    def test_flush_empty_queue(self):
        """Test flush on empty queue"""
        queue = WriteQueue()
        
        count = queue.flush()
        
        assert count == 0


class TestMemoryMonitor:
    """Test memory monitoring and cleanup"""
    
    @patch('psutil.Process')
    def test_get_memory_usage(self, mock_process_class):
        """Test getting current memory usage"""
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 400 * 1024 * 1024  # 400 MB
        mock_process_class.return_value = mock_process
        
        monitor = MemoryMonitor()
        monitor.process = mock_process
        
        usage = monitor.get_memory_usage_mb()
        
        assert usage == 400.0
    
    @patch('psutil.Process')
    @patch('gc.collect')
    def test_check_and_cleanup_below_threshold(self, mock_gc, mock_process_class):
        """Test no cleanup when below threshold"""
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 300 * 1024 * 1024  # 300 MB
        mock_process_class.return_value = mock_process
        
        monitor = MemoryMonitor(warning_threshold_mb=400.0)
        monitor.process = mock_process
        
        result = monitor.check_and_cleanup()
        
        assert result is False
        mock_gc.assert_not_called()
    
    @patch('psutil.Process')
    @patch('gc.collect')
    def test_check_and_cleanup_warning_threshold(self, mock_gc, mock_process_class):
        """Test standard cleanup at warning threshold"""
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 420 * 1024 * 1024  # 420 MB
        mock_process_class.return_value = mock_process
        
        monitor = MemoryMonitor(warning_threshold_mb=400.0, critical_threshold_mb=480.0)
        monitor.process = mock_process
        
        result = monitor.check_and_cleanup()
        
        assert result is True
        mock_gc.assert_called_once()
    
    @patch('psutil.Process')
    @patch('gc.collect')
    def test_check_and_cleanup_critical_threshold(self, mock_gc, mock_process_class):
        """Test aggressive cleanup at critical threshold"""
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 490 * 1024 * 1024  # 490 MB
        mock_process_class.return_value = mock_process
        
        monitor = MemoryMonitor(warning_threshold_mb=400.0, critical_threshold_mb=480.0)
        monitor.process = mock_process
        
        result = monitor.check_and_cleanup()
        
        assert result is True
        # Should call gc.collect with generation=2 for aggressive cleanup
        mock_gc.assert_called_with(generation=2)


class TestGracefulDegradation:
    """Test graceful degradation management"""
    
    def test_mark_degraded(self):
        """Test marking component as degraded"""
        degradation = GracefulDegradation()
        
        degradation.mark_degraded("DataManager", "Redis unavailable")
        
        assert degradation.is_degraded("DataManager")
        assert "DataManager" in degradation.get_degraded_components()
    
    def test_mark_recovered(self):
        """Test marking component as recovered"""
        degradation = GracefulDegradation()
        
        degradation.mark_degraded("DataManager", "Redis unavailable")
        degradation.mark_recovered("DataManager")
        
        assert not degradation.is_degraded("DataManager")
        assert "DataManager" not in degradation.get_degraded_components()
    
    def test_multiple_degraded_components(self):
        """Test tracking multiple degraded components"""
        degradation = GracefulDegradation()
        
        degradation.mark_degraded("DataManager", "Redis unavailable")
        degradation.mark_degraded("EmailService", "SendGrid rate limit")
        
        assert degradation.is_degraded("DataManager")
        assert degradation.is_degraded("EmailService")
        assert len(degradation.get_degraded_components()) == 2


class TestResilientOperation:
    """Test resilient operation wrapper"""
    
    def test_execute_with_fallback_success(self):
        """Test successful primary operation"""
        operation = ResilientOperation("TestComponent")
        
        def primary():
            return "primary_result"
        
        def fallback():
            return "fallback_result"
        
        result = operation.execute_with_fallback(primary, fallback, "test_op")
        
        assert result == "primary_result"
    
    def test_execute_with_fallback_uses_fallback(self):
        """Test fallback is used when primary fails"""
        operation = ResilientOperation("TestComponent")
        
        def primary():
            raise RuntimeError("Primary failed")
        
        def fallback():
            return "fallback_result"
        
        result = operation.execute_with_fallback(primary, fallback, "test_op")
        
        assert result == "fallback_result"
        assert operation.degradation.is_degraded("TestComponent")
    
    def test_execute_with_fallback_both_fail(self):
        """Test returns None when both primary and fallback fail"""
        operation = ResilientOperation("TestComponent")
        
        def primary():
            raise RuntimeError("Primary failed")
        
        def fallback():
            raise RuntimeError("Fallback failed")
        
        result = operation.execute_with_fallback(primary, fallback, "test_op")
        
        assert result is None
    
    def test_execute_with_fallback_no_fallback(self):
        """Test returns None when primary fails and no fallback"""
        operation = ResilientOperation("TestComponent")
        
        def primary():
            raise RuntimeError("Primary failed")
        
        result = operation.execute_with_fallback(primary, None, "test_op")
        
        assert result is None


class TestNetworkErrorHandling:
    """Test network error handling with retry"""
    
    def test_handle_network_error_success(self):
        """Test successful network operation"""
        def operation():
            return "success"
        
        result = handle_network_error(operation)
        
        assert result == "success"
    
    def test_handle_network_error_retry_and_succeed(self):
        """Test retry succeeds after initial failure"""
        attempts = [0]
        
        def operation():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ConnectionError("Network error")
            return "success"
        
        result = handle_network_error(operation, max_retries=3, backoff_base=0.01)
        
        assert result == "success"
        assert attempts[0] == 2
    
    def test_handle_network_error_all_retries_fail(self):
        """Test returns None when all retries fail"""
        def operation():
            raise ConnectionError("Network error")
        
        result = handle_network_error(operation, max_retries=2, backoff_base=0.01)
        
        assert result is None


class TestRateLimitErrorHandling:
    """Test rate limit error handling"""
    
    @patch('time.sleep')
    def test_handle_rate_limit_with_reset_time(self, mock_sleep):
        """Test waiting until rate limit reset time"""
        reset_time = datetime.now() + timedelta(seconds=30)
        
        handle_rate_limit_error(reset_time)
        
        # Should have slept approximately 30 seconds
        assert mock_sleep.called
        sleep_duration = mock_sleep.call_args[0][0]
        assert 25 <= sleep_duration <= 35  # Allow some tolerance
    
    @patch('time.sleep')
    def test_handle_rate_limit_without_reset_time(self, mock_sleep):
        """Test default wait when reset time unknown"""
        handle_rate_limit_error(None)
        
        # Should sleep default 60 seconds
        mock_sleep.assert_called_once_with(60)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
