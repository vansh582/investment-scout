"""
Market Monitor for Investment Scout

Continuously monitors stock markets 24/7 with dual TTL polling strategy:
- Active stocks: Poll every 15 seconds
- Watchlist stocks: Poll every 60 seconds

Implements failover chain: yfinance → Finnhub → Twelve Data → cache
"""

import logging
import threading
import time
from typing import List, Optional, Set, Dict
from datetime import datetime

from src.clients.yfinance_client_scout import YFinanceClient
from src.clients.finnhub_client_scout import FinnhubClient
from src.clients.twelve_data_client_scout import TwelveDataClient
from src.utils.data_manager_scout import DataManager
from src.models.investment_scout_models import Quote


logger = logging.getLogger(__name__)


class MarketMonitor:
    """
    Continuously monitors stock markets with dual TTL polling strategy.
    
    - Active stocks: 15-second polling interval
    - Watchlist stocks: 60-second polling interval
    - Failover chain: yfinance → Finnhub → Twelve Data → cache
    - Rejects stale data (>30s latency)
    """
    
    ACTIVE_INTERVAL = 15  # seconds
    WATCHLIST_INTERVAL = 60  # seconds
    
    def __init__(
        self,
        data_manager: DataManager,
        yfinance_client: YFinanceClient,
        finnhub_client: Optional[FinnhubClient] = None,
        twelve_data_client: Optional[TwelveDataClient] = None
    ):
        """
        Initialize Market Monitor.
        
        Args:
            data_manager: Data manager for caching and persistence
            yfinance_client: Primary data source
            finnhub_client: Secondary data source (optional)
            twelve_data_client: Tertiary data source (optional)
        """
        self.data_manager = data_manager
        self.yfinance_client = yfinance_client
        self.finnhub_client = finnhub_client
        self.twelve_data_client = twelve_data_client
        
        self.active_symbols: Set[str] = set()
        self.watchlist_symbols: Set[str] = set()
        
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Track last poll times
        self._last_active_poll: Dict[str, float] = {}
        self._last_watchlist_poll: Dict[str, float] = {}
        
        # Statistics
        self.stats = {
            "total_polls": 0,
            "successful_polls": 0,
            "failed_polls": 0,
            "stale_data_rejections": 0,
            "cache_hits": 0,
            "failover_events": 0
        }
        
        logger.info("MarketMonitor initialized")
    
    def start_monitoring(self, active_symbols: List[str], watchlist_symbols: List[str] = None):
        """
        Start 24/7 continuous monitoring.
        
        Args:
            active_symbols: Symbols to monitor every 15 seconds
            watchlist_symbols: Symbols to monitor every 60 seconds
        """
        if self._monitoring:
            logger.warning("Market monitoring already running")
            return
        
        self.active_symbols = set(active_symbols)
        self.watchlist_symbols = set(watchlist_symbols or [])
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info(
            f"Started market monitoring: {len(self.active_symbols)} active, "
            f"{len(self.watchlist_symbols)} watchlist"
        )
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        if not self._monitoring:
            return
        
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        logger.info("Stopped market monitoring")
    
    def update_watchlist(self, active_symbols: List[str], watchlist_symbols: List[str]):
        """
        Update monitored symbols dynamically.
        
        Args:
            active_symbols: New active symbols list
            watchlist_symbols: New watchlist symbols list
        """
        self.active_symbols = set(active_symbols)
        self.watchlist_symbols = set(watchlist_symbols)
        
        logger.info(
            f"Updated watchlist: {len(self.active_symbols)} active, "
            f"{len(self.watchlist_symbols)} watchlist"
        )
    
    def get_current_price(self, symbol: str) -> Optional[Quote]:
        """
        Get current price with failover chain.
        
        Failover order: yfinance → Finnhub → Twelve Data → cache
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Quote object or None if all sources fail
        """
        # Try yfinance (primary)
        quote = self.yfinance_client.get_quote(symbol)
        if quote and self.is_data_fresh(quote):
            return quote
        
        if quote and not self.is_data_fresh(quote):
            self.stats["stale_data_rejections"] += 1
            logger.warning(
                f"Rejected stale data from yfinance for {symbol}: "
                f"latency {quote.latency.total_seconds():.1f}s"
            )
        
        # Try Finnhub (secondary)
        if self.finnhub_client:
            self.stats["failover_events"] += 1
            logger.info(f"Failing over to Finnhub for {symbol}")
            
            quote = self.finnhub_client.get_quote(symbol)
            if quote and self.is_data_fresh(quote):
                return quote
            
            if quote and not self.is_data_fresh(quote):
                self.stats["stale_data_rejections"] += 1
                logger.warning(
                    f"Rejected stale data from Finnhub for {symbol}: "
                    f"latency {quote.latency.total_seconds():.1f}s"
                )
        
        # Try Twelve Data (tertiary)
        if self.twelve_data_client:
            self.stats["failover_events"] += 1
            logger.info(f"Failing over to TwelveData for {symbol}")
            
            quote = self.twelve_data_client.get_quote(symbol)
            if quote and self.is_data_fresh(quote):
                return quote
            
            if quote and not self.is_data_fresh(quote):
                self.stats["stale_data_rejections"] += 1
                logger.warning(
                    f"Rejected stale data from TwelveData for {symbol}: "
                    f"latency {quote.latency.total_seconds():.1f}s"
                )
        
        # Try cache (last resort)
        logger.warning(f"All API sources failed for {symbol}, trying cache")
        cached_quote = self.data_manager.get_cached_quote(symbol)
        if cached_quote:
            self.stats["cache_hits"] += 1
            logger.info(f"Retrieved {symbol} from cache")
            return cached_quote
        
        logger.error(f"Failed to get quote for {symbol} from all sources")
        return None
    
    def is_data_fresh(self, quote: Quote) -> bool:
        """
        Validate data freshness (<30 seconds latency).
        
        Args:
            quote: Quote to validate
            
        Returns:
            True if fresh, False if stale
        """
        return quote.is_fresh
    
    def poll_market_data(self):
        """Poll all monitored symbols based on their intervals"""
        current_time = time.time()
        
        # Poll active stocks (15s interval)
        for symbol in self.active_symbols:
            last_poll = self._last_active_poll.get(symbol, 0)
            if current_time - last_poll >= self.ACTIVE_INTERVAL:
                self._poll_symbol(symbol, is_active=True)
                self._last_active_poll[symbol] = current_time
        
        # Poll watchlist stocks (60s interval)
        for symbol in self.watchlist_symbols:
            last_poll = self._last_watchlist_poll.get(symbol, 0)
            if current_time - last_poll >= self.WATCHLIST_INTERVAL:
                self._poll_symbol(symbol, is_active=False)
                self._last_watchlist_poll[symbol] = current_time
    
    def _poll_symbol(self, symbol: str, is_active: bool):
        """
        Poll a single symbol and cache/store the result.
        
        Args:
            symbol: Stock symbol
            is_active: True for active stock, False for watchlist
        """
        self.stats["total_polls"] += 1
        
        try:
            quote = self.get_current_price(symbol)
            
            if quote:
                # Cache with appropriate TTL
                self.data_manager.cache_quote(symbol, quote, is_active=is_active)
                
                # Store in PostgreSQL for historical analysis
                self.data_manager.store_historical_quote(quote)
                
                self.stats["successful_polls"] += 1
                logger.debug(
                    f"Polled {symbol}: ${quote.price} "
                    f"(latency: {quote.latency.total_seconds():.1f}s)"
                )
            else:
                self.stats["failed_polls"] += 1
                logger.warning(f"Failed to poll {symbol}")
                
        except Exception as e:
            self.stats["failed_polls"] += 1
            logger.error(f"Error polling {symbol}: {e}")
    
    def _monitoring_loop(self):
        """Main monitoring loop running 24/7"""
        logger.info("Market monitoring loop started")
        
        while self._monitoring:
            try:
                self.poll_market_data()
                
                # Sleep briefly to avoid tight loop
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Wait before retrying
        
        logger.info("Market monitoring loop stopped")
    
    def get_stats(self) -> Dict:
        """Get monitoring statistics"""
        return {
            **self.stats,
            "active_symbols": len(self.active_symbols),
            "watchlist_symbols": len(self.watchlist_symbols),
            "monitoring": self._monitoring
        }
