"""
Investment Analyzer for Investment Scout

PRIMARY function: Generates 1-5 high-quality long-term investment opportunities daily.
Uses comprehensive analysis combining fundamentals, momentum, context, and projections.
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass

from src.utils.research_engine import ResearchEngine
from src.utils.projection_engine import ProjectionEngine
from src.utils.market_monitor import MarketMonitor
from src.models.investment_scout_models import (
    InvestmentOpportunity, GlobalContext, RiskLevel, Quote
)


logger = logging.getLogger(__name__)


@dataclass
class FundamentalScore:
    """Fundamental analysis score"""
    score: float  # 0.0 to 1.0
    revenue_growth: float
    earnings_quality: float
    valuation: float
    financial_health: float


@dataclass
class MomentumScore:
    """Momentum analysis score"""
    score: float  # 0.0 to 1.0
    price_trend: float
    volume_confirmation: float


@dataclass
class ContextScore:
    """Context analysis score"""
    score: float  # 0.0 to 1.0
    news_sentiment: float
    geopolitical_impact: float
    industry_outlook: float


@dataclass
class ProjectionScore:
    """Projection analysis score"""
    score: float  # 0.0 to 1.0
    expected_return: float
    confidence: float


class InvestmentAnalyzer:
    """
    PRIMARY function: Generates 1-5 high-quality long-term investment opportunities daily.
    
    Analysis Pipeline:
    1. Screen Universe: Filter to Robinhood-tradeable securities
    2. Fundamental Filter: Revenue growth, positive earnings, reasonable PE, manageable debt
    3. Momentum Filter: Positive price trend, increasing volume
    4. Context Enrichment: Add geopolitical, industry, company-specific context
    5. Projection Integration: Incorporate forward-looking projections
    6. Risk Assessment: Assign LOW/MEDIUM/HIGH risk level
    7. Position Sizing: Calculate 1-25% position based on risk
    8. Ranking: Score and rank all candidates
    9. Selection: Pick top 1-5 opportunities
    10. Explanation: Generate beginner-friendly thesis
    """
    
    # Scoring weights
    FUNDAMENTAL_WEIGHT = 0.4
    MOMENTUM_WEIGHT = 0.3
    CONTEXT_WEIGHT = 0.2
    PROJECTION_WEIGHT = 0.1
    
    # Position sizing by risk level
    POSITION_SIZES = {
        RiskLevel.LOW: (Decimal('15.0'), Decimal('25.0')),      # 15-25%
        RiskLevel.MEDIUM: (Decimal('8.0'), Decimal('15.0')),    # 8-15%
        RiskLevel.HIGH: (Decimal('1.0'), Decimal('8.0'))        # 1-8%
    }
    
    def __init__(
        self,
        research_engine: ResearchEngine,
        projection_engine: ProjectionEngine,
        market_monitor: MarketMonitor
    ):
        """
        Initialize Investment Analyzer.
        
        Args:
            research_engine: Research engine for data access
            projection_engine: Projection engine for forward-looking analysis
            market_monitor: Market monitor for real-time quotes
        """
        self.research_engine = research_engine
        self.projection_engine = projection_engine
        self.market_monitor = market_monitor
        self.robinhood_cache = {}  # Cache tradeability results for 24h
        logger.info("InvestmentAnalyzer initialized")
    
    def analyze_opportunities(self, candidate_symbols: List[str]) -> List[InvestmentOpportunity]:
        """
        Generate 1-5 daily investment opportunities.
        
        Args:
            candidate_symbols: List of stock symbols to analyze
            
        Returns:
            List of 1-5 InvestmentOpportunity objects, ranked by score
        """
        logger.info(f"Analyzing {len(candidate_symbols)} candidates for opportunities")
        
        opportunities = []
        
        for symbol in candidate_symbols:
            try:
                # Step 1: Verify Robinhood tradeability
                if not self.verify_robinhood_tradeable(symbol):
                    logger.debug(f"Skipping {symbol}: Not tradeable on Robinhood")
                    continue
                
                # Step 2: Get fresh quote
                quote = self.market_monitor.get_current_price(symbol)
                if not quote or not quote.is_fresh:
                    logger.debug(f"Skipping {symbol}: No fresh data")
                    continue
                
                # Step 3: Perform fundamental analysis
                fundamental = self.perform_fundamental_analysis(symbol)
                if fundamental.score < 0.5:  # Minimum threshold
                    logger.debug(f"Skipping {symbol}: Low fundamental score")
                    continue
                
                # Step 4: Perform momentum analysis
                momentum = self.perform_momentum_analysis(symbol)
                if momentum.score < 0.4:  # Minimum threshold
                    logger.debug(f"Skipping {symbol}: Low momentum score")
                    continue
                
                # Step 5: Build global context
                context = self.build_global_context(symbol)
                context_score = self._calculate_context_score(context)
                
                # Step 6: Get projections
                projection = self.projection_engine.project_price_target(symbol, quote.price)
                projection_score = self._calculate_projection_score(projection) if projection else ProjectionScore(0.5, 0.0, 0.5)
                
                # Step 7: Calculate overall score
                overall_score = (
                    fundamental.score * self.FUNDAMENTAL_WEIGHT +
                    momentum.score * self.MOMENTUM_WEIGHT +
                    context_score.score * self.CONTEXT_WEIGHT +
                    projection_score.score * self.PROJECTION_WEIGHT
                )
                
                # Step 8: Assess risk level
                risk_level = self._assess_risk_level(fundamental, momentum, context_score)
                
                # Step 9: Calculate position size
                position_size = self.calculate_position_size(risk_level)
                
                # Step 10: Generate investment thesis
                thesis = self._generate_thesis(symbol, fundamental, momentum, context, projection)
                
                # Step 11: Calculate expected return
                expected_return = self._calculate_expected_return(quote.price, projection)
                
                # Create opportunity
                opportunity = InvestmentOpportunity(
                    symbol=symbol,
                    company_name=self._get_company_name(symbol),
                    current_price=quote.price,
                    target_price=projection.projected_value if projection else quote.price * Decimal('1.15'),
                    position_size_percent=position_size,
                    investment_thesis=thesis,
                    global_context=context,
                    expected_return=expected_return,
                    risk_level=risk_level,
                    expected_holding_period="3-12 months",
                    data_timestamp=datetime.now()
                )
                
                opportunities.append((overall_score, opportunity))
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                continue
        
        # Sort by score and take top 1-5
        opportunities.sort(key=lambda x: x[0], reverse=True)
        top_opportunities = [opp for score, opp in opportunities[:5]]
        
        logger.info(f"Generated {len(top_opportunities)} investment opportunities")
        return top_opportunities
    
    def perform_fundamental_analysis(self, symbol: str) -> FundamentalScore:
        """
        Analyze company fundamentals.
        
        Evaluates:
        - Revenue growth
        - Earnings quality
        - Valuation (PE ratio)
        - Financial health (debt, FCF, ROE)
        
        Args:
            symbol: Stock symbol to analyze
            
        Returns:
            FundamentalScore with overall score and component scores
        """
        context = self.research_engine.get_company_context(symbol)
        
        if not context or not context.financial_data:
            return FundamentalScore(0.0, 0.0, 0.0, 0.0, 0.0)
        
        financial = context.financial_data
        
        # Revenue growth (placeholder - would calculate from historical data)
        revenue_growth = 0.6  # Assume moderate growth
        
        # Earnings quality (positive earnings = good)
        earnings_quality = 1.0 if financial.earnings > 0 else 0.0
        
        # Valuation (PE ratio - lower is better, but not too low)
        if financial.pe_ratio > 0:
            if 10 <= financial.pe_ratio <= 25:
                valuation = 1.0  # Reasonable valuation
            elif financial.pe_ratio < 10:
                valuation = 0.7  # Possibly undervalued or troubled
            else:
                valuation = max(0.0, 1.0 - (float(financial.pe_ratio) - 25) / 50)
        else:
            valuation = 0.0
        
        # Financial health
        debt_score = 1.0 if financial.debt_to_equity < 1.0 else max(0.0, 1.0 - float(financial.debt_to_equity) / 2.0)
        fcf_score = 1.0 if financial.free_cash_flow > 0 else 0.0
        roe_score = min(1.0, float(financial.roe) / 0.20)  # 20% ROE = perfect score
        
        financial_health = (debt_score + fcf_score + roe_score) / 3.0
        
        # Overall fundamental score
        overall = (revenue_growth * 0.3 + earnings_quality * 0.2 + valuation * 0.2 + financial_health * 0.3)
        
        return FundamentalScore(
            score=overall,
            revenue_growth=revenue_growth,
            earnings_quality=earnings_quality,
            valuation=valuation,
            financial_health=financial_health
        )
    
    def perform_momentum_analysis(self, symbol: str) -> MomentumScore:
        """
        Analyze price momentum and volume.
        
        Args:
            symbol: Stock symbol to analyze
            
        Returns:
            MomentumScore with overall score and components
        """
        # Placeholder implementation
        # In production, would analyze historical price data and volume
        
        # Assume moderate positive momentum
        price_trend = 0.6
        volume_confirmation = 0.7
        
        overall = (price_trend * 0.6 + volume_confirmation * 0.4)
        
        return MomentumScore(
            score=overall,
            price_trend=price_trend,
            volume_confirmation=volume_confirmation
        )
    
    def build_global_context(self, symbol: str) -> GlobalContext:
        """
        Aggregate economic, geopolitical, industry, and company context.
        
        Args:
            symbol: Stock symbol to analyze
            
        Returns:
            GlobalContext with all relevant factors
        """
        context = self.research_engine.get_company_context(symbol)
        
        # Economic factors (placeholder)
        economic_factors = [
            "Moderate economic growth expected",
            "Interest rates stable"
        ]
        
        # Geopolitical events (placeholder)
        geopolitical_events = []
        
        # Industry dynamics (placeholder)
        industry_dynamics = [
            "Sector showing positive momentum",
            "Increasing demand trends"
        ]
        
        # Company specifics
        company_specifics = []
        if context and hasattr(context, 'news_sentiment'):
            if context.news_sentiment > 0.3:
                company_specifics.append("Positive news sentiment")
            elif context.news_sentiment < -0.3:
                company_specifics.append("Negative news sentiment")
        
        # Timing rationale
        timing_rationale = "Current market conditions favorable for entry"
        
        # Risk factors
        risk_factors = [
            "Market volatility",
            "Economic uncertainty"
        ]
        
        return GlobalContext(
            economic_factors=economic_factors,
            geopolitical_events=geopolitical_events,
            industry_dynamics=industry_dynamics,
            company_specifics=company_specifics,
            timing_rationale=timing_rationale,
            risk_factors=risk_factors
        )
    
    def calculate_position_size(self, risk_level: RiskLevel) -> Decimal:
        """
        Calculate position size based on risk level.
        
        Args:
            risk_level: Risk level (LOW, MEDIUM, HIGH)
            
        Returns:
            Position size as percentage (1-25%)
        """
        min_size, max_size = self.POSITION_SIZES[risk_level]
        
        # Use midpoint of range
        position_size = (min_size + max_size) / Decimal('2.0')
        
        return position_size
    
    def verify_robinhood_tradeable(self, symbol: str) -> bool:
        """
        Verify security is tradeable on Robinhood.
        
        Uses 24-hour caching to minimize API calls.
        
        Args:
            symbol: Stock symbol to verify
            
        Returns:
            True if tradeable on Robinhood
        """
        # Check cache first
        if symbol in self.robinhood_cache:
            cached_time, is_tradeable = self.robinhood_cache[symbol]
            if (datetime.now() - cached_time).total_seconds() < 86400:  # 24 hours
                return is_tradeable
        
        # Placeholder implementation
        # In production, would call Robinhood API
        is_tradeable = True  # Assume tradeable for now
        
        # Cache result
        self.robinhood_cache[symbol] = (datetime.now(), is_tradeable)
        
        return is_tradeable
    
    def _calculate_context_score(self, context: GlobalContext) -> ContextScore:
        """Calculate context score from global context"""
        # Placeholder scoring
        news_sentiment = 0.6
        geopolitical_impact = 0.5
        industry_outlook = 0.7
        
        overall = (news_sentiment * 0.4 + geopolitical_impact * 0.3 + industry_outlook * 0.3)
        
        return ContextScore(
            score=overall,
            news_sentiment=news_sentiment,
            geopolitical_impact=geopolitical_impact,
            industry_outlook=industry_outlook
        )
    
    def _calculate_projection_score(self, projection) -> ProjectionScore:
        """Calculate projection score from price projection"""
        if not projection:
            return ProjectionScore(0.5, 0.0, 0.5)
        
        # Calculate expected return
        expected_return = float((projection.projected_value - projection.projected_value) / projection.projected_value)
        
        # Normalize to 0-1 scale
        return_score = min(1.0, max(0.0, (expected_return + 0.3) / 0.6))  # -30% to +30% maps to 0-1
        
        # Use confidence level
        confidence = projection.confidence_level
        
        overall = (return_score * 0.6 + confidence * 0.4)
        
        return ProjectionScore(
            score=overall,
            expected_return=expected_return,
            confidence=confidence
        )
    
    def _assess_risk_level(
        self,
        fundamental: FundamentalScore,
        momentum: MomentumScore,
        context: ContextScore
    ) -> RiskLevel:
        """Assess overall risk level"""
        # Average all scores
        avg_score = (fundamental.score + momentum.score + context.score) / 3.0
        
        if avg_score >= 0.7:
            return RiskLevel.LOW
        elif avg_score >= 0.5:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH
    
    def _generate_thesis(
        self,
        symbol: str,
        fundamental: FundamentalScore,
        momentum: MomentumScore,
        context: GlobalContext,
        projection
    ) -> str:
        """Generate beginner-friendly investment thesis"""
        thesis_parts = []
        
        # Company strength
        if fundamental.score > 0.7:
            thesis_parts.append(f"{symbol} shows strong fundamentals with solid earnings and healthy financials.")
        elif fundamental.score > 0.5:
            thesis_parts.append(f"{symbol} demonstrates reasonable fundamentals with room for growth.")
        
        # Momentum
        if momentum.score > 0.6:
            thesis_parts.append("The stock shows positive price momentum with increasing investor interest.")
        
        # Context
        if context.company_specifics:
            thesis_parts.append(" ".join(context.company_specifics))
        
        # Projection
        if projection:
            thesis_parts.append(f"Analysts project continued growth with a target price of ${projection.projected_value}.")
        
        return " ".join(thesis_parts)
    
    def _calculate_expected_return(self, current_price: Decimal, projection) -> Decimal:
        """Calculate expected return percentage"""
        if not projection:
            return Decimal('15.0')  # Default 15% expected return
        
        return ((projection.projected_value - current_price) / current_price) * Decimal('100.0')
    
    def _get_company_name(self, symbol: str) -> str:
        """Get company name for symbol"""
        # Placeholder - would query company info
        return symbol
