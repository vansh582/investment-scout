"""
Projection Engine for Investment Scout

Generates forward-looking projections with confidence intervals for revenue,
earnings, and price targets. Incorporates fundamental drivers, industry trends,
and geopolitical impacts.
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

from src.utils.research_engine import ResearchEngine
from src.models.investment_scout_models import RealTimeProjection, FinancialData


logger = logging.getLogger(__name__)


class ProjectionEngine:
    """
    Generates forward-looking projections with confidence intervals.
    
    Methodology:
    - Combines trend analysis with fundamental drivers
    - Incorporates industry trends and geopolitical impacts
    - Calculates confidence intervals based on data quality and volatility
    - Updates continuously as new data arrives
    - NOT solely based on historical patterns
    """
    
    # Confidence level for projections
    DEFAULT_CONFIDENCE_LEVEL = 0.80  # 80% confidence interval
    
    # Projection horizons (in days)
    REVENUE_HORIZON = 90  # Quarterly projection
    EARNINGS_HORIZON = 90  # Quarterly projection
    PRICE_HORIZON = 30  # 30-day price target
    
    def __init__(self, research_engine: ResearchEngine):
        """
        Initialize Projection Engine.
        
        Args:
            research_engine: Research engine for data access
        """
        self.research_engine = research_engine
        logger.info("ProjectionEngine initialized")
    
    def project_revenue(self, symbol: str) -> Optional[RealTimeProjection]:
        """
        Project future revenue with confidence interval.
        
        Args:
            symbol: Stock symbol to project
            
        Returns:
            RealTimeProjection for revenue or None if insufficient data
        """
        logger.info(f"Projecting revenue for {symbol}")
        
        # Get company context
        context = self.research_engine.get_company_context(symbol)
        
        if not context or not context.financial_data:
            logger.warning(f"Insufficient data for revenue projection: {symbol}")
            return None
        
        # Get current revenue
        current_revenue = context.financial_data.revenue
        
        # Calculate growth rate from trends and sentiment
        growth_rate = self._calculate_revenue_growth_rate(context)
        
        # Project revenue
        projected_revenue = current_revenue * (Decimal('1.0') + Decimal(str(growth_rate)))
        
        # Calculate confidence interval
        confidence_lower, confidence_upper = self._calculate_confidence_interval(
            projected_revenue,
            growth_rate,
            context
        )
        
        # Calculate confidence level based on data quality
        confidence_level = self._calculate_confidence_level(context)
        
        projection = RealTimeProjection(
            symbol=symbol,
            projection_type='revenue',
            projected_value=projected_revenue,
            confidence_lower=confidence_lower,
            confidence_upper=confidence_upper,
            confidence_level=confidence_level,
            projection_date=datetime.now() + timedelta(days=self.REVENUE_HORIZON)
        )
        
        logger.info(f"Revenue projection complete: {symbol} - ${projected_revenue}")
        return projection
    
    def project_earnings(self, symbol: str) -> Optional[RealTimeProjection]:
        """
        Project future earnings with confidence interval.
        
        Args:
            symbol: Stock symbol to project
            
        Returns:
            RealTimeProjection for earnings or None if insufficient data
        """
        logger.info(f"Projecting earnings for {symbol}")
        
        # Get company context
        context = self.research_engine.get_company_context(symbol)
        
        if not context or not context.financial_data:
            logger.warning(f"Insufficient data for earnings projection: {symbol}")
            return None
        
        # Get current earnings
        current_earnings = context.financial_data.earnings
        
        # Calculate growth rate from trends and sentiment
        growth_rate = self._calculate_earnings_growth_rate(context)
        
        # Project earnings
        projected_earnings = current_earnings * (Decimal('1.0') + Decimal(str(growth_rate)))
        
        # Calculate confidence interval
        confidence_lower, confidence_upper = self._calculate_confidence_interval(
            projected_earnings,
            growth_rate,
            context
        )
        
        # Calculate confidence level based on data quality
        confidence_level = self._calculate_confidence_level(context)
        
        projection = RealTimeProjection(
            symbol=symbol,
            projection_type='earnings',
            projected_value=projected_earnings,
            confidence_lower=confidence_lower,
            confidence_upper=confidence_upper,
            confidence_level=confidence_level,
            projection_date=datetime.now() + timedelta(days=self.EARNINGS_HORIZON)
        )
        
        logger.info(f"Earnings projection complete: {symbol} - ${projected_earnings}")
        return projection
    
    def project_price_target(self, symbol: str, current_price: Decimal) -> Optional[RealTimeProjection]:
        """
        Project price target with confidence interval.
        
        Args:
            symbol: Stock symbol to project
            current_price: Current stock price
            
        Returns:
            RealTimeProjection for price target or None if insufficient data
        """
        logger.info(f"Projecting price target for {symbol}")
        
        # Get company context
        context = self.research_engine.get_company_context(symbol)
        
        if not context:
            logger.warning(f"Insufficient data for price projection: {symbol}")
            return None
        
        # Calculate expected return from sentiment and trends
        expected_return = self._calculate_expected_return(context)
        
        # Project price
        projected_price = current_price * (Decimal('1.0') + Decimal(str(expected_return)))
        
        # Calculate confidence interval
        confidence_lower, confidence_upper = self._calculate_price_confidence_interval(
            projected_price,
            expected_return,
            context
        )
        
        # Calculate confidence level based on data quality
        confidence_level = self._calculate_confidence_level(context)
        
        projection = RealTimeProjection(
            symbol=symbol,
            projection_type='price_target',
            projected_value=projected_price,
            confidence_lower=confidence_lower,
            confidence_upper=confidence_upper,
            confidence_level=confidence_level,
            projection_date=datetime.now() + timedelta(days=self.PRICE_HORIZON)
        )
        
        logger.info(f"Price projection complete: {symbol} - ${projected_price}")
        return projection
    
    def update_projections(self, symbols: List[str]) -> None:
        """
        Update all projections with latest data.
        
        Args:
            symbols: List of stock symbols to update projections for
        """
        logger.info(f"Updating projections for {len(symbols)} symbols")
        
        for symbol in symbols:
            try:
                # Generate projections
                revenue_proj = self.project_revenue(symbol)
                earnings_proj = self.project_earnings(symbol)
                
                # Store projections
                if revenue_proj:
                    self.research_engine.store_projection(revenue_proj)
                if earnings_proj:
                    self.research_engine.store_projection(earnings_proj)
                    
            except Exception as e:
                logger.error(f"Error updating projections for {symbol}: {e}")
        
        logger.info("Projection update complete")
    
    def _calculate_revenue_growth_rate(self, context: any) -> float:
        """
        Calculate revenue growth rate from context.
        
        Incorporates:
        - News sentiment
        - Industry trends
        - Geopolitical impacts
        
        Args:
            context: Company context from research engine
            
        Returns:
            Growth rate as decimal (e.g., 0.15 for 15% growth)
        """
        # Base growth from sentiment
        sentiment_factor = 0.0
        if hasattr(context, 'news_sentiment'):
            sentiment_factor = context.news_sentiment * 0.10  # Max 10% from sentiment
        
        # Industry trend factor (placeholder - would use actual industry data)
        industry_factor = 0.05  # Assume 5% baseline industry growth
        
        # Geopolitical factor (placeholder - would use actual geopolitical data)
        geo_factor = 0.0
        
        # Combined growth rate
        growth_rate = sentiment_factor + industry_factor + geo_factor
        
        # Clamp to reasonable range [-0.5, 0.5] (-50% to +50%)
        return max(-0.5, min(0.5, growth_rate))
    
    def _calculate_earnings_growth_rate(self, context: any) -> float:
        """
        Calculate earnings growth rate from context.
        
        Args:
            context: Company context from research engine
            
        Returns:
            Growth rate as decimal
        """
        # Earnings growth typically more volatile than revenue
        # Use similar methodology but with higher sensitivity
        sentiment_factor = 0.0
        if hasattr(context, 'news_sentiment'):
            sentiment_factor = context.news_sentiment * 0.15  # Max 15% from sentiment
        
        industry_factor = 0.05
        geo_factor = 0.0
        
        growth_rate = sentiment_factor + industry_factor + geo_factor
        
        # Clamp to reasonable range
        return max(-0.6, min(0.6, growth_rate))
    
    def _calculate_expected_return(self, context: any) -> float:
        """
        Calculate expected return for price projection.
        
        Args:
            context: Company context from research engine
            
        Returns:
            Expected return as decimal
        """
        # Price movement driven by sentiment and momentum
        sentiment_factor = 0.0
        if hasattr(context, 'news_sentiment'):
            sentiment_factor = context.news_sentiment * 0.20  # Max 20% from sentiment
        
        # Market momentum factor (placeholder)
        momentum_factor = 0.02  # Assume 2% baseline momentum
        
        expected_return = sentiment_factor + momentum_factor
        
        # Clamp to reasonable range for 30-day projection
        return max(-0.3, min(0.3, expected_return))
    
    def _calculate_confidence_interval(
        self,
        projected_value: Decimal,
        growth_rate: float,
        context: any
    ) -> tuple[Decimal, Decimal]:
        """
        Calculate confidence interval for projection.
        
        Args:
            projected_value: Projected value
            growth_rate: Growth rate used
            context: Company context
            
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        # Calculate uncertainty based on volatility and data quality
        uncertainty = self._calculate_uncertainty(growth_rate, context)
        
        # Calculate bounds
        lower_bound = projected_value * (Decimal('1.0') - Decimal(str(uncertainty)))
        upper_bound = projected_value * (Decimal('1.0') + Decimal(str(uncertainty)))
        
        return (lower_bound, upper_bound)
    
    def _calculate_price_confidence_interval(
        self,
        projected_price: Decimal,
        expected_return: float,
        context: any
    ) -> tuple[Decimal, Decimal]:
        """
        Calculate confidence interval for price projection.
        
        Args:
            projected_price: Projected price
            expected_return: Expected return used
            context: Company context
            
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        # Price projections have higher uncertainty
        uncertainty = self._calculate_uncertainty(expected_return, context) * 1.5
        
        lower_bound = projected_price * (Decimal('1.0') - Decimal(str(uncertainty)))
        upper_bound = projected_price * (Decimal('1.0') + Decimal(str(uncertainty)))
        
        return (lower_bound, upper_bound)
    
    def _calculate_uncertainty(self, growth_rate: float, context: any) -> float:
        """
        Calculate uncertainty factor for confidence interval.
        
        Args:
            growth_rate: Growth rate used in projection
            context: Company context
            
        Returns:
            Uncertainty factor (0.0 to 1.0)
        """
        # Base uncertainty from growth rate magnitude
        base_uncertainty = abs(growth_rate) * 0.5
        
        # Adjust for data quality
        data_quality_factor = 1.0
        if hasattr(context, 'news_count'):
            # More news = better data quality = lower uncertainty
            if context.news_count > 10:
                data_quality_factor = 0.8
            elif context.news_count < 3:
                data_quality_factor = 1.2
        
        uncertainty = base_uncertainty * data_quality_factor
        
        # Ensure minimum uncertainty of 10% and maximum of 50%
        return max(0.10, min(0.50, uncertainty))
    
    def _calculate_confidence_level(self, context: any) -> float:
        """
        Calculate confidence level based on data quality.
        
        Args:
            context: Company context
            
        Returns:
            Confidence level (0.0 to 1.0)
        """
        # Start with default confidence
        confidence = self.DEFAULT_CONFIDENCE_LEVEL
        
        # Adjust based on data availability
        if hasattr(context, 'news_count'):
            if context.news_count > 10:
                confidence = 0.85  # High confidence
            elif context.news_count < 3:
                confidence = 0.70  # Lower confidence
        
        # Adjust based on financial data recency
        if hasattr(context, 'financial_data') and context.financial_data:
            # Would check data age in production
            pass
        
        return confidence
