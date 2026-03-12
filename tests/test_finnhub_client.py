"""Unit tests for Finnhub client"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from decimal import Decimal
from time import time

from src.clients.finnhub_client import FinnhubClient
from src.models import Quote, NewsArticle


class TestFinnhubClient(unittest.TestCase):
    """Test cases for FinnhubClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.patcher_credential = patch('src.clients.finnhub_client.credential_manager')
        self.mock_credential_manager = self.patcher_credential.start()
        self.mock_credential_manager.get_credential.return_value = 'test_api_key'
        
        with patch('src.clients.finnhub_client.finnhub.Client'):
            self.client = FinnhubClient()
            self.client.client = Mock()
    
    def tearDown(self):
        """Clean up after tests"""
        self.patcher_credential.stop()


class TestRateLimiting(TestFinnhubClient):
    """Test rate limiting enforcement"""
    
    def test_rate_limit_enforcement_within_limit(self):
        """Test that requests within rate limit are allowed"""
        # Make requests within limit (60 per minute)
        for i in range(60):
            result = self.client._check_rate_limit()
            self.assertTrue(result)
    
    def test_rate_limit_enforcement_exceeds_limit(self):
        """Test that requests exceeding rate limit are blocked"""
        # Fill up the rate limit
        for i in range(60):
            self.client._check_rate_limit()
        
        # Next request should be blocked
        result = self.client._check_rate_limit()
        self.assertFalse(result)
    
    def test_rate_limit_window_expiration(self):
        """Test that rate limit resets after time window"""
        # Fill up the rate limit
        for i in range(60):
            self.client._check_rate_limit()
        
        # Simulate time passing (61 seconds)
        old_time = time() - 61
        self.client.request_timestamps = [old_time] * 60
        
        # Should be allowed now
        result = self.client._check_rate_limit()
        self.assertTrue(result)
    
    def test_rate_limit_timestamp_cleanup(self):
        """Test that old timestamps are cleaned up"""
        # Add old timestamps
        old_time = time() - 70
        self.client.request_timestamps = [old_time] * 30
        
        # Make a new request
        self.client._check_rate_limit()
        
        # Old timestamps should be removed
        self.assertEqual(len(self.client.request_timestamps), 1)


class TestGetQuote(TestFinnhubClient):
    """Test get_quote method"""
    
    def test_get_quote_success(self):
        """Test successful quote retrieval"""
        self.client.client.quote.return_value = {
            'c': 150.50,  # current price
            't': time(),  # timestamp
            'h': 152.0,   # high
            'l': 149.0,   # low
            'o': 150.0,   # open
            'pc': 149.5   # previous close
        }
        
        quote = self.client.get_quote('AAPL')
        
        self.assertIsNotNone(quote)
        self.assertIsInstance(quote, Quote)
        self.assertEqual(quote.symbol, 'AAPL')
        self.assertEqual(quote.price, Decimal('150.50'))
        self.assertIsInstance(quote.exchange_timestamp, datetime)
        self.assertIsInstance(quote.received_timestamp, datetime)
        self.client.client.quote.assert_called_once_with('AAPL')
    
    def test_get_quote_no_data(self):
        """Test quote retrieval when no data available"""
        self.client.client.quote.return_value = {}
        
        quote = self.client.get_quote('INVALID')
        
        self.assertIsNone(quote)
    
    def test_get_quote_rate_limit_exceeded(self):
        """Test quote retrieval when rate limit exceeded"""
        # Fill up rate limit
        for i in range(60):
            self.client._check_rate_limit()
        
        quote = self.client.get_quote('AAPL')
        
        self.assertIsNone(quote)
        # API should not be called
        self.client.client.quote.assert_not_called()
    
    def test_get_quote_exception(self):
        """Test quote retrieval with exception"""
        self.client.client.quote.side_effect = Exception("API error")
        
        quote = self.client.get_quote('AAPL')
        
        self.assertIsNone(quote)
    
    def test_get_quote_timestamp_recording(self):
        """Test that timestamps are properly recorded"""
        test_timestamp = time()
        self.client.client.quote.return_value = {
            'c': 150.50,
            't': test_timestamp
        }
        
        before = datetime.now()
        quote = self.client.get_quote('AAPL')
        after = datetime.now()
        
        self.assertIsNotNone(quote)
        self.assertGreaterEqual(quote.received_timestamp, before)
        self.assertLessEqual(quote.received_timestamp, after)
        self.assertEqual(quote.exchange_timestamp, datetime.fromtimestamp(test_timestamp))


