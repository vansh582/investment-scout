"""Twelve Data client for tertiary market data (free tier: 8 calls/min, 800 credits/day)"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict
from time import time
from twelvedata import TDClient

from ..models import Quote
from ..utils.credential_manager import credential_manager


logger = logging.getLogger(__name__)


class TwelveDataClient:
    """Client for Twelve Data API with rate limiting"""
    
    def __init__(self):
        """Initialize Twelve Data client"""
        api_key = credential_manager.get_credential('twelve_data_api_key')
        self.client = TDClient(apikey=api_key)
        
        # Rate limiting (8 calls per minute, 800 credits per day for free tier)
        self.rate_limit_per_minute = 8
        self.rate_window = 60  # seconds
        self.daily_credit_limit = 800
        self.request_timestamps: list[float] = []
        self.daily_credits_used = 0
        self.credits_reset_time: Optional[datetime] = None
    
    def _check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits
        
        Returns:
            True if request can proceed, False if rate limit exceeded
        """
        current_time = time()
        
        # Reset daily credits if needed
        if self.credits_reset_time is None or datetime.now() >= self.credits_reset_time:
            self.daily_credits_used = 0
            # Reset at midnight
            tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            from datetime import timedelta
            self.credits_reset_time = tomorrow + timedelta(days=1)
        
        # Check daily credit limit
        if self.daily_credits_used >= self.daily_credit_limit:
            logger.warning("Twelve Data daily credit limit reached")
            return False
        
        # Remove timestamps older than rate window
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if current_time - ts < self.rate_window
        ]
        
        # Check per-minute rate limit
        if len(self.request_timestamps) >= self.rate_limit_per_minute:
            logger.warning("Twelve Data per-minute rate limit reached")
            return False
        
        # Record this request
        self.request_timestamps.append(current_time)
        self.daily_credits_used += 1  # Most endpoints use 1 credit
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
            # Get real-time price
            ts = self.client.time_series(
                symbol=symbol,
                interval="1min",
                outputsize=1
            )
            
            quote_data = ts.as_json()
            
            if not quote_data or len(quote_data) == 0:
                logger.warning(f"No quote data available for {symbol}")
                return None
            
            # Get the most recent data point
            latest = quote_data[0]
            price = Decimal(str(latest.get('close', 0)))
            
            # Timestamps
            received_timestamp = datetime.now()
            try:
                exchange_timestamp = datetime.fromisoformat(latest.get('datetime', ''))
            except:
                exchange_timestamp = received_timestamp
            
            quote = Quote(
                symbol=symbol,
                price=price,
                exchange_timestamp=exchange_timestamp,
                received_timestamp=received_timestamp,
                bid=price,  # Twelve Data doesn't provide bid/ask in free tier
                ask=price,
                volume=int(latest.get('volume', 0))
            )
            
            logger.debug(f"Retrieved Twelve Data quote for {symbol}: ${price}")
            return quote
        
        except Exception as e:
            logger.error(f"Error getting Twelve Data quote for {symbol}: {e}")
            return None
    
    def get_time_series(self, symbol: str, interval: str = "1day") -> Optional[Dict]:
        """
        Get time series data
        
        Args:
            symbol: Stock ticker symbol
            interval: Time interval (1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month)
        
        Returns:
            Dictionary with time series data or None if error
        """
        if not self._check_rate_limit():
            return None
        
        try:
            ts = self.client.time_series(
                symbol=symbol,
                interval=interval,
                outputsize=30  # Last 30 data points
            )
            
            data = ts.as_json()
            
            if not data:
                logger.warning(f"No time series data available for {symbol}")
                return None
            
            logger.debug(f"Retrieved time series data for {symbol}")
            return data
        
        except Exception as e:
            logger.error(f"Error getting time series for {symbol}: {e}")
            return None
    
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
            # Note: Company profile may not be available in free tier
            # This is a placeholder for when/if it becomes available
            logger.warning(f"Company profile not available in Twelve Data free tier for {symbol}")
            return None
        
        except Exception as e:
            logger.error(f"Error getting company profile for {symbol}: {e}")
            return None
