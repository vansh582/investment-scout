"""
Error Handling and Resilience for Investment Scout

Provides graceful degradation, reconnection logic, memory pressure handling,
and resilient operation during component failures.
"""

import time
import psutil
import gc
from typing import Optional, Callable, Any, List
from datetime import datetime, timedelta
from collections import deque
from threading import Lock

from src.utils.logger import get_logger


logger = get_logger("ErrorHandler")


class DatabaseConnectionManager:
    """
    Manages database connections with automatic reconnection logic.
    
    Handles both Redis and PostgreSQL connections with exponential backoff
    and graceful degradation during outages.
    """
    
    def __init__(self, db_type: str, reconnect_interval: int = 30):
        """
        Initialize database connection manager.
        
        Args:
            db_type: Database type ("redis" or "postgresql")
            reconnect_interval: Seconds between reconnection attempts
        """
        self.db_type = db_type
        self.reconnect_interval = reconnect_interval
        self.is_connected = False
        self.last_reconnect_attempt: Optional[datetime] = None
        self.connection = None
        self.logger = get_logger(f"DatabaseConnectionManager-{db_type}")
    
    def connect(self, connection_func: Callable) -> bool:
        """
        Attempt to establish database connection.
        
        Args:
            connection_func: Function that returns a database connection
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection = connection_func()
            self.is_connected = True
            self.logger.log_db_connection_change(self.db_type, "connected")
            return True
        except Exception as e:
            self.is_connected = False
            self.logger.error(
                "db_connection_failed",
                f"Failed to connect to {self.db_type}",
                error=e,
                database=self.db_type
            )
            return False
    
    def reconnect_if_needed(self, connection_func: Callable) -> bool:
        """
        Attempt reconnection if disconnected and interval has passed.
        
        Args:
            connection_func: Function that returns a database connection
            
        Returns:
            True if connected (or reconnected), False otherwise
        """
        if self.is_connected:
            return True
        
        # Check if enough time has passed since last attempt
        now = datetime.now()
        if self.last_reconnect_attempt:
            elapsed = (now - self.last_reconnect_attempt).total_seconds()
            if elapsed < self.reconnect_interval:
                return False
        
        # Attempt reconnection
        self.last_reconnect_attempt = now
        self.logger.log_db_connection_change(self.db_type, "reconnecting")
        return self.connect(connection_func)
    
    def disconnect(self):
        """Mark connection as disconnected"""
        if self.is_connected:
            self.is_connected = False
            self.logger.log_db_connection_change(self.db_type, "disconnected")
    
    def execute_with_reconnect(
        self,
        operation: Callable,
        connection_func: Callable,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """
        Execute database operation with automatic reconnection.
        
        Args:
            operation: Database operation to execute
            connection_func: Function to create new connection
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation
            
        Returns:
            Operation result, or None if operation fails
        """
        # Try reconnecting if disconnected
        if not self.is_connected:
            self.reconnect_if_needed(connection_func)
        
        # If still not connected, return None
        if not self.is_connected:
            return None
        
        # Attempt operation
        try:
            result = operation(*args, **kwargs)
            return result
        except Exception as e:
            self.logger.error(
                "db_operation_failed",
                f"Database operation failed on {self.db_type}",
                error=e,
                database=self.db_type
            )
            self.disconnect()
            return None


class WriteQueue:
    """
    In-memory queue for database writes during PostgreSQL outage.
    
    Queues up to 1000 writes in memory and flushes when connection restored.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize write queue.
        
        Args:
            max_size: Maximum number of writes to queue
        """
        self.max_size = max_size
        self.queue: deque = deque(maxlen=max_size)
        self.lock = Lock()
        self.logger = get_logger("WriteQueue")
    
    def enqueue(self, operation: Callable, *args, **kwargs):
        """
        Add write operation to queue.
        
        Args:
            operation: Write operation function
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        with self.lock:
            if len(self.queue) >= self.max_size:
                self.logger.warning(
                    "write_queue_full",
                    f"Write queue full ({self.max_size} items), dropping oldest write",
                    queue_size=len(self.queue)
                )
            
            self.queue.append((operation, args, kwargs))
            self.logger.debug(
                "write_queued",
                f"Write operation queued (queue size: {len(self.queue)})",
                queue_size=len(self.queue)
            )
    
    def flush(self) -> int:
        """
        Flush all queued writes.
        
        Returns:
            Number of writes successfully flushed
        """
        with self.lock:
            if not self.queue:
                return 0
            
            success_count = 0
            failed_count = 0
            
            while self.queue:
                operation, args, kwargs = self.queue.popleft()
                try:
                    operation(*args, **kwargs)
                    success_count += 1
                except Exception as e:
                    failed_count += 1
                    self.logger.error(
                        "queued_write_failed",
                        "Failed to execute queued write",
                        error=e
                    )
            
            self.logger.info(
                "write_queue_flushed",
                f"Flushed write queue: {success_count} succeeded, {failed_count} failed",
                success_count=success_count,
                failed_count=failed_count
            )
            
            return success_count
    
    def size(self) -> int:
        """Get current queue size"""
        with self.lock:
            return len(self.queue)


