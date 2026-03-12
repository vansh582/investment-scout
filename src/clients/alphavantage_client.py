"""
Alpha Vantage API Client for Investment Scout

Free tier: 25 requests per day (very limited)
Provides news and sentiment data.
"""

import logging
from datetime import datetime
from typing import List, Optional
import requests

from src.clients.base_api_client import BaseAPIClient
from src.models.investment_scout_models import NewsArticle


logger = logging.getLogger(__name__)


class AlphaVantageClient(BaseAPIClient):
    """
    Alpha Vantage client for news and sentiment data.
    
    Free tier: 25 requests per day (very limited)
    """
    
    def __init__(self, api_key: str):
        super().__init__(
            name="AlphaVantage",
            requests_per_minute=1,  # 25/day, very conservative
            failure_threshold=5,
            circuit_timeout=60
        )
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
    
    def get_news_sentiment(
        self,
        tickers: Optional[str] = None,
        topics: Optional[str] = None,
        limit: int = 50
    ) -> List[NewsArticle]:
        """
        Get news articles with sentiment analysis.
        
        Args:
            tickers: Comma-separated ticker symbols (e.g., "AAPL,MSFT")
            topics: Topics to filter (e.g., "technology,earnings")
            limit: Number of results (max 1000)
            
        Returns:
            List of NewsArticle objects with sentiment scores
        """
        def _fetch():
            params = {
                'function': 'NEWS_SENTIMENT',
                'apikey': self.api_key,
                'limit': limit
            }
            
            if tickers:
                params['tickers'] = tickers
            if topics:
                params['topics'] = topics
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                raise ValueError(f"Alpha Vantage error: {data['Error Message']}")
            if 'Note' in data:
                # Rate limit message
                raise ValueError(f"Alpha Vantage rate limit: {data['Note']}")
            
            articles = []
            for item in data.get('feed', []):
                try:
                    # Parse timestamp
                    time_str = item.get('time_published', '')
                    # Format: YYYYMMDDTHHMMSS
                    published_at = datetime.strptime(time_str, '%Y%m%dT%H%M%S')
                    
                    # Extract overall sentiment score
                    sentiment_score = float(item.get('overall_sentiment_score', 0))
                    # Alpha Vantage sentiment: -1 (bearish) to 1 (bullish)
                    
                    article = NewsArticle(
                        title=item.get('title', ''),
                        summary=item.get('summary', ''),
                        source=item.get('source', 'Unknown'),
                        published_at=published_at,
                        url=item.get('url', ''),
                        sentiment=sentiment_score
                    )
                    articles.append(article)
                except Exception as e:
                    logger.warning(f"Error parsing Alpha Vantage article: {e}")
                    continue
            
            logger.info(f"Retrieved {len(articles)} articles from Alpha Vantage")
            return articles
        
        try:
            return self.call_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Failed to get news from Alpha Vantage: {e}")
            return []
