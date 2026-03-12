"""Unit tests for yfinance client"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from decimal import Decimal
import pandas as pd

from src.clients.yfinance_client import YFinanceClient
from src.models import Quote, FinancialData


class TestYFinanceClient(unittest.TestCase):
    """Test cases for YFinanceClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = YFinanceClient()


class TestGetQuote(TestYFinanceClient):
    """Test get_quote method"""
    
    @patch('src.clients.yfinance_client.yf.Ticker')
    def test_get_quote_success(self, mock_ticker_class):
        """Test successful quote retrieval"""
        # Mock ticker instance
        mock_ticker = Mock()
        mock_ticker.info = {
            'regularMarketPrice': 150.50,
            'bid': 150.45,
            'ask': 150.55,
            'volume': 1000000
        }
        mock_ticker_class.return_value = mock_ticker
        
        quote = self.client.get_quote('AAPL')
        
        self.assertIsNotNone(quote)
        self.assertIsInstance(quote, Quote)
        self.assertEqual(quote.symbol, 'AAPL')
        self.assertEqual(quote.price, Decimal('150.50'))
        self.assertEqual(quote.bid, Decimal('150.45'))
        self.assertEqual(quote.ask, Decimal('150.55'))
        self.assertEqual(quote.volume, 1000000)
        self.assertIsInstance(quote.exchange_timestamp, datetime)
        self.assertIsInstance(quote.received_timestamp, datetime)
    
    @patch('src.clients.yfinance_client.yf.Ticker')
    def test_get_quote_missing_bid_ask(self, mock_ticker_class):
        """Test quote retrieval when bid/ask are missing"""
        mock_ticker = Mock()
        mock_ticker.info = {
            'regularMarketPrice': 150.50,
            'volume': 1000000
        }
        mock_ticker_class.return_value = mock_ticker
        
        quote = self.client.get_quote('AAPL')
        
        self.assertIsNotNone(quote)
        self.assertEqual(quote.price, Decimal('150.50'))
        # Should default to price when bid/ask missing
        self.assertEqual(quote.bid, Decimal('150.50'))
        self.assertEqual(quote.ask, Decimal('150.50'))
    
    @patch('src.clients.yfinance_client.yf.Ticker')
    def test_get_quote_no_data(self, mock_ticker_class):
        """Test quote retrieval when no data available"""
        mock_ticker = Mock()
        mock_ticker.info = {}
        mock_ticker_class.return_value = mock_ticker
        
        quote = self.client.get_quote('INVALID')
        
        self.assertIsNone(quote)
    
    @patch('src.clients.yfinance_client.yf.Ticker')
    def test_get_quote_missing_price(self, mock_ticker_class):
        """Test quote retrieval when price is missing"""
        mock_ticker = Mock()
        mock_ticker.info = {
            'volume': 1000000
        }
        mock_ticker_class.return_value = mock_ticker
        
        quote = self.client.get_quote('AAPL')
        
        self.assertIsNone(quote)
    
    @patch('src.clients.yfinance_client.yf.Ticker')
    def test_get_quote_exception(self, mock_ticker_class):
        """Test quote retrieval with exception"""
        mock_ticker_class.side_effect = Exception("API error")
        
        quote = self.client.get_quote('AAPL')
        
        self.assertIsNone(quote)
    
    @patch('src.clients.yfinance_client.yf.Ticker')
    def test_get_quote_timestamp_recording(self, mock_ticker_class):
        """Test that timestamps are properly recorded"""
        mock_ticker = Mock()
        mock_ticker.info = {
            'regularMarketPrice': 150.50,
            'volume': 1000000
        }
        mock_ticker_class.return_value = mock_ticker
        
        before = datetime.now()
        quote = self.client.get_quote('AAPL')
        after = datetime.now()
        
        self.assertIsNotNone(quote)
        self.assertGreaterEqual(quote.received_timestamp, before)
        self.assertLessEqual(quote.received_timestamp, after)
        self.assertGreaterEqual(quote.exchange_timestamp, before)
        self.assertLessEqual(quote.exchange_timestamp, after)


