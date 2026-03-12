"""
Robinhood API Client for Investment Scout

Used for verifying security tradeability on Robinhood platform.
Results are cached for 24 hours to minimize API calls.
"""

import logging
from typing import Optional, Dict
import requests

from src.clients.base_api_client import BaseAPIClient


logger = logging.getLogger(__name__)


class RobinhoodClient(BaseAPIClient):
    """
    Robinhood client for security tradeability verification.
    
    Conservative rate limit: ~100 requests per minute
    """
    
    BASE_URL = "https://api.robinhood.com"
    
    def __init__(self):
        super().__init__(
            name="Robinhood",
            requests_per_minute=100,  # Conservative estimate
            failure_threshold=5,
            circuit_timeout=60
        )
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; InvestmentScout/1.0)"
        })
    
    def is_tradeable(self, symbol: str) -> bool:
        """
        Check if a security is tradeable on Robinhood.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if tradeable, False otherwise
        """
        def _fetch():
            # Search for the instrument
            url = f"{self.BASE_URL}/instruments/"
            params = {"symbol": symbol}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('results'):
                return False
            
            instrument = data['results'][0]
            
            # Check if tradeable
            tradeable = instrument.get('tradeable', False)
            
            return tradeable
        
        try:
            result = self.call_with_retry(_fetch)
            logger.debug(f"Robinhood tradeability for {symbol}: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to check Robinhood tradeability for {symbol}: {e}")
            # Default to False if we can't verify
            return False
    
    def supports_fractional_shares(self, symbol: str) -> bool:
        """
        Check if a security supports fractional shares on Robinhood.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if fractional shares supported, False otherwise
        """
        def _fetch():
            url = f"{self.BASE_URL}/instruments/"
            params = {"symbol": symbol}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('results'):
                return False
            
            instrument = data['results'][0]
            
            # Check fractional share support
            fractional = instrument.get('fractional_tradeable', False)
            
            return fractional
        
        try:
            result = self.call_with_retry(_fetch)
            logger.debug(f"Robinhood fractional shares for {symbol}: {result}")
            return result
        except Exception as e:
            logger.error(
                f"Failed to check Robinhood fractional shares for {symbol}: {e}"
            )
            # Default to False if we can't verify
            return False
    
    def get_instrument_info(self, symbol: str) -> Optional[Dict]:
        """
        Get full instrument information from Robinhood.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with instrument info or None if failed
        """
        def _fetch():
            url = f"{self.BASE_URL}/instruments/"
            params = {"symbol": symbol}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('results'):
                raise ValueError(f"No instrument found for {symbol}")
            
            return data['results'][0]
        
        try:
            return self.call_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Failed to get Robinhood instrument info for {symbol}: {e}")
            return None