class TestGetCompanyNews(TestFinnhubClient):
    """Test get_company_news method"""
    
    def test_get_company_news_success(self):
        """Test successful company news retrieval"""
        test_time = time()
        self.client.client.company_news.return_value = [
            {
                'headline': 'Apple announces new product',
                'summary': 'Apple has announced a new product line.',
                'source': 'TechCrunch',
                'datetime': test_time,
                'url': 'https://example.com/article1',
                'sentiment': 0.8
            },
            {
                'headline': 'Apple earnings beat expectations',
                'summary': 'Apple reported strong quarterly earnings.',
                'source': 'Bloomberg',
                'datetime': test_time - 3600,
                'url': 'https://example.com/article2',
                'sentiment': 0.9
            }
        ]
        
        from_date = date(2024, 1, 1)
        to_date = date(2024, 1, 31)
        articles = self.client.get_company_news('AAPL', from_date, to_date)
        
        self.assertEqual(len(articles), 2)
        self.assertIsInstance(articles[0], NewsArticle)
        self.assertEqual(articles[0].title, 'Apple announces new product')
        self.assertEqual(articles[0].source, 'TechCrunch')
        self.assertEqual(articles[0].sentiment, 0.8)
        self.client.client.company_news.assert_called_once_with(
            'AAPL',
            _from='2024-01-01',
            to='2024-01-31'
        )
    
    def test_get_company_news_no_data(self):
        """Test company news retrieval when no data available"""
        self.client.client.company_news.return_value = []
        
        articles = self.client.get_company_news('AAPL', date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(len(articles), 0)
    
    def test_get_company_news_rate_limit_exceeded(self):
        """Test company news retrieval when rate limit exceeded"""
        # Fill up rate limit
        for i in range(60):
            self.client._check_rate_limit()
        
        articles = self.client.get_company_news('AAPL', date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(len(articles), 0)
        self.client.client.company_news.assert_not_called()
    
    def test_get_company_news_exception(self):
        """Test company news retrieval with exception"""
        self.client.client.company_news.side_effect = Exception("API error")
        
        articles = self.client.get_company_news('AAPL', date(2024, 1, 1), date(2024, 1, 31))
        
        self.assertEqual(len(articles), 0)
    
    def test_get_company_news_partial_failure(self):
        """Test company news with some articles failing to parse"""
        test_time = time()
        self.client.client.company_news.return_value = [
            {
                'headline': 'Valid article',
                'summary': 'This is valid.',
                'source': 'Source1',
                'datetime': test_time,
                'url': 'https://example.com/1'
            },
            {
                # Missing required fields
                'headline': 'Invalid article'
            },
            {
                'headline': 'Another valid article',
                'summary': 'This is also valid.',
                'source': 'Source2',
                'datetime': test_time,
                'url': 'https://example.com/2'
            }
        ]
        
        articles = self.client.get_company_news('AAPL', date(2024, 1, 1), date(2024, 1, 31))
        
        # Should only get valid articles
        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0].title, 'Valid article')
        self.assertEqual(articles[1].title, 'Another valid article')