class TestGetHistoricalData(TestYFinanceClient):
    """Test get_historical_data method"""
    
    @patch('src.clients.yfinance_client.yf.Ticker')
    def test_get_historical_data_success(self, mock_ticker_class):
        """Test successful historical data retrieval"""
        mock_ticker = Mock()
        mock_df = pd.DataFrame({
            'Open': [150.0, 151.0, 152.0],
            'High': [151.0, 152.0, 153.0],
            'Low': [149.0, 150.0, 151.0],
            'Close': [150.5, 151.5, 152.5],
            'Volume': [1000000, 1100000, 1200000]
        })
        mock_ticker.history.return_value = mock_df
        mock_ticker_class.return_value = mock_ticker
        
        data = self.client.get_historical_data('AAPL', '1mo')
        
        self.assertIsNotNone(data)
        self.assertIsInstance(data, pd.DataFrame)
        self.assertEqual(len(data), 3)
        mock_ticker.history.assert_called_once_with(period='1mo')
    
    @patch('src.clients.yfinance_client.yf.Ticker')
    def test_get_historical_data_empty(self, mock_ticker_class):
        """Test historical data retrieval with empty result"""
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_class.return_value = mock_ticker
        
        data = self.client.get_historical_data('INVALID')
        
        self.assertIsNone(data)
    
    @patch('src.clients.yfinance_client.yf.Ticker')
    def test_get_historical_data_exception(self, mock_ticker_class):
        """Test historical data retrieval with exception"""
        mock_ticker = Mock()
        mock_ticker.history.side_effect = Exception("API error")
        mock_ticker_class.return_value = mock_ticker
        
        data = self.client.get_historical_data('AAPL')
        
        self.assertIsNone(data)
    
    @patch('src.clients.yfinance_client.yf.Ticker')
    def test_get_historical_data_custom_period(self, mock_ticker_class):
        """Test historical data retrieval with custom period"""
        mock_ticker = Mock()
        mock_df = pd.DataFrame({'Close': [150.0]})
        mock_ticker.history.return_value = mock_df
        mock_ticker_class.return_value = mock_ticker
        
        data = self.client.get_historical_data('AAPL', '6mo')
        
        self.assertIsNotNone(data)
        mock_ticker.history.assert_called_once_with(period='6mo')


class TestGetFinancialStatements(TestYFinanceClient):
    """Test get_financial_statements method"""
    
    @patch('src.clients.yfinance_client.yf.Ticker')
    def test_get_financial_statements_success(self, mock_ticker_class):
        """Test successful financial statements retrieval"""
        mock_ticker = Mock()
        mock_ticker.info = {
            'totalRevenue': 394328000000,
            'netIncomeToCommon': 99803000000,
            'trailingPE': 28.5,
            'debtToEquity': 1.73,
            'freeCashflow': 111443000000,
            'returnOnEquity': 1.47
        }
        mock_ticker_class.return_value = mock_ticker
        
        financial_data = self.client.get_financial_statements('AAPL')
        
        self.assertIsNotNone(financial_data)
        self.assertIsInstance(financial_data, FinancialData)
        self.assertEqual(financial_data.symbol, 'AAPL')
        self.assertEqual(financial_data.revenue, Decimal('394328000000'))
        self.assertEqual(financial_data.earnings, Decimal('99803000000'))
        self.assertEqual(financial_data.pe_ratio, Decimal('28.5'))
        self.assertEqual(financial_data.debt_to_equity, Decimal('1.73'))
        self.assertEqual(financial_data.free_cash_flow, Decimal('111443000000'))
        self.assertEqual(financial_data.roe, Decimal('1.47'))
        self.assertIsInstance(financial_data.updated_at, datetime)
    
    @patch('src.clients.yfinance_client.yf.Ticker')
    def test_get_financial_statements_missing_fields(self, mock_ticker_class):
        """Test financial statements with missing fields"""
        mock_ticker = Mock()
        mock_ticker.info = {
            'totalRevenue': 394328000000,
            'trailingPE': 28.5
        }
        mock_ticker_class.return_value = mock_ticker
        
        financial_data = self.client.get_financial_statements('AAPL')
        
        self.assertIsNotNone(financial_data)
        self.assertEqual(financial_data.revenue, Decimal('394328000000'))
        self.assertEqual(financial_data.earnings, Decimal('0'))
        self.assertEqual(financial_data.pe_ratio, Decimal('28.5'))
        self.assertEqual(financial_data.debt_to_equity, Decimal('0'))
    
    @patch('src.clients.yfinance_client.yf.Ticker')
    def test_get_financial_statements_no_data(self, mock_ticker_class):
        """Test financial statements when no data available"""
        mock_ticker = Mock()
        mock_ticker.info = None
        mock_ticker_class.return_value = mock_ticker
        
        financial_data = self.client.get_financial_statements('INVALID')
        
        self.assertIsNone(financial_data)
    
    @patch('src.clients.yfinance_client.yf.Ticker')
    def test_get_financial_statements_exception(self, mock_ticker_class):
        """Test financial statements retrieval with exception"""
        mock_ticker_class.side_effect = Exception("API error")
        
        financial_data = self.client.get_financial_statements('AAPL')
        
        self.assertIsNone(financial_data)


