"""Finnhub client for secondary market data and news (free tier: 60 req/min)"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict
import finnhub
from time import time

from ..models import Quote, NewsArticle
from ..utils.credential_manager import credential_manager


logger = logging.getLogger(__name__)


class FinnhubClient:
    """Client for Finnhub API with rate limiting"""
    
    def __init__(self):
        """Initialize Finnhub client"""
        api_key = credential_manager.get_credential('finnhub_api_key')
        self.client = finnhub.Client(api_key=api_key)
        
        # Rate limiting (60 requests per minute for free tier)
        self.rate_limit = 60
        self.rate_window = 60  # seconds
        self.request_timestamps: List[float] = []
    
    def _check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits
        
        Returns:
            True if request can proceed, False if rate limit exceeded
        """
        current_time = time()
        
        # Remove timestamps older than rate window
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if current_time - ts < self.rate_window
        ]
        
        # Check if we're at the limit
        if len(self.request_timestamps) >= self.rate_limit:
            logger.warning("Finnhub rate limit reached")
            return False
        
        # Record this request
        self.request_timestamps.append(current_time)
        return True
    
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """
        Get current quote for a symbol
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            Quote object or None if error
        """
        if not self._check_rate_limit():
            return None
        
        try:
            quote_data = self.client.quote(symbol)
            
            if not quote_data or 'c' not in quote_data:
                logger.warning(f"No quote data available for {symbol}")
                return None
            
            # Finnhub quote fields: c=current, h=high, l=low, o=open, pc=previous close, t=timestamp
            price = Decimal(str(quote_data['c']))
            
            # Timestamps
            received_timestamp = datetime.now()
            exchange_timestamp = datetime.fromtimestamp(quote_data.get('t', time()))
            
            quote = Quote(
                symbol=symbol,
                price=price,
                exchange_timestamp=exchange_timestamp,
                received_timestamp=received_timestamp,
                bid=price,  # Finnhub doesn't provide bid/ask in free tier
                ask=price,
                volume=0  # Volume not in quote endpoint
            )
            
            logger.debug(f"Retrieved Finnhub quote for {symbol}: ${price}")
            return quote
        
        except Exception as e:
            logger.error(f"Error getting Finnhub quote for {symbol}: {e}")
            return None
    
    def get_company_news(self, symbol: str, from_date: date, to_date: date) -> List[NewsArticle]:
        """
        Get company news articles
        
        Args:
            symbol: Stock ticker symbol
            from_date: Start date
            to_date: End date
        
        Returns:
            List of NewsArticle objects
        """
        if not self._check_rate_limit():
            return []
        
        try:
            news_data = self.client.company_news(
                symbol, 
                _from=from_date.strftime('%Y-%m-%d'),
                to=to_date.strftime('%Y-%m-%d')
            )
            
            if not news_data:
                logger.debug(f"No news available for {symbol}")
                return []
            
            articles = []
            for item in news_data:
                try:
                    article = NewsArticle(
                        title=item.get('headline', ''),
                        summary=item.get('summary', ''),
                        source=item.get('source', 'Unknown'),
                        published_at=datetime.fromtimestamp(item.get('datetime', time())),
                        url=item.get('url', ''),
                        sentiment=item.get('sentiment')  # May be None
                    )
                    articles.append(article)
                except Exception as e:
                    logger.warning(f"Error parsing news article: {e}")
                    continue
            
            logger.debug(f"Retrieved {len(articles)} news articles for {symbol}")
            return articles
        
        except Exception as e:
            logger.error(f"Error getting company news for {symbol}: {e}")
            return []
    
    def get_market_news(self, category: str = "general") -> List[NewsArticle]:
        """
        Get general market news
        
        Args:
            category: News category (general, forex, crypto, merger)
        
        Returns:
            List of NewsArticle objects
        """
        if not self._check_rate_limit():
            return []
        
        try:
            news_data = self.client.general_news(category)
            
            if not news_data:
                logger.debug(f"No market news available for category {category}")
                return []
            
            articles = []
            for item in news_data:
                try:
                    article = NewsArticle(
                        title=item.get('headline', ''),
                        summary=item.get('summary', ''),
                        source=item.get('source', 'Unknown'),
                        published_at=datetime.fromtimestamp(item.get('datetime', time())),
                        url=item.get('url', ''),
                        sentiment=None
                    )
                    articles.append(article)
                except Exception as e:
                    logger.warning(f"Error parsing market news article: {e}")
                    continue
            
            logger.debug(f"Retrieved {len(articles)} market news articles")
            return articles
        
        except Exception as e:
            logger.error(f"Error getting market news: {e}")
            return []
    
    def get_company_profile(self, symbol: str) -> Optional[Dict]:
        """
        Get company profile information
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            Dictionary with company profile or None if error
        """
        if not self._check_rate_limit():
            return None
        
        try:
            profile = self.client.company_profile2(symbol=symbol)
            
            if not profile:
                logger.warning(f"No company profile available for {symbol}")
                return None
            
            logger.debug(f"Retrieved company profile for {symbol}")
            return profile
        
        except Exception as e:
            logger.error(f"Error getting company profile for {symbol}: {e}")
            return None