class TestGetMarketNews(TestFinnhubClient):
    """Test get_market_news method"""
    
    def test_get_market_news_success(self):
        """Test successful market news retrieval"""
        test_time = time()
        self.client.client.general_news.return_value = [
            {
                'headline': 'Market reaches new high',
                'summary': 'Stock market hits record levels.',
                'source': 'Reuters',
                'datetime': test_time,
                'url': 'https://example.com/market1'
            }
        ]
        
        articles = self.client.get_market_news('general')
        
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].title, 'Market reaches new high')
        self.assertEqual(articles[0].source, 'Reuters')
        self.assertIsNone(articles[0].sentiment)
        self.client.client.general_news.assert_called_once_with('general')
    
    def test_get_market_news_no_data(self):
        """Test market news retrieval when no data available"""
        self.client.client.general_news.return_value = []
        
        articles = self.client.get_market_news('forex')
        
        self.assertEqual(len(articles), 0)
    
    def test_get_market_news_rate_limit_exceeded(self):
        """Test market news retrieval when rate limit exceeded"""
        # Fill up rate limit
        for i in range(60):
            self.client._check_rate_limit()
        
        articles = self.client.get_market_news('general')
        
        self.assertEqual(len(articles), 0)
        self.client.client.general_news.assert_not_called()
    
    def test_get_market_news_exception(self):
        """Test market news retrieval with exception"""
        self.client.client.general_news.side_effect = Exception("API error")
        
        articles = self.client.get_market_news('general')
        
        self.assertEqual(len(articles), 0)


class TestGetCompanyProfile(TestFinnhubClient):
    """Test get_company_profile method"""
    
    def test_get_company_profile_success(self):
        """Test successful company profile retrieval"""
        self.client.client.company_profile2.return_value = {
            'name': 'Apple Inc.',
            'ticker': 'AAPL',
            'exchange': 'NASDAQ',
            'ipo': '1980-12-12',
            'marketCapitalization': 2800000,
            'shareOutstanding': 16000,
            'logo': 'https://example.com/logo.png',
            'phone': '1-408-996-1010',
            'weburl': 'https://www.apple.com'
        }
        
        profile = self.client.get_company_profile('AAPL')
        
        self.assertIsNotNone(profile)
        self.assertEqual(profile['name'], 'Apple Inc.')
        self.assertEqual(profile['ticker'], 'AAPL')
        self.client.client.company_profile2.assert_called_once_with(symbol='AAPL')
    
    def test_get_company_profile_no_data(self):
        """Test company profile retrieval when no data available"""
        self.client.client.company_profile2.return_value = None
        
        profile = self.client.get_company_profile('INVALID')
        
        self.assertIsNone(profile)
    
    def test_get_company_profile_rate_limit_exceeded(self):
        """Test company profile retrieval when rate limit exceeded"""
        # Fill up rate limit
        for i in range(60):
            self.client._check_rate_limit()
        
        profile = self.client.get_company_profile('AAPL')
        
        self.assertIsNone(profile)
        self.client.client.company_profile2.assert_not_called()
    
    def test_get_company_profile_exception(self):
        """Test company profile retrieval with exception"""
        self.client.client.company_profile2.side_effect = Exception("API error")
        
        profile = self.client.get_company_profile('AAPL')
        
        self.assertIsNone(profile)


class TestErrorHandling(TestFinnhubClient):
    """Test error handling and retries"""
    
    def test_api_error_returns_none(self):
        """Test that API errors return None gracefully"""
        self.client.client.quote.side_effect = Exception("Network error")
        
        quote = self.client.get_quote('AAPL')
        
        self.assertIsNone(quote)
    
    def test_invalid_response_handled(self):
        """Test that invalid API responses are handled"""
        self.client.client.quote.return_value = None
        
        quote = self.client.get_quote('AAPL')
        
        self.assertIsNone(quote)
    
    def test_missing_required_fields_handled(self):
        """Test that missing required fields are handled"""
        self.client.client.quote.return_value = {
            't': time()
            # Missing 'c' (current price)
        }
        
        quote = self.client.get_quote('AAPL')
        
        self.assertIsNone(quote)


if __name__ == '__main__':
    unittest.main()