class TestGetCompanyInfo(TestYFinanceClient):
    """Test get_company_info method"""
    
    @patch('src.clients.yfinance_client.yf.Ticker')
    def test_get_company_info_success(self, mock_ticker_class):
        """Test successful company info retrieval"""
        mock_ticker = Mock()
        mock_ticker.info = {
            'longName': 'Apple Inc.',
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'longBusinessSummary': 'Apple designs and manufactures consumer electronics.',
            'website': 'https://www.apple.com',
            'marketCap': 2800000000000,
            'averageVolume': 50000000
        }
        mock_ticker_class.return_value = mock_ticker
        
        info = self.client.get_company_info('AAPL')
        
        self.assertIsNotNone(info)
        self.assertEqual(info['symbol'], 'AAPL')
        self.assertEqual(info['name'], 'Apple Inc.')
        self.assertEqual(info['sector'], 'Technology')
        self.assertEqual(info['industry'], 'Consumer Electronics')
        self.assertEqual(info['website'], 'https://www.apple.com')
        self.assertEqual(info['market_cap'], 2800000000000)
        self.assertEqual(info['average_volume'], 50000000)
    
    @patch('src.clients.yfinance_client.yf.Ticker')
    def test_get_company_info_missing_fields(self, mock_ticker_class):
        """Test company info with missing fields"""
        mock_ticker = Mock()
        mock_ticker.info = {
            'longName': 'Apple Inc.'
        }
        mock_ticker_class.return_value = mock_ticker
        
        info = self.client.get_company_info('AAPL')
        
        self.assertIsNotNone(info)
        self.assertEqual(info['name'], 'Apple Inc.')
        self.assertEqual(info['sector'], 'Unknown')
        self.assertEqual(info['industry'], 'Unknown')
        self.assertEqual(info['website'], '')
    
    @patch('src.clients.yfinance_client.yf.Ticker')
    def test_get_company_info_no_data(self, mock_ticker_class):
        """Test company info when no data available"""
        mock_ticker = Mock()
        mock_ticker.info = None
        mock_ticker_class.return_value = mock_ticker
        
        info = self.client.get_company_info('INVALID')
        
        self.assertIsNone(info)
    
    @patch('src.clients.yfinance_client.yf.Ticker')
    def test_get_company_info_exception(self, mock_ticker_class):
        """Test company info retrieval with exception"""
        mock_ticker_class.side_effect = Exception("API error")
        
        info = self.client.get_company_info('AAPL')
        
        self.assertIsNone(info)


if __name__ == '__main__':
    unittest.main()
