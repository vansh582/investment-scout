"""
Finnhub API Client for Investment Scout

Secondary data source for market quotes, news, and company information.
Free tier: 60 requests per minute.
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict
from time import time
import finnhub

from src.clients.base_api_client import BaseAPIClient
from src.models.investment_scout_models import Quote, NewsArticle


logger = logging.getLogger(__name__)


class FinnhubClient(BaseAPIClient):
    """
    Finnhub client for market data, news, and company information.
    
    Free tier: 60 requests per minute
    """
    
    def __init__(self, api_key: str):
        super().__init__(
            name="Finnhub",
            requests_per_minute=60,  # Free tier limit
            failure_threshold=5,
            circuit_timeout=60
        )
        self.client = finnhub.Client(api_key=api_key)
    
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """
        Get current quote for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Quote object or None if failed
        """
        def _fetch():
            quote_data = self.client.quote(symbol)
            
            if not quote_data or 'c' not in quote_data:
                raise ValueError(f"No quote data available for {symbol}")
            
            # Finnhub quote fields: c=current, h=high, l=low, o=open, pc=previous close, t=timestamp
            price = Decimal(str(quote_data['c']))
            
            # Timestamps
            received_timestamp = datetime.now()
            exchange_timestamp = datetime.fromtimestamp(quote_data.get('t', time()))
            
            return Quote(
                symbol=symbol,
                price=price,
                exchange_timestamp=exchange_timestamp,
                received_timestamp=received_timestamp,
                bid=price,  # Finnhub free tier doesn't provide bid/ask
                ask=price,
                volume=0  # Volume not in quote endpoint
            )
        
        try:
            return self.call_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol} from Finnhub: {e}")
            return None
    
    def get_company_news(
        self,
        symbol: str,
        from_date: date,
        to_date: date
    ) -> List[NewsArticle]:
        """
        Get company news articles.
        
        Args:
            symbol: Stock symbol
            from_date: Start date
            to_date: End date
            
        Returns:
            List of NewsArticle objects
        """
        def _fetch():
            news_data = self.client.company_news(
                symbol,
                _from=from_date.strftime('%Y-%m-%d'),
                to=to_date.strftime('%Y-%m-%d')
            )
            
            if not news_data:
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
            
            return articles
        
        try:
            return self.call_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Failed to get company news for {symbol} from Finnhub: {e}")
            return []
    
    def get_market_news(self, category: str = "general") -> List[NewsArticle]:
        """
        Get general market news.
        
        Args:
            category: News category (general, forex, crypto, merger)
            
        Returns:
            List of NewsArticle objects
        """
        def _fetch():
            news_data = self.client.general_news(category)
            
            if not news_data:
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
            
            return articles
        
        try:
            return self.call_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Failed to get market news from Finnhub: {e}")
            return []
    
    def get_company_profile(self, symbol: str) -> Optional[Dict]:
        """
        Get company profile information.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with company profile or None if failed
        """
        def _fetch():
            profile = self.client.company_profile2(symbol=symbol)
            
            if not profile:
                raise ValueError(f"No company profile available for {symbol}")
            
            return profile
        
        try:
            return self.call_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Failed to get company profile for {symbol} from Finnhub: {e}")
            return None
