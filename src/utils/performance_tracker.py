"""
Performance Tracker for Investment Scout

Monitors portfolio performance and compares against S&P 500 benchmark.
Tracks recommendations, calculates returns, and generates performance metrics.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from src.models.investment_scout_models import InvestmentOpportunity, RiskLevel


logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Tracks portfolio performance and compares against S&P 500 benchmark.
    
    Monitors all recommendations from entry to exit, calculates performance metrics,
    and provides attribution analysis.
    """
    
    def __init__(self, postgres_url: str, min_pool_size: int = 1, max_pool_size: int = 5):
        """
        Initialize Performance Tracker with PostgreSQL connection.
        
        Args:
            postgres_url: PostgreSQL connection URL
            min_pool_size: Minimum connection pool size
            max_pool_size: Maximum connection pool size
        """
        self.pg_pool = SimpleConnectionPool(min_pool_size, max_pool_size, postgres_url)
        self._ensure_schema()
        logger.info("PerformanceTracker initialized successfully")
    
    def _ensure_schema(self):
        """Create performance tracking tables if they don't exist"""
        conn = self.pg_pool.getconn()
        try:
            with conn.cursor() as cur:
                # Recommendations tracking table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS recommendations (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        recommendation_type VARCHAR(20) NOT NULL,
                        entry_price NUMERIC(20, 6) NOT NULL,
                        entry_date TIMESTAMP NOT NULL,
                        position_size_percent NUMERIC(5, 2) NOT NULL,
                        target_price NUMERIC(20, 6),
                        stop_loss NUMERIC(20, 6),
                        exit_price NUMERIC(20, 6),
                        exit_date TIMESTAMP,
                        status VARCHAR(20) NOT NULL DEFAULT 'open',
                        return_percent NUMERIC(10, 4),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Performance snapshots table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS performance_snapshots (
                        id SERIAL PRIMARY KEY,
                        snapshot_date DATE NOT NULL UNIQUE,
                        portfolio_value NUMERIC(20, 2),
                        total_return_percent NUMERIC(10, 4),
                        sp500_return_percent NUMERIC(10, 4),
                        relative_performance NUMERIC(10, 4),
                        sharpe_ratio NUMERIC(10, 4),
                        max_drawdown NUMERIC(10, 4),
                        win_rate NUMERIC(5, 2),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                cur.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_symbol ON recommendations(symbol)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_status ON recommendations(status)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_entry_date ON recommendations(entry_date DESC)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_performance_snapshots_date ON performance_snapshots(snapshot_date DESC)")
                
                conn.commit()
                logger.info("Performance tracking schema ensured")
        finally:
            self.pg_pool.putconn(conn)
    
    def track_recommendation(self, opportunity: InvestmentOpportunity) -> None:
        """
        Start tracking a new investment recommendation.
        
        Args:
            opportunity: InvestmentOpportunity to track
        """
        conn = self.pg_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO recommendations 
                    (symbol, recommendation_type, entry_price, entry_date, position_size_percent, 
                     target_price, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    opportunity.symbol,
                    'investment',
                    opportunity.current_price,
                    opportunity.data_timestamp,
                    opportunity.position_size_percent,
                    opportunity.target_price,
                    'open'
                ))
                conn.commit()
                logger.info(f"Started tracking recommendation for {opportunity.symbol} at ${opportunity.current_price}")
        except psycopg2.Error as e:
            logger.error(f"Error tracking recommendation: {e}")
            conn.rollback()
        finally:
            self.pg_pool.putconn(conn)
    
    def update_positions(self, current_prices: Dict[str, Decimal]) -> None:
        """
        Update all open position values with current prices.
        
        Args:
            current_prices: Dictionary mapping symbols to current prices
        """
        conn = self.pg_pool.getconn()
        try:
            with conn.cursor() as cur:
                # Get all open positions
                cur.execute("""
                    SELECT id, symbol, entry_price, position_size_percent
                    FROM recommendations
                    WHERE status = 'open'
                """)
                open_positions = cur.fetchall()
                
                for position_id, symbol, entry_price, position_size in open_positions:
                    if symbol in current_prices:
                        current_price = current_prices[symbol]
                        return_percent = ((current_price - entry_price) / entry_price) * 100
                        
                        cur.execute("""
                            UPDATE recommendations
                            SET return_percent = %s
                            WHERE id = %s
                        """, (return_percent, position_id))
                
                conn.commit()
                logger.debug(f"Updated {len(open_positions)} open positions")
        except psycopg2.Error as e:
            logger.error(f"Error updating positions: {e}")
            conn.rollback()
        finally:
            self.pg_pool.putconn(conn)
    
    def calculate_returns(self) -> Dict[str, Decimal]:
        """
        Calculate portfolio performance metrics.
        
        Returns:
            Dictionary containing performance metrics:
            - total_return_percent: Total portfolio return
            - annualized_return: Annualized return
            - sharpe_ratio: Risk-adjusted return
            - max_drawdown: Maximum peak-to-trough decline
            - win_rate: Percentage of profitable trades
            - avg_gain_per_winner: Average gain on winning trades
            - loss_rate: Percentage of losing trades
            - avg_loss_per_loser: Average loss on losing trades
        """
        conn = self.pg_pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get all recommendations with returns
                cur.execute("""
                    SELECT 
                        symbol,
                        entry_price,
                        entry_date,
                        exit_price,
                        exit_date,
                        position_size_percent,
                        return_percent,
                        status
                    FROM recommendations
                    ORDER BY entry_date
                """)
                recommendations = cur.fetchall()
                
                if not recommendations:
                    return self._empty_metrics()
                
                # Calculate total return (weighted by position size)
                total_return = Decimal('0')
                returns_list = []
                
                for rec in recommendations:
                    if rec['return_percent'] is not None:
                        weighted_return = (rec['return_percent'] * rec['position_size_percent']) / 100
                        total_return += weighted_return
                        returns_list.append(float(rec['return_percent']))
                
                # Calculate win/loss metrics
                closed_positions = [r for r in recommendations if r['status'] == 'closed']
                if closed_positions:
                    winners = [r for r in closed_positions if r['return_percent'] and r['return_percent'] > 0]
                    losers = [r for r in closed_positions if r['return_percent'] and r['return_percent'] <= 0]
                    
                    win_rate = Decimal(len(winners)) / Decimal(len(closed_positions)) * 100
                    loss_rate = Decimal(len(losers)) / Decimal(len(closed_positions)) * 100
                    
                    avg_gain = Decimal(sum(r['return_percent'] for r in winners)) / Decimal(len(winners)) if winners else Decimal('0')
                    avg_loss = Decimal(sum(r['return_percent'] for r in losers)) / Decimal(len(losers)) if losers else Decimal('0')
                else:
                    win_rate = Decimal('0')
                    loss_rate = Decimal('0')
                    avg_gain = Decimal('0')
                    avg_loss = Decimal('0')
                
                # Calculate annualized return
                if recommendations:
                    first_date = recommendations[0]['entry_date']
                    days_elapsed = (datetime.now() - first_date).days
                    if days_elapsed > 0:
                        years = Decimal(days_elapsed) / Decimal('365')
                        annualized_return = ((Decimal('1') + total_return / Decimal('100')) ** (Decimal('1') / years) - Decimal('1')) * Decimal('100')
                    else:
                        annualized_return = Decimal('0')
                else:
                    annualized_return = Decimal('0')
                
                # Calculate Sharpe ratio (simplified: return / volatility)
                if len(returns_list) > 1:
                    import statistics
                    mean_return = statistics.mean(returns_list)
                    std_dev = statistics.stdev(returns_list)
                    sharpe_ratio = Decimal(mean_return / std_dev) if std_dev > 0 else Decimal('0')
                else:
                    sharpe_ratio = Decimal('0')
                
                # Calculate max drawdown
                max_drawdown = self._calculate_max_drawdown(recommendations)
                
                return {
                    'total_return_percent': total_return,
                    'annualized_return': annualized_return,
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown,
                    'win_rate': win_rate,
                    'avg_gain_per_winner': avg_gain,
                    'loss_rate': loss_rate,
                    'avg_loss_per_loser': avg_loss
                }
        finally:
            self.pg_pool.putconn(conn)
    
    def _calculate_max_drawdown(self, recommendations: List[Dict]) -> Decimal:
        """
        Calculate maximum drawdown from peak to trough.
        
        Args:
            recommendations: List of recommendation records
            
        Returns:
            Maximum drawdown as percentage
        """
        if not recommendations:
            return Decimal('0')
        
        # Build cumulative return series
        cumulative_returns = []
        cumulative = Decimal('0')
        
        for rec in recommendations:
            if rec['return_percent'] is not None:
                weighted_return = (rec['return_percent'] * rec['position_size_percent']) / 100
                cumulative += weighted_return
                cumulative_returns.append(cumulative)
        
        if not cumulative_returns:
            return Decimal('0')
        
        # Calculate max drawdown
        peak = cumulative_returns[0]
        max_dd = Decimal('0')
        
        for value in cumulative_returns:
            if value > peak:
                peak = value
            drawdown = peak - value
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd
    
    def _empty_metrics(self) -> Dict[str, Decimal]:
        """Return empty metrics when no data available"""
        return {
            'total_return_percent': Decimal('0'),
            'annualized_return': Decimal('0'),
            'sharpe_ratio': Decimal('0'),
            'max_drawdown': Decimal('0'),
            'win_rate': Decimal('0'),
            'avg_gain_per_winner': Decimal('0'),
            'loss_rate': Decimal('0'),
            'avg_loss_per_loser': Decimal('0')
        }
    
    def compare_to_benchmark(self, sp500_return: Decimal) -> Dict[str, Decimal]:
        """
        Compare portfolio performance to S&P 500 benchmark.
        
        Args:
            sp500_return: S&P 500 return percentage over same period
            
        Returns:
            Dictionary containing:
            - sp500_return_percent: S&P 500 return
            - relative_performance: Portfolio return - S&P 500 return
        """
        metrics = self.calculate_returns()
        portfolio_return = metrics['total_return_percent']
        relative_performance = portfolio_return - sp500_return
        
        # Log warning if trailing by >5% over 90 days
        conn = self.pg_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT MIN(entry_date) as first_entry
                    FROM recommendations
                """)
                result = cur.fetchone()
                
                if result and result[0]:
                    days_elapsed = (datetime.now() - result[0]).days
                    if days_elapsed >= 90 and relative_performance < Decimal('-5.0'):
                        logger.warning(
                            f"Portfolio trailing S&P 500 by {abs(relative_performance):.2f}% "
                            f"over {days_elapsed} days"
                        )
        finally:
            self.pg_pool.putconn(conn)
        
        return {
            'sp500_return_percent': sp500_return,
            'relative_performance': relative_performance
        }
    
    def generate_attribution(self) -> List[Dict[str, any]]:
        """
        Analyze which opportunity types contribute most to returns.
        
        Returns:
            List of dictionaries with attribution analysis by symbol
        """
        conn = self.pg_pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        symbol,
                        COUNT(*) as num_recommendations,
                        AVG(return_percent) as avg_return,
                        SUM(return_percent * position_size_percent / 100) as contribution,
                        MIN(entry_date) as first_entry,
                        MAX(entry_date) as last_entry
                    FROM recommendations
                    WHERE return_percent IS NOT NULL
                    GROUP BY symbol
                    ORDER BY contribution DESC
                """)
                
                attributions = []
                for row in cur.fetchall():
                    attributions.append({
                        'symbol': row['symbol'],
                        'num_recommendations': row['num_recommendations'],
                        'avg_return': row['avg_return'],
                        'contribution': row['contribution'],
                        'first_entry': row['first_entry'],
                        'last_entry': row['last_entry']
                    })
                
                return attributions
        finally:
            self.pg_pool.putconn(conn)
    
    def close(self):
        """Close all connections"""
        self.pg_pool.closeall()
        logger.info("PerformanceTracker connections closed")
