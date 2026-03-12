"""Unit tests for Robinhood API client"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.clients.robinhood_client import RobinhoodClient, TradingHours
from src.models import Security


class TestRobinhoodClient(unittest.TestCase):
    """Test cases for RobinhoodClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.patcher_credential = patch('src.clients.robinhood_client.credential_manager')
        self.mock_credential_manager = self.patcher_credential.start()
        self.mock_credential_manager.get_credential.side_effect = lambda key: {
            'robinhood_username': 'test_user',
            'robinhood_password': 'test_pass'
        }.get(key)
        
        self.client = RobinhoodClient()
    
    def tearDown(self):
        """Clean up after tests"""
        self.patcher_credential.stop()


class TestAuthentication(TestRobinhoodClient):
    """Test authentication flow"""
    
    @patch('src.clients.robinhood_client.rh.login')
    def test_authenticate_success(self, mock_login):
        """Test successful authentication"""
        mock_login.return_value = {'success': True}
        
        result = self.client._authenticate()
        
        self.assertTrue(result)
        self.assertTrue(self.client._authenticated)
        mock_login.assert_called_once_with('test_user', 'test_pass')
    
    @patch('src.clients.robinhood_client.rh.login')
    def test_authenticate_failure(self, mock_login):
        """Test failed authentication"""
        mock_login.return_value = None
        
        result = self.client._authenticate()
        
        self.assertFalse(result)
        self.assertFalse(self.client._authenticated)
    
    @patch('src.clients.robinhood_client.rh.login')
    def test_authenticate_exception(self, mock_login):
        """Test authentication with exception"""
        mock_login.side_effect = Exception("Network error")
        
        result = self.client._authenticate()
        
        self.assertFalse(result)
        self.assertFalse(self.client._authenticated)
    
    @patch('src.clients.robinhood_client.rh.login')
    def test_authenticate_already_authenticated(self, mock_login):
        """Test authentication when already authenticated"""
        self.client._authenticated = True
        
        result = self.client._authenticate()
        
        self.assertTrue(result)
        mock_login.assert_not_called()


