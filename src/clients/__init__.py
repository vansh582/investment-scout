"""API clients for external services"""

# Import new Investment Scout clients
from .base_api_client import BaseAPIClient, CircuitBreaker, RateLimiter
from .yfinance_client_scout import YFinanceClient
from .finnhub_client_scout import FinnhubClient
from .twelve_data_client_scout import TwelveDataClient
from .robinhood_client_scout import RobinhoodClient

# Import free data source clients (Task 24)
from .newsapi_client import NewsAPIClient
from .alphavantage_client import AlphaVantageClient
from .fred_client import FREDClient
from .worldbank_client import WorldBankClient
from .rss_feed_client import RSSFeedClient
from .web_scraper_client import WebScraperClient

__all__ = [
    "BaseAPIClient",
    "CircuitBreaker",
    "RateLimiter",
    "YFinanceClient",
    "FinnhubClient",
    "TwelveDataClient",
    "RobinhoodClient",
    "NewsAPIClient",
    "AlphaVantageClient",
    "FREDClient",
    "WorldBankClient",
    "RSSFeedClient",
    "WebScraperClient"
]
