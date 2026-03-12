"""
Geopolitical Monitor for Investment Scout

Tracks and analyzes global political events, policy changes, elections, conflicts,
trade agreements, and sanctions that impact markets.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from src.utils.research_engine import ResearchEngine
from src.models.investment_scout_models import GeopoliticalEvent, NewsArticle


logger = logging.getLogger(__name__)


class GeopoliticalMonitor:
    """
    Monitors and analyzes geopolitical events worldwide.
    
    Tracks:
    - Elections and political transitions
    - Policy changes (tax, regulation, trade)
    - International conflicts and tensions
    - Trade agreements and tariffs
    - Sanctions and embargoes
    """
    
    # Event type classifications
    EVENT_TYPES = {
        'election': ['election', 'vote', 'referendum', 'ballot'],
        'policy': ['policy', 'regulation', 'law', 'bill', 'legislation'],
        'conflict': ['war', 'conflict', 'military', 'attack', 'tension'],
        'trade': ['trade', 'tariff', 'export', 'import', 'agreement'],
        'sanction': ['sanction', 'embargo', 'ban', 'restriction']
    }
    
    # Sector impact mapping
    SECTOR_IMPACTS = {
        'election': ['Financial', 'Healthcare', 'Energy'],
        'policy': ['All'],  # Policies can affect all sectors
        'conflict': ['Defense', 'Energy', 'Materials'],
        'trade': ['Technology', 'Manufacturing', 'Agriculture'],
        'sanction': ['Energy', 'Financial', 'Technology']
    }
    
    def __init__(self, research_engine: ResearchEngine):
        """
        Initialize Geopolitical Monitor.
        
        Args:
            research_engine: Research engine for data storage
        """
        self.research_engine = research_engine
        logger.info("GeopoliticalMonitor initialized")
    
    def collect_events(self, news_articles: List[NewsArticle]) -> List[GeopoliticalEvent]:
        """
        Collect geopolitical events from news articles.
        
        Args:
            news_articles: List of news articles to analyze
            
        Returns:
            List of identified GeopoliticalEvent objects
        """
        events = []
        
        for article in news_articles:
            event = self._extract_event_from_article(article)
            if event:
                events.append(event)
        
        logger.info(f"Collected {len(events)} geopolitical events from {len(news_articles)} articles")
        return events
    
    def _extract_event_from_article(self, article: NewsArticle) -> Optional[GeopoliticalEvent]:
        """
        Extract geopolitical event from a news article.
        
        Args:
            article: News article to analyze
            
        Returns:
            GeopoliticalEvent if article contains relevant event, None otherwise
        """
        # Combine title and summary for analysis
        text = f"{article.title} {article.summary}".lower()
        
        # Classify event type
        event_type = self._classify_event_type(text)
        if not event_type:
            return None  # Not a geopolitical event
        
        # Extract affected regions (simplified - would use NER in production)
        affected_regions = self._extract_regions(text)
        
        # Determine affected sectors
        affected_sectors = self.SECTOR_IMPACTS.get(event_type, [])
        
        # Calculate impact score based on sentiment and event type
        impact_score = self._calculate_impact_score(article.sentiment, event_type)
        
        event = GeopoliticalEvent(
            event_type=event_type,
            title=article.title,
            description=article.summary,
            affected_regions=affected_regions,
            affected_sectors=affected_sectors,
            impact_score=impact_score,
            event_date=article.published_at
        )
        
        return event
    
    def _classify_event_type(self, text: str) -> Optional[str]:
        """
        Classify event type based on keywords.
        
        Args:
            text: Text to analyze
            
        Returns:
            Event type or None if not geopolitical
        """
        for event_type, keywords in self.EVENT_TYPES.items():
            if any(keyword in text for keyword in keywords):
                return event_type
        
        return None
    
    def _extract_regions(self, text: str) -> List[str]:
        """
        Extract affected regions from text.
        
        This is a simplified implementation. Production would use:
        - Named Entity Recognition (NER)
        - Geopolitical entity databases
        - Location extraction libraries
        
        Args:
            text: Text to analyze
            
        Returns:
            List of region names
        """
        # Common regions and countries
        regions = {
            'US': ['united states', 'america', 'u.s.', 'usa'],
            'China': ['china', 'chinese', 'beijing'],
            'Europe': ['europe', 'european', 'eu'],
            'Russia': ['russia', 'russian', 'moscow'],
            'Middle East': ['middle east', 'iran', 'saudi', 'israel'],
            'Asia': ['asia', 'asian'],
            'Global': ['global', 'worldwide', 'international']
        }
        
        found_regions = []
        for region, keywords in regions.items():
            if any(keyword in text for keyword in keywords):
                found_regions.append(region)
        
        return found_regions if found_regions else ['Global']
    
    def _calculate_impact_score(self, sentiment: Optional[float], event_type: str) -> float:
        """
        Calculate market impact score for an event.
        
        Args:
            sentiment: Article sentiment (-1.0 to 1.0)
            event_type: Type of geopolitical event
            
        Returns:
            Impact score from -1.0 (highly negative) to 1.0 (highly positive)
        """
        # Base impact on sentiment
        base_impact = sentiment if sentiment is not None else 0.0
        
        # Adjust based on event type severity
        severity_multipliers = {
            'conflict': 1.5,  # Conflicts have amplified impact
            'sanction': 1.3,
            'policy': 1.0,
            'trade': 1.2,
            'election': 0.8  # Elections have moderate impact
        }
        
        multiplier = severity_multipliers.get(event_type, 1.0)
        impact = base_impact * multiplier
        
        # Clamp to [-1.0, 1.0]
        return max(-1.0, min(1.0, impact))
    
    def analyze_impact(self, event: GeopoliticalEvent) -> Dict[str, any]:
        """
        Analyze the market impact of a geopolitical event.
        
        Args:
            event: GeopoliticalEvent to analyze
            
        Returns:
            Dictionary with impact analysis
        """
        analysis = {
            'event_type': event.event_type,
            'impact_score': event.impact_score,
            'severity': self._classify_severity(event.impact_score),
            'affected_regions': event.affected_regions,
            'affected_sectors': event.affected_sectors,
            'market_implications': self._generate_implications(event)
        }
        
        logger.debug(f"Analyzed impact for event: {event.title[:50]}")
        return analysis
    
    def _classify_severity(self, impact_score: float) -> str:
        """Classify event severity based on impact score"""
        abs_score = abs(impact_score)
        
        if abs_score >= 0.7:
            return 'High'
        elif abs_score >= 0.4:
            return 'Medium'
        else:
            return 'Low'
    
    def _generate_implications(self, event: GeopoliticalEvent) -> List[str]:
        """
        Generate market implications for an event.
        
        Args:
            event: GeopoliticalEvent to analyze
            
        Returns:
            List of market implication strings
        """
        implications = []
        
        # Type-specific implications
        if event.event_type == 'conflict':
            implications.append("Increased volatility in defense and energy sectors")
            implications.append("Flight to safe-haven assets (gold, bonds)")
        elif event.event_type == 'trade':
            implications.append("Impact on international supply chains")
            implications.append("Currency fluctuations in affected regions")
        elif event.event_type == 'policy':
            implications.append("Regulatory changes affecting specific sectors")
            implications.append("Potential shifts in market dynamics")
        elif event.event_type == 'sanction':
            implications.append("Restricted market access for affected companies")
            implications.append("Supply chain disruptions")
        elif event.event_type == 'election':
            implications.append("Policy uncertainty during transition period")
            implications.append("Sector-specific impacts based on platform")
        
        # Impact direction
        if event.impact_score > 0.3:
            implications.append("Overall positive market sentiment expected")
        elif event.impact_score < -0.3:
            implications.append("Overall negative market sentiment expected")
        
        return implications
    
    def get_affected_securities(self, event: GeopoliticalEvent) -> List[str]:
        """
        Identify securities affected by a geopolitical event.
        
        This is a placeholder - production would use:
        - Sector-to-symbol mapping database
        - Company exposure analysis
        - Supply chain impact modeling
        
        Args:
            event: GeopoliticalEvent to analyze
            
        Returns:
            List of affected stock symbols
        """
        # Placeholder implementation
        # In production, would query database for companies in affected sectors/regions
        affected_symbols = []
        
        logger.debug(f"Identified {len(affected_symbols)} affected securities for event")
        return affected_symbols
    
    def store_event(self, event: GeopoliticalEvent) -> None:
        """
        Store geopolitical event in research engine.
        
        Args:
            event: GeopoliticalEvent to store
        """
        self.research_engine.store_geopolitical_event(event)
        logger.debug(f"Stored geopolitical event: {event.title[:50]}")
    
    def get_recent_events(
        self,
        days: int = 30,
        event_types: List[str] = None,
        regions: List[str] = None,
        min_impact: float = None
    ) -> List[GeopoliticalEvent]:
        """
        Retrieve recent geopolitical events with filtering.
        
        Args:
            days: Number of days to look back
            event_types: Filter by event types
            regions: Filter by affected regions
            min_impact: Minimum absolute impact score
            
        Returns:
            List of filtered GeopoliticalEvent objects
        """
        # This would query the database with filters
        # Placeholder for now
        events = self.research_engine.get_geopolitical_events(
            days=days,
            event_types=event_types,
            regions=regions
        )
        
        # Apply impact filter if specified
        if min_impact is not None:
            events = [e for e in events if abs(e.impact_score) >= min_impact]
        
        logger.debug(f"Retrieved {len(events)} recent geopolitical events")
        return events
