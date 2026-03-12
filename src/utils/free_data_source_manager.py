"""
Free Data Source Manager for Investment Scout

Aggregates data from multiple free sources with failover and usage monitoring.
Implements Requirements 19.1-19.12.
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict
from collections import defaultdict

from src.clients.newsapi_client import NewsAPIClient
from src.clients.alphavantage_client import AlphaVantageClient
from src.clients.fred_client import FREDClient
from src.clients.worldbank_client import WorldBankClient
from src.clients.rss_feed_client import RSSFeedClient
from src.clients.web_scraper_client import WebScraperClient
from src.models.investment_scout_models import NewsArticle


logger = logging.getLogger(__name__)


class FreeDataSourceManager:
    """
    Manages multiple free data sources with failover and usage tracking.
    
    Implements:
    - Multi-source aggregation (Req 19.1, 19.5)
    - Failover across sources (Req 19.6)
    - Rate limit monitoring (Req 19.10)
    - Aggressive caching (Req 19.12)
    - Robots.txt compliance (Req 19.8)
    """
    
    def __init__(
        self,
        newsapi_key: Optional[str] = None,
        alphavantage_key: Optional[str] = None,
        fred_key: Optional[str] = None
    ):
        """
        Initialize free data source manager.
        
        Args:
            newsapi_key: NewsAPI key (optional)
            alphavantage_key: Alpha Vantage key (optional)
            fred_key: FRED API key (optional)
        """
        # Initialize clients
        self.newsapi = NewsAPIClient(newsapi_key) if newsapi_key else None
        self.alphavantage = AlphaVantageClient(alphavantage_key) if alphavantage_key else None
        self.fred = FREDClient(fred_key) if fred_key else None
        self.worldbank = WorldBankClient()
        self.rss = RSSFeedClient()
        self.scraper = WebScraperClient()
        
        # Usage tracking for free tier monitoring
        self.usage_stats = defaultdict(int)
        self.last_reset = datetime.now()
        
        # Daily limits for free tiers
        self.daily_limits = {
            'newsapi': 100,
            'alphavantage': 25,
            'fred': 1000,  # Self-imposed
            'worldbank': 1000,  # Self-imposed
            'rss': 500,  # Self-imposed
            'scraper': 100  # Self-imposed
        }
        
        logger.info("Initialized FreeDataSourceManager with available sources")
    
    def _check_and_reset_usage(self):
        """Reset usage counters daily"""
        now = datetime.now()
        if (now - self.last_reset).days >= 1:
            logger.info("Resetting daily usage counters")
            self.usage_stats.clear()
            self.last_reset = now
    
    def _can_use_source(self, source_name: str) -> bool:
        """
        Check if source is within usage limits.
        
        Args:
            source_name: Name of the data source
            
        Returns:
            True if within limits, False otherwise
        """
        self._check_and_reset_usage()
        
        current_usage = self.usage_stats[source_name]
        limit = self.daily_limits.get(source_name, 1000)
        
        if current_usage >= limit:
            logger.warning(
                f"{source_name} has reached daily limit "
                f"({current_usage}/{limit})"
            )
            return False
        
        return True
    
    def _record_usage(self, source_name: str, count: int = 1):
        """Record API usage"""
        self.usage_stats[source_name] += count
        logger.debug(
            f"{source_name} usage: {self.usage_stats[source_name]}/"
            f"{self.daily_limits.get(source_name, 'unlimited')}"
        )
    
    def get_market_news(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        max_articles: int = 100
    ) -> List[NewsArticle]:
        """
        Get market news from multiple sources with failover.
        
        Tries sources in order:
        1. RSS feeds (free, unlimited)
        2. NewsAPI (100/day)
        3. Alpha Vantage (25/day, has sentiment)
        
        Args:
            from_date: Start date
            to_date: End date
            max_articles: Maximum articles to return
            
        Returns:
            Aggregated list of NewsArticle objects
        """
        all_articles = []
        
        # Try RSS feeds first (free, unlimited)
        if self._can_use_source('rss'):
            try:
                logger.info("Fetching market news from RSS feeds")
                articles = self.rss.parse_multiple_feeds()
                all_articles.extend(articles)
                self._record_usage('rss', 1)
                logger.info(f"Retrieved {len(articles)} articles from RSS feeds")
            except Exception as e:
                logger.error(f"RSS feed fetch failed: {e}")
        
        # If we need more articles, try NewsAPI
        if len(all_articles) < max_articles and self.newsapi and self._can_use_source('newsapi'):
            try:
                logger.info("Fetching market news from NewsAPI")
                articles = self.newsapi.get_market_news(
                    from_date=from_date,
                    to_date=to_date,
                    page_size=max_articles - len(all_articles)
                )
                all_articles.extend(articles)
                self._record_usage('newsapi', 1)
                logger.info(f"Retrieved {len(articles)} articles from NewsAPI")
            except Exception as e:
                logger.error(f"NewsAPI fetch failed: {e}")
        
        # If still need more and want sentiment, try Alpha Vantage
        if len(all_articles) < max_articles and self.alphavantage and self._can_use_source('alphavantage'):
            try:
                logger.info("Fetching market news from Alpha Vantage")
                articles = self.alphavantage.get_news_sentiment(
                    topics='economy,finance',
                    limit=max_articles - len(all_articles)
                )
                all_articles.extend(articles)
                self._record_usage('alphavantage', 1)
                logger.info(f"Retrieved {len(articles)} articles from Alpha Vantage")
            except Exception as e:
                logger.error(f"Alpha Vantage fetch failed: {e}")
        
        # Remove duplicates based on title similarity
        unique_articles = self._deduplicate_articles(all_articles)
        
        logger.info(
            f"Aggregated {len(unique_articles)} unique articles from "
            f"multiple sources"
        )
        return unique_articles[:max_articles]
    
    def get_company_news(
        self,
        symbol: str,
        company_name: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        max_articles: int = 50
    ) -> List[NewsArticle]:
        """
        Get company-specific news with failover.
        
        Args:
            symbol: Stock symbol
            company_name: Company name
            from_date: Start date
            to_date: End date
            max_articles: Maximum articles
            
        Returns:
            List of NewsArticle objects
        """
        all_articles = []
        
        # Try Alpha Vantage first (has sentiment)
        if self.alphavantage and self._can_use_source('alphavantage'):
            try:
                logger.info(f"Fetching news for {symbol} from Alpha Vantage")
                articles = self.alphavantage.get_news_sentiment(
                    tickers=symbol,
                    limit=max_articles
                )
                all_articles.extend(articles)
                self._record_usage('alphavantage', 1)
            except Exception as e:
                logger.error(f"Alpha Vantage fetch failed for {symbol}: {e}")
        
        # Fallback to NewsAPI
        if len(all_articles) < max_articles and self.newsapi and self._can_use_source('newsapi'):
            try:
                logger.info(f"Fetching news for {company_name} from NewsAPI")
                articles = self.newsapi.get_company_news(
                    company_name,
                    from_date=from_date,
                    to_date=to_date,
                    page_size=max_articles - len(all_articles)
                )
                all_articles.extend(articles)
                self._record_usage('newsapi', 1)
            except Exception as e:
                logger.error(f"NewsAPI fetch failed for {company_name}: {e}")
        
        unique_articles = self._deduplicate_articles(all_articles)
        return unique_articles[:max_articles]
    
    def get_economic_indicators(
        self,
        country_code: str = 'US',
        from_date: Optional[date] = None
    ) -> Dict[str, List[Dict]]:
        """
        Get economic indicators from FRED and World Bank with failover.
        
        Args:
            country_code: Country code (default US)
            from_date: Start date
            
        Returns:
            Dictionary with indicator data
        """
        indicators = {}
        
        # Try FRED first (US data, more frequent updates)
        if country_code == 'US' and self.fred and self._can_use_source('fred'):
            try:
                logger.info("Fetching US economic indicators from FRED")
                indicators['gdp'] = self.fred.get_gdp(from_date=from_date)
                indicators['unemployment'] = self.fred.get_unemployment_rate(from_date=from_date)
                indicators['interest_rate'] = self.fred.get_federal_funds_rate(from_date=from_date)
                indicators['inflation'] = self.fred.get_inflation_rate(from_date=from_date)
                self._record_usage('fred', 4)
                logger.info("Retrieved economic indicators from FRED")
            except Exception as e:
                logger.error(f"FRED fetch failed: {e}")
        
        # Fallback to World Bank (global data)
        if not indicators and self._can_use_source('worldbank'):
            try:
                logger.info(f"Fetching economic indicators for {country_code} from World Bank")
                start_year = from_date.year if from_date else None
                indicators['gdp'] = self.worldbank.get_gdp(country_code, start_year=start_year)
                indicators['gdp_growth'] = self.worldbank.get_gdp_growth(country_code, start_year=start_year)
                indicators['inflation'] = self.worldbank.get_inflation(country_code, start_year=start_year)
                indicators['unemployment'] = self.worldbank.get_unemployment(country_code, start_year=start_year)
                self._record_usage('worldbank', 4)
                logger.info("Retrieved economic indicators from World Bank")
            except Exception as e:
                logger.error(f"World Bank fetch failed: {e}")
        
        return indicators
    
    def _deduplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """
        Remove duplicate articles based on title similarity.
        
        Args:
            articles: List of articles
            
        Returns:
            Deduplicated list
        """
        if not articles:
            return []
        
        # Simple deduplication by exact title match
        seen_titles = set()
        unique = []
        
        for article in articles:
            title_lower = article.title.lower().strip()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique.append(article)
        
        return unique
    
    def get_usage_report(self) -> Dict[str, Dict]:
        """
        Get current usage statistics.
        
        Returns:
            Dictionary with usage stats for each source
        """
        self._check_and_reset_usage()
        
        report = {}
        for source, limit in self.daily_limits.items():
            usage = self.usage_stats[source]
            report[source] = {
                'usage': usage,
                'limit': limit,
                'remaining': limit - usage,
                'percentage': (usage / limit * 100) if limit > 0 else 0
            }
        
        return report
