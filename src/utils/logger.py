"""
Structured Logging System for Investment Scout

Provides JSON-formatted structured logging with configurable log levels
and comprehensive event tracking across all system components.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum


class LogLevel(Enum):
    """Log levels for the system"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogger:
    """
    Structured logger that outputs JSON-formatted log entries.
    
    All log entries include:
    - timestamp: ISO 8601 formatted timestamp
    - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - component: Name of the component generating the log
    - event: Type of event being logged
    - message: Human-readable message
    - Additional context fields as needed
    """
    
    def __init__(self, component: str, log_level: str = "INFO"):
        """
        Initialize structured logger for a component.
        
        Args:
            component: Name of the component (e.g., "MarketMonitor", "EmailService")
            log_level: Minimum log level to output (default: INFO)
        """
        self.component = component
        self.log_level = getattr(logging, log_level.upper())
        
        # Create logger instance
        self.logger = logging.getLogger(component)
        self.logger.setLevel(self.log_level)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []
        
        # Create console handler with JSON formatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.log_level)
        handler.setFormatter(JSONFormatter())
        
        self.logger.addHandler(handler)
        self.logger.propagate = False
    
    def _log(self, level: str, event: str, message: str, **kwargs):
        """
        Internal method to create structured log entry.
        
        Args:
            level: Log level
            event: Event type
            message: Log message
            **kwargs: Additional context fields
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "component": self.component,
            "event": event,
            "message": message
        }
        
        # Add any additional context
        log_entry.update(kwargs)
        
        # Log at appropriate level
        log_method = getattr(self.logger, level.lower())
        log_method(json.dumps(log_entry))
    
    def debug(self, event: str, message: str, **kwargs):
        """Log DEBUG level message"""
        self._log("DEBUG", event, message, **kwargs)
    
    def info(self, event: str, message: str, **kwargs):
        """Log INFO level message"""
        self._log("INFO", event, message, **kwargs)
    
    def warning(self, event: str, message: str, **kwargs):
        """Log WARNING level message"""
        self._log("WARNING", event, message, **kwargs)
    
    def error(self, event: str, message: str, error: Optional[Exception] = None, **kwargs):
        """
        Log ERROR level message with optional exception details.
        
        Args:
            event: Event type
            message: Error message
            error: Exception object (will include stack trace)
            **kwargs: Additional context
        """
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_details"] = str(error)
            
            # Include stack trace for errors
            import traceback
            kwargs["stack_trace"] = traceback.format_exc()
        
        self._log("ERROR", event, message, **kwargs)
    
    def critical(self, event: str, message: str, error: Optional[Exception] = None, **kwargs):
        """
        Log CRITICAL level message with optional exception details.
        
        Args:
            event: Event type
            message: Critical error message
            error: Exception object (will include stack trace)
            **kwargs: Additional context
        """
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_details"] = str(error)
            
            # Include stack trace for critical errors
            import traceback
            kwargs["stack_trace"] = traceback.format_exc()
        
        self._log("CRITICAL", event, message, **kwargs)
    
    # Convenience methods for common events
    
    def log_startup(self, **kwargs):
        """Log component startup"""
        self.info("component_startup", f"{self.component} starting up", **kwargs)
    
    def log_shutdown(self, **kwargs):
        """Log component shutdown"""
        self.info("component_shutdown", f"{self.component} shutting down", **kwargs)
    
    def log_api_request(
        self,
        provider: str,
        endpoint: str,
        status: str,
        latency_ms: float,
        **kwargs
    ):
        """
        Log API request with timing information.
        
        Args:
            provider: API provider name (e.g., "yfinance", "finnhub")
            endpoint: API endpoint called
            status: Request status ("success", "failure", "rate_limited")
            latency_ms: Request latency in milliseconds
            **kwargs: Additional context
        """
        self.info(
            "api_request",
            f"API request to {provider} {endpoint}",
            provider=provider,
            endpoint=endpoint,
            status=status,
            latency_ms=latency_ms,
            **kwargs
        )
    
    def log_data_freshness_violation(
        self,
        symbol: str,
        latency_seconds: float,
        provider: str,
        **kwargs
    ):
        """
        Log data freshness violation (>30s latency).
        
        Args:
            symbol: Stock symbol
            latency_seconds: Data latency in seconds
            provider: Data provider
            **kwargs: Additional context
        """
        self.warning(
            "stale_data_detected",
            f"Stale data detected for {symbol} from {provider}",
            symbol=symbol,
            latency_seconds=latency_seconds,
            provider=provider,
            **kwargs
        )
    
    def log_failover(
        self,
        from_provider: str,
        to_provider: str,
        reason: str,
        **kwargs
    ):
        """
        Log failover event between providers.
        
        Args:
            from_provider: Provider that failed
            to_provider: Provider being failed over to
            reason: Reason for failover
            **kwargs: Additional context
        """
        self.warning(
            "failover_event",
            f"Failing over from {from_provider} to {to_provider}: {reason}",
            from_provider=from_provider,
            to_provider=to_provider,
            reason=reason,
            **kwargs
        )
    
    def log_newsletter_generation(
        self,
        opportunity_count: int,
        generation_time_ms: float,
        **kwargs
    ):
        """
        Log newsletter generation event.
        
        Args:
            opportunity_count: Number of opportunities in newsletter
            generation_time_ms: Time taken to generate newsletter
            **kwargs: Additional context
        """
        self.info(
            "newsletter_generated",
            f"Newsletter generated with {opportunity_count} opportunities",
            opportunity_count=opportunity_count,
            generation_time_ms=generation_time_ms,
            **kwargs
        )
    
    def log_newsletter_delivery(
        self,
        status: str,
        recipient_count: int,
        **kwargs
    ):
        """
        Log newsletter delivery event.
        
        Args:
            status: Delivery status ("success", "failure", "partial")
            recipient_count: Number of recipients
            **kwargs: Additional context
        """
        if status == "success":
            self.info(
                "newsletter_delivered",
                f"Newsletter delivered to {recipient_count} recipients",
                status=status,
                recipient_count=recipient_count,
                **kwargs
            )
        else:
            self.error(
                "newsletter_delivery_failed",
                f"Newsletter delivery failed for {recipient_count} recipients",
                status=status,
                recipient_count=recipient_count,
                **kwargs
            )
    
    def log_alert_generation(
        self,
        symbol: str,
        signal_type: str,
        generation_time_ms: float,
        **kwargs
    ):
        """
        Log trading alert generation.
        
        Args:
            symbol: Stock symbol
            signal_type: "BUY" or "SELL"
            generation_time_ms: Time taken to generate alert
            **kwargs: Additional context
        """
        self.info(
            "alert_generated",
            f"{signal_type} alert generated for {symbol}",
            symbol=symbol,
            signal_type=signal_type,
            generation_time_ms=generation_time_ms,
            **kwargs
        )
    
    def log_alert_delivery(
        self,
        symbol: str,
        signal_type: str,
        status: str,
        **kwargs
    ):
        """
        Log trading alert delivery.
        
        Args:
            symbol: Stock symbol
            signal_type: "BUY" or "SELL"
            status: Delivery status
            **kwargs: Additional context
        """
        if status == "success":
            self.info(
                "alert_delivered",
                f"{signal_type} alert for {symbol} delivered",
                symbol=symbol,
                signal_type=signal_type,
                status=status,
                **kwargs
            )
        else:
            self.error(
                "alert_delivery_failed",
                f"{signal_type} alert for {symbol} delivery failed",
                symbol=symbol,
                signal_type=signal_type,
                status=status,
                **kwargs
            )
    
    def log_performance_update(
        self,
        total_return: float,
        sp500_return: float,
        relative_performance: float,
        **kwargs
    ):
        """
        Log performance metric update.
        
        Args:
            total_return: Portfolio total return percentage
            sp500_return: S&P 500 return percentage
            relative_performance: Difference from S&P 500
            **kwargs: Additional context
        """
        self.info(
            "performance_updated",
            f"Performance: {total_return:.2f}% (S&P 500: {sp500_return:.2f}%, Relative: {relative_performance:+.2f}%)",
            total_return=total_return,
            sp500_return=sp500_return,
            relative_performance=relative_performance,
            **kwargs
        )
    
    def log_db_connection_change(
        self,
        database: str,
        status: str,
        **kwargs
    ):
        """
        Log database connection status change.
        
        Args:
            database: Database name ("redis", "postgresql")
            status: Connection status ("connected", "disconnected", "reconnecting")
            **kwargs: Additional context
        """
        if status == "connected":
            self.info(
                "db_connection_established",
                f"Connected to {database}",
                database=database,
                status=status,
                **kwargs
            )
        elif status == "disconnected":
            self.error(
                "db_connection_lost",
                f"Lost connection to {database}",
                database=database,
                status=status,
                **kwargs
            )
        else:
            self.warning(
                "db_connection_reconnecting",
                f"Reconnecting to {database}",
                database=database,
                status=status,
                **kwargs
            )
    
    def log_memory_warning(
        self,
        current_mb: float,
        threshold_mb: float,
        **kwargs
    ):
        """
        Log memory usage warning.
        
        Args:
            current_mb: Current memory usage in MB
            threshold_mb: Warning threshold in MB
            **kwargs: Additional context
        """
        self.warning(
            "memory_warning",
            f"Memory usage {current_mb:.1f} MB exceeds threshold {threshold_mb:.1f} MB",
            current_mb=current_mb,
            threshold_mb=threshold_mb,
            **kwargs
        )


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON.
    
    This formatter is used internally by StructuredLogger.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON string.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        # The message is already JSON from StructuredLogger
        return record.getMessage()


def get_logger(component: str, log_level: str = "INFO") -> StructuredLogger:
    """
    Factory function to create a structured logger for a component.
    
    Args:
        component: Component name
        log_level: Minimum log level (default: INFO)
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(component, log_level)



def setup_logging(log_level: str = "INFO"):
    """
    Set up global logging configuration.
    
    Args:
        log_level: Minimum log level (default: INFO)
    """
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