class MemoryMonitor:
    """
    Monitors memory usage and triggers cleanup when threshold exceeded.
    
    Helps system stay within 512 MB RAM constraint of free hosting.
    """
    
    def __init__(self, warning_threshold_mb: float = 400.0, critical_threshold_mb: float = 480.0):
        """
        Initialize memory monitor.
        
        Args:
            warning_threshold_mb: Threshold for warning (default: 400 MB)
            critical_threshold_mb: Threshold for aggressive cleanup (default: 480 MB)
        """
        self.warning_threshold_mb = warning_threshold_mb
        self.critical_threshold_mb = critical_threshold_mb
        self.logger = get_logger("MemoryMonitor")
        self.process = psutil.Process()
    
    def get_memory_usage_mb(self) -> float:
        """
        Get current memory usage in MB.
        
        Returns:
            Memory usage in megabytes
        """
        return self.process.memory_info().rss / (1024 * 1024)
    
    def check_and_cleanup(self) -> bool:
        """
        Check memory usage and trigger cleanup if needed.
        
        Returns:
            True if cleanup was triggered, False otherwise
        """
        current_mb = self.get_memory_usage_mb()
        
        if current_mb >= self.critical_threshold_mb:
            self.logger.log_memory_warning(
                current_mb,
                self.critical_threshold_mb,
                severity="critical"
            )
            self._aggressive_cleanup()
            return True
        
        elif current_mb >= self.warning_threshold_mb:
            self.logger.log_memory_warning(
                current_mb,
                self.warning_threshold_mb,
                severity="warning"
            )
            self._standard_cleanup()
            return True
        
        return False
    
    def _standard_cleanup(self):
        """Perform standard garbage collection"""
        self.logger.debug(
            "memory_cleanup",
            "Performing standard memory cleanup"
        )
        gc.collect()
        
        after_mb = self.get_memory_usage_mb()
        self.logger.info(
            "memory_cleanup_complete",
            f"Memory cleanup complete: {after_mb:.1f} MB",
            memory_mb=after_mb
        )
    
    def _aggressive_cleanup(self):
        """Perform aggressive garbage collection"""
        self.logger.warning(
            "memory_cleanup_aggressive",
            "Performing aggressive memory cleanup"
        )
        
        # Force full garbage collection
        gc.collect(generation=2)
        
        after_mb = self.get_memory_usage_mb()
        self.logger.info(
            "memory_cleanup_complete",
            f"Aggressive cleanup complete: {after_mb:.1f} MB",
            memory_mb=after_mb
        )


class GracefulDegradation:
    """
    Manages graceful degradation when components fail.
    
    Allows system to continue operating with reduced functionality
    rather than complete failure.
    """
    
    def __init__(self):
        """Initialize graceful degradation manager"""
        self.degraded_components: set = set()
        self.logger = get_logger("GracefulDegradation")
    
    def mark_degraded(self, component: str, reason: str):
        """
        Mark a component as degraded.
        
        Args:
            component: Component name
            reason: Reason for degradation
        """
        if component not in self.degraded_components:
            self.degraded_components.add(component)
            self.logger.warning(
                "component_degraded",
                f"Component {component} operating in degraded mode: {reason}",
                component=component,
                reason=reason
            )
    
    def mark_recovered(self, component: str):
        """
        Mark a component as recovered.
        
        Args:
            component: Component name
        """
        if component in self.degraded_components:
            self.degraded_components.remove(component)
            self.logger.info(
                "component_recovered",
                f"Component {component} recovered from degraded mode",
                component=component
            )
    
    def is_degraded(self, component: str) -> bool:
        """
        Check if component is degraded.
        
        Args:
            component: Component name
            
        Returns:
            True if component is degraded
        """
        return component in self.degraded_components
    
    def get_degraded_components(self) -> List[str]:
        """
        Get list of all degraded components.
        
        Returns:
            List of degraded component names
        """
        return list(self.degraded_components)


