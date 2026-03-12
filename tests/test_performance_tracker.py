"""
Unit tests for Performance Tracker

Tests portfolio performance tracking, metrics calculation, and S&P 500 comparison.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
import psycopg2

from src.utils.performance_tracker import PerformanceTracker
from src.models.investment_scout_models import (
    InvestmentOpportunity, GlobalContext, RiskLevel
)


@pytest.fixture
def mock_pg_pool():
    """Create mock PostgreSQL connection pool"""
    pool = MagicMock()
    conn = MagicMock()
    cursor = MagicMock()
    
    pool.getconn.return_value = conn
    conn.cursor.return_value.__enter__.return_value = cursor
    conn.cursor.return_value.__exit__.return_value = None
    
    return pool, conn, cursor


@pytest.fixture
def performance_tracker(mock_pg_pool):
    """Create PerformanceTracker with mocked database"""
    pool, conn, cursor = mock_pg_pool
    
    with patch('src.utils.performance_tracker.SimpleConnectionPool', return_value=pool):
        tracker = PerformanceTracker('postgresql://test')
        tracker.pg_pool = pool
        return tracker


@pytest.fixture
def sample_opportunity():
    """Create sample investment opportunity"""
    return InvestmentOpportunity(
        symbol='AAPL',
        company_name='Apple Inc.',
        current_price=Decimal('150.00'),
        target_price=Decimal('180.00'),
        position_size_percent=Decimal('10.0'),
        investment_thesis='Strong fundamentals',
        global_context=GlobalContext(
            economic_factors=[],
            geopolitical_events=[],
            industry_dynamics=[],
            company_specifics=[],
            timing_rationale='',
            risk_factors=[]
        ),
        expected_return=Decimal('20.0'),
        risk_level=RiskLevel.MEDIUM,
        expected_holding_period='3-6 months',
        data_timestamp=datetime.now()
    )


class TestPerformanceTrackerInitialization:
    """Test PerformanceTracker initialization"""
    
    def test_initialization_creates_schema(self, mock_pg_pool):
        """Test that initialization creates database schema"""
        pool, conn, cursor = mock_pg_pool
        
        with patch('src.utils.performance_tracker.SimpleConnectionPool', return_value=pool):
            tracker = PerformanceTracker('postgresql://test')
            
            # Verify schema creation was called
            assert cursor.execute.called
            execute_calls = [call[0][0] for call in cursor.execute.call_args_list]
            
            # Check that recommendations table was created
            assert any('CREATE TABLE IF NOT EXISTS recommendations' in call for call in execute_calls)
            # Check that performance_snapshots table was created
            assert any('CREATE TABLE IF NOT EXISTS performance_snapshots' in call for call in execute_calls)


class TestTrackRecommendation:
    """Test tracking new recommendations"""
    
    def test_track_recommendation_inserts_record(self, performance_tracker, sample_opportunity, mock_pg_pool):
        """Test that track_recommendation inserts a new record"""
        pool, conn, cursor = mock_pg_pool
        
        performance_tracker.track_recommendation(sample_opportunity)
        
        # Verify INSERT was executed
        cursor.execute.assert_called()
        call_args = cursor.execute.call_args[0]
        assert 'INSERT INTO recommendations' in call_args[0]
        
        # Verify correct values
        values = call_args[1]
        assert values[0] == 'AAPL'
        assert values[1] == 'investment'
        assert values[2] == Decimal('150.00')
        assert values[4] == Decimal('10.0')
        assert values[5] == Decimal('180.00')
        assert values[6] == 'open'
    
    def test_track_recommendation_handles_database_error(self, performance_tracker, sample_opportunity, mock_pg_pool):
        """Test that database errors are handled gracefully"""
        pool, conn, cursor = mock_pg_pool
        cursor.execute.side_effect = psycopg2.Error("Database error")
        
        # Should not raise exception
        performance_tracker.track_recommendation(sample_opportunity)
        
        # Verify rollback was called
        conn.rollback.assert_called_once()


class TestUpdatePositions:
    """Test updating open position values"""
    
    def test_update_positions_calculates_returns(self, performance_tracker, mock_pg_pool):
        """Test that update_positions calculates returns correctly"""
        pool, conn, cursor = mock_pg_pool
        
        # Mock open positions
        cursor.fetchall.return_value = [
            (1, 'AAPL', Decimal('150.00'), Decimal('10.0')),
            (2, 'MSFT', Decimal('300.00'), Decimal('15.0'))
        ]
        
        current_prices = {
            'AAPL': Decimal('165.00'),  # +10% return
            'MSFT': Decimal('270.00')   # -10% return
        }
        
        performance_tracker.update_positions(current_prices)
        
        # Verify UPDATE was called for each position
        update_calls = [call for call in cursor.execute.call_args_list if 'UPDATE recommendations' in str(call)]
        assert len(update_calls) == 2
    
    def test_update_positions_skips_missing_prices(self, performance_tracker, mock_pg_pool):
        """Test that positions without current prices are skipped"""
        pool, conn, cursor = mock_pg_pool
        
        cursor.fetchall.return_value = [
            (1, 'AAPL', Decimal('150.00'), Decimal('10.0')),
            (2, 'UNKNOWN', Decimal('100.00'), Decimal('5.0'))
        ]
        
        current_prices = {'AAPL': Decimal('165.00')}
        
        performance_tracker.update_positions(current_prices)
        
        # Only one UPDATE should be executed (for AAPL)
        update_calls = [call for call in cursor.execute.call_args_list if 'UPDATE recommendations' in str(call)]
        assert len(update_calls) == 1


class TestCalculateReturns:
    """Test portfolio return calculations"""
    
    def test_calculate_returns_with_no_data(self, performance_tracker, mock_pg_pool):
        """Test returns calculation with no recommendations"""
        pool, conn, cursor = mock_pg_pool
        cursor.fetchall.return_value = []
        
        metrics = performance_tracker.calculate_returns()
        
        assert metrics['total_return_percent'] == Decimal('0')
        assert metrics['win_rate'] == Decimal('0')
        assert metrics['sharpe_ratio'] == Decimal('0')
    
    def test_calculate_returns_with_single_position(self, performance_tracker, mock_pg_pool):
        """Test returns calculation with single position"""
        pool, conn, cursor = mock_pg_pool
        
        now = datetime.now()
        cursor.fetchall.return_value = [
            {
                'symbol': 'AAPL',
                'entry_price': Decimal('150.00'),
                'entry_date': now - timedelta(days=30),
                'exit_price': Decimal('165.00'),
                'exit_date': now,
                'position_size_percent': Decimal('10.0'),
                'return_percent': Decimal('10.0'),
                'status': 'closed'
            }
        ]
        
        metrics = performance_tracker.calculate_returns()
        
        # Total return = 10% * 10% position = 1%
        assert metrics['total_return_percent'] == Decimal('1.0')
        assert metrics['win_rate'] == Decimal('100.0')
        assert metrics['avg_gain_per_winner'] == Decimal('10.0')
    
    def test_calculate_returns_with_multiple_positions(self, performance_tracker, mock_pg_pool):
        """Test returns calculation with multiple positions"""
        pool, conn, cursor = mock_pg_pool
        
        now = datetime.now()
        cursor.fetchall.return_value = [
            {
                'symbol': 'AAPL',
                'entry_price': Decimal('150.00'),
                'entry_date': now - timedelta(days=60),
                'exit_price': Decimal('165.00'),
                'exit_date': now - timedelta(days=30),
                'position_size_percent': Decimal('10.0'),
                'return_percent': Decimal('10.0'),
                'status': 'closed'
            },
            {
                'symbol': 'MSFT',
                'entry_price': Decimal('300.00'),
                'entry_date': now - timedelta(days=30),
                'exit_price': Decimal('270.00'),
                'exit_date': now,
                'position_size_percent': Decimal('15.0'),
                'return_percent': Decimal('-10.0'),
                'status': 'closed'
            }
        ]
        
        metrics = performance_tracker.calculate_returns()
        
        # Total return = (10% * 10%) + (-10% * 15%) = 1% - 1.5% = -0.5%
        assert metrics['total_return_percent'] == Decimal('-0.5')
        assert metrics['win_rate'] == Decimal('50.0')
        assert metrics['loss_rate'] == Decimal('50.0')
    
    def test_calculate_returns_win_loss_metrics(self, performance_tracker, mock_pg_pool):
        """Test win/loss rate calculations"""
        pool, conn, cursor = mock_pg_pool
        
        now = datetime.now()
        cursor.fetchall.return_value = [
            {'symbol': 'WIN1', 'entry_price': Decimal('100'), 'entry_date': now, 'exit_price': Decimal('110'),
             'exit_date': now, 'position_size_percent': Decimal('10'), 'return_percent': Decimal('10'), 'status': 'closed'},
            {'symbol': 'WIN2', 'entry_price': Decimal('100'), 'entry_date': now, 'exit_price': Decimal('120'),
             'exit_date': now, 'position_size_percent': Decimal('10'), 'return_percent': Decimal('20'), 'status': 'closed'},
            {'symbol': 'LOSS1', 'entry_price': Decimal('100'), 'entry_date': now, 'exit_price': Decimal('90'),
             'exit_date': now, 'position_size_percent': Decimal('10'), 'return_percent': Decimal('-10'), 'status': 'closed'},
        ]
        
        metrics = performance_tracker.calculate_returns()
        
        # 2 winners out of 3 = 66.67% win rate
        assert abs(metrics['win_rate'] - Decimal('66.67')) < Decimal('0.01')
        # Average gain = (10 + 20) / 2 = 15%
        assert metrics['avg_gain_per_winner'] == Decimal('15.0')
        # Average loss = -10%
        assert metrics['avg_loss_per_loser'] == Decimal('-10.0')


class TestMaxDrawdown:
    """Test maximum drawdown calculation"""
    
    def test_max_drawdown_with_no_decline(self, performance_tracker):
        """Test max drawdown when portfolio only increases"""
        recommendations = [
            {'return_percent': Decimal('5.0'), 'position_size_percent': Decimal('10.0')},
            {'return_percent': Decimal('10.0'), 'position_size_percent': Decimal('10.0')},
            {'return_percent': Decimal('15.0'), 'position_size_percent': Decimal('10.0')}
        ]
        
        max_dd = performance_tracker._calculate_max_drawdown(recommendations)
        
        assert max_dd == Decimal('0')
    
    def test_max_drawdown_with_decline(self, performance_tracker):
        """Test max drawdown calculation with decline"""
        recommendations = [
            {'return_percent': Decimal('10.0'), 'position_size_percent': Decimal('10.0')},  # +1%
            {'return_percent': Decimal('20.0'), 'position_size_percent': Decimal('10.0')},  # +2%, total +3%
            {'return_percent': Decimal('-30.0'), 'position_size_percent': Decimal('10.0')}, # -3%, total 0%
        ]
        
        max_dd = performance_tracker._calculate_max_drawdown(recommendations)
        
        # Peak at 3%, trough at 0%, drawdown = 3%
        assert max_dd == Decimal('3.0')


class TestCompareToBenchmark:
    """Test S&P 500 benchmark comparison"""
    
    def test_compare_to_benchmark_outperforming(self, performance_tracker, mock_pg_pool):
        """Test comparison when outperforming S&P 500"""
        pool, conn, cursor = mock_pg_pool
        
        now = datetime.now()
        cursor.fetchall.return_value = [
            {
                'symbol': 'AAPL',
                'entry_price': Decimal('100'),
                'entry_date': now - timedelta(days=30),
                'exit_price': Decimal('120'),
                'exit_date': now,
                'position_size_percent': Decimal('100.0'),
                'return_percent': Decimal('20.0'),
                'status': 'closed'
            }
        ]
        
        # Mock the MIN query for warning check
        cursor.fetchone.return_value = (now - timedelta(days=30),)
        
        comparison = performance_tracker.compare_to_benchmark(Decimal('10.0'))
        
        assert comparison['sp500_return_percent'] == Decimal('10.0')
        assert comparison['relative_performance'] == Decimal('10.0')  # 20% - 10%
    
    def test_compare_to_benchmark_underperforming(self, performance_tracker, mock_pg_pool):
        """Test comparison when underperforming S&P 500"""
        pool, conn, cursor = mock_pg_pool
        
        now = datetime.now()
        cursor.fetchall.return_value = [
            {
                'symbol': 'AAPL',
                'entry_price': Decimal('100'),
                'entry_date': now - timedelta(days=30),
                'exit_price': Decimal('105'),
                'exit_date': now,
                'position_size_percent': Decimal('100.0'),
                'return_percent': Decimal('5.0'),
                'status': 'closed'
            }
        ]
        
        cursor.fetchone.return_value = (now - timedelta(days=30),)
        
        comparison = performance_tracker.compare_to_benchmark(Decimal('10.0'))
        
        assert comparison['sp500_return_percent'] == Decimal('10.0')
        assert comparison['relative_performance'] == Decimal('-5.0')  # 5% - 10%
    
    def test_compare_to_benchmark_logs_warning_when_trailing(self, performance_tracker, mock_pg_pool, caplog):
        """Test that warning is logged when trailing by >5% over 90 days"""
        pool, conn, cursor = mock_pg_pool
        
        now = datetime.now()
        cursor.fetchall.return_value = [
            {
                'symbol': 'AAPL',
                'entry_price': Decimal('100'),
                'entry_date': now - timedelta(days=100),
                'exit_price': Decimal('100'),
                'exit_date': now,
                'position_size_percent': Decimal('100.0'),
                'return_percent': Decimal('0.0'),
                'status': 'closed'
            }
        ]
        
        # Mock MIN query to return 100 days ago
        cursor.fetchone.return_value = (now - timedelta(days=100),)
        
        with caplog.at_level('WARNING'):
            comparison = performance_tracker.compare_to_benchmark(Decimal('10.0'))
        
        # Should log warning since trailing by 10% over 100 days
        assert 'trailing S&P 500' in caplog.text


class TestGenerateAttribution:
    """Test performance attribution analysis"""
    
    def test_generate_attribution_groups_by_symbol(self, performance_tracker, mock_pg_pool):
        """Test that attribution groups recommendations by symbol"""
        pool, conn, cursor = mock_pg_pool
        
        now = datetime.now()
        cursor.fetchall.return_value = [
            {
                'symbol': 'AAPL',
                'num_recommendations': 3,
                'avg_return': Decimal('15.0'),
                'contribution': Decimal('4.5'),
                'first_entry': now - timedelta(days=90),
                'last_entry': now - timedelta(days=30)
            },
            {
                'symbol': 'MSFT',
                'num_recommendations': 2,
                'avg_return': Decimal('10.0'),
                'contribution': Decimal('2.0'),
                'first_entry': now - timedelta(days=60),
                'last_entry': now - timedelta(days=10)
            }
        ]
        
        attributions = performance_tracker.generate_attribution()
        
        assert len(attributions) == 2
        assert attributions[0]['symbol'] == 'AAPL'
        assert attributions[0]['num_recommendations'] == 3
        assert attributions[0]['avg_return'] == Decimal('15.0')
        assert attributions[1]['symbol'] == 'MSFT'
    
    def test_generate_attribution_orders_by_contribution(self, performance_tracker, mock_pg_pool):
        """Test that attribution is ordered by contribution (descending)"""
        pool, conn, cursor = mock_pg_pool
        
        # Results should already be ordered by SQL query
        cursor.fetchall.return_value = [
            {'symbol': 'HIGH', 'num_recommendations': 1, 'avg_return': Decimal('50'), 
             'contribution': Decimal('10'), 'first_entry': datetime.now(), 'last_entry': datetime.now()},
            {'symbol': 'LOW', 'num_recommendations': 1, 'avg_return': Decimal('5'), 
             'contribution': Decimal('1'), 'first_entry': datetime.now(), 'last_entry': datetime.now()}
        ]
        
        attributions = performance_tracker.generate_attribution()
        
        # Verify order
        assert attributions[0]['symbol'] == 'HIGH'
        assert attributions[1]['symbol'] == 'LOW'
        assert attributions[0]['contribution'] > attributions[1]['contribution']


class TestClose:
    """Test resource cleanup"""
    
    def test_close_closes_pool(self, performance_tracker, mock_pg_pool):
        """Test that close() closes the connection pool"""
        pool, conn, cursor = mock_pg_pool
        
        performance_tracker.close()
        
        pool.closeall.assert_called_once()
