"""Unit tests for Twelve Data client"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal
from time import time

from src.clients.twelve_data_client import TwelveDataClient
from src.models import Quote


class TestTwelveDataClient(unittest.TestCase):
    """Test cases for TwelveDataClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.patcher_credential = patch('src.clients.twelve_data_client.credential_manager')
        self.mock_credential_manager = self.patcher_credential.start()
        self.mock_credential_manager.get_credential.return_value = 'test_api_key'
        
        with patch('src.clients.twelve_data_client.TDClient'):
            self.client = TwelveDataClient()
            self.client.client = Mock()
    
    def tearDown(self):
        """Clean up after tests"""
        self.patcher_credential.stop()


class TestRateLimiting(TestTwelveDataClient):
    """Test rate limiting enforcement"""
    
    def test_rate_limit_enforcement_within_limit(self):
        """Test that requests within rate limit are allowed"""
        # Make requests within limit (8 per minute)
        for i in range(8):
            result = self.client._check_rate_limit()
            self.assertTrue(result)
    
    def test_rate_limit_enforcement_exceeds_per_minute_limit(self):
        """Test that requests exceeding per-minute rate limit are blocked"""
        # Fill up the per-minute rate limit
        for i in range(8):
            self.client._check_rate_limit()
        
        # Next request should be blocked
        result = self.client._check_rate_limit()
        self.assertFalse(result)
    
    def test_rate_limit_enforcement_exceeds_daily_limit(self):
        """Test that requests exceeding daily credit limit are blocked"""
        # Set daily credits to limit
        self.client.daily_credits_used = 800
        
        result = self.client._check_rate_limit()
        
        self.assertFalse(result)
    
    def test_rate_limit_window_expiration(self):
        """Test that per-minute rate limit resets after time window"""
        # Fill up the rate limit
        for i in range(8):
            self.client._check_rate_limit()
        
        # Simulate time passing (61 seconds)
        old_time = time() - 61
        self.client.request_timestamps = [old_time] * 8
        
        # Should be allowed now
        result = self.client._check_rate_limit()
        self.assertTrue(result)
    
    def test_daily_credit_reset(self):
        """Test that daily credits reset at midnight"""
        # Set credits to limit
        self.client.daily_credits_used = 800
        
        # Set reset time to past
        self.client.credits_reset_time = datetime.now() - timedelta(hours=1)
        
        # Should reset and allow request
        result = self.client._check_rate_limit()
        self.assertTrue(result)
        self.assertEqual(self.client.daily_credits_used, 1)
    
    def test_rate_limit_timestamp_cleanup(self):
        """Test that old timestamps are cleaned up"""
        # Add old timestamps
        old_time = time() - 70
        self.client.request_timestamps = [old_time] * 5
        
        # Make a new request
        self.client._check_rate_limit()
        
        # Old timestamps should be removed
        self.assertEqual(len(self.client.request_timestamps), 1)
    
    def test_daily_credit_tracking(self):
        """Test that daily credits are properly tracked"""
        initial_credits = self.client.daily_credits_used
        
        self.client._check_rate_limit()
        
        self.assertEqual(self.client.daily_credits_used, initial_credits + 1)


