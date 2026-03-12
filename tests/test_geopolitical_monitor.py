"""
Unit tests for GeopoliticalMonitor
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from src.utils.geopolitical_monitor import GeopoliticalMonitor
from src.models.investment_scout_models import GeopoliticalEvent, NewsArticle


@pytest.fixture
def mock_research_engine():
    """Create mock research engine"""
    engine = Mock()
    engine.store_geopolitical_event = Mock()
    engine.get_geopolitical_events = Mock(return_value=[])
    return engine


@pytest.fixture
def monitor(mock_research_engine):
    """Create GeopoliticalMonitor instance"""
    return GeopoliticalMonitor(mock_research_engine)


class TestEventCollection:
    """Test event collection from news articles"""
    
    def test_collect_events_from_articles(self, monitor):
        """Test collecting geopolitical events from news articles"""
        articles = [
            NewsArticle(
                title="US Election Results Impact Markets",
                summary="Presidential election results show major policy shifts ahead",
                source="Reuters",
                url="https://example.com/1",
                published_at=datetime.now(),
                sentiment=0.5
            ),
            NewsArticle(
                title="China Announces New Trade Policy",
                summary="New tariffs on technology imports announced",
                source="Bloomberg",
                url="https://example.com/2",
                published_at=datetime.now(),
                sentiment=-0.3
            ),
            NewsArticle(
                title="Tech Company Earnings Beat Expectations",
                summary="Strong quarterly results from major tech firm",
                source="CNBC",
                url="https://example.com/3",
                published_at=datetime.now(),
                sentiment=0.8
            )
        ]
        
        events = monitor.collect_events(articles)
        
        # Should identify 2 geopolitical events (election and trade)
        assert len(events) == 2
        assert all(isinstance(e, GeopoliticalEvent) for e in events)
    
    def test_collect_events_empty_list(self, monitor):
        """Test collecting events from empty article list"""
        events = monitor.collect_events([])
        assert events == []
    
    def test_collect_events_no_geopolitical_content(self, monitor):
        """Test collecting events when no geopolitical content exists"""
        articles = [
            NewsArticle(
                title="Company Reports Strong Earnings",
                summary="Quarterly profits exceed analyst expectations",
                source="CNBC",
                url="https://example.com/1",
                published_at=datetime.now(),
                sentiment=0.7
            )
        ]
        
        events = monitor.collect_events(articles)
        assert len(events) == 0


class TestEventClassification:
    """Test event type classification"""
    
    def test_classify_election_event(self, monitor):
        """Test classification of election events"""
        text = "presidential election results show major changes"
        event_type = monitor._classify_event_type(text)
        assert event_type == 'election'
    
    def test_classify_policy_event(self, monitor):
        """Test classification of policy events"""
        text = "new regulation on financial sector announced"
        event_type = monitor._classify_event_type(text)
        assert event_type == 'policy'
    
    def test_classify_conflict_event(self, monitor):
        """Test classification of conflict events"""
        text = "military conflict escalates in region"
        event_type = monitor._classify_event_type(text)
        assert event_type == 'conflict'
    
    def test_classify_trade_event(self, monitor):
        """Test classification of trade events"""
        text = "new tariff agreement between countries"
        event_type = monitor._classify_event_type(text)
        assert event_type == 'trade'
    
    def test_classify_sanction_event(self, monitor):
        """Test classification of sanction events"""
        text = "economic sanctions imposed on country"
        event_type = monitor._classify_event_type(text)
        assert event_type == 'sanction'
    
    def test_classify_non_geopolitical(self, monitor):
        """Test classification returns None for non-geopolitical text"""
        text = "company announces new product launch"
        event_type = monitor._classify_event_type(text)
        assert event_type is None


class TestRegionExtraction:
    """Test region extraction from text"""
    
    def test_extract_us_region(self, monitor):
        """Test extraction of US region"""
        text = "united states announces new policy"
        regions = monitor._extract_regions(text)
        assert 'US' in regions
    
    def test_extract_china_region(self, monitor):
        """Test extraction of China region"""
        text = "china implements new trade restrictions"
        regions = monitor._extract_regions(text)
        assert 'China' in regions
    
    def test_extract_europe_region(self, monitor):
        """Test extraction of Europe region"""
        text = "european union passes new regulation"
        regions = monitor._extract_regions(text)
        assert 'Europe' in regions
    
    def test_extract_multiple_regions(self, monitor):
        """Test extraction of multiple regions"""
        text = "trade agreement between united states and china"
        regions = monitor._extract_regions(text)
        assert 'US' in regions
        assert 'China' in regions
    
    def test_extract_global_default(self, monitor):
        """Test default to Global when no specific region found"""
        text = "international markets react to news"
        regions = monitor._extract_regions(text)
        assert regions == ['Global']


class TestImpactCalculation:
    """Test impact score calculation"""
    
    def test_calculate_conflict_impact(self, monitor):
        """Test impact calculation for conflict events"""
        impact = monitor._calculate_impact_score(-0.5, 'conflict')
        # Conflict has 1.5x multiplier: -0.5 * 1.5 = -0.75
        assert impact == -0.75
    
    def test_calculate_sanction_impact(self, monitor):
        """Test impact calculation for sanction events"""
        impact = monitor._calculate_impact_score(-0.6, 'sanction')
        # Sanction has 1.3x multiplier: -0.6 * 1.3 = -0.78
        assert impact == -0.78
    
    def test_calculate_trade_impact(self, monitor):
        """Test impact calculation for trade events"""
        impact = monitor._calculate_impact_score(0.5, 'trade')
        # Trade has 1.2x multiplier: 0.5 * 1.2 = 0.6
        assert impact == 0.6
    
    def test_calculate_election_impact(self, monitor):
        """Test impact calculation for election events"""
        impact = monitor._calculate_impact_score(0.5, 'election')
        # Election has 0.8x multiplier: 0.5 * 0.8 = 0.4
        assert impact == 0.4
    
    def test_impact_clamped_to_range(self, monitor):
        """Test impact score is clamped to [-1.0, 1.0]"""
        # Test upper bound
        impact_high = monitor._calculate_impact_score(0.9, 'conflict')
        assert impact_high == 1.0  # 0.9 * 1.5 = 1.35, clamped to 1.0
        
        # Test lower bound
        impact_low = monitor._calculate_impact_score(-0.9, 'conflict')
        assert impact_low == -1.0  # -0.9 * 1.5 = -1.35, clamped to -1.0
    
    def test_impact_with_none_sentiment(self, monitor):
        """Test impact calculation with None sentiment"""
        impact = monitor._calculate_impact_score(None, 'policy')
        assert impact == 0.0


class TestImpactAnalysis:
    """Test impact analysis functionality"""
    
    def test_analyze_high_severity_event(self, monitor):
        """Test analysis of high severity event"""
        event = GeopoliticalEvent(
            event_type='conflict',
            title='Major Conflict Escalates',
            description='Military tensions rise significantly',
            affected_regions=['Middle East'],
            affected_sectors=['Defense', 'Energy'],
            impact_score=-0.8,
            event_date=datetime.now()
        )
        
        analysis = monitor.analyze_impact(event)
        
        assert analysis['event_type'] == 'conflict'
        assert analysis['impact_score'] == -0.8
        assert analysis['severity'] == 'High'
        assert 'Middle East' in analysis['affected_regions']
        assert len(analysis['market_implications']) > 0
    
    def test_analyze_medium_severity_event(self, monitor):
        """Test analysis of medium severity event"""
        event = GeopoliticalEvent(
            event_type='trade',
            title='New Trade Agreement',
            description='Countries sign trade deal',
            affected_regions=['US', 'China'],
            affected_sectors=['Technology', 'Manufacturing'],
            impact_score=0.5,
            event_date=datetime.now()
        )
        
        analysis = monitor.analyze_impact(event)
        assert analysis['severity'] == 'Medium'
    
    def test_analyze_low_severity_event(self, monitor):
        """Test analysis of low severity event"""
        event = GeopoliticalEvent(
            event_type='election',
            title='Local Election Results',
            description='Minor political changes',
            affected_regions=['Europe'],
            affected_sectors=['Financial'],
            impact_score=0.2,
            event_date=datetime.now()
        )
        
        analysis = monitor.analyze_impact(event)
        assert analysis['severity'] == 'Low'
    
    def test_implications_for_conflict(self, monitor):
        """Test market implications for conflict events"""
        event = GeopoliticalEvent(
            event_type='conflict',
            title='Conflict Event',
            description='Test',
            affected_regions=['Global'],
            affected_sectors=['Defense'],
            impact_score=-0.7,
            event_date=datetime.now()
        )
        
        analysis = monitor.analyze_impact(event)
        implications = analysis['market_implications']
        
        assert any('defense' in imp.lower() for imp in implications)
        assert any('safe-haven' in imp.lower() for imp in implications)
        assert any('negative' in imp.lower() for imp in implications)
    
    def test_implications_for_positive_event(self, monitor):
        """Test market implications for positive events"""
        event = GeopoliticalEvent(
            event_type='trade',
            title='Positive Trade Deal',
            description='Test',
            affected_regions=['Global'],
            affected_sectors=['Technology'],
            impact_score=0.6,
            event_date=datetime.now()
        )
        
        analysis = monitor.analyze_impact(event)
        implications = analysis['market_implications']
        
        assert any('positive' in imp.lower() for imp in implications)


class TestEventStorage:
    """Test event storage functionality"""
    
    def test_store_event(self, monitor, mock_research_engine):
        """Test storing geopolitical event"""
        event = GeopoliticalEvent(
            event_type='policy',
            title='New Policy Announced',
            description='Government announces new regulation',
            affected_regions=['US'],
            affected_sectors=['Financial'],
            impact_score=0.3,
            event_date=datetime.now()
        )
        
        monitor.store_event(event)
        
        mock_research_engine.store_geopolitical_event.assert_called_once_with(event)
    
    def test_get_recent_events(self, monitor, mock_research_engine):
        """Test retrieving recent events"""
        mock_events = [
            GeopoliticalEvent(
                event_type='trade',
                title='Event 1',
                description='Test',
                affected_regions=['US'],
                affected_sectors=['Technology'],
                impact_score=0.5,
                event_date=datetime.now()
            )
        ]
        mock_research_engine.get_geopolitical_events.return_value = mock_events
        
        events = monitor.get_recent_events(days=7)
        
        assert len(events) == 1
        mock_research_engine.get_geopolitical_events.assert_called_once()
    
    def test_get_recent_events_with_filters(self, monitor, mock_research_engine):
        """Test retrieving events with filters"""
        mock_events = [
            GeopoliticalEvent(
                event_type='conflict',
                title='High Impact Event',
                description='Test',
                affected_regions=['Middle East'],
                affected_sectors=['Energy'],
                impact_score=0.8,
                event_date=datetime.now()
            ),
            GeopoliticalEvent(
                event_type='election',
                title='Low Impact Event',
                description='Test',
                affected_regions=['Europe'],
                affected_sectors=['Financial'],
                impact_score=0.2,
                event_date=datetime.now()
            )
        ]
        mock_research_engine.get_geopolitical_events.return_value = mock_events
        
        # Filter by minimum impact
        events = monitor.get_recent_events(days=30, min_impact=0.5)
        
        assert len(events) == 1
        assert events[0].impact_score == 0.8


class TestEventExtraction:
    """Test full event extraction from articles"""
    
    def test_extract_complete_event(self, monitor):
        """Test extracting complete event from article"""
        article = NewsArticle(
            title="United States Election Results Show Policy Shift",
            summary="Presidential election brings major changes to economic policy in America",
            source="Reuters",
            url="https://example.com/1",
            published_at=datetime.now(),
            sentiment=0.4
        )
        
        event = monitor._extract_event_from_article(article)
        
        assert event is not None
        assert event.event_type == 'election'
        assert event.title == article.title
        assert event.description == article.summary
        assert 'US' in event.affected_regions
        assert len(event.affected_sectors) > 0
        assert -1.0 <= event.impact_score <= 1.0
    
    def test_extract_event_with_negative_sentiment(self, monitor):
        """Test extracting event with negative sentiment"""
        article = NewsArticle(
            title="Conflict Escalates in Region",
            summary="Military tensions rise as conflict intensifies",
            source="BBC",
            url="https://example.com/1",
            published_at=datetime.now(),
            sentiment=-0.7
        )
        
        event = monitor._extract_event_from_article(article)
        
        assert event is not None
        assert event.event_type == 'conflict'
        assert event.impact_score < 0
    
    def test_extract_event_returns_none_for_non_geopolitical(self, monitor):
        """Test extraction returns None for non-geopolitical articles"""
        article = NewsArticle(
            title="Company Launches New Product",
            summary="Tech company unveils latest innovation",
            source="TechCrunch",
            url="https://example.com/1",
            published_at=datetime.now(),
            sentiment=0.6
        )
        
        event = monitor._extract_event_from_article(article)
        assert event is None
