"""
Unit tests for Structured Logging System
"""

import json
import pytest
from io import StringIO
import sys
from unittest.mock import patch

from src.utils.logger import StructuredLogger, get_logger, LogLevel


class TestStructuredLogger:
    """Test structured logging functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.component = "TestComponent"
        self.logger = StructuredLogger(self.component, "DEBUG")
    
    def _capture_log_output(self, log_func, *args, **kwargs):
        """Helper to capture log output"""
        # Capture stdout
        captured_output = StringIO()
        handler = self.logger.logger.handlers[0]
        old_stream = handler.stream
        handler.stream = captured_output
        
        try:
            log_func(*args, **kwargs)
            output = captured_output.getvalue()
            return json.loads(output.strip()) if output.strip() else None
        finally:
            handler.stream = old_stream
    
    def test_debug_log(self):
        """Test DEBUG level logging"""
        log_entry = self._capture_log_output(
            self.logger.debug,
            "test_event",
            "Debug message",
            extra_field="value"
        )
        
        assert log_entry is not None
        assert log_entry["level"] == "DEBUG"
        assert log_entry["component"] == self.component
        assert log_entry["event"] == "test_event"
        assert log_entry["message"] == "Debug message"
        assert log_entry["extra_field"] == "value"
        assert "timestamp" in log_entry
    
    def test_info_log(self):
        """Test INFO level logging"""
        log_entry = self._capture_log_output(
            self.logger.info,
            "test_event",
            "Info message"
        )
        
        assert log_entry["level"] == "INFO"
        assert log_entry["message"] == "Info message"
    
    def test_warning_log(self):
        """Test WARNING level logging"""
        log_entry = self._capture_log_output(
            self.logger.warning,
            "test_event",
            "Warning message"
        )
        
        assert log_entry["level"] == "WARNING"
        assert log_entry["message"] == "Warning message"
    
    def test_error_log_with_exception(self):
        """Test ERROR level logging with exception"""
        try:
            raise ValueError("Test error")
        except ValueError as e:
            log_entry = self._capture_log_output(
                self.logger.error,
                "test_event",
                "Error occurred",
                error=e
            )
        
        assert log_entry["level"] == "ERROR"
        assert log_entry["error_type"] == "ValueError"
        assert log_entry["error_details"] == "Test error"
        assert "stack_trace" in log_entry
    
    def test_critical_log_with_exception(self):
        """Test CRITICAL level logging with exception"""
        try:
            raise RuntimeError("Critical error")
        except RuntimeError as e:
            log_entry = self._capture_log_output(
                self.logger.critical,
                "test_event",
                "Critical error occurred",
                error=e
            )
        
        assert log_entry["level"] == "CRITICAL"
        assert log_entry["error_type"] == "RuntimeError"
        assert log_entry["error_details"] == "Critical error"
        assert "stack_trace" in log_entry
    
    def test_log_startup(self):
        """Test component startup logging"""
        log_entry = self._capture_log_output(
            self.logger.log_startup,
            version="1.0.0"
        )
        
        assert log_entry["event"] == "component_startup"
        assert log_entry["version"] == "1.0.0"
    
    def test_log_shutdown(self):
        """Test component shutdown logging"""
        log_entry = self._capture_log_output(
            self.logger.log_shutdown
        )
        
        assert log_entry["event"] == "component_shutdown"
    
    def test_log_api_request(self):
        """Test API request logging"""
        log_entry = self._capture_log_output(
            self.logger.log_api_request,
            provider="yfinance",
            endpoint="/quote/AAPL",
            status="success",
            latency_ms=125.5
        )
        
        assert log_entry["event"] == "api_request"
        assert log_entry["provider"] == "yfinance"
        assert log_entry["endpoint"] == "/quote/AAPL"
        assert log_entry["status"] == "success"
        assert log_entry["latency_ms"] == 125.5
    
    def test_log_data_freshness_violation(self):
        """Test data freshness violation logging"""
        log_entry = self._capture_log_output(
            self.logger.log_data_freshness_violation,
            symbol="AAPL",
            latency_seconds=45.2,
            provider="finnhub"
        )
        
        assert log_entry["level"] == "WARNING"
        assert log_entry["event"] == "stale_data_detected"
        assert log_entry["symbol"] == "AAPL"
        assert log_entry["latency_seconds"] == 45.2
        assert log_entry["provider"] == "finnhub"
    
    def test_log_failover(self):
        """Test failover event logging"""
        log_entry = self._capture_log_output(
            self.logger.log_failover,
            from_provider="yfinance",
            to_provider="finnhub",
            reason="timeout"
        )
        
        assert log_entry["level"] == "WARNING"
        assert log_entry["event"] == "failover_event"
        assert log_entry["from_provider"] == "yfinance"
        assert log_entry["to_provider"] == "finnhub"
        assert log_entry["reason"] == "timeout"
    
    def test_log_newsletter_generation(self):
        """Test newsletter generation logging"""
        log_entry = self._capture_log_output(
            self.logger.log_newsletter_generation,
            opportunity_count=3,
            generation_time_ms=1250.0
        )
        
        assert log_entry["event"] == "newsletter_generated"
        assert log_entry["opportunity_count"] == 3
        assert log_entry["generation_time_ms"] == 1250.0
    
    def test_log_newsletter_delivery_success(self):
        """Test successful newsletter delivery logging"""
        log_entry = self._capture_log_output(
            self.logger.log_newsletter_delivery,
            status="success",
            recipient_count=5
        )
        
        assert log_entry["level"] == "INFO"
        assert log_entry["event"] == "newsletter_delivered"
        assert log_entry["status"] == "success"
        assert log_entry["recipient_count"] == 5
    
    def test_log_newsletter_delivery_failure(self):
        """Test failed newsletter delivery logging"""
        log_entry = self._capture_log_output(
            self.logger.log_newsletter_delivery,
            status="failure",
            recipient_count=5
        )
        
        assert log_entry["level"] == "ERROR"
        assert log_entry["event"] == "newsletter_delivery_failed"
        assert log_entry["status"] == "failure"
    
    def test_log_alert_generation(self):
        """Test trading alert generation logging"""
        log_entry = self._capture_log_output(
            self.logger.log_alert_generation,
            symbol="TSLA",
            signal_type="BUY",
            generation_time_ms=85.0
        )
        
        assert log_entry["event"] == "alert_generated"
        assert log_entry["symbol"] == "TSLA"
        assert log_entry["signal_type"] == "BUY"
        assert log_entry["generation_time_ms"] == 85.0
    
    def test_log_alert_delivery_success(self):
        """Test successful alert delivery logging"""
        log_entry = self._capture_log_output(
            self.logger.log_alert_delivery,
            symbol="TSLA",
            signal_type="BUY",
            status="success"
        )
        
        assert log_entry["level"] == "INFO"
        assert log_entry["event"] == "alert_delivered"
    
    def test_log_alert_delivery_failure(self):
        """Test failed alert delivery logging"""
        log_entry = self._capture_log_output(
            self.logger.log_alert_delivery,
            symbol="TSLA",
            signal_type="SELL",
            status="failure"
        )
        
        assert log_entry["level"] == "ERROR"
        assert log_entry["event"] == "alert_delivery_failed"
    
    def test_log_performance_update(self):
        """Test performance metric update logging"""
        log_entry = self._capture_log_output(
            self.logger.log_performance_update,
            total_return=12.5,
            sp500_return=8.3,
            relative_performance=4.2
        )
        
        assert log_entry["event"] == "performance_updated"
        assert log_entry["total_return"] == 12.5
        assert log_entry["sp500_return"] == 8.3
        assert log_entry["relative_performance"] == 4.2
    
    def test_log_db_connection_established(self):
        """Test database connection established logging"""
        log_entry = self._capture_log_output(
            self.logger.log_db_connection_change,
            database="redis",
            status="connected"
        )
        
        assert log_entry["level"] == "INFO"
        assert log_entry["event"] == "db_connection_established"
        assert log_entry["database"] == "redis"
    
    def test_log_db_connection_lost(self):
        """Test database connection lost logging"""
        log_entry = self._capture_log_output(
            self.logger.log_db_connection_change,
            database="postgresql",
            status="disconnected"
        )
        
        assert log_entry["level"] == "ERROR"
        assert log_entry["event"] == "db_connection_lost"
    
    def test_log_db_connection_reconnecting(self):
        """Test database reconnection logging"""
        log_entry = self._capture_log_output(
            self.logger.log_db_connection_change,
            database="redis",
            status="reconnecting"
        )
        
        assert log_entry["level"] == "WARNING"
        assert log_entry["event"] == "db_connection_reconnecting"
    
    def test_log_memory_warning(self):
        """Test memory usage warning logging"""
        log_entry = self._capture_log_output(
            self.logger.log_memory_warning,
            current_mb=425.5,
            threshold_mb=400.0
        )
        
        assert log_entry["level"] == "WARNING"
        assert log_entry["event"] == "memory_warning"
        assert log_entry["current_mb"] == 425.5
        assert log_entry["threshold_mb"] == 400.0
    
    def test_get_logger_factory(self):
        """Test logger factory function"""
        logger = get_logger("FactoryTest", "DEBUG")
        
        assert isinstance(logger, StructuredLogger)
        assert logger.component == "FactoryTest"
    
    def test_log_level_filtering(self):
        """Test that log level filtering works"""
        # Create logger with INFO level
        info_logger = StructuredLogger("InfoTest", "INFO")
        
        # Capture stdout
        captured_output = StringIO()
        handler = info_logger.logger.handlers[0]
        old_stream = handler.stream
        handler.stream = captured_output
        
        try:
            # DEBUG should not appear
            info_logger.debug("test_event", "Debug message")
            debug_output = captured_output.getvalue()
            
            # INFO should appear
            info_logger.info("test_event", "Info message")
            info_output = captured_output.getvalue()
            
            # DEBUG message should not be logged
            assert "Debug message" not in debug_output
            # INFO message should be logged
            assert "Info message" in info_output
        finally:
            handler.stream = old_stream
    
    def test_structured_format(self):
        """Test that all logs follow structured JSON format"""
        log_entry = self._capture_log_output(
            self.logger.info,
            "test_event",
            "Test message",
            custom_field="custom_value"
        )
        
        # Verify required fields
        required_fields = ["timestamp", "level", "component", "event", "message"]
        for field in required_fields:
            assert field in log_entry, f"Missing required field: {field}"
        
        # Verify custom field is included
        assert log_entry["custom_field"] == "custom_value"
        
        # Verify timestamp format (ISO 8601)
        assert log_entry["timestamp"].endswith("Z")
        assert "T" in log_entry["timestamp"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
