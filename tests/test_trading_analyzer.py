"""
Unit tests for Trading Analyzer

Tests buy signal detection, sell signal detection, alert frequency limiting,
and entry/exit calculation.

Requirements: 12.1-12.7
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch

from src.utils.trading_analyzer import TradingAnalyzer, TradingLevels
from src.models.investment_scout_models import Quote, SignalType, TradingAlert


class TestTradingAnalyzer:
    """Test suite for TradingAnalyzer"""
    
    @pytest.fixture
    def mock_data_manager(self):
        """Create mock data manager"""
        dm = Mock()
        dm.redis_client = Mock()
        dm.get_historical_quotes = Mock(return_value=[])
        dm.get_financial_data = Mock(return_value={'company_name': 'Test Company'})
        return dm
    
    @pytest.fixture
    def mock_research_engine(self):
        """Create mock research engine"""
        re = Mock()
        # Create a mock CompanyContext object
        mock_context = Mock()
        mock_context.symbol = 'TEST'
        mock_context.financial_data = None
        mock_context.recent_news = []
        mock_context.news_sentiment = None  # Will be overridden in tests
        mock_context.relevant_geo_events = []
        mock_context.industry_trends = []
        mock_context.projections = []
        re.get_company_context = Mock(return_value=mock_context)
        return re
    
    @pytest.fixture
    def analyzer(self, mock_data_manager, mock_research_engine):
        """Create TradingAnalyzer instance"""
        return TradingAnalyzer(
            data_manager=mock_data_manager,
            research_engine=mock_research_engine,
            max_alerts_per_day=5
        )
    
    @pytest.fixture
    def fresh_quote(self):
        """Create a fresh quote (<30s latency)"""
        now = datetime.now()
        return Quote(
            symbol='TEST',
            price=Decimal('100.00'),
            exchange_timestamp=now - timedelta(seconds=10),
            received_timestamp=now,
            bid=Decimal('99.95'),
            ask=Decimal('100.05'),
            volume=1000000
        )
    
    @pytest.fixture
    def stale_quote(self):
        """Create a stale quote (>30s latency)"""
        now = datetime.now()
        return Quote(
            symbol='TEST',
            price=Decimal('100.00'),
            exchange_timestamp=now - timedelta(seconds=45),
            received_timestamp=now,
            bid=Decimal('99.95'),
            ask=Decimal('100.05'),
            volume=1000000
        )
    
    def test_analyze_real_time_rejects_stale_data(self, analyzer, stale_quote):
        """Test that stale data is rejected (Requirement 12.8)"""
        result = analyzer.analyze_real_time(stale_quote)
        assert result is None
    
    def test_analyze_real_time_accepts_fresh_data(self, analyzer, fresh_quote, mock_data_manager):
        """Test that fresh data is accepted"""
        # Not enough historical data, so no signal
        mock_data_manager.get_historical_quotes.return_value = []
        result = analyzer.analyze_real_time(fresh_quote)
        # Should not reject due to freshness, but may return None due to no signal
        assert result is None or isinstance(result, TradingAlert)
    
    def test_check_alert_limit_no_alerts_today(self, analyzer, mock_data_manager):
        """Test alert limit check when no alerts sent today"""
        mock_data_manager.redis_client.get.return_value = None
        assert analyzer.check_alert_limit() is True
    
    def test_check_alert_limit_under_limit(self, analyzer, mock_data_manager):
        """Test alert limit check when under limit"""
        mock_data_manager.redis_client.get.return_value = '2'
        assert analyzer.check_alert_limit() is True
    
    def test_check_alert_limit_at_limit(self, analyzer, mock_data_manager):
        """Test alert limit check when at limit (Requirement 12.10)"""
        mock_data_manager.redis_client.get.return_value = '5'
        assert analyzer.check_alert_limit() is False
    
    def test_check_alert_limit_over_limit(self, analyzer, mock_data_manager):
        """Test alert limit check when over limit"""
        mock_data_manager.redis_client.get.return_value = '6'
        assert analyzer.check_alert_limit() is False
    
    def test_increment_alert_count(self, analyzer, mock_data_manager):
        """Test incrementing alert count"""
        analyzer.increment_alert_count()
        mock_data_manager.redis_client.incr.assert_called_once()
        mock_data_manager.redis_client.expire.assert_called_once()
    
    def test_detect_buy_signal_breakout(self, analyzer, fresh_quote, mock_data_manager, mock_research_engine):
        """Test buy signal detection for breakout (Requirement 12.3)"""
        # Create historical data showing price below SMA, then breaking out
        historical_quotes = []
        for i in range(20):
            historical_quotes.append({
                'symbol': 'TEST',
                'price': 95.0,  # Below current price
                'timestamp': datetime.now() - timedelta(days=20-i)
            })
        
        mock_data_manager.get_historical_quotes.return_value = historical_quotes
        mock_context = Mock()
        mock_context.news_sentiment = 0.0
        mock_research_engine.get_company_context.return_value = mock_context
        
        result = analyzer.detect_buy_signal(fresh_quote)
        
        # Should detect breakout
        assert result is not None
        assert result.signal_type == SignalType.BUY
        assert result.symbol == 'TEST'
        assert 'Breakout' in result.rationale or 'breakout' in result.rationale.lower()
    
    def test_detect_buy_signal_oversold_bounce(self, analyzer, fresh_quote, mock_data_manager, mock_research_engine):
        """Test buy signal detection for oversold bounce (Requirement 12.3)"""
        # Create historical data showing >5% drop then bounce
        historical_quotes = []
        for i in range(20):
            if i < 19:
                historical_quotes.append({
                    'symbol': 'TEST',
                    'price': 110.0,  # Higher price before drop
                    'timestamp': datetime.now() - timedelta(days=20-i)
                })
            else:
                historical_quotes.append({
                    'symbol': 'TEST',
                    'price': 99.0,  # Lower than current, showing bounce
                    'timestamp': datetime.now() - timedelta(days=1)
                })
        
        mock_data_manager.get_historical_quotes.return_value = historical_quotes
        mock_context = Mock()
        mock_context.news_sentiment = 0.0
        mock_research_engine.get_company_context.return_value = mock_context
        
        result = analyzer.detect_buy_signal(fresh_quote)
        
        # Should detect oversold bounce
        assert result is not None
        assert result.signal_type == SignalType.BUY
    
    def test_detect_buy_signal_positive_catalyst(self, analyzer, fresh_quote, mock_data_manager, mock_research_engine):
        """Test buy signal detection for positive news catalyst (Requirement 12.3)"""
        # Flat price history
        historical_quotes = []
        for i in range(20):
            historical_quotes.append({
                'symbol': 'TEST',
                'price': 100.0,
                'timestamp': datetime.now() - timedelta(days=20-i)
            })
        
        mock_data_manager.get_historical_quotes.return_value = historical_quotes
        
        # Positive news sentiment
        mock_context = Mock()
        mock_context.news_sentiment = 0.5  # Positive
        mock_research_engine.get_company_context.return_value = mock_context
        
        result = analyzer.detect_buy_signal(fresh_quote)
        
        # Should detect positive catalyst
        assert result is not None
        assert result.signal_type == SignalType.BUY
        assert 'sentiment' in result.rationale.lower() or 'news' in result.rationale.lower()
    
    def test_detect_sell_signal_breakdown(self, analyzer, fresh_quote, mock_data_manager, mock_research_engine):
        """Test sell signal detection for breakdown (Requirement 12.3)"""
        # Create historical data showing price above SMA, then breaking down
        historical_quotes = []
        for i in range(20):
            historical_quotes.append({
                'symbol': 'TEST',
                'price': 105.0,  # Above current price
                'timestamp': datetime.now() - timedelta(days=20-i)
            })
        
        mock_data_manager.get_historical_quotes.return_value = historical_quotes
        mock_context = Mock()
        mock_context.news_sentiment = 0.0
        mock_research_engine.get_company_context.return_value = mock_context
        
        result = analyzer.detect_sell_signal(fresh_quote)
        
        # Should detect breakdown
        assert result is not None
        assert result.signal_type == SignalType.SELL
        assert 'Breakdown' in result.rationale or 'breakdown' in result.rationale.lower()
    
    def test_detect_sell_signal_overbought_reversal(self, analyzer, fresh_quote, mock_data_manager, mock_research_engine):
        """Test sell signal detection for overbought reversal (Requirement 12.3)"""
        # Create historical data showing >10% rally then reversal
        historical_quotes = []
        for i in range(20):
            if i < 19:
                historical_quotes.append({
                    'symbol': 'TEST',
                    'price': 85.0,  # Lower price before rally
                    'timestamp': datetime.now() - timedelta(days=20-i)
                })
            else:
                historical_quotes.append({
                    'symbol': 'TEST',
                    'price': 101.0,  # Higher than current, showing reversal
                    'timestamp': datetime.now() - timedelta(days=1)
                })
        
        mock_data_manager.get_historical_quotes.return_value = historical_quotes
        mock_context = Mock()
        mock_context.news_sentiment = 0.0
        mock_research_engine.get_company_context.return_value = mock_context
        
        result = analyzer.detect_sell_signal(fresh_quote)
        
        # Should detect overbought reversal
        assert result is not None
        assert result.signal_type == SignalType.SELL
    
    def test_detect_sell_signal_negative_news(self, analyzer, fresh_quote, mock_data_manager, mock_research_engine):
        """Test sell signal detection for negative news (Requirement 12.3)"""
        # Flat price history
        historical_quotes = []
        for i in range(20):
            historical_quotes.append({
                'symbol': 'TEST',
                'price': 100.0,
                'timestamp': datetime.now() - timedelta(days=20-i)
            })
        
        mock_data_manager.get_historical_quotes.return_value = historical_quotes
        
        # Negative news sentiment
        mock_context = Mock()
        mock_context.news_sentiment = -0.5  # Negative
        mock_research_engine.get_company_context.return_value = mock_context
        
        result = analyzer.detect_sell_signal(fresh_quote)
        
        # Should detect negative news
        assert result is not None
        assert result.signal_type == SignalType.SELL
        assert 'sentiment' in result.rationale.lower() or 'news' in result.rationale.lower()
    
    def test_calculate_entry_exit_buy(self, analyzer):
        """Test entry/exit calculation for buy signal (Requirement 12.9)"""
        current_price = Decimal('100.00')
        volatility = Decimal('2.00')
        
        levels = analyzer.calculate_entry_exit(
            symbol='TEST',
            current_price=current_price,
            signal_type=SignalType.BUY,
            volatility=volatility
        )
        
        assert levels.entry_price == current_price
        assert levels.target_price > current_price  # Target above entry
        assert levels.stop_loss < current_price  # Stop below entry
        assert levels.stop_loss > Decimal('0')  # Stop loss not negative
        assert levels.risk_reward_ratio == Decimal('2.0')  # 2:1 ratio
    
    def test_calculate_entry_exit_sell(self, analyzer):
        """Test entry/exit calculation for sell signal (Requirement 12.9)"""
        current_price = Decimal('100.00')
        volatility = Decimal('2.00')
        
        levels = analyzer.calculate_entry_exit(
            symbol='TEST',
            current_price=current_price,
            signal_type=SignalType.SELL,
            volatility=volatility
        )
        
        assert levels.entry_price == current_price
        assert levels.target_price < current_price  # Target below entry (short)
        assert levels.stop_loss > current_price  # Stop above entry (short)
        assert levels.risk_reward_ratio == Decimal('2.0')  # 2:1 ratio
    
    def test_calculate_entry_exit_prevents_negative_stop_loss(self, analyzer):
        """Test that stop loss is never negative"""
        current_price = Decimal('1.00')
        volatility = Decimal('5.00')  # Large volatility
        
        levels = analyzer.calculate_entry_exit(
            symbol='TEST',
            current_price=current_price,
            signal_type=SignalType.BUY,
            volatility=volatility
        )
        
        assert levels.stop_loss >= Decimal('0.01')  # Minimum stop loss
    
    def test_calculate_trading_position_size_low_volatility(self, analyzer):
        """Test position sizing for low volatility"""
        volatility = Decimal('1.00')
        current_price = Decimal('100.00')
        
        position_size = analyzer._calculate_trading_position_size(volatility, current_price)
        
        # Low volatility (<2%) should give larger position
        assert Decimal('15.0') <= position_size <= Decimal('25.0')
    
    def test_calculate_trading_position_size_medium_volatility(self, analyzer):
        """Test position sizing for medium volatility"""
        volatility = Decimal('3.00')
        current_price = Decimal('100.00')
        
        position_size = analyzer._calculate_trading_position_size(volatility, current_price)
        
        # Medium volatility (2-5%) should give medium position
        assert Decimal('8.0') <= position_size <= Decimal('15.0')
    
    def test_calculate_trading_position_size_high_volatility(self, analyzer):
        """Test position sizing for high volatility"""
        volatility = Decimal('6.00')
        current_price = Decimal('100.00')
        
        position_size = analyzer._calculate_trading_position_size(volatility, current_price)
        
        # High volatility (>5%) should give smaller position
        assert Decimal('1.0') <= position_size <= Decimal('8.0')
    
    def test_trading_alert_includes_required_fields(self, analyzer, fresh_quote, mock_data_manager, mock_research_engine):
        """Test that trading alerts include all required fields (Requirement 12.6)"""
        # Setup for buy signal
        historical_quotes = []
        for i in range(20):
            historical_quotes.append({
                'symbol': 'TEST',
                'price': 95.0,
                'timestamp': datetime.now() - timedelta(days=20-i)
            })
        
        mock_data_manager.get_historical_quotes.return_value = historical_quotes
        mock_context = Mock()
        mock_context.news_sentiment = 0.0
        mock_research_engine.get_company_context.return_value = mock_context
        
        result = analyzer.detect_buy_signal(fresh_quote)
        
        assert result is not None
        assert result.symbol == 'TEST'
        assert result.company_name is not None
        assert result.signal_type in [SignalType.BUY, SignalType.SELL]
        assert result.current_price > 0
        assert result.entry_price > 0
        assert result.target_price > 0
        assert result.stop_loss > 0
        assert Decimal('1.0') <= result.position_size_percent <= Decimal('25.0')
        assert result.rationale is not None
        assert len(result.rationale) > 0
        assert result.expected_holding_period == "minutes to days"
        assert result.data_timestamp is not None
    
    def test_no_signal_with_insufficient_data(self, analyzer, fresh_quote, mock_data_manager):
        """Test that no signal is generated with insufficient historical data"""
        # Only 10 data points (need 20)
        historical_quotes = []
        for i in range(10):
            historical_quotes.append({
                'symbol': 'TEST',
                'price': 100.0,
                'timestamp': datetime.now() - timedelta(days=10-i)
            })
        
        mock_data_manager.get_historical_quotes.return_value = historical_quotes
        
        buy_result = analyzer.detect_buy_signal(fresh_quote)
        sell_result = analyzer.detect_sell_signal(fresh_quote)
        
        assert buy_result is None
        assert sell_result is None
    
    def test_analyze_real_time_respects_alert_limit(self, analyzer, fresh_quote, mock_data_manager):
        """Test that analyze_real_time respects daily alert limit"""
        # Set alert count at limit
        mock_data_manager.redis_client.get.return_value = '5'
        
        # Even with a potential signal, should return None due to limit
        result = analyzer.analyze_real_time(fresh_quote)
        
        assert result is None
