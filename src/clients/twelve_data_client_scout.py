"""
Twelve Data API Client for Investment Scout

Tertiary data source for technical indicators and market data.
Free tier: 8 requests per minute (very limited).
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict
import requests

from src.clients.base_api_client import BaseAPIClient
from src.models.investment_scout_models import Quote


logger = logging.getLogger(__name__)


class TwelveDataClient(BaseAPIClient):
    """
    Twelve Data client for technical indicators and market data.
    
    Free tier: 8 requests per minute (very limited, use sparingly)
    """
    
    BASE_URL = "https://api.twelvedata.com"
    
    def __init__(self, api_key: str):
        super().__init__(
            name="TwelveData",
            requests_per_minute=8,  # Free tier limit (very restrictive)
            failure_threshold=3,  # Lower threshold due to limited quota
            circuit_timeout=120  # Longer timeout due to limited quota
        )
        self.api_key = api_key
    
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """
        Get current quote for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Quote object or None if failed
        """
        def _fetch():
            url = f"{self.BASE_URL}/quote"
            params = {
                "symbol": symbol,
                "apikey": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'code' in data and data['code'] != 200:
                raise ValueError(f"API error: {data.get('message', 'Unknown error')}")
            
            if 'close' not in data:
                raise ValueError(f"No quote data available for {symbol}")
            
            price = Decimal(str(data['close']))
            
            # Twelve Data doesn't provide exchange timestamp in free tier
            now = datetime.now()
            
            return Quote(
                symbol=symbol,
                price=price,
                exchange_timestamp=now,  # Approximation
                received_timestamp=now,
                bid=price,  # Free tier doesn't provide bid/ask
                ask=price,
                volume=int(data.get('volume', 0))
            )
        
        try:
            return self.call_with_retry(_fetch, max_retries=2)  # Fewer retries due to quota
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol} from TwelveData: {e}")
            return None
    
    def get_technical_indicator(
        self,
        symbol: str,
        indicator: str,
        interval: str = "1day",
        **params
    ) -> Optional[Dict]:
        """
        Get technical indicator data.
        
        Args:
            symbol: Stock symbol
            indicator: Indicator name (e.g., 'rsi', 'macd', 'sma')
            interval: Time interval (e.g., '1min', '5min', '1day')
            **params: Additional indicator-specific parameters
            
        Returns:
            Dictionary with indicator data or None if failed
        """
        def _fetch():
            url = f"{self.BASE_URL}/{indicator}"
            request_params = {
                "symbol": symbol,
                "interval": interval,
                "apikey": self.api_key,
                **params
            }
            
            response = requests.get(url, params=request_params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'code' in data and data['code'] != 200:
                raise ValueError(f"API error: {data.get('message', 'Unknown error')}")
            
            return data
        
        try:
            return self.call_with_retry(_fetch, max_retries=2)
        except Exception as e:
            logger.error(
                f"Failed to get {indicator} for {symbol} from TwelveData: {e}"
            )
            return None
    
    def get_time_series(
        self,
        symbol: str,
        interval: str = "1day",
        outputsize: int = 30
    ) -> Optional[Dict]:
        """
        Get time series data.
        
        Args:
            symbol: Stock symbol
            interval: Time interval
            outputsize: Number of data points
            
        Returns:
            Dictionary with time series data or None if failed
        """
        def _fetch():
            url = f"{self.BASE_URL}/time_series"
            params = {
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'code' in data and data['code'] != 200:
                raise ValueError(f"API error: {data.get('message', 'Unknown error')}")
            
            return data
        
        try:
            return self.call_with_retry(_fetch, max_retries=2)
        except Exception as e:
            logger.error(f"Failed to get time series for {symbol} from TwelveData: {e}")
            return None
