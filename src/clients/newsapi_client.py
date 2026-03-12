"""
NewsAPI Client for Investment Scout

Free tier: 100 requests per day, 1000 results per request
Provides market news from various sources.
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Optional
import requests

from src.clients.base_api_client import BaseAPIClient
from src.models.investment_scout_models import NewsArticle


logger = logging.getLogger(__name__)


class NewsAPIClient(BaseAPIClient):
    """
    NewsAPI client for market news collection.
    
    Free tier: 100 requests per day
    """
    
    def __init__(self, api_key: str):
        super().__init__(
            name="NewsAPI",
            requests_per_minute=4,  # 100/day ≈ 4/hour, conservative rate
            failure_threshold=5,
            circuit_timeout=60
        )
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
    
    def get_market_news(
        self,
        query: str = "stock market OR economy OR finance",
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        language: str = "en",
        page_size: int = 100
    ) -> List[NewsArticle]:
        """
        Get market news articles.
        
        Args:
            query: Search query
            from_date: Start date (defaults to 7 days ago)
            to_date: End date (defaults to today)
            language: Language code
            page_size: Number of results (max 100)
            
        Returns:
            List of NewsArticle objects
        """
        if from_date is None:
            from_date = date.today() - timedelta(days=7)
        if to_date is None:
            to_date = date.today()
        
        def _fetch():
            params = {
                'q': query,
                'from': from_date.isoformat(),
                'to': to_date.isoformat(),
                'language': language,
                'sortBy': 'publishedAt',
                'pageSize': page_size,
                'apiKey': self.api_key
            }
            
            response = requests.get(
                f"{self.base_url}/everything",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'ok':
                raise ValueError(f"NewsAPI error: {data.get('message', 'Unknown error')}")
            
            articles = []
            for item in data.get('articles', []):
                try:
                    # Parse published date
                    published_str = item.get('publishedAt', '')
                    published_at = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                    
                    article = NewsArticle(
                        title=item.get('title', ''),
                        summary=item.get('description', ''),
                        source=item.get('source', {}).get('name', 'Unknown'),
                        published_at=published_at,
                        url=item.get('url', ''),
                        sentiment=None  # NewsAPI doesn't provide sentiment
                    )
                    articles.append(article)
                except Exception as e:
                    logger.warning(f"Error parsing NewsAPI article: {e}")
                    continue
            
            logger.info(f"Retrieved {len(articles)} articles from NewsAPI")
            return articles
        
        try:
            return self.call_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Failed to get market news from NewsAPI: {e}")
            return []
    
    def get_company_news(
        self,
        company_name: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        page_size: int = 100
    ) -> List[NewsArticle]:
        """
        Get news articles about a specific company.
        
        Args:
            company_name: Company name to search for
            from_date: Start date
            to_date: End date
            page_size: Number of results
            
        Returns:
            List of NewsArticle objects
        """
        query = f'"{company_name}" AND (stock OR shares OR earnings OR revenue)'
        return self.get_market_news(query, from_date, to_date, page_size=page_size)
