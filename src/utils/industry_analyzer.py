"""
Industry Analyzer for Investment Scout

Monitors sector trends, competitive dynamics, regulatory changes, and technological
disruptions across industries.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.utils.research_engine import ResearchEngine
from src.models.investment_scout_models import IndustryTrend, NewsArticle, FinancialData


logger = logging.getLogger(__name__)


@dataclass
class SectorAnalysis:
    """Analysis of a sector's trends and outlook"""
    sector: str
    trend_direction: str  # 'bullish', 'bearish', 'neutral'
    momentum_score: float  # -1.0 to 1.0
    key_trends: List[str]
    regulatory_outlook: str
    technological_disruptions: List[str]
    growth_outlook: str
    timestamp: datetime


@dataclass
class CompetitiveAnalysis:
    """Analysis of a company's competitive position"""
    symbol: str
    market_position: str  # 'leader', 'challenger', 'follower', 'niche'
    competitive_advantages: List[str]
    competitive_threats: List[str]
    market_share_trend: str  # 'growing', 'stable', 'declining'
    innovation_score: float  # 0.0 to 1.0
    timestamp: datetime


class IndustryAnalyzer:
    """
    Analyzes industry trends, competitive dynamics, and sector outlook.
    
    Monitors:
    - Sector trends and momentum
    - Competitive positioning
    - Regulatory environment changes
    - Technological disruptions
    - Supply chain dynamics
    - Sector rotation trends
    """
    
    # Sector classifications
    SECTORS = [
        'Technology', 'Healthcare', 'Financial', 'Energy', 'Materials',
        'Industrials', 'Consumer Discretionary', 'Consumer Staples',
        'Utilities', 'Real Estate', 'Communication Services'
    ]
    
    # Trend keywords for sector analysis
    TREND_KEYWORDS = {
        'growth': ['growth', 'expansion', 'increase', 'surge', 'boom'],
        'decline': ['decline', 'decrease', 'fall', 'drop', 'slump'],
        'innovation': ['innovation', 'breakthrough', 'advancement', 'technology'],
        'regulation': ['regulation', 'policy', 'compliance', 'law', 'rule'],
        'disruption': ['disruption', 'disruptive', 'transformation', 'revolution']
    }
    
    def __init__(self, research_engine: ResearchEngine):
        """
        Initialize Industry Analyzer.
        
        Args:
            research_engine: Research engine for data access
        """
        self.research_engine = research_engine
        logger.info("IndustryAnalyzer initialized")
    
    def analyze_sector(self, sector: str, days: int = 30) -> SectorAnalysis:
        """
        Analyze sector trends and outlook.
        
        Args:
            sector: Sector name to analyze
            days: Number of days to look back for analysis
            
        Returns:
            SectorAnalysis with trends and outlook
        """
        logger.info(f"Analyzing sector: {sector}")
        
        # Get industry trends for this sector
        trends = self._get_sector_trends(sector, days)
        
        # Calculate momentum score from trends
        momentum_score = self._calculate_sector_momentum(trends)
        
        # Determine trend direction
        trend_direction = self._classify_trend_direction(momentum_score)
        
        # Extract key trends
        key_trends = self._extract_key_trends(trends)
        
        # Analyze regulatory outlook
        regulatory_outlook = self._analyze_regulatory_outlook(trends)
        
        # Identify technological disruptions
        tech_disruptions = self._identify_tech_disruptions(trends)
        
        # Determine growth outlook
        growth_outlook = self._determine_growth_outlook(momentum_score, key_trends)
        
        analysis = SectorAnalysis(
            sector=sector,
            trend_direction=trend_direction,
            momentum_score=momentum_score,
            key_trends=key_trends,
            regulatory_outlook=regulatory_outlook,
            technological_disruptions=tech_disruptions,
            growth_outlook=growth_outlook,
            timestamp=datetime.now()
        )
        
        logger.info(f"Sector analysis complete: {sector} - {trend_direction}")
        return analysis
    
    def analyze_competitive_position(
        self,
        symbol: str,
        sector: str = None
    ) -> CompetitiveAnalysis:
        """
        Analyze company's competitive position.
        
        Args:
            symbol: Stock symbol to analyze
            sector: Optional sector name (will be inferred if not provided)
            
        Returns:
            CompetitiveAnalysis with competitive positioning
        """
        logger.info(f"Analyzing competitive position: {symbol}")
        
        # Get company context
        context = self.research_engine.get_company_context(symbol)
        
        # Determine market position
        market_position = self._determine_market_position(symbol, context)
        
        # Identify competitive advantages
        advantages = self._identify_competitive_advantages(context)
        
        # Identify competitive threats
        threats = self._identify_competitive_threats(context)
        
        # Analyze market share trend
        market_share_trend = self._analyze_market_share_trend(context)
        
        # Calculate innovation score
        innovation_score = self._calculate_innovation_score(context)
        
        analysis = CompetitiveAnalysis(
            symbol=symbol,
            market_position=market_position,
            competitive_advantages=advantages,
            competitive_threats=threats,
            market_share_trend=market_share_trend,
            innovation_score=innovation_score,
            timestamp=datetime.now()
        )
        
        logger.info(f"Competitive analysis complete: {symbol} - {market_position}")
        return analysis
    
    def detect_disruptions(self, industry: str, days: int = 90) -> List[IndustryTrend]:
        """
        Detect technological or regulatory disruptions in an industry.
        
        Args:
            industry: Industry name to monitor
            days: Number of days to look back
            
        Returns:
            List of IndustryTrend objects representing disruptions
        """
        logger.info(f"Detecting disruptions in: {industry}")
        
        # Get all industry trends
        all_trends = self._get_sector_trends(industry, days)
        
        # Filter for disruption-related trends
        disruptions = []
        for trend in all_trends:
            if self._is_disruption(trend):
                disruptions.append(trend)
        
        logger.info(f"Detected {len(disruptions)} disruptions in {industry}")
        return disruptions
    
    def identify_leaders(self, sector: str, min_score: float = 0.7) -> List[str]:
        """
        Identify emerging leaders in a sector.
        
        This is a placeholder - production would use:
        - Market cap and revenue growth data
        - Innovation metrics
        - Market share analysis
        - Analyst ratings
        
        Args:
            sector: Sector name
            min_score: Minimum leadership score (0.0 to 1.0)
            
        Returns:
            List of stock symbols representing sector leaders
        """
        logger.info(f"Identifying leaders in: {sector}")
        
        # Placeholder implementation
        # In production, would query financial data and calculate leadership scores
        leaders = []
        
        logger.info(f"Identified {len(leaders)} leaders in {sector}")
        return leaders
    
    def _get_sector_trends(self, sector: str, days: int) -> List[IndustryTrend]:
        """Get industry trends for a sector"""
        # This would query the research engine for stored trends
        # Placeholder for now
        trends = []
        return trends
    
    def _calculate_sector_momentum(self, trends: List[IndustryTrend]) -> float:
        """
        Calculate sector momentum score from trends.
        
        Args:
            trends: List of industry trends
            
        Returns:
            Momentum score from -1.0 (bearish) to 1.0 (bullish)
        """
        if not trends:
            return 0.0
        
        # Calculate average impact score
        total_impact = sum(trend.impact_score for trend in trends)
        momentum = total_impact / len(trends)
        
        # Clamp to [-1.0, 1.0]
        return max(-1.0, min(1.0, momentum))
    
    def _classify_trend_direction(self, momentum_score: float) -> str:
        """Classify trend direction based on momentum score"""
        if momentum_score > 0.3:
            return 'bullish'
        elif momentum_score < -0.3:
            return 'bearish'
        else:
            return 'neutral'
    
    def _extract_key_trends(self, trends: List[IndustryTrend]) -> List[str]:
        """Extract key trends from industry trend data"""
        if not trends:
            return []
        
        # Sort by impact score and take top trends
        sorted_trends = sorted(trends, key=lambda t: abs(t.impact_score), reverse=True)
        key_trends = [f"{trend.trend_type}: {trend.description}" for trend in sorted_trends[:5]]
        
        return key_trends
    
    def _analyze_regulatory_outlook(self, trends: List[IndustryTrend]) -> str:
        """
        Analyze regulatory outlook from trends.
        
        Args:
            trends: List of industry trends
            
        Returns:
            Regulatory outlook description
        """
        # Filter for regulation-related trends
        reg_trends = [
            t for t in trends
            if t.trend_type == 'regulatory' or any(keyword in t.description.lower() for keyword in self.TREND_KEYWORDS['regulation'])
        ]
        
        if not reg_trends:
            return "Stable regulatory environment"
        
        # Analyze sentiment of regulatory trends
        avg_impact = sum(t.impact_score for t in reg_trends) / len(reg_trends)
        
        if avg_impact > 0.3:
            return "Favorable regulatory changes expected"
        elif avg_impact < -0.3:
            return "Increased regulatory scrutiny expected"
        else:
            return "Mixed regulatory outlook"
    
    def _identify_tech_disruptions(self, trends: List[IndustryTrend]) -> List[str]:
        """Identify technological disruptions from trends"""
        disruptions = []
        
        for trend in trends:
            # Check for technological trends or disruption keywords
            if trend.trend_type == 'technological':
                disruptions.append(trend.description)
            elif any(keyword in trend.description.lower() for keyword in self.TREND_KEYWORDS['disruption']):
                disruptions.append(trend.description)
            elif any(keyword in trend.description.lower() for keyword in self.TREND_KEYWORDS['innovation']):
                disruptions.append(trend.description)
        
        return disruptions[:3]  # Return top 3
    
    def _determine_growth_outlook(self, momentum_score: float, key_trends: List[str]) -> str:
        """
        Determine growth outlook for sector.
        
        Args:
            momentum_score: Sector momentum score
            key_trends: List of key trends
            
        Returns:
            Growth outlook description
        """
        # Check for growth keywords in trends
        growth_indicators = sum(
            1 for trend in key_trends
            if any(keyword in trend.lower() for keyword in self.TREND_KEYWORDS['growth'])
        )
        
        decline_indicators = sum(
            1 for trend in key_trends
            if any(keyword in trend.lower() for keyword in self.TREND_KEYWORDS['decline'])
        )
        
        if momentum_score > 0.5 or growth_indicators > decline_indicators:
            return "Strong growth expected"
        elif momentum_score < -0.5 or decline_indicators > growth_indicators:
            return "Contraction expected"
        elif momentum_score > 0:
            return "Moderate growth expected"
        else:
            return "Flat to modest growth expected"
    
    def _determine_market_position(self, symbol: str, context: any) -> str:
        """
        Determine company's market position.
        
        This is simplified - production would use:
        - Market cap ranking
        - Revenue and market share data
        - Competitive analysis
        
        Args:
            symbol: Stock symbol
            context: Company context from research engine
            
        Returns:
            Market position: 'leader', 'challenger', 'follower', or 'niche'
        """
        # Placeholder logic based on news sentiment
        if context and hasattr(context, 'news_sentiment'):
            if context.news_sentiment > 0.5:
                return 'leader'
            elif context.news_sentiment > 0:
                return 'challenger'
            elif context.news_sentiment > -0.3:
                return 'follower'
        
        return 'niche'
    
    def _identify_competitive_advantages(self, context: any) -> List[str]:
        """
        Identify competitive advantages from company context.
        
        This is simplified - production would use:
        - Financial metrics analysis
        - Patent and IP data
        - Market position data
        - NLP on company filings
        
        Args:
            context: Company context
            
        Returns:
            List of competitive advantage descriptions
        """
        advantages = []
        
        # Placeholder logic
        if context and hasattr(context, 'news_sentiment') and context.news_sentiment > 0.3:
            advantages.append("Strong brand recognition")
            advantages.append("Positive market sentiment")
        
        return advantages if advantages else ["Market presence"]
    
    def _identify_competitive_threats(self, context: any) -> List[str]:
        """
        Identify competitive threats from company context.
        
        Args:
            context: Company context
            
        Returns:
            List of competitive threat descriptions
        """
        threats = []
        
        # Placeholder logic
        if context and hasattr(context, 'news_sentiment') and context.news_sentiment < -0.3:
            threats.append("Negative market sentiment")
            threats.append("Competitive pressure")
        
        return threats if threats else ["Market competition"]
    
    def _analyze_market_share_trend(self, context: any) -> str:
        """
        Analyze market share trend.
        
        Args:
            context: Company context
            
        Returns:
            Trend: 'growing', 'stable', or 'declining'
        """
        # Placeholder logic based on sentiment
        if context and hasattr(context, 'news_sentiment'):
            if context.news_sentiment > 0.3:
                return 'growing'
            elif context.news_sentiment < -0.3:
                return 'declining'
        
        return 'stable'
    
    def _calculate_innovation_score(self, context: any) -> float:
        """
        Calculate innovation score for company.
        
        This is simplified - production would use:
        - R&D spending as % of revenue
        - Patent filings
        - Product launch frequency
        - Technology adoption metrics
        
        Args:
            context: Company context
            
        Returns:
            Innovation score from 0.0 to 1.0
        """
        # Placeholder logic
        if context and hasattr(context, 'news_sentiment'):
            # Map sentiment to innovation score
            score = (context.news_sentiment + 1.0) / 2.0  # Convert [-1,1] to [0,1]
            return max(0.0, min(1.0, score))
        
        return 0.5  # Default neutral score
    
    def _is_disruption(self, trend: IndustryTrend) -> bool:
        """
        Determine if a trend represents a disruption.
        
        Args:
            trend: IndustryTrend to evaluate
            
        Returns:
            True if trend is a disruption
        """
        # Check for technological trends
        if trend.trend_type == 'technological':
            return True
        
        # Check for disruption keywords in description
        text = trend.description.lower()
        
        is_disruptive = any(
            keyword in text
            for keyword in self.TREND_KEYWORDS['disruption'] + self.TREND_KEYWORDS['innovation']
        )
        
        # Also consider high-impact trends as potential disruptions
        has_high_impact = abs(trend.impact_score) > 0.6
        
        return is_disruptive or has_high_impact