class TestTradeableSecurities(TestRobinhoodClient):
    """Test tradeable securities fetching and caching"""
    
    @patch('src.clients.robinhood_client.rh.get_latest_price')
    @patch('src.clients.robinhood_client.rh.get_instrument_by_symbol')
    @patch('src.clients.robinhood_client.rh.get_all_stocks_from_market_tag')
    @patch('src.clients.robinhood_client.rh.login')
    def test_get_tradeable_securities_success(self, mock_login, mock_get_stocks, 
                                             mock_get_instrument, mock_get_price):
        """Test successful fetching of tradeable securities"""
        mock_login.return_value = {'success': True}
        mock_get_stocks.return_value = [
            {'symbol': 'AAPL'},
            {'symbol': 'GOOGL'},
        ]
        mock_get_instrument.side_effect = [
            {
                'symbol': 'AAPL',
                'simple_name': 'Apple Inc.',
                'tradeable': True,
                'fractional_tradability': 'tradable'
            },
            {
                'symbol': 'GOOGL',
                'simple_name': 'Alphabet Inc.',
                'tradeable': True,
                'fractional_tradability': 'untradable'
            }
        ]
        mock_get_price.return_value = ['150.00']
        
        securities = self.client.get_tradeable_securities()
        
        self.assertEqual(len(securities), 2)
        self.assertEqual(securities[0].symbol, 'AAPL')
        self.assertEqual(securities[0].name, 'Apple Inc.')
        self.assertTrue(securities[0].tradeable_on_robinhood)
        self.assertTrue(securities[0].supports_fractional_shares)
        self.assertEqual(securities[1].symbol, 'GOOGL')
        self.assertFalse(securities[1].supports_fractional_shares)
    
    @patch('src.clients.robinhood_client.rh.get_latest_price')
    @patch('src.clients.robinhood_client.rh.get_instrument_by_symbol')
    @patch('src.clients.robinhood_client.rh.get_all_stocks_from_market_tag')
    @patch('src.clients.robinhood_client.rh.login')
    def test_get_tradeable_securities_filters_untradeable(self, mock_login, mock_get_stocks,
                                                          mock_get_instrument, mock_get_price):
        """Test that untradeable securities are filtered out"""
        mock_login.return_value = {'success': True}
        mock_get_stocks.return_value = [
            {'symbol': 'AAPL'},
            {'symbol': 'UNTRADE'},
        ]
        mock_get_instrument.side_effect = [
            {
                'symbol': 'AAPL',
                'simple_name': 'Apple Inc.',
                'tradeable': True,
                'fractional_tradability': 'tradable'
            },
            {
                'symbol': 'UNTRADE',
                'simple_name': 'Untradeable Stock',
                'tradeable': False,
                'fractional_tradability': 'untradable'
            }
        ]
        mock_get_price.return_value = ['150.00']
        
        securities = self.client.get_tradeable_securities()
        
        self.assertEqual(len(securities), 1)
        self.assertEqual(securities[0].symbol, 'AAPL')
    
    @patch('src.clients.robinhood_client.rh.get_all_stocks_from_market_tag')
    @patch('src.clients.robinhood_client.rh.login')
    def test_get_tradeable_securities_caching(self, mock_login, mock_get_stocks):
        """Test that tradeable securities are cached for 24 hours"""
        mock_login.return_value = {'success': True}
        mock_get_stocks.return_value = []
        
        # First call - should fetch from API
        securities1 = self.client.get_tradeable_securities()
        self.assertEqual(mock_get_stocks.call_count, 1)
        
        # Second call - should use cache
        securities2 = self.client.get_tradeable_securities()
        self.assertEqual(mock_get_stocks.call_count, 1)  # No additional call
        
        # Verify cache was used
        self.assertIs(securities1, securities2)
    
    @patch('src.clients.robinhood_client.rh.get_all_stocks_from_market_tag')
    @patch('src.clients.robinhood_client.rh.login')
    def test_get_tradeable_securities_cache_expiration(self, mock_login, mock_get_stocks):
        """Test that cache expires after 24 hours"""
        mock_login.return_value = {'success': True}
        mock_get_stocks.return_value = []
        
        # First call
        self.client.get_tradeable_securities()
        self.assertEqual(mock_get_stocks.call_count, 1)
        
        # Simulate cache expiration
        self.client._cache_timestamp = datetime.now() - timedelta(hours=25)
        
        # Second call - should fetch from API again
        self.client.get_tradeable_securities()
        self.assertEqual(mock_get_stocks.call_count, 2)
    
    @patch('src.clients.robinhood_client.rh.login')
    def test_get_tradeable_securities_authentication_failure(self, mock_login):
        """Test handling of authentication failure"""
        mock_login.return_value = None
        
        securities = self.client.get_tradeable_securities()
        
        self.assertEqual(len(securities), 0)
    
    @patch('src.clients.robinhood_client.rh.get_all_stocks_from_market_tag')
    @patch('src.clients.robinhood_client.rh.login')
    def test_get_tradeable_securities_api_exception(self, mock_login, mock_get_stocks):
        """Test handling of API exception"""
        mock_login.return_value = {'success': True}
        mock_get_stocks.side_effect = Exception("API error")
        
        securities = self.client.get_tradeable_securities()
        
        self.assertEqual(len(securities), 0)


