"""
Trading Analyzer - SECONDARY Function

Generates real-time trading alerts for short-term buy/sell opportunities.
Limited to max 5 alerts per day due to capital constraints.

Requirements: 12.1-12.10
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, List
from dataclasses import dataclass

from src.models.investment_scout_models import (
    Quote, TradingAlert, SignalType, RiskLevel
)
from src.utils.data_manager_scout import DataManager
from src.utils.research_engine import ResearchEngine

logger = logging.getLogger(__name__)


@dataclass
class TradingLevels:
    """Entry, target, and stop loss levels for a trade"""
    entry_price: Decimal
    target_price: Decimal
    stop_loss: Decimal
    expected_return: Decimal
    risk_reward_ratio: Decimal


class TradingAnalyzer:
    """
    SECONDARY function: Generate instant trading alerts for short-term opportunities.
    
    Max 5 alerts per day due to capital constraints.
    All analysis uses only fresh data (<30s latency).
    Alerts generated within 10 seconds of opportunity detection.
    """
    
    def __init__(
        self,
        data_manager: DataManager,
        research_engine: ResearchEngine,
        max_alerts_per_day: int = 5
    ):
        """
        Initialize Trading Analyzer.
        
        Args:
            data_manager: Data manager for caching and persistence
            research_engine: Research engine for context data
            max_alerts_per_day: Maximum alerts per day (default 5, requirement says 2-3 but design says max 5)
        """
        self.data_manager = data_manager
        self.research_engine = research_engine
        self.max_alerts_per_day = max_alerts_per_day
        
        logger.info(
            "TradingAnalyzer initialized",
            extra={
                "component": "TradingAnalyzer",
                "max_alerts_per_day": max_alerts_per_day
            }
        )
    
    def analyze_real_time(self, quote: Quote) -> Optional[TradingAlert]:
        """
        Analyze a fresh quote for trading opportunities.
        
        Requirements: 12.1, 12.8
        
        Args:
            quote: Fresh market quote (<30s latency)
            
        Returns:
            TradingAlert if opportunity detected, None otherwise
        """
        # Validate data freshness (Requirement 12.8)
        if not quote.is_fresh:
            logger.warning(
                "Stale data rejected in trading analysis",
                extra={
                    "component": "TradingAnalyzer",
                    "event": "stale_data_rejected",
                    "symbol": quote.symbol,
                    "latency_seconds": quote.latency.total_seconds()
                }
            )
            return None
        
        # Check alert limit (Requirement 12.10)
        if not self.check_alert_limit():
            logger.info(
                "Alert limit reached for today",
                extra={
                    "component": "TradingAnalyzer",
                    "event": "alert_limit_reached",
                    "max_alerts": self.max_alerts_per_day
                }
            )
            return None
        
        # Try buy signal first
        buy_alert = self.detect_buy_signal(quote)
        if buy_alert:
            return buy_alert
        
        # Try sell signal
        sell_alert = self.detect_sell_signal(quote)
        if sell_alert:
            return sell_alert
        
        return None
    
    def detect_buy_signal(self, quote: Quote) -> Optional[TradingAlert]:
        """
        Detect buy opportunities: breakouts, oversold bounces, positive catalysts.
        
        Requirements: 12.3
        
        Args:
            quote: Fresh market quote
            
        Returns:
            TradingAlert for buy signal, None if no opportunity
        """
        symbol = quote.symbol
        
        # Get historical data for technical analysis
        historical_quotes = self.data_manager.get_historical_quotes(symbol, days=30)
        if len(historical_quotes) < 20:
            return None  # Not enough data
        
        # Get recent prices
        recent_prices = [Decimal(str(q['price'])) for q in historical_quotes[-20:]]
        current_price = quote.price
        
        # Calculate technical indicators
        sma_20 = sum(recent_prices) / len(recent_prices)
        price_change_pct = ((current_price - recent_prices[0]) / recent_prices[0]) * 100
        
        # Calculate volatility (simple standard deviation)
        mean_price = sum(recent_prices) / len(recent_prices)
        variance = sum((p - mean_price) ** 2 for p in recent_prices) / len(recent_prices)
        std_dev = variance ** Decimal('0.5')
        
        # Detect breakout: price crosses above 20-day SMA with volume
        breakout_detected = (
            current_price > sma_20 and
            recent_prices[-1] <= sma_20 and  # Was below yesterday
            quote.volume > 0  # Volume confirmation
        )
        
        # Detect oversold bounce: price dropped >5% but showing recovery
        oversold_bounce = (
            price_change_pct < -5 and
            current_price > recent_prices[-1]  # Bouncing up
        )
        
        # Check for positive news catalyst
        company_context = self.research_engine.get_company_context(symbol, days=1)
        positive_catalyst = (
            company_context.news_sentiment and
            company_context.news_sentiment > 0.3  # Positive sentiment
        )
        
        # Generate buy signal if any condition met
        if breakout_detected or oversold_bounce or positive_catalyst:
            # Calculate entry/exit levels
            levels = self.calculate_entry_exit(
                symbol=symbol,
                current_price=current_price,
                signal_type=SignalType.BUY,
                volatility=std_dev
            )
            
            # Build rationale
            rationale_parts = []
            if breakout_detected:
                rationale_parts.append("Breakout above 20-day moving average with volume confirmation")
            if oversold_bounce:
                rationale_parts.append(f"Oversold bounce after {abs(price_change_pct):.1f}% decline")
            if positive_catalyst:
                rationale_parts.append(f"Positive news sentiment ({company_context.news_sentiment:.2f})")
            
            rationale = ". ".join(rationale_parts) + "."
            
            # Get company name
            company_name = self._get_company_name(symbol)
            
            # Calculate position size based on volatility
            position_size = self._calculate_trading_position_size(std_dev, current_price)
            
            alert = TradingAlert(
                symbol=symbol,
                company_name=company_name,
                signal_type=SignalType.BUY,
                current_price=current_price,
                entry_price=levels.entry_price,
                target_price=levels.target_price,
                stop_loss=levels.stop_loss,
                position_size_percent=position_size,
                rationale=rationale,
                expected_holding_period="minutes to days",
                data_timestamp=quote.received_timestamp
            )
            
            logger.info(
                "Buy signal detected",
                extra={
                    "component": "TradingAnalyzer",
                    "event": "buy_signal_detected",
                    "symbol": symbol,
                    "price": float(current_price),
                    "target": float(levels.target_price),
                    "stop_loss": float(levels.stop_loss)
                }
            )
            
            return alert
        
        return None
    
    def detect_sell_signal(self, quote: Quote) -> Optional[TradingAlert]:
        """
        Detect sell opportunities: breakdowns, overbought reversals, negative news.
        
        Requirements: 12.3
        
        Args:
            quote: Fresh market quote
            
        Returns:
            TradingAlert for sell signal, None if no opportunity
        """
        symbol = quote.symbol
        
        # Get historical data
        historical_quotes = self.data_manager.get_historical_quotes(symbol, days=30)
        if len(historical_quotes) < 20:
            return None
        
        # Get recent prices
        recent_prices = [Decimal(str(q['price'])) for q in historical_quotes[-20:]]
        current_price = quote.price
        
        # Calculate technical indicators
        sma_20 = sum(recent_prices) / len(recent_prices)
        price_change_pct = ((current_price - recent_prices[0]) / recent_prices[0]) * 100
        
        # Calculate volatility
        mean_price = sum(recent_prices) / len(recent_prices)
        variance = sum((p - mean_price) ** 2 for p in recent_prices) / len(recent_prices)
        std_dev = variance ** Decimal('0.5')
        
        # Detect breakdown: price crosses below 20-day SMA
        breakdown_detected = (
            current_price < sma_20 and
            recent_prices[-1] >= sma_20 and  # Was above yesterday
            quote.volume > 0
        )
        
        # Detect overbought reversal: price up >10% but showing weakness
        overbought_reversal = (
            price_change_pct > 10 and
            current_price < recent_prices[-1]  # Starting to decline
        )
        
        # Check for negative news
        company_context = self.research_engine.get_company_context(symbol, days=1)
        negative_news = (
            company_context.news_sentiment and
            company_context.news_sentiment < -0.3  # Negative sentiment
        )
        
        # Generate sell signal if any condition met
        if breakdown_detected or overbought_reversal or negative_news:
            # Calculate entry/exit levels
            levels = self.calculate_entry_exit(
                symbol=symbol,
                current_price=current_price,
                signal_type=SignalType.SELL,
                volatility=std_dev
            )
            
            # Build rationale
            rationale_parts = []
            if breakdown_detected:
                rationale_parts.append("Breakdown below 20-day moving average")
            if overbought_reversal:
                rationale_parts.append(f"Overbought reversal after {price_change_pct:.1f}% rally")
            if negative_news:
                rationale_parts.append(f"Negative news sentiment ({company_context.news_sentiment:.2f})")
            
            rationale = ". ".join(rationale_parts) + "."
            
            # Get company name
            company_name = self._get_company_name(symbol)
            
            # Calculate position size
            position_size = self._calculate_trading_position_size(std_dev, current_price)
            
            alert = TradingAlert(
                symbol=symbol,
                company_name=company_name,
                signal_type=SignalType.SELL,
                current_price=current_price,
                entry_price=levels.entry_price,
                target_price=levels.target_price,
                stop_loss=levels.stop_loss,
                position_size_percent=position_size,
                rationale=rationale,
                expected_holding_period="minutes to days",
                data_timestamp=quote.received_timestamp
            )
            
            logger.info(
                "Sell signal detected",
                extra={
                    "component": "TradingAnalyzer",
                    "event": "sell_signal_detected",
                    "symbol": symbol,
                    "price": float(current_price),
                    "target": float(levels.target_price),
                    "stop_loss": float(levels.stop_loss)
                }
            )
            
            return alert
        
        return None
    
    def calculate_entry_exit(
        self,
        symbol: str,
        current_price: Decimal,
        signal_type: SignalType,
        volatility: Decimal
    ) -> TradingLevels:
        """
        Calculate entry price, target price, and stop loss levels.
        
        Requirements: 12.9
        
        Args:
            symbol: Stock symbol
            current_price: Current market price
            signal_type: BUY or SELL
            volatility: Price volatility (standard deviation)
            
        Returns:
            TradingLevels with entry, target, stop loss
        """
        # Entry price is current price (immediate execution)
        entry_price = current_price
        
        # Calculate risk/reward based on volatility
        # Use 2x volatility for target, 1x volatility for stop loss (2:1 reward:risk)
        risk_amount = volatility
        reward_amount = volatility * 2
        
        if signal_type == SignalType.BUY:
            # For buy: target above, stop below
            target_price = entry_price + reward_amount
            stop_loss = entry_price - risk_amount
        else:
            # For sell (short): target below, stop above
            target_price = entry_price - reward_amount
            stop_loss = entry_price + risk_amount
        
        # Ensure stop loss is not negative
        if stop_loss < Decimal('0.01'):
            stop_loss = Decimal('0.01')
        
        # Calculate expected return and risk/reward ratio
        expected_return = ((target_price - entry_price) / entry_price) * 100
        risk_reward_ratio = Decimal('2.0')  # 2:1 by design
        
        return TradingLevels(
            entry_price=entry_price,
            target_price=target_price,
            stop_loss=stop_loss,
            expected_return=expected_return,
            risk_reward_ratio=risk_reward_ratio
        )
    
    def check_alert_limit(self) -> bool:
        """
        Check if we can send more alerts today.
        
        Requirements: 12.10
        
        Returns:
            True if under limit, False if limit reached
        """
        # Get today's date
        today = datetime.now().date()
        cache_key = f"trading_alerts:{today}"
        
        # Try to get count from Redis
        try:
            count_str = self.data_manager.redis_client.get(cache_key)
            if count_str is None:
                # No alerts today yet
                return True
            
            count = int(count_str)
            return count < self.max_alerts_per_day
        except Exception as e:
            logger.error(
                "Error checking alert limit",
                extra={
                    "component": "TradingAnalyzer",
                    "event": "alert_limit_check_error",
                    "error": str(e)
                }
            )
            # On error, allow the alert (fail open)
            return True
    
    def increment_alert_count(self) -> None:
        """
        Increment today's alert count.
        
        Should be called after successfully sending an alert.
        """
        today = datetime.now().date()
        cache_key = f"trading_alerts:{today}"
        
        try:
            # Increment counter with 24-hour expiry
            self.data_manager.redis_client.incr(cache_key)
            self.data_manager.redis_client.expire(cache_key, 86400)  # 24 hours
            
            logger.info(
                "Alert count incremented",
                extra={
                    "component": "TradingAnalyzer",
                    "event": "alert_count_incremented",
                    "date": str(today)
                }
            )
        except Exception as e:
            logger.error(
                "Error incrementing alert count",
                extra={
                    "component": "TradingAnalyzer",
                    "event": "alert_count_increment_error",
                    "error": str(e)
                }
            )
    
    def _calculate_trading_position_size(
        self,
        volatility: Decimal,
        current_price: Decimal
    ) -> Decimal:
        """
        Calculate position size for trading based on volatility.
        
        Higher volatility = smaller position size for risk management.
        
        Args:
            volatility: Price standard deviation
            current_price: Current price
            
        Returns:
            Position size as percentage (1-25%)
        """
        # Calculate volatility as percentage of price
        volatility_pct = (volatility / current_price) * 100
        
        # Position sizing based on volatility
        # Low volatility (<2%): 15-25% position
        # Medium volatility (2-5%): 8-15% position
        # High volatility (>5%): 1-8% position
        
        if volatility_pct < 2:
            position_size = Decimal('20.0')  # Mid-range for low volatility
        elif volatility_pct < 5:
            position_size = Decimal('12.0')  # Mid-range for medium volatility
        else:
            position_size = Decimal('5.0')  # Mid-range for high volatility
        
        # Ensure within bounds
        position_size = max(Decimal('1.0'), min(Decimal('25.0'), position_size))
        
        return position_size
    
    def _get_company_name(self, symbol: str) -> str:
        """
        Get company name for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Company name or symbol if not found
        """
        try:
            # Try to get from financial data
            financial_data = self.data_manager.get_financial_data(symbol)
            if financial_data and 'company_name' in financial_data:
                return financial_data['company_name']
        except Exception as e:
            logger.warning(
                "Error getting company name",
                extra={
                    "component": "TradingAnalyzer",
                    "symbol": symbol,
                    "error": str(e)
                }
            )
        
        # Fallback to symbol
        return symbol