class TestGetQuote(TestTwelveDataClient):
    """Test get_quote method"""
    
    def test_get_quote_success(self):
        """Test successful quote retrieval"""
        mock_ts = Mock()
        mock_ts.as_json.return_value = [
            {
                'datetime': '2024-01-15T10:30:00',
                'close': '150.50',
                'volume': '1000000'
            }
        ]
        self.client.client.time_series.return_value = mock_ts
        
        quote = self.client.get_quote('AAPL')
        
        self.assertIsNotNone(quote)
        self.assertIsInstance(quote, Quote)
        self.assertEqual(quote.symbol, 'AAPL')
        self.assertEqual(quote.price, Decimal('150.50'))
        self.assertEqual(quote.volume, 1000000)
        self.assertIsInstance(quote.exchange_timestamp, datetime)
        self.assertIsInstance(quote.received_timestamp, datetime)
        self.client.client.time_series.assert_called_once_with(
            symbol='AAPL',
            interval='1min',
            outputsize=1
        )
    
    def test_get_quote_no_data(self):
        """Test quote retrieval when no data available"""
        mock_ts = Mock()
        mock_ts.as_json.return_value = []
        self.client.client.time_series.return_value = mock_ts
        
        quote = self.client.get_quote('INVALID')
        
        self.assertIsNone(quote)
    
    def test_get_quote_rate_limit_exceeded(self):
        """Test quote retrieval when rate limit exceeded"""
        # Fill up rate limit
        for i in range(8):
            self.client._check_rate_limit()
        
        quote = self.client.get_quote('AAPL')
        
        self.assertIsNone(quote)
        # API should not be called
        self.client.client.time_series.assert_not_called()
    
    def test_get_quote_exception(self):
        """Test quote retrieval with exception"""
        self.client.client.time_series.side_effect = Exception("API error")
        
        quote = self.client.get_quote('AAPL')
        
        self.assertIsNone(quote)
    
    def test_get_quote_timestamp_recording(self):
        """Test that timestamps are properly recorded"""
        test_datetime = '2024-01-15T10:30:00'
        mock_ts = Mock()
        mock_ts.as_json.return_value = [
            {
                'datetime': test_datetime,
                'close': '150.50',
                'volume': '1000000'
            }
        ]
        self.client.client.time_series.return_value = mock_ts
        
        before = datetime.now()
        quote = self.client.get_quote('AAPL')
        after = datetime.now()
        
        self.assertIsNotNone(quote)
        self.assertGreaterEqual(quote.received_timestamp, before)
        self.assertLessEqual(quote.received_timestamp, after)
        self.assertEqual(quote.exchange_timestamp, datetime.fromisoformat(test_datetime))
    
    def test_get_quote_invalid_timestamp(self):
        """Test quote retrieval with invalid timestamp format"""
        mock_ts = Mock()
        mock_ts.as_json.return_value = [
            {
                'datetime': 'invalid-timestamp',
                'close': '150.50',
                'volume': '1000000'
            }
        ]
        self.client.client.time_series.return_value = mock_ts
        
        quote = self.client.get_quote('AAPL')
        
        # Should still return quote with received_timestamp as exchange_timestamp
        self.assertIsNotNone(quote)
        self.assertEqual(quote.exchange_timestamp, quote.received_timestamp)


class TestGetTimeSeries(TestTwelveDataClient):
    """Test get_time_series method"""
    
    def test_get_time_series_success(self):
        """Test successful time series retrieval"""
        mock_ts = Mock()
        mock_data = [
            {
                'datetime': '2024-01-15',
                'open': '150.00',
                'high': '152.00',
                'low': '149.00',
                'close': '151.00',
                'volume': '1000000'
            },
            {
                'datetime': '2024-01-14',
                'open': '149.00',
                'high': '151.00',
                'low': '148.00',
                'close': '150.00',
                'volume': '950000'
            }
        ]
        mock_ts.as_json.return_value = mock_data
        self.client.client.time_series.return_value = mock_ts
        
        data = self.client.get_time_series('AAPL', '1day')
        
        self.assertIsNotNone(data)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['close'], '151.00')
        self.client.client.time_series.assert_called_once_with(
            symbol='AAPL',
            interval='1day',
            outputsize=30
        )
    
    def test_get_time_series_no_data(self):
        """Test time series retrieval when no data available"""
        mock_ts = Mock()
        mock_ts.as_json.return_value = None
        self.client.client.time_series.return_value = mock_ts
        
        data = self.client.get_time_series('INVALID')
        
        self.assertIsNone(data)
    
    def test_get_time_series_rate_limit_exceeded(self):
        """Test time series retrieval when rate limit exceeded"""
        # Fill up rate limit
        for i in range(8):
            self.client._check_rate_limit()
        
        data = self.client.get_time_series('AAPL')
        
        self.assertIsNone(data)
        self.client.client.time_series.assert_not_called()
    
    def test_get_time_series_exception(self):
        """Test time series retrieval with exception"""
        self.client.client.time_series.side_effect = Exception("API error")
        
        data = self.client.get_time_series('AAPL')
        
        self.assertIsNone(data)
    
    def test_get_time_series_custom_interval(self):
        """Test time series retrieval with custom interval"""
        mock_ts = Mock()
        mock_ts.as_json.return_value = [{'close': '150.00'}]
        self.client.client.time_series.return_value = mock_ts
        
        data = self.client.get_time_series('AAPL', '1h')
        
        self.assertIsNotNone(data)
        self.client.client.time_series.assert_called_once_with(
            symbol='AAPL',
            interval='1h',
            outputsize=30
        )