class ResilientOperation:
    """
    Wrapper for operations that need resilience and graceful degradation.
    """
    
    def __init__(self, component: str):
        """
        Initialize resilient operation wrapper.
        
        Args:
            component: Component name
        """
        self.component = component
        self.logger = get_logger(f"ResilientOperation-{component}")
        self.degradation = GracefulDegradation()
    
    def execute_with_fallback(
        self,
        primary_operation: Callable,
        fallback_operation: Optional[Callable] = None,
        operation_name: str = "operation",
        *args,
        **kwargs
    ) -> Optional[Any]:
        """
        Execute operation with fallback on failure.
        
        Args:
            primary_operation: Primary operation to attempt
            fallback_operation: Fallback operation if primary fails
            operation_name: Name of operation for logging
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Operation result, or None if both primary and fallback fail
        """
        # Try primary operation
        try:
            result = primary_operation(*args, **kwargs)
            
            # Mark as recovered if was degraded
            if self.degradation.is_degraded(self.component):
                self.degradation.mark_recovered(self.component)
            
            return result
            
        except Exception as e:
            self.logger.error(
                "operation_failed",
                f"{operation_name} failed in {self.component}",
                error=e,
                operation=operation_name
            )
            
            # Try fallback if available
            if fallback_operation:
                try:
                    self.logger.warning(
                        "using_fallback",
                        f"Using fallback for {operation_name}",
                        operation=operation_name
                    )
                    
                    self.degradation.mark_degraded(
                        self.component,
                        f"{operation_name} using fallback"
                    )
                    
                    return fallback_operation(*args, **kwargs)
                    
                except Exception as fallback_error:
                    self.logger.error(
                        "fallback_failed",
                        f"Fallback also failed for {operation_name}",
                        error=fallback_error,
                        operation=operation_name
                    )
            
            return None


# Global instances for shared use
memory_monitor = MemoryMonitor()
write_queue = WriteQueue()


def handle_network_error(
    operation: Callable,
    max_retries: int = 3,
    backoff_base: float = 1.0,
    *args,
    **kwargs
) -> Optional[Any]:
    """
    Handle network errors with retry and exponential backoff.
    
    Args:
        operation: Network operation to execute
        max_retries: Maximum retry attempts
        backoff_base: Base delay for exponential backoff
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Operation result, or None if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            if attempt < max_retries:
                delay = backoff_base * (3 ** attempt)  # 1s, 3s, 9s
                logger.warning(
                    "network_retry",
                    f"Network operation failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay}s",
                    attempt=attempt + 1,
                    max_retries=max_retries + 1,
                    delay_seconds=delay,
                    error=str(e)
                )
                time.sleep(delay)
    
    logger.error(
        "network_operation_failed",
        f"Network operation failed after {max_retries + 1} attempts",
        error=last_exception
    )
    return None


def handle_rate_limit_error(reset_time: Optional[datetime] = None):
    """
    Handle rate limit error by waiting until reset time.
    
    Args:
        reset_time: When rate limit resets (if known)
    """
    if reset_time:
        wait_seconds = (reset_time - datetime.now()).total_seconds()
        if wait_seconds > 0:
            logger.warning(
                "rate_limit_wait",
                f"Rate limit hit, waiting {wait_seconds:.0f}s until reset",
                wait_seconds=wait_seconds
            )
            time.sleep(wait_seconds)
    else:
        # Default wait if reset time unknown
        logger.warning(
            "rate_limit_wait",
            "Rate limit hit, waiting 60s",
            wait_seconds=60
        )
        time.sleep(60)