class TestFractionalShares(TestRobinhoodClient):
    """Test fractional shares verification"""
    
    @patch('src.clients.robinhood_client.rh.get_instrument_by_symbol')
    @patch('src.clients.robinhood_client.rh.login')
    def test_supports_fractional_shares_true(self, mock_login, mock_get_instrument):
        """Test checking fractional shares support - supported"""
        mock_login.return_value = {'success': True}
        mock_get_instrument.return_value = {
            'symbol': 'AAPL',
            'fractional_tradability': 'tradable'
        }
        
        result = self.client.supports_fractional_shares('AAPL')
        
        self.assertTrue(result)
        mock_get_instrument.assert_called_once_with('AAPL')
    
    @patch('src.clients.robinhood_client.rh.get_instrument_by_symbol')
    @patch('src.clients.robinhood_client.rh.login')
    def test_supports_fractional_shares_false(self, mock_login, mock_get_instrument):
        """Test checking fractional shares support - not supported"""
        mock_login.return_value = {'success': True}
        mock_get_instrument.return_value = {
            'symbol': 'GOOGL',
            'fractional_tradability': 'untradable'
        }
        
        result = self.client.supports_fractional_shares('GOOGL')
        
        self.assertFalse(result)
    
    @patch('src.clients.robinhood_client.rh.get_instrument_by_symbol')
    @patch('src.clients.robinhood_client.rh.login')
    def test_supports_fractional_shares_missing_field(self, mock_login, mock_get_instrument):
        """Test checking fractional shares when field is missing"""
        mock_login.return_value = {'success': True}
        mock_get_instrument.return_value = {
            'symbol': 'TSLA'
        }
        
        result = self.client.supports_fractional_shares('TSLA')
        
        self.assertFalse(result)
    
    @patch('src.clients.robinhood_client.rh.get_instrument_by_symbol')
    @patch('src.clients.robinhood_client.rh.login')
    def test_supports_fractional_shares_instrument_not_found(self, mock_login, mock_get_instrument):
        """Test checking fractional shares when instrument not found"""
        mock_login.return_value = {'success': True}
        mock_get_instrument.return_value = None
        
        result = self.client.supports_fractional_shares('INVALID')
        
        self.assertFalse(result)
    
    @patch('src.clients.robinhood_client.rh.login')
    def test_supports_fractional_shares_authentication_failure(self, mock_login):
        """Test fractional shares check with authentication failure"""
        mock_login.return_value = None
        
        result = self.client.supports_fractional_shares('AAPL')
        
        self.assertFalse(result)
    
    @patch('src.clients.robinhood_client.rh.get_instrument_by_symbol')
    @patch('src.clients.robinhood_client.rh.login')
    def test_supports_fractional_shares_exception(self, mock_login, mock_get_instrument):
        """Test fractional shares check with exception"""
        mock_login.return_value = {'success': True}
        mock_get_instrument.side_effect = Exception("API error")
        
        result = self.client.supports_fractional_shares('AAPL')
        
        self.assertFalse(result)