class TestGetCompanyProfile(TestTwelveDataClient):
    """Test get_company_profile method"""
    
    def test_get_company_profile_not_available(self):
        """Test that company profile is not available in free tier"""
        profile = self.client.get_company_profile('AAPL')
        
        # Should return None as it's not available in free tier
        self.assertIsNone(profile)
    
    def test_get_company_profile_rate_limit_exceeded(self):
        """Test company profile retrieval when rate limit exceeded"""
        # Fill up rate limit
        for i in range(8):
            self.client._check_rate_limit()
        
        profile = self.client.get_company_profile('AAPL')
        
        self.assertIsNone(profile)
    
    def test_get_company_profile_exception(self):
        """Test company profile retrieval with exception"""
        # Even with exception, should return None gracefully
        profile = self.client.get_company_profile('AAPL')
        
        self.assertIsNone(profile)


class TestErrorHandling(TestTwelveDataClient):
    """Test error handling and retries"""
    
    def test_api_error_returns_none(self):
        """Test that API errors return None gracefully"""
        self.client.client.time_series.side_effect = Exception("Network error")
        
        quote = self.client.get_quote('AAPL')
        
        self.assertIsNone(quote)
    
    def test_invalid_response_handled(self):
        """Test that invalid API responses are handled"""
        mock_ts = Mock()
        mock_ts.as_json.return_value = None
        self.client.client.time_series.return_value = mock_ts
        
        quote = self.client.get_quote('AAPL')
        
        self.assertIsNone(quote)
    
    def test_missing_required_fields_handled(self):
        """Test that missing required fields are handled"""
        mock_ts = Mock()
        mock_ts.as_json.return_value = [
            {
                'datetime': '2024-01-15T10:30:00'
                # Missing 'close' price
            }
        ]
        self.client.client.time_series.return_value = mock_ts
        
        quote = self.client.get_quote('AAPL')
        
        # Should handle missing price gracefully
        self.assertIsNotNone(quote)
        self.assertEqual(quote.price, Decimal('0'))


class TestDailyLimitManagement(TestTwelveDataClient):
    """Test daily credit limit management"""
    
    def test_daily_limit_initialization(self):
        """Test that daily limit is properly initialized"""
        self.assertEqual(self.client.daily_credit_limit, 800)
        self.assertEqual(self.client.daily_credits_used, 0)
    
    def test_daily_limit_reset_time_set(self):
        """Test that reset time is set on first check"""
        self.client.credits_reset_time = None
        
        self.client._check_rate_limit()
        
        self.assertIsNotNone(self.client.credits_reset_time)
        self.assertIsInstance(self.client.credits_reset_time, datetime)
    
    def test_daily_limit_prevents_requests(self):
        """Test that daily limit prevents further requests"""
        self.client.daily_credits_used = 800
        
        result = self.client._check_rate_limit()
        
        self.assertFalse(result)
    
    def test_daily_limit_resets_at_midnight(self):
        """Test that daily limit resets at midnight"""
        self.client.daily_credits_used = 800
        self.client.credits_reset_time = datetime.now() - timedelta(hours=1)
        
        result = self.client._check_rate_limit()
        
        self.assertTrue(result)
        self.assertEqual(self.client.daily_credits_used, 1)
        # Reset time should be set to next midnight
        self.assertGreater(self.client.credits_reset_time, datetime.now())


if __name__ == '__main__':
    unittest.main()
