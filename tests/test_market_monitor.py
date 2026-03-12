"""
Unit Tests for Market Monitor

Tests failover chain, stale data rejection, and dual TTL polling.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from src.utils.market_monitor import MarketMonitor
from src.models.investment_scout_models import Quote


def create_mock_quote(symbol: str, latency_seconds: float = 5.0) -> Quote:
    """Helper to create a mock quote with specific latency"""
    now = datetime.now()
    exchange_ts = now - timedelta(seconds=latency_seconds)
    
    return Quote(
        symbol=symbol,
        price=Decimal('100.00'),
        exchange_timestamp=exchange_ts,
        received_timestamp=now,
        bid=Decimal('99.99'),
        ask=Decimal('100.01'),
        volume=1000000
    )


def test_failover_chain_yfinance_success():
    """Test that yfinance is tried first and succeeds"""
    # Mock dependencies
    mock_dm = Mock()
    mock_yf = Mock()
    mock_fh = Mock()
    mock_td = Mock()
    
    # yfinance returns fresh quote
    fresh_quote = create_mock_quote("AAPL", latency_seconds=5.0)
    mock_yf.get_quote.return_value = fresh_quote
    
    monitor = MarketMonitor(mock_dm, mock_yf, mock_fh, mock_td)
    result = monitor.get_current_price("AAPL")
    
    # Should return yfinance result
    assert result == fresh_quote
    assert mock_yf.get_quote.called
    assert not mock_fh.get_quote.called  # Should not try Finnhub
    assert not mock_td.get_quote.called  # Should not try TwelveData


def test_failover_chain_yfinance_stale_finnhub_success():
    """Test failover to Finnhub when yfinance returns stale data"""
    mock_dm = Mock()
    mock_yf = Mock()
    mock_fh = Mock()
    mock_td = Mock()
    
    # yfinance returns stale quote
    stale_quote = create_mock_quote("AAPL", latency_seconds=45.0)
    mock_yf.get_quote.return_value = stale_quote
    
    # Finnhub returns fresh quote
    fresh_quote = create_mock_quote("AAPL", latency_seconds=5.0)
    mock_fh.get_quote.return_value = fresh_quote
    
    monitor = MarketMonitor(mock_dm, mock_yf, mock_fh, mock_td)
    result = monitor.get_current_price("AAPL")
    
    # Should return Finnhub result
    assert result == fresh_quote
    assert mock_yf.get_quote.called
    assert mock_fh.get_quote.called  # Should try Finnhub
    assert not mock_td.get_quote.called  # Should not try TwelveData
    assert monitor.stats["failover_events"] == 1
    assert monitor.stats["stale_data_rejections"] == 1


def test_failover_chain_all_fail_use_cache():
    """Test cache fallback when all API sources fail"""
    mock_dm = Mock()
    mock_yf = Mock()
    mock_fh = Mock()
    mock_td = Mock()
    
    # All API sources return None
    mock_yf.get_quote.return_value = None
    mock_fh.get_quote.return_value = None
    mock_td.get_quote.return_value = None
    
    # Cache returns fresh quote
    cached_quote = create_mock_quote("AAPL", latency_seconds=10.0)
    mock_dm.get_cached_quote.return_value = cached_quote
    
    monitor = MarketMonitor(mock_dm, mock_yf, mock_fh, mock_td)
    result = monitor.get_current_price("AAPL")
    
    # Should return cached result
    assert result == cached_quote
    assert mock_dm.get_cached_quote.called
    assert monitor.stats["cache_hits"] == 1
    assert monitor.stats["failover_events"] == 2  # Tried Finnhub and TwelveData


def test_stale_data_rejection():
    """Test that stale data (>30s) is rejected"""
    mock_dm = Mock()
    mock_yf = Mock()
    
    # Create stale quote (45 seconds old)
    stale_quote = create_mock_quote("AAPL", latency_seconds=45.0)
    
    monitor = MarketMonitor(mock_dm, mock_yf)
    
    # Should reject stale data
    assert not monitor.is_data_fresh(stale_quote)
    assert stale_quote.latency.total_seconds() > 30.0


def test_fresh_data_acceptance():
    """Test that fresh data (<=30s) is accepted"""
    mock_dm = Mock()
    mock_yf = Mock()
    
    # Create fresh quote (10 seconds old)
    fresh_quote = create_mock_quote("AAPL", latency_seconds=10.0)
    
    monitor = MarketMonitor(mock_dm, mock_yf)
    
    # Should accept fresh data
    assert monitor.is_data_fresh(fresh_quote)
    assert fresh_quote.latency.total_seconds() <= 30.0


def test_edge_case_exactly_30_seconds():
    """Test edge case: exactly 30 seconds should be considered fresh"""
    mock_dm = Mock()
    mock_yf = Mock()
    
    # Create quote exactly 30 seconds old
    quote_30s = create_mock_quote("AAPL", latency_seconds=30.0)
    
    monitor = MarketMonitor(mock_dm, mock_yf)
    
    # Should accept data at exactly 30 seconds
    assert monitor.is_data_fresh(quote_30s)


def test_dual_ttl_polling_intervals():
    """Test that active and watchlist stocks have different polling intervals"""
    monitor = MarketMonitor(Mock(), Mock())
    
    # Verify intervals match requirements
    assert monitor.ACTIVE_INTERVAL == 15  # Active stocks: 15 seconds
    assert monitor.WATCHLIST_INTERVAL == 60  # Watchlist stocks: 60 seconds


def test_update_watchlist():
    """Test dynamic watchlist updates"""
    mock_dm = Mock()
    mock_yf = Mock()
    
    monitor = MarketMonitor(mock_dm, mock_yf)
    
    # Start with initial symbols
    monitor.start_monitoring(["AAPL", "MSFT"], ["GOOGL"])
    assert len(monitor.active_symbols) == 2
    assert len(monitor.watchlist_symbols) == 1
    
    # Update watchlist
    monitor.update_watchlist(["AAPL", "TSLA"], ["GOOGL", "AMZN"])
    assert len(monitor.active_symbols) == 2
    assert "TSLA" in monitor.active_symbols
    assert "MSFT" not in monitor.active_symbols
    assert len(monitor.watchlist_symbols) == 2


def test_poll_symbol_caches_with_correct_ttl():
    """Test that polling caches quotes with appropriate TTL"""
    mock_dm = Mock()
    mock_yf = Mock()
    
    fresh_quote = create_mock_quote("AAPL", latency_seconds=5.0)
    mock_yf.get_quote.return_value = fresh_quote
    
    monitor = MarketMonitor(mock_dm, mock_yf)
    
    # Poll active symbol
    monitor._poll_symbol("AAPL", is_active=True)
    
    # Should cache with is_active=True
    mock_dm.cache_quote.assert_called_once()
    call_args = mock_dm.cache_quote.call_args
    assert call_args[0][0] == "AAPL"  # symbol
    assert call_args[0][1] == fresh_quote  # quote
    assert call_args[1]["is_active"] is True  # is_active flag
    
    # Should also store in PostgreSQL
    mock_dm.store_historical_quote.assert_called_once_with(fresh_quote)


def test_statistics_tracking():
    """Test that monitoring statistics are tracked correctly"""
    mock_dm = Mock()
    mock_yf = Mock()
    
    fresh_quote = create_mock_quote("AAPL", latency_seconds=5.0)
    mock_yf.get_quote.return_value = fresh_quote
    
    monitor = MarketMonitor(mock_dm, mock_yf)
    
    # Initial stats
    assert monitor.stats["total_polls"] == 0
    assert monitor.stats["successful_polls"] == 0
    
    # Poll a symbol
    monitor._poll_symbol("AAPL", is_active=True)
    
    # Stats should update
    assert monitor.stats["total_polls"] == 1
    assert monitor.stats["successful_polls"] == 1
    assert monitor.stats["failed_polls"] == 0


def test_failed_poll_statistics():
    """Test that failed polls are tracked"""
    mock_dm = Mock()
    mock_yf = Mock()
    
    # All sources return None
    mock_yf.get_quote.return_value = None
    mock_dm.get_cached_quote.return_value = None
    
    monitor = MarketMonitor(mock_dm, mock_yf)
    
    # Poll a symbol
    monitor._poll_symbol("AAPL", is_active=True)
    
    # Should track failure
    assert monitor.stats["total_polls"] == 1
    assert monitor.stats["successful_polls"] == 0
    assert monitor.stats["failed_polls"] == 1