class TestTradingHours(TestRobinhoodClient):
    """Test trading hours logic"""
    
    @patch('src.clients.robinhood_client.rh.get_market_today_hours')
    @patch('src.clients.robinhood_client.rh.login')
    def test_is_market_open_true(self, mock_login, mock_get_hours):
        """Test checking if market is open - open"""
        mock_login.return_value = {'success': True}
        mock_get_hours.return_value = {
            'is_open': True
        }
        
        result = self.client.is_market_open()
        
        self.assertTrue(result)
        mock_get_hours.assert_called_once_with('XNYS')
    
    @patch('src.clients.robinhood_client.rh.get_market_today_hours')
    @patch('src.clients.robinhood_client.rh.login')
    def test_is_market_open_false(self, mock_login, mock_get_hours):
        """Test checking if market is open - closed"""
        mock_login.return_value = {'success': True}
        mock_get_hours.return_value = {
            'is_open': False
        }
        
        result = self.client.is_market_open()
        
        self.assertFalse(result)
    
    @patch('src.clients.robinhood_client.rh.get_market_today_hours')
    @patch('src.clients.robinhood_client.rh.login')
    def test_is_market_open_no_data(self, mock_login, mock_get_hours):
        """Test checking if market is open when no data available"""
        mock_login.return_value = {'success': True}
        mock_get_hours.return_value = None
        
        result = self.client.is_market_open()
        
        self.assertFalse(result)
    
    @patch('src.clients.robinhood_client.rh.login')
    def test_is_market_open_authentication_failure(self, mock_login):
        """Test market open check with authentication failure"""
        mock_login.return_value = None
        
        result = self.client.is_market_open()
        
        self.assertFalse(result)
    
    @patch('src.clients.robinhood_client.rh.get_market_today_hours')
    @patch('src.clients.robinhood_client.rh.login')
    def test_is_market_open_exception(self, mock_login, mock_get_hours):
        """Test market open check with exception"""
        mock_login.return_value = {'success': True}
        mock_get_hours.side_effect = Exception("API error")
        
        result = self.client.is_market_open()
        
        self.assertFalse(result)
    
    @patch('src.clients.robinhood_client.rh.get_market_today_hours')
    @patch('src.clients.robinhood_client.rh.login')
    def test_get_trading_hours_with_times(self, mock_login, mock_get_hours):
        """Test getting trading hours with open/close times"""
        mock_login.return_value = {'success': True}
        mock_get_hours.return_value = {
            'is_open': True,
            'opens_at': '2024-01-15T09:30:00Z',
            'closes_at': '2024-01-15T16:00:00Z'
        }
        
        hours = self.client.get_trading_hours()
        
        self.assertIsInstance(hours, TradingHours)
        self.assertTrue(hours.is_open)
        self.assertIsNotNone(hours.opens_at)
        self.assertIsNotNone(hours.closes_at)
        self.assertIsInstance(hours.opens_at, datetime)
        self.assertIsInstance(hours.closes_at, datetime)
    
    @patch('src.clients.robinhood_client.rh.get_market_today_hours')
    @patch('src.clients.robinhood_client.rh.login')
    def test_get_trading_hours_closed(self, mock_login, mock_get_hours):
        """Test getting trading hours when market is closed"""
        mock_login.return_value = {'success': True}
        mock_get_hours.return_value = {
            'is_open': False
        }
        
        hours = self.client.get_trading_hours()
        
        self.assertIsInstance(hours, TradingHours)
        self.assertFalse(hours.is_open)
    
    @patch('src.clients.robinhood_client.rh.get_market_today_hours')
    @patch('src.clients.robinhood_client.rh.login')
    def test_get_trading_hours_no_data(self, mock_login, mock_get_hours):
        """Test getting trading hours when no data available"""
        mock_login.return_value = {'success': True}
        mock_get_hours.return_value = None
        
        hours = self.client.get_trading_hours()
        
        self.assertIsInstance(hours, TradingHours)
        self.assertFalse(hours.is_open)
        self.assertIsNone(hours.opens_at)
        self.assertIsNone(hours.closes_at)
    
    @patch('src.clients.robinhood_client.rh.login')
    def test_get_trading_hours_authentication_failure(self, mock_login):
        """Test getting trading hours with authentication failure"""
        mock_login.return_value = None
        
        hours = self.client.get_trading_hours()
        
        self.assertIsInstance(hours, TradingHours)
        self.assertFalse(hours.is_open)
    
    @patch('src.clients.robinhood_client.rh.get_market_today_hours')
    @patch('src.clients.robinhood_client.rh.login')
    def test_get_trading_hours_exception(self, mock_login, mock_get_hours):
        """Test getting trading hours with exception"""
        mock_login.return_value = {'success': True}
        mock_get_hours.side_effect = Exception("API error")
        
        hours = self.client.get_trading_hours()
        
        self.assertIsInstance(hours, TradingHours)
        self.assertFalse(hours.is_open)
    
    @patch('src.clients.robinhood_client.rh.get_market_today_hours')
    @patch('src.clients.robinhood_client.rh.login')
    def test_get_trading_hours_invalid_timestamp_format(self, mock_login, mock_get_hours):
        """Test getting trading hours with invalid timestamp format"""
        mock_login.return_value = {'success': True}
        mock_get_hours.return_value = {
            'is_open': True,
            'opens_at': 'invalid-timestamp',
            'closes_at': 'invalid-timestamp'
        }
        
        hours = self.client.get_trading_hours()
        
        self.assertIsInstance(hours, TradingHours)
        self.assertTrue(hours.is_open)
        self.assertIsNone(hours.opens_at)
        self.assertIsNone(hours.closes_at)


class TestLogout(TestRobinhoodClient):
    """Test logout functionality"""
    
    @patch('src.clients.robinhood_client.rh.logout')
    def test_logout_success(self, mock_logout):
        """Test successful logout"""
        self.client._authenticated = True
        
        self.client.logout()
        
        self.assertFalse(self.client._authenticated)
        mock_logout.assert_called_once()
    
    @patch('src.clients.robinhood_client.rh.logout')
    def test_logout_exception(self, mock_logout):
        """Test logout with exception"""
        self.client._authenticated = True
        mock_logout.side_effect = Exception("Logout error")
        
        # Should not raise exception
        self.client.logout()
        
        mock_logout.assert_called_once()


if __name__ == '__main__':
    unittest.main()
