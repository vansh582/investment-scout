"""
Unit tests for IndustryAnalyzer
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass

from src.utils.industry_analyzer import IndustryAnalyzer, SectorAnalysis, CompetitiveAnalysis
from src.models.investment_scout_models import IndustryTrend


def create_industry_trend(description: str, impact_score: float, trend_type: str = "technological", sector: str = "Technology") -> IndustryTrend:
    """Helper to create IndustryTrend with correct fields"""
    return IndustryTrend(
        sector=sector,
        industry=sector,
        trend_type=trend_type,
        description=description,
        impact_score=impact_score,
        affected_companies=[],
        timestamp=datetime.now()
    )


@dataclass
class MockCompanyContext:
    """Mock company context for testing"""
    news_sentiment: float


@pytest.fixture
def mock_research_engine():
    """Create mock research engine"""
    engine = Mock()
    engine.get_company_context = Mock()
    return engine


@pytest.fixture
def analyzer(mock_research_engine):
    """Create IndustryAnalyzer instance"""
    return IndustryAnalyzer(mock_research_engine)


class TestSectorAnalysis:
    """Test sector analysis functionality"""
    
    def test_analyze_sector_bullish(self, analyzer, monkeypatch):
        """Test sector analysis with bullish trends"""
        # Mock trends with positive impact
        mock_trends = [
            create_industry_trend("AI Innovation Surge - Rapid AI adoption", 0.7),
            create_industry_trend("Cloud Growth Acceleration - Cloud services expanding", 0.6)
        ]
        
        monkeypatch.setattr(analyzer, '_get_sector_trends', lambda s, d: mock_trends)
        
        analysis = analyzer.analyze_sector("Technology")
        
        assert isinstance(analysis, SectorAnalysis)
        assert analysis.sector == "Technology"
        assert analysis.trend_direction == "bullish"
        assert analysis.momentum_score > 0.3
        assert len(analysis.key_trends) > 0
    
    def test_analyze_sector_bearish(self, analyzer, monkeypatch):
        """Test sector analysis with bearish trends"""
        mock_trends = [
            create_industry_trend("Sector Decline - Market contraction", -0.6, sector="Energy"),
            create_industry_trend("Regulatory Pressure - New restrictions", -0.5, trend_type="regulatory", sector="Energy")
        ]
        
        monkeypatch.setattr(analyzer, '_get_sector_trends', lambda s, d: mock_trends)
        
        analysis = analyzer.analyze_sector("Energy")
        
        assert analysis.trend_direction == "bearish"
        assert analysis.momentum_score < -0.3
    
    def test_analyze_sector_neutral(self, analyzer, monkeypatch):
        """Test sector analysis with neutral trends"""
        mock_trends = [
            create_industry_trend("Stable Market - No major changes", 0.1, sector="Utilities")
        ]
        
        monkeypatch.setattr(analyzer, '_get_sector_trends', lambda s, d: mock_trends)
        
        analysis = analyzer.analyze_sector("Utilities")
        
        assert analysis.trend_direction == "neutral"
        assert -0.3 <= analysis.momentum_score <= 0.3
    
    def test_analyze_sector_no_trends(self, analyzer, monkeypatch):
        """Test sector analysis with no trends"""
        monkeypatch.setattr(analyzer, '_get_sector_trends', lambda s, d: [])
        
        analysis = analyzer.analyze_sector("Healthcare")
        
        assert analysis.momentum_score == 0.0
        assert analysis.trend_direction == "neutral"
        assert analysis.key_trends == []


class TestMomentumCalculation:
    """Test momentum score calculation"""
    
    def test_calculate_positive_momentum(self, analyzer):
        """Test calculation of positive momentum"""
        trends = [
            create_industry_trend("Growth trend", 0.8),
            create_industry_trend("Expansion trend", 0.6)
        ]
        
        momentum = analyzer._calculate_sector_momentum(trends)
        
        assert momentum == 0.7  # (0.8 + 0.6) / 2
    
    def test_calculate_negative_momentum(self, analyzer):
        """Test calculation of negative momentum"""
        trends = [
            create_industry_trend("Decline trend", -0.7, sector="Energy"),
            create_industry_trend("Contraction trend", -0.5, sector="Energy")
        ]
        
        momentum = analyzer._calculate_sector_momentum(trends)
        
        assert momentum == -0.6  # (-0.7 + -0.5) / 2
    
    def test_momentum_clamped_to_range(self, analyzer):
        """Test momentum is clamped to [-1.0, 1.0]"""
        trends = [
            create_industry_trend("Extreme trend", 1.5)  # Out of range
        ]
        
        momentum = analyzer._calculate_sector_momentum(trends)
        
        assert momentum == 1.0  # Clamped to max
    
    def test_momentum_empty_trends(self, analyzer):
        """Test momentum calculation with empty trends"""
        momentum = analyzer._calculate_sector_momentum([])
        assert momentum == 0.0


class TestTrendClassification:
    """Test trend direction classification"""
    
    def test_classify_bullish(self, analyzer):
        """Test classification of bullish trend"""
        direction = analyzer._classify_trend_direction(0.5)
        assert direction == "bullish"
    
    def test_classify_bearish(self, analyzer):
        """Test classification of bearish trend"""
        direction = analyzer._classify_trend_direction(-0.5)
        assert direction == "bearish"
    
    def test_classify_neutral_positive(self, analyzer):
        """Test classification of neutral (slightly positive)"""
        direction = analyzer._classify_trend_direction(0.2)
        assert direction == "neutral"
    
    def test_classify_neutral_negative(self, analyzer):
        """Test classification of neutral (slightly negative)"""
        direction = analyzer._classify_trend_direction(-0.2)
        assert direction == "neutral"
    
    def test_classify_boundary_bullish(self, analyzer):
        """Test classification at bullish boundary"""
        direction = analyzer._classify_trend_direction(0.31)
        assert direction == "bullish"
    
    def test_classify_boundary_bearish(self, analyzer):
        """Test classification at bearish boundary"""
        direction = analyzer._classify_trend_direction(-0.31)
        assert direction == "bearish"


class TestCompetitiveAnalysis:
    """Test competitive position analysis"""
    
    def test_analyze_competitive_position_leader(self, analyzer, mock_research_engine):
        """Test competitive analysis for market leader"""
        mock_context = MockCompanyContext(news_sentiment=0.7)
        mock_research_engine.get_company_context.return_value = mock_context
        
        analysis = analyzer.analyze_competitive_position("AAPL")
        
        assert isinstance(analysis, CompetitiveAnalysis)
        assert analysis.symbol == "AAPL"
        assert analysis.market_position == "leader"
        assert analysis.market_share_trend == "growing"
        assert analysis.innovation_score > 0.5
    
    def test_analyze_competitive_position_challenger(self, analyzer, mock_research_engine):
        """Test competitive analysis for challenger"""
        mock_context = MockCompanyContext(news_sentiment=0.3)
        mock_research_engine.get_company_context.return_value = mock_context
        
        analysis = analyzer.analyze_competitive_position("MSFT")
        
        assert analysis.market_position == "challenger"
        assert analysis.market_share_trend == "stable"  # 0.3 is not > 0.3, so stable
    
    def test_analyze_competitive_position_follower(self, analyzer, mock_research_engine):
        """Test competitive analysis for follower"""
        mock_context = MockCompanyContext(news_sentiment=-0.1)
        mock_research_engine.get_company_context.return_value = mock_context
        
        analysis = analyzer.analyze_competitive_position("XYZ")
        
        assert analysis.market_position == "follower"
        assert analysis.market_share_trend == "stable"
    
    def test_analyze_competitive_position_declining(self, analyzer, mock_research_engine):
        """Test competitive analysis for declining company"""
        mock_context = MockCompanyContext(news_sentiment=-0.6)
        mock_research_engine.get_company_context.return_value = mock_context
        
        analysis = analyzer.analyze_competitive_position("ABC")
        
        assert analysis.market_share_trend == "declining"
        assert len(analysis.competitive_threats) > 0


class TestRegulatoryAnalysis:
    """Test regulatory outlook analysis"""
    
    def test_regulatory_outlook_favorable(self, analyzer):
        """Test favorable regulatory outlook"""
        trends = [
            create_industry_trend("Favorable Policy Changes - New regulations support growth", 0.5, trend_type="regulatory")
        ]
        
        outlook = analyzer._analyze_regulatory_outlook(trends)
        
        assert "favorable" in outlook.lower()
    
    def test_regulatory_outlook_unfavorable(self, analyzer):
        """Test unfavorable regulatory outlook"""
        trends = [
            create_industry_trend("Increased Regulation - New compliance requirements", -0.5, trend_type="regulatory", sector="Financial")
        ]
        
        outlook = analyzer._analyze_regulatory_outlook(trends)
        
        assert "scrutiny" in outlook.lower() or "increased" in outlook.lower()
    
    def test_regulatory_outlook_stable(self, analyzer):
        """Test stable regulatory outlook"""
        trends = [
            create_industry_trend("Market Growth - No regulatory changes", 0.5)
        ]
        
        outlook = analyzer._analyze_regulatory_outlook(trends)
        
        assert "stable" in outlook.lower()


class TestDisruptionDetection:
    """Test disruption detection"""
    
    def test_detect_disruptions(self, analyzer, monkeypatch):
        """Test detection of industry disruptions"""
        mock_trends = [
            create_industry_trend("AI Disruption in Healthcare - AI transforming diagnostics", 0.8, trend_type="technological", sector="Healthcare"),
            create_industry_trend("Blockchain Revolution - Decentralized finance growth", 0.7, trend_type="technological", sector="Financial"),
            create_industry_trend("Stable Market Conditions - No major changes", 0.1, trend_type="competitive", sector="Utilities")  # Not technological
        ]
        
        monkeypatch.setattr(analyzer, '_get_sector_trends', lambda i, d: mock_trends)
        
        disruptions = analyzer.detect_disruptions("Technology")
        
        # Should detect 2 disruptions (AI and Blockchain, not the stable one)
        assert len(disruptions) == 2
        assert all(isinstance(d, IndustryTrend) for d in disruptions)
    
    def test_is_disruption_by_keyword(self, analyzer):
        """Test disruption detection by keyword"""
        trend = create_industry_trend("Disruptive Technology breakthrough", 0.3)
        
        assert analyzer._is_disruption(trend) is True
    
    def test_is_disruption_by_impact(self, analyzer):
        """Test disruption detection by high impact"""
        trend = create_industry_trend("Major Market Shift", 0.8)
        
        assert analyzer._is_disruption(trend) is True
    
    def test_is_not_disruption(self, analyzer):
        """Test non-disruption trend"""
        trend = create_industry_trend("Stable Growth pattern", 0.2, trend_type="competitive")  # Not technological
        
        assert analyzer._is_disruption(trend) is False


class TestGrowthOutlook:
    """Test growth outlook determination"""
    
    def test_strong_growth_outlook(self, analyzer):
        """Test strong growth outlook"""
        key_trends = ["Revenue Growth", "Market Expansion", "Increase in Demand"]
        outlook = analyzer._determine_growth_outlook(0.6, key_trends)
        
        assert "strong growth" in outlook.lower()
    
    def test_contraction_outlook(self, analyzer):
        """Test contraction outlook"""
        key_trends = ["Market Decline", "Revenue Drop", "Falling Demand"]
        outlook = analyzer._determine_growth_outlook(-0.6, key_trends)
        
        assert "contraction" in outlook.lower()
    
    def test_moderate_growth_outlook(self, analyzer):
        """Test moderate growth outlook"""
        key_trends = ["technological: Steady Progress", "competitive: Gradual Expansion"]
        outlook = analyzer._determine_growth_outlook(0.2, key_trends)
        
        # With positive momentum (0.2 > 0), expect moderate/modest growth
        assert "growth" in outlook.lower()
    
    def test_flat_outlook(self, analyzer):
        """Test flat growth outlook"""
        key_trends = ["Stable Market", "Consistent Performance"]
        outlook = analyzer._determine_growth_outlook(-0.1, key_trends)
        
        assert "flat" in outlook.lower() or "modest" in outlook.lower()


class TestInnovationScore:
    """Test innovation score calculation"""
    
    def test_high_innovation_score(self, analyzer):
        """Test high innovation score"""
        context = MockCompanyContext(news_sentiment=0.8)
        score = analyzer._calculate_innovation_score(context)
        
        assert 0.8 <= score <= 1.0
    
    def test_low_innovation_score(self, analyzer):
        """Test low innovation score"""
        context = MockCompanyContext(news_sentiment=-0.6)
        score = analyzer._calculate_innovation_score(context)
        
        assert 0.0 <= score <= 0.3
    
    def test_neutral_innovation_score(self, analyzer):
        """Test neutral innovation score"""
        context = MockCompanyContext(news_sentiment=0.0)
        score = analyzer._calculate_innovation_score(context)
        
        assert 0.4 <= score <= 0.6
    
    def test_innovation_score_no_context(self, analyzer):
        """Test innovation score with no context"""
        score = analyzer._calculate_innovation_score(None)
        assert score == 0.5  # Default neutral


class TestLeaderIdentification:
    """Test sector leader identification"""
    
    def test_identify_leaders(self, analyzer):
        """Test identifying sector leaders"""
        leaders = analyzer.identify_leaders("Technology")
        
        # Placeholder returns empty list
        assert isinstance(leaders, list)
    
    def test_identify_leaders_with_min_score(self, analyzer):
        """Test identifying leaders with minimum score"""
        leaders = analyzer.identify_leaders("Healthcare", min_score=0.8)
        
        assert isinstance(leaders, list)


class TestKeyTrendExtraction:
    """Test key trend extraction"""
    
    def test_extract_key_trends(self, analyzer):
        """Test extracting key trends"""
        trends = [
            create_industry_trend(f"Trend description {i}", 0.9 - (i * 0.1))
            for i in range(10)
        ]
        
        key_trends = analyzer._extract_key_trends(trends)
        
        # Should return top 5 trends
        assert len(key_trends) == 5
        assert "Trend description 0" in key_trends[0]  # Highest impact
    
    def test_extract_key_trends_empty(self, analyzer):
        """Test extracting key trends from empty list"""
        key_trends = analyzer._extract_key_trends([])
        assert key_trends == []
