"""Robinhood API client for tradeable securities and market hours"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import robin_stocks.robinhood as rh

from ..models import Security
from ..utils.credential_manager import credential_manager


logger = logging.getLogger(__name__)


class TradingHours:
    """Trading hours information"""
    def __init__(self, is_open: bool, opens_at: Optional[datetime] = None, closes_at: Optional[datetime] = None):
        self.is_open = is_open
        self.opens_at = opens_at
        self.closes_at = closes_at


class RobinhoodClient:
    """Client for interacting with Robinhood API"""
    
    def __init__(self):
        """Initialize Robinhood client"""
        self.username = credential_manager.get_credential('robinhood_username')
        self.password = credential_manager.get_credential('robinhood_password')
        self._authenticated = False
        self._tradeable_securities_cache: Optional[List[Security]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(hours=24)
    
    def _authenticate(self) -> bool:
        """
        Authenticate with Robinhood API
        
        Returns:
            True if authentication successful, False otherwise
        """
        if self._authenticated:
            return True
        
        try:
            login = rh.login(self.username, self.password)
            if login:
                self._authenticated = True
                logger.info("Successfully authenticated with Robinhood")
                return True
            else:
                logger.error("Failed to authenticate with Robinhood")
                return False
        except Exception as e:
            logger.error(f"Robinhood authentication error: {e}")
            return False
    
    def get_tradeable_securities(self) -> List[Security]:
        """
        Get list of tradeable securities on Robinhood
        
        Returns:
            List of Security objects
        
        Note:
            Results are cached for 24 hours to reduce API calls
        """
        # Check cache
        if self._tradeable_securities_cache and self._cache_timestamp:
            if datetime.now() - self._cache_timestamp < self._cache_ttl:
                logger.debug("Returning cached tradeable securities")
                return self._tradeable_securities_cache
        
        # Authenticate if needed
        if not self._authenticate():
            logger.error("Cannot fetch tradeable securities: authentication failed")
            return []
        
        try:
            # Get all stocks available on Robinhood
            # Note: robin_stocks doesn't have a direct "get all tradeable" method,
            # so we'll use a workaround by getting popular stocks
            instruments = rh.get_all_stocks_from_market_tag('top-movers')
            
            securities = []
            for instrument in instruments[:100]:  # Limit to avoid rate limits
                try:
                    symbol = instrument.get('symbol')
                    if not symbol:
                        continue
                    
                    # Get instrument details
                    instrument_data = rh.get_instrument_by_symbol(symbol)
                    if not instrument_data:
                        continue
                    
                    # Check if tradeable
                    tradeable = instrument_data.get('tradeable', False)
                    if not tradeable:
                        continue
                    
                    # Get quote for volume data
                    quote = rh.get_latest_price(symbol)
                    volume = 0
                    if quote:
                        try:
                            volume = int(float(quote[0]) * 1000000)  # Estimate
                        except:
                            pass
                    
                    security = Security(
                        symbol=symbol,
                        name=instrument_data.get('simple_name', symbol),
                        tradeable_on_robinhood=True,
                        supports_fractional_shares=instrument_data.get('fractional_tradability', 'untradable') != 'untradable',
                        average_volume=volume,
                        sector='Unknown',  # Robinhood API doesn't provide this directly
                        industry='Unknown'
                    )
                    securities.append(security)
                
                except Exception as e:
                    logger.warning(f"Error processing instrument {instrument.get('symbol', 'unknown')}: {e}")
                    continue
            
            # Update cache
            self._tradeable_securities_cache = securities
            self._cache_timestamp = datetime.now()
            
            logger.info(f"Fetched {len(securities)} tradeable securities from Robinhood")
            return securities
        
        except Exception as e:
            logger.error(f"Error fetching tradeable securities: {e}")
            return []
    
    def supports_fractional_shares(self, ticker: str) -> bool:
        """
        Check if a ticker supports fractional share trading on Robinhood
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            True if fractional shares are supported, False otherwise
        """
        if not self._authenticate():
            return False
        
        try:
            instrument = rh.get_instrument_by_symbol(ticker)
            if not instrument:
                return False
            
            fractional_tradability = instrument.get('fractional_tradability', 'untradable')
            return fractional_tradability != 'untradable'
        
        except Exception as e:
            logger.error(f"Error checking fractional shares for {ticker}: {e}")
            return False
    
    def is_market_open(self) -> bool:
        """
        Check if the market is currently open
        
        Returns:
            True if market is open, False otherwise
        """
        if not self._authenticate():
            return False
        
        try:
            # Get market hours for today
            hours = rh.get_market_today_hours('XNYS')  # NYSE
            if not hours:
                return False
            
            is_open = hours.get('is_open', False)
            return is_open
        
        except Exception as e:
            logger.error(f"Error checking market hours: {e}")
            return False
    
    def get_trading_hours(self) -> TradingHours:
        """
        Get trading hours for today
        
        Returns:
            TradingHours object with market status and times
        """
        if not self._authenticate():
            return TradingHours(is_open=False)
        
        try:
            hours = rh.get_market_today_hours('XNYS')  # NYSE
            if not hours:
                return TradingHours(is_open=False)
            
            is_open = hours.get('is_open', False)
            opens_at = None
            closes_at = None
            
            if 'opens_at' in hours:
                try:
                    opens_at = datetime.fromisoformat(hours['opens_at'].replace('Z', '+00:00'))
                except:
                    pass
            
            if 'closes_at' in hours:
                try:
                    closes_at = datetime.fromisoformat(hours['closes_at'].replace('Z', '+00:00'))
                except:
                    pass
            
            return TradingHours(is_open=is_open, opens_at=opens_at, closes_at=closes_at)
        
        except Exception as e:
            logger.error(f"Error getting trading hours: {e}")
            return TradingHours(is_open=False)
    
    def logout(self):
        """Logout from Robinhood"""
        try:
            rh.logout()
            self._authenticated = False
            logger.info("Logged out from Robinhood")
        except Exception as e:
            logger.error(f"Error logging out: {e}")
