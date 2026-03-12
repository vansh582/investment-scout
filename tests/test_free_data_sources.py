"""
Unit tests for Free Data Source Integration (Task 24)

Tests multi-source aggregation, failover logic, rate limit monitoring,
and caching efficiency.
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from src.utils.free_data_source_manager import FreeDataSourceManager
from src.models.investment_scout_models import NewsArticle


class TestFreeDataSourceManager:
    """Test suite for FreeDataSourceManager"""
    
    @pytest.fixture
    def manager(self):
        """Create manager with mock API keys"""
        return FreeDataSourceManager(
            newsapi_key='test_newsapi_key',
            alphavantage_key='test_av_key',
            fred_key='test_fred_key'
        )
    
    def test_initialization(self, manager):
        """Test manager initializes with all clients"""
        assert manager.newsapi is not None
        assert manager.alphavantage is not None
        assert manager.fred is not None
        assert manager.worldbank is not None
        assert manager.rss is not None
        assert manager.scraper is not None
    
    def test_usage_tracking(self, manager):
        """Test usage tracking and limits"""
        # Record usage
        manager._record_usage('newsapi', 5)
        assert manager.usage_stats['newsapi'] == 5
        
        # Check can use
        assert manager._can_use_source('newsapi') is True
        
        # Exceed limit
        manager._record_usage('newsapi', 100)
        assert manager._can_use_source('newsapi') is False
    
    def test_usage_reset(self, manager):
        """Test daily usage reset"""
        # Record usage
        manager._record_usage('newsapi', 50)
        assert manager.usage_stats['newsapi'] == 50
        
        # Simulate day passing
        manager.last_reset = datetime.now() - timedelta(days=2)
        manager._check_and_reset_usage()
        
        # Usage should be reset
        assert manager.usage_stats['newsapi'] == 0
    
    @patch('src.clients.rss_feed_client.RSSFeedClient.parse_multiple_feeds')
    def test_market_news_rss_primary(self, mock_rss, manager):
        """Test market news fetches from RSS first"""
        # Mock RSS response
        mock_articles = [
            NewsArticle(
                title='Test Article 1',
                summary='Summary 1',
                source='RSS Feed',
                published_at=datetime.now(),
                url='http://example.com/1',
                sentiment=None
            )
        ]
        mock_rss.return_value = mock_articles
        
        # Get market news
        articles = manager.get_market_news(max_articles=10)
        
        # Should use RSS
        assert len(articles) > 0
        assert mock_rss.called
        assert manager.usage_stats['rss'] > 0
    
    @patch('src.clients.rss_feed_client.RSSFeedClient.parse_multiple_feeds')
    @patch('src.clients.newsapi_client.NewsAPIClient.get_market_news')
    def test_market_news_failover(self, mock_newsapi, mock_rss, manager):
        """Test failover from RSS to NewsAPI"""
        # RSS returns empty
        mock_rss.return_value = []
        
        # NewsAPI returns articles
        mock_newsapi.return_value = [
            NewsArticle(
                title='NewsAPI Article',
                summary='Summary',
                source='NewsAPI',
                published_at=datetime.now(),
                url='http://example.com/2',
                sentiment=None
            )
        ]
        
        # Get market news
        articles = manager.get_market_news(max_articles=10)
        
        # Should try both sources
        assert mock_rss.called
        assert mock_newsapi.called
        assert len(articles) > 0
    
    @patch('src.clients.alphavantage_client.AlphaVantageClient.get_news_sentiment')
    def test_company_news_with_sentiment(self, mock_av, manager):
        """Test company news fetches with sentiment from Alpha Vantage"""
        # Mock Alpha Vantage response
        mock_av.return_value = [
            NewsArticle(
                title='Company News',
                summary='Summary',
                source='Alpha Vantage',
                published_at=datetime.now(),
                url='http://example.com/3',
                sentiment=0.5
            )
        ]
        
        # Get company news
        articles = manager.get_company_news('AAPL', 'Apple Inc.')
        
        # Should use Alpha Vantage
        assert len(articles) > 0
        assert articles[0].sentiment is not None
        assert mock_av.called
    
    @patch('src.clients.fred_client.FREDClient.get_gdp')
    @patch('src.clients.fred_client.FREDClient.get_unemployment_rate')
    @patch('src.clients.fred_client.FREDClient.get_federal_funds_rate')
    @patch('src.clients.fred_client.FREDClient.get_inflation_rate')
    def test_economic_indicators_fred(self, mock_inf, mock_rate, mock_unemp, mock_gdp, manager):
        """Test economic indicators from FRED"""
        # Mock FRED responses
        mock_gdp.return_value = [{'date': date.today(), 'value': Decimal('20000')}]
        mock_unemp.return_value = [{'date': date.today(), 'value': Decimal('4.5')}]
        mock_rate.return_value = [{'date': date.today(), 'value': Decimal('5.0')}]
        mock_inf.return_value = [{'date': date.today(), 'value': Decimal('3.2')}]
        
        # Get indicators
        indicators = manager.get_economic_indicators('US')
        
        # Should have all indicators
        assert 'gdp' in indicators
        assert 'unemployment' in indicators
        assert 'interest_rate' in indicators
        assert 'inflation' in indicators
        assert manager.usage_stats['fred'] == 4
    
    @patch('src.clients.worldbank_client.WorldBankClient.get_gdp')
    @patch('src.clients.worldbank_client.WorldBankClient.get_gdp_growth')
    @patch('src.clients.worldbank_client.WorldBankClient.get_inflation')
    @patch('src.clients.worldbank_client.WorldBankClient.get_unemployment')
    def test_economic_indicators_worldbank_fallback(self, mock_unemp, mock_inf, mock_growth, mock_gdp, manager):
        """Test World Bank fallback for non-US countries"""
        # Mock World Bank responses
        mock_gdp.return_value = [{'year': 2023, 'value': Decimal('15000')}]
        mock_growth.return_value = [{'year': 2023, 'value': Decimal('3.5')}]
        mock_inf.return_value = [{'year': 2023, 'value': Decimal('2.8')}]
        mock_unemp.return_value = [{'year': 2023, 'value': Decimal('5.2')}]
        
        # Get indicators for China
        indicators = manager.get_economic_indicators('CN')
        
        # Should use World Bank
        assert 'gdp' in indicators
        assert manager.usage_stats['worldbank'] == 4
    
    def test_deduplication(self, manager):
        """Test article deduplication"""
        # Create duplicate articles
        articles = [
            NewsArticle(
                title='Same Title',
                summary='Summary 1',
                source='Source 1',
                published_at=datetime.now(),
                url='http://example.com/1',
                sentiment=None
            ),
            NewsArticle(
                title='Same Title',
                summary='Summary 2',
                source='Source 2',
                published_at=datetime.now(),
                url='http://example.com/2',
                sentiment=None
            ),
            NewsArticle(
                title='Different Title',
                summary='Summary 3',
                source='Source 3',
                published_at=datetime.now(),
                url='http://example.com/3',
                sentiment=None
            )
        ]
        
        # Deduplicate
        unique = manager._deduplicate_articles(articles)
        
        # Should have 2 unique articles
        assert len(unique) == 2
    
    def test_usage_report(self, manager):
        """Test usage report generation"""
        # Record some usage
        manager._record_usage('newsapi', 25)
        manager._record_usage('alphavantage', 10)
        
        # Get report
        report = manager.get_usage_report()
        
        # Check report structure
        assert 'newsapi' in report
        assert report['newsapi']['usage'] == 25
        assert report['newsapi']['limit'] == 100
        assert report['newsapi']['remaining'] == 75
        assert report['newsapi']['percentage'] == 25.0
        
        assert 'alphavantage' in report
        assert report['alphavantage']['usage'] == 10
    
    def test_rate_limit_prevents_usage(self, manager):
        """Test rate limit prevents further API calls"""
        # Exhaust NewsAPI limit
        manager._record_usage('newsapi', 100)
        
        # Try to use NewsAPI
        with patch('src.clients.newsapi_client.NewsAPIClient.get_market_news') as mock_api:
            manager.get_market_news(max_articles=10)
            
            # NewsAPI should not be called
            assert not mock_api.called


class TestRSSFeedClient:
    """Test RSS feed parsing"""
    
    @pytest.fixture
    def rss_client(self):
        from src.clients.rss_feed_client import RSSFeedClient
        return RSSFeedClient()
    
    def test_extract_source(self, rss_client):
        """Test source extraction from URL"""
        assert rss_client._extract_source('https://feeds.finance.yahoo.com/rss') == 'Yahoo Finance'
        assert rss_client._extract_source('https://www.cnbc.com/rss') == 'CNBC'
        assert rss_client._extract_source('https://www.reuters.com/rss') == 'Reuters'
        assert rss_client._extract_source('https://unknown.com/rss') == 'RSS Feed'


class TestWebScraperClient:
    """Test web scraper with robots.txt compliance"""
    
    @pytest.fixture
    def scraper(self):
        from src.clients.web_scraper_client import WebScraperClient
        return WebScraperClient()
    
    def test_robots_txt_compliance(self, scraper):
        """Test robots.txt checking"""
        # This is a basic test - actual robots.txt checking would need mocking
        url = 'https://example.com/page'
        
        # Should not raise exception
        can_fetch = scraper.can_fetch(url)
        assert isinstance(can_fetch, bool)
    
    @patch('src.clients.web_scraper_client.WebScraperClient.can_fetch')
    def test_respects_robots_disallow(self, mock_can_fetch, scraper):
        """Test scraper respects robots.txt disallow"""
        mock_can_fetch.return_value = False
        
        # Try to scrape
        result = scraper.scrape_page('https://example.com/disallowed')
        
        # Should return None
        assert result is None


class TestMultiSourceAggregation:
    """Test multi-source data aggregation"""
    
    @patch('src.clients.rss_feed_client.RSSFeedClient.parse_multiple_feeds')
    @patch('src.clients.newsapi_client.NewsAPIClient.get_market_news')
    @patch('src.clients.alphavantage_client.AlphaVantageClient.get_news_sentiment')
    def test_aggregates_from_all_sources(self, mock_av, mock_newsapi, mock_rss):
        """Test aggregation from multiple sources"""
        # Mock responses from each source
        mock_rss.return_value = [
            NewsArticle(
                title='RSS Article',
                summary='Summary',
                source='RSS',
                published_at=datetime.now(),
                url='http://example.com/rss',
                sentiment=None
            )
        ]
        
        mock_newsapi.return_value = [
            NewsArticle(
                title='NewsAPI Article',
                summary='Summary',
                source='NewsAPI',
                published_at=datetime.now(),
                url='http://example.com/newsapi',
                sentiment=None
            )
        ]
        
        mock_av.return_value = [
            NewsArticle(
                title='AV Article',
                summary='Summary',
                source='Alpha Vantage',
                published_at=datetime.now(),
                url='http://example.com/av',
                sentiment=0.5
            )
        ]
        
        # Create manager and get news
        manager = FreeDataSourceManager(
            newsapi_key='test',
            alphavantage_key='test',
            fred_key='test'
        )
        
        articles = manager.get_market_news(max_articles=100)
        
        # Should aggregate from all sources
        assert len(articles) >= 3
        sources = {a.source for a in articles}
        assert 'RSS' in sources or 'NewsAPI' in sources or 'Alpha Vantage' in sources


class TestCachingEfficiency:
    """Test aggressive caching for free tier efficiency"""
    
    def test_usage_tracking_prevents_overuse(self):
        """Test usage tracking prevents exceeding limits"""
        manager = FreeDataSourceManager(
            newsapi_key='test',
            alphavantage_key='test'
        )
        
        # Record usage up to limit
        for i in range(100):
            manager._record_usage('newsapi', 1)
        
        # Should not be able to use anymore
        assert not manager._can_use_source('newsapi')
    
    def test_daily_reset_restores_access(self):
        """Test daily reset restores API access"""
        manager = FreeDataSourceManager(newsapi_key='test')
        
        # Exhaust limit
        manager._record_usage('newsapi', 100)
        assert not manager._can_use_source('newsapi')
        
        # Simulate day passing
        manager.last_reset = datetime.now() - timedelta(days=2)
        
        # Should be able to use again
        assert manager._can_use_source('newsapi')
