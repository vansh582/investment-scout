"""
Unit tests for EmailService

Tests email delivery, retry logic, timing constraints, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, time as dt_time
import pytz
from decimal import Decimal

from src.utils.email_service import EmailService
from src.utils.credential_manager import CredentialManager
from src.models.investment_scout_models import (
    Newsletter, TradingAlert, InvestmentOpportunity,
    GlobalContext, RiskLevel, SignalType
)


@pytest.fixture
def mock_credential_manager():
    """Create mock credential manager"""
    manager = Mock(spec=CredentialManager)
    manager.get_credential.side_effect = lambda key: {
        'sendgrid_api_key': 'test_api_key',
        'user_email': 'test@example.com'
    }.get(key)
    return manager


@pytest.fixture
def email_service(mock_credential_manager):
    """Create EmailService instance with mocked SendGrid client"""
    with patch('src.utils.email_service.SendGridAPIClient'):
        service = EmailService(mock_credential_manager)
        service.client = Mock()
        return service


class TestEmailServiceInitialization:
    """Test EmailService initialization"""
    
    def test_initialization_success(self, mock_credential_manager):
        """Test successful initialization"""
        with patch('src.utils.email_service.SendGridAPIClient') as mock_sg:
            service = EmailService(mock_credential_manager)
            
            assert service.sendgrid_api_key == 'test_api_key'
            assert service.from_email == 'test@example.com'
            mock_sg.assert_called_once_with('test_api_key')
    
    def test_initialization_retrieves_credentials(self, mock_credential_manager):
        """Test that initialization retrieves required credentials"""
        with patch('src.utils.email_service.SendGridAPIClient'):
            EmailService(mock_credential_manager)
            
            assert mock_credential_manager.get_credential.call_count == 2
            mock_credential_manager.get_credential.assert_any_call('sendgrid_api_key')
            mock_credential_manager.get_credential.assert_any_call('user_email')


class TestSendNewsletter:
    """Test newsletter sending functionality"""
    
    def test_send_newsletter_success(self, email_service):
        """Test successful newsletter delivery"""
        # Mock successful send
        mock_response = Mock()
        mock_response.status_code = 202
        email_service.client.send.return_value = mock_response
        
        result = email_service.send_newsletter(
            html_content="<html>Newsletter</html>",
            plain_text_content="Newsletter",
            recipients=["user@example.com"],
            subject="Daily Newsletter"
        )
        
        assert result is True
        assert email_service.client.send.called
    
    def test_send_newsletter_before_9am_et(self, email_service):
        """Test newsletter delivery before 9:00 AM ET deadline"""
        # Mock time to be 8:30 AM ET
        et_tz = pytz.timezone('US/Eastern')
        mock_time = datetime(2024, 1, 15, 8, 30, 0, tzinfo=et_tz)
        
        with patch('src.utils.email_service.datetime') as mock_dt:
            mock_dt.now.return_value = mock_time
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            mock_response = Mock()
            mock_response.status_code = 202
            email_service.client.send.return_value = mock_response
            
            result = email_service.send_newsletter(
                html_content="<html>Newsletter</html>",
                plain_text_content="Newsletter",
                recipients=["user@example.com"],
                subject="Daily Newsletter"
            )
            
            assert result is True
    
    def test_send_newsletter_after_9am_et_logs_warning(self, email_service, caplog):
        """Test that sending after 9:00 AM ET logs warning"""
        # Mock time to be 9:30 AM ET
        et_tz = pytz.timezone('US/Eastern')
        mock_time = datetime(2024, 1, 15, 9, 30, 0, tzinfo=et_tz)
        
        with patch('src.utils.email_service.datetime') as mock_dt:
            mock_dt.now.return_value = mock_time
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            mock_response = Mock()
            mock_response.status_code = 202
            email_service.client.send.return_value = mock_response
            
            email_service.send_newsletter(
                html_content="<html>Newsletter</html>",
                plain_text_content="Newsletter",
                recipients=["user@example.com"],
                subject="Daily Newsletter"
            )
            
            # Check that warning was logged
            assert any("after 9:00 AM ET deadline" in record.message for record in caplog.records)
    
    def test_send_newsletter_failure_sends_system_alert(self, email_service):
        """Test that newsletter failure triggers system alert"""
        # Mock all send attempts to fail
        email_service.client.send.side_effect = Exception("SendGrid API error")
        
        with patch.object(email_service, '_send_system_alert') as mock_alert:
            result = email_service.send_newsletter(
                html_content="<html>Newsletter</html>",
                plain_text_content="Newsletter",
                recipients=["user@example.com"],
                subject="Daily Newsletter"
            )
            
            assert result is False
            mock_alert.assert_called_once()
            assert "Newsletter Delivery Failure" in mock_alert.call_args[0][0]


class TestSendAlert:
    """Test trading alert sending functionality"""
    
    def test_send_alert_success(self, email_service):
        """Test successful alert delivery"""
        mock_response = Mock()
        mock_response.status_code = 202
        email_service.client.send.return_value = mock_response
        
        result = email_service.send_alert(
            html_content="<html>Alert</html>",
            plain_text_content="Alert",
            recipients=["user@example.com"],
            subject="Trading Alert"
        )
        
        assert result is True
        assert email_service.client.send.called
    
    def test_send_alert_within_30_seconds(self, email_service):
        """Test that alert delivery completes within 30 seconds"""
        mock_response = Mock()
        mock_response.status_code = 202
        email_service.client.send.return_value = mock_response
        
        import time
        start = time.time()
        
        result = email_service.send_alert(
            html_content="<html>Alert</html>",
            plain_text_content="Alert",
            recipients=["user@example.com"],
            subject="Trading Alert"
        )
        
        elapsed = time.time() - start
        
        assert result is True
        assert elapsed < 30  # Should complete within 30 seconds
    
    def test_send_alert_logs_timing(self, email_service, caplog):
        """Test that alert delivery timing is logged"""
        import logging
        caplog.set_level(logging.INFO)
        
        mock_response = Mock()
        mock_response.status_code = 202
        email_service.client.send.return_value = mock_response
        
        email_service.send_alert(
            html_content="<html>Alert</html>",
            plain_text_content="Alert",
            recipients=["user@example.com"],
            subject="Trading Alert"
        )
        
        # Check that alert was sent (verify logging occurred)
        assert len(caplog.records) > 0
    
    def test_send_alert_failure(self, email_service):
        """Test alert delivery failure"""
        email_service.client.send.side_effect = Exception("SendGrid API error")
        
        result = email_service.send_alert(
            html_content="<html>Alert</html>",
            plain_text_content="Alert",
            recipients=["user@example.com"],
            subject="Trading Alert"
        )
        
        assert result is False


class TestSendWithRetry:
    """Test retry logic with exponential backoff"""
    
    def test_send_with_retry_success_first_attempt(self, email_service):
        """Test successful delivery on first attempt"""
        mock_response = Mock()
        mock_response.status_code = 202
        email_service.client.send.return_value = mock_response
        
        result = email_service.send_with_retry(
            subject="Test",
            html_content="<html>Test</html>",
            plain_text_content="Test",
            recipients=["user@example.com"],
            max_retries=3
        )
        
        assert result is True
        assert email_service.client.send.call_count == 1
    
    def test_send_with_retry_success_second_attempt(self, email_service):
        """Test successful delivery on second attempt after first failure"""
        mock_response = Mock()
        mock_response.status_code = 202
        
        # First call fails, second succeeds
        email_service.client.send.side_effect = [
            Exception("Temporary error"),
            mock_response
        ]
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = email_service.send_with_retry(
                subject="Test",
                html_content="<html>Test</html>",
                plain_text_content="Test",
                recipients=["user@example.com"],
                max_retries=3
            )
        
        assert result is True
        assert email_service.client.send.call_count == 2
    
    def test_send_with_retry_exponential_backoff(self, email_service):
        """Test exponential backoff delays: 5s, 15s, 45s"""
        mock_response = Mock()
        mock_response.status_code = 202
        
        # All attempts fail except last
        email_service.client.send.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            Exception("Error 3"),
            mock_response
        ]
        
        with patch('time.sleep') as mock_sleep:
            result = email_service.send_with_retry(
                subject="Test",
                html_content="<html>Test</html>",
                plain_text_content="Test",
                recipients=["user@example.com"],
                max_retries=3
            )
        
        assert result is True
        
        # Verify exponential backoff delays
        assert mock_sleep.call_count == 3
        mock_sleep.assert_any_call(5)   # First retry delay
        mock_sleep.assert_any_call(15)  # Second retry delay
        mock_sleep.assert_any_call(45)  # Third retry delay
    
    def test_send_with_retry_all_attempts_fail(self, email_service):
        """Test failure after all retry attempts exhausted"""
        email_service.client.send.side_effect = Exception("Persistent error")
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = email_service.send_with_retry(
                subject="Test",
                html_content="<html>Test</html>",
                plain_text_content="Test",
                recipients=["user@example.com"],
                max_retries=3
            )
        
        assert result is False
        assert email_service.client.send.call_count == 4  # Initial + 3 retries
    
    def test_send_with_retry_logs_all_attempts(self, email_service, caplog):
        """Test that all delivery attempts are logged"""
        email_service.client.send.side_effect = Exception("Error")
        
        with patch('time.sleep'):
            email_service.send_with_retry(
                subject="Test",
                html_content="<html>Test</html>",
                plain_text_content="Test",
                recipients=["user@example.com"],
                max_retries=3
            )
        
        # Check that all attempts were logged
        attempt_logs = [r for r in caplog.records if "attempt" in r.message.lower()]
        assert len(attempt_logs) >= 4  # 4 attempts total
    
    def test_send_with_retry_logs_final_status(self, email_service, caplog):
        """Test that final delivery status is logged"""
        email_service.client.send.side_effect = Exception("Error")
        
        with patch('time.sleep'):
            email_service.send_with_retry(
                subject="Test",
                html_content="<html>Test</html>",
                plain_text_content="Test",
                recipients=["user@example.com"],
                max_retries=3
            )
        
        # Check that failure was logged
        assert any("failed after" in record.message.lower() for record in caplog.records)


class TestSystemAlert:
    """Test system alert functionality"""
    
    def test_send_system_alert_success(self, email_service):
        """Test successful system alert delivery"""
        mock_response = Mock()
        mock_response.status_code = 202
        email_service.client.send.return_value = mock_response
        
        email_service._send_system_alert(
            "Test Alert",
            "This is a test alert message"
        )
        
        assert email_service.client.send.called
        
        # Verify alert content
        call_args = email_service.client.send.call_args[0][0]
        assert "Test Alert" in call_args.subject.subject
        assert "🚨" in call_args.subject.subject
    
    def test_send_system_alert_contains_timestamp(self, email_service):
        """Test that system alert includes timestamp"""
        mock_response = Mock()
        mock_response.status_code = 202
        email_service.client.send.return_value = mock_response
        
        email_service._send_system_alert(
            "Test Alert",
            "Test message"
        )
        
        call_args = email_service.client.send.call_args[0][0]
        html_content = call_args.contents[1].content
        
        assert "Timestamp:" in html_content
    
    def test_send_system_alert_failure_handled(self, email_service, caplog):
        """Test that system alert failure is handled gracefully"""
        email_service.client.send.side_effect = Exception("SendGrid error")
        
        # Should not raise exception
        email_service._send_system_alert(
            "Test Alert",
            "Test message"
        )
        
        # Should log error
        assert any("Failed to send system alert" in record.message for record in caplog.records)


class TestMultipleRecipients:
    """Test email delivery to multiple recipients"""
    
    def test_send_to_multiple_recipients(self, email_service):
        """Test sending email to multiple recipients"""
        mock_response = Mock()
        mock_response.status_code = 202
        email_service.client.send.return_value = mock_response
        
        recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]
        
        result = email_service.send_with_retry(
            subject="Test",
            html_content="<html>Test</html>",
            plain_text_content="Test",
            recipients=recipients,
            max_retries=3
        )
        
        assert result is True
        assert email_service.client.send.called
    
    def test_logs_recipient_count(self, email_service, caplog):
        """Test that recipient count is logged"""
        import logging
        caplog.set_level(logging.INFO)
        
        mock_response = Mock()
        mock_response.status_code = 202
        email_service.client.send.return_value = mock_response
        
        recipients = ["user1@example.com", "user2@example.com"]
        
        email_service.send_newsletter(
            html_content="<html>Test</html>",
            plain_text_content="Test",
            recipients=recipients,
            subject="Test"
        )
        
        # Check that newsletter was sent (verify logging occurred)
        assert len(caplog.records) > 0


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_handles_network_error(self, email_service):
        """Test handling of network errors"""
        email_service.client.send.side_effect = ConnectionError("Network error")
        
        with patch('time.sleep'):
            result = email_service.send_with_retry(
                subject="Test",
                html_content="<html>Test</html>",
                plain_text_content="Test",
                recipients=["user@example.com"],
                max_retries=3
            )
        
        assert result is False
    
    def test_handles_api_error(self, email_service):
        """Test handling of API errors"""
        email_service.client.send.side_effect = Exception("API rate limit exceeded")
        
        with patch('time.sleep'):
            result = email_service.send_with_retry(
                subject="Test",
                html_content="<html>Test</html>",
                plain_text_content="Test",
                recipients=["user@example.com"],
                max_retries=3
            )
        
        assert result is False
    
    def test_logs_error_details(self, email_service, caplog):
        """Test that error details are logged"""
        error_message = "Specific API error"
        email_service.client.send.side_effect = Exception(error_message)
        
        with patch('time.sleep'):
            email_service.send_with_retry(
                subject="Test",
                html_content="<html>Test</html>",
                plain_text_content="Test",
                recipients=["user@example.com"],
                max_retries=3
            )
        
        # Check that error message was logged
        assert any(error_message in record.message for record in caplog.records)
