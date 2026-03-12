"""
Unit tests for InvestmentAnalyzer
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass

from src.utils.investment_analyzer import (
    InvestmentAnalyzer, FundamentalScore, MomentumScore, ContextScore, ProjectionScore
)
from src.models.investment_scout_models import (
    InvestmentOpportunity, GlobalContext, RiskLevel, Quote, RealTimeProjection, FinancialData
)


@dataclass
class MockFinancialData:
    """Mock financial data"""
    revenue: Decimal
    earnings: Decimal
    pe_ratio: Decimal
    debt_to_equity: Decimal
    free_cash_flow: Decimal
    roe: Decimal


@dataclass
class MockCompanyContext:
    """Mock company context"""
    financial_data: MockFinancialData
    news_sentiment: float = 0.5


@pytest.fixture
def mock_research_engine():
    """Create mock research engine"""
    engine = Mock()
    engine.get_company_context = Mock()
    return engine


@pytest.fixture
def mock_projection_engine():
    """Create mock projection engine"""
    engine = Mock()
    engine.project_price_target = Mock()
    return engine


@pytest.fixture
def mock_market_monitor():
    """Create mock market monitor"""
    monitor = Mock()
    monitor.get_current_price = Mock()
    return monitor


@pytest.fixture
def analyzer(mock_research_engine, mock_projection_engine, mock_market_monitor):
    """Create InvestmentAnalyzer instance"""
    return InvestmentAnalyzer(
        mock_research_engine,
        mock_projection_engine,
        mock_market_monitor
    )


class TestFundamentalAnalysis:
    """Test fundamental analysis functionality"""
    
    def test_perform_fundamental_analysis_strong(self, analyzer, mock_research_engine):
        """Test fundamental analysis with strong financials"""
        mock_context = MockCompanyContext(
            financial_data=MockFinancialData(
                revenue=Decimal('1000000000'),
                earnings=Decimal('100000000'),  # Positive
                pe_ratio=Decimal('20'),  # Reasonable
                debt_to_equity=Decimal('0.5'),  # Low debt
                free_cash_flow=Decimal('50000000'),  # Positive
                roe=Decimal('0.20')  # Strong ROE
            )
        )
        mock_research_engine.get_company_context.return_value = mock_context
        
        score = analyzer.perform_fundamental_analysis("AAPL")
        
        assert isinstance(score, FundamentalScore)
        assert score.score > 0.7  # Strong fundamentals
        assert score.earnings_quality == 1.0  # Positive earnings
        assert score.financial_health > 0.7
    
    def test_perform_fundamental_analysis_weak(self, analyzer, mock_research_engine):
        """Test fundamental analysis with weak financials"""
        mock_context = MockCompanyContext(
            financial_data=MockFinancialData(
                revenue=Decimal('1000000000'),
                earnings=Decimal('-10000000'),  # Negative
                pe_ratio=Decimal('50'),  # High
                debt_to_equity=Decimal('2.0'),  # High debt
                free_cash_flow=Decimal('-5000000'),  # Negative
                roe=Decimal('0.05')  # Low ROE
            )
        )
        mock_research_engine.get_company_context.return_value = mock_context
        
        score = analyzer.perform_fundamental_analysis("XYZ")
        
        assert score.score < 0.5  # Weak fundamentals
        assert score.earnings_quality == 0.0  # Negative earnings
    
    def test_perform_fundamental_analysis_no_data(self, analyzer, mock_research_engine):
        """Test fundamental analysis with no data"""
        mock_research_engine.get_company_context.return_value = None
        
        score = analyzer.perform_fundamental_analysis("ABC")
        
        assert score.score == 0.0


class TestMomentumAnalysis:
    """Test momentum analysis functionality"""
    
    def test_perform_momentum_analysis(self, analyzer):
        """Test momentum analysis"""
        score = analyzer.perform_momentum_analysis("AAPL")
        
        assert isinstance(score, MomentumScore)
        assert 0.0 <= score.score <= 1.0
        assert 0.0 <= score.price_trend <= 1.0
        assert 0.0 <= score.volume_confirmation <= 1.0


class TestGlobalContext:
    """Test global context building"""
    
    def test_build_global_context(self, analyzer, mock_research_engine):
        """Test building global context"""
        mock_context = MockCompanyContext(
            financial_data=None,
            news_sentiment=0.6
        )
        mock_research_engine.get_company_context.return_value = mock_context
        
        context = analyzer.build_global_context("MSFT")
        
        assert isinstance(context, GlobalContext)
        assert len(context.economic_factors) > 0
        assert len(context.industry_dynamics) > 0
        assert len(context.risk_factors) > 0
        assert context.timing_rationale != ""
    
    def test_build_global_context_positive_sentiment(self, analyzer, mock_research_engine):
        """Test context with positive sentiment"""
        mock_context = MockCompanyContext(
            financial_data=None,
            news_sentiment=0.7
        )
        mock_research_engine.get_company_context.return_value = mock_context
        
        context = analyzer.build_global_context("GOOGL")
        
        assert any("positive" in s.lower() for s in context.company_specifics)
    
    def test_build_global_context_negative_sentiment(self, analyzer, mock_research_engine):
        """Test context with negative sentiment"""
        mock_context = MockCompanyContext(
            financial_data=None,
            news_sentiment=-0.7
        )
        mock_research_engine.get_company_context.return_value = mock_context
        
        context = analyzer.build_global_context("ABC")
        
        assert any("negative" in s.lower() for s in context.company_specifics)


class TestPositionSizing:
    """Test position sizing calculation"""
    
    def test_calculate_position_size_low_risk(self, analyzer):
        """Test position sizing for low risk"""
        size = analyzer.calculate_position_size(RiskLevel.LOW)
        
        assert Decimal('15.0') <= size <= Decimal('25.0')
    
    def test_calculate_position_size_medium_risk(self, analyzer):
        """Test position sizing for medium risk"""
        size = analyzer.calculate_position_size(RiskLevel.MEDIUM)
        
        assert Decimal('8.0') <= size <= Decimal('15.0')
    
    def test_calculate_position_size_high_risk(self, analyzer):
        """Test position sizing for high risk"""
        size = analyzer.calculate_position_size(RiskLevel.HIGH)
        
        assert Decimal('1.0') <= size <= Decimal('8.0')


class TestRobinhoodTradeability:
    """Test Robinhood tradeability verification"""
    
    def test_verify_robinhood_tradeable(self, analyzer):
        """Test Robinhood tradeability check"""
        is_tradeable = analyzer.verify_robinhood_tradeable("AAPL")
        
        assert isinstance(is_tradeable, bool)
    
    def test_verify_robinhood_tradeable_caching(self, analyzer):
        """Test that tradeability results are cached"""
        # First call
        result1 = analyzer.verify_robinhood_tradeable("MSFT")
        
        # Second call should use cache
        result2 = analyzer.verify_robinhood_tradeable("MSFT")
        
        assert result1 == result2
        assert "MSFT" in analyzer.robinhood_cache


class TestRiskAssessment:
    """Test risk level assessment"""
    
    def test_assess_risk_level_low(self, analyzer):
        """Test low risk assessment"""
        fundamental = FundamentalScore(0.8, 0.8, 0.8, 0.8, 0.8)
        momentum = MomentumScore(0.8, 0.8, 0.8)
        context = ContextScore(0.8, 0.8, 0.8, 0.8)
        
        risk = analyzer._assess_risk_level(fundamental, momentum, context)
        
        assert risk == RiskLevel.LOW
    
    def test_assess_risk_level_medium(self, analyzer):
        """Test medium risk assessment"""
        fundamental = FundamentalScore(0.6, 0.6, 0.6, 0.6, 0.6)
        momentum = MomentumScore(0.6, 0.6, 0.6)
        context = ContextScore(0.6, 0.6, 0.6, 0.6)
        
        risk = analyzer._assess_risk_level(fundamental, momentum, context)
        
        assert risk == RiskLevel.MEDIUM
    
    def test_assess_risk_level_high(self, analyzer):
        """Test high risk assessment"""
        fundamental = FundamentalScore(0.3, 0.3, 0.3, 0.3, 0.3)
        momentum = MomentumScore(0.3, 0.3, 0.3)
        context = ContextScore(0.3, 0.3, 0.3, 0.3)
        
        risk = analyzer._assess_risk_level(fundamental, momentum, context)
        
        assert risk == RiskLevel.HIGH


class TestThesisGeneration:
    """Test investment thesis generation"""
    
    def test_generate_thesis(self, analyzer):
        """Test thesis generation"""
        fundamental = FundamentalScore(0.8, 0.8, 0.8, 0.8, 0.8)
        momentum = MomentumScore(0.7, 0.7, 0.7)
        context = GlobalContext(
            economic_factors=[],
            geopolitical_events=[],
            industry_dynamics=[],
            company_specifics=["Strong market position"],
            timing_rationale="Good entry point",
            risk_factors=[]
        )
        projection = RealTimeProjection(
            symbol="AAPL",
            projection_type="price_target",
            projected_value=Decimal('200.00'),
            confidence_lower=Decimal('180.00'),
            confidence_upper=Decimal('220.00'),
            confidence_level=0.8,
            projection_date=datetime.now() + timedelta(days=30)
        )
        
        thesis = analyzer._generate_thesis("AAPL", fundamental, momentum, context, projection)
        
        assert isinstance(thesis, str)
        assert len(thesis) > 0
        assert "AAPL" in thesis


class TestExpectedReturn:
    """Test expected return calculation"""
    
    def test_calculate_expected_return_with_projection(self, analyzer):
        """Test expected return with projection"""
        current_price = Decimal('150.00')
        projection = RealTimeProjection(
            symbol="AAPL",
            projection_type="price_target",
            projected_value=Decimal('180.00'),
            confidence_lower=Decimal('170.00'),
            confidence_upper=Decimal('190.00'),
            confidence_level=0.8,
            projection_date=datetime.now() + timedelta(days=30)
        )
        
        expected_return = analyzer._calculate_expected_return(current_price, projection)
        
        assert expected_return == Decimal('20.0')  # (180-150)/150 * 100 = 20%
    
    def test_calculate_expected_return_no_projection(self, analyzer):
        """Test expected return without projection"""
        current_price = Decimal('150.00')
        
        expected_return = analyzer._calculate_expected_return(current_price, None)
        
        assert expected_return == Decimal('15.0')  # Default


class TestOpportunityAnalysis:
    """Test full opportunity analysis"""
    
    def test_analyze_opportunities_success(
        self,
        analyzer,
        mock_research_engine,
        mock_projection_engine,
        mock_market_monitor
    ):
        """Test successful opportunity analysis"""
        # Setup mocks
        mock_quote = Quote(
            symbol="AAPL",
            price=Decimal('150.00'),
            exchange_timestamp=datetime.now(),
            received_timestamp=datetime.now(),
            bid=Decimal('149.90'),
            ask=Decimal('150.10'),
            volume=1000000
        )
        mock_market_monitor.get_current_price.return_value = mock_quote
        
        mock_context = MockCompanyContext(
            financial_data=MockFinancialData(
                revenue=Decimal('1000000000'),
                earnings=Decimal('100000000'),
                pe_ratio=Decimal('20'),
                debt_to_equity=Decimal('0.5'),
                free_cash_flow=Decimal('50000000'),
                roe=Decimal('0.20')
            ),
            news_sentiment=0.6
        )
        mock_research_engine.get_company_context.return_value = mock_context
        
        mock_projection = RealTimeProjection(
            symbol="AAPL",
            projection_type="price_target",
            projected_value=Decimal('180.00'),
            confidence_lower=Decimal('170.00'),
            confidence_upper=Decimal('190.00'),
            confidence_level=0.8,
            projection_date=datetime.now() + timedelta(days=30)
        )
        mock_projection_engine.project_price_target.return_value = mock_projection
        
        opportunities = analyzer.analyze_opportunities(["AAPL"])
        
        assert len(opportunities) >= 1
        assert isinstance(opportunities[0], InvestmentOpportunity)
        assert opportunities[0].symbol == "AAPL"
        assert Decimal('1.0') <= opportunities[0].position_size_percent <= Decimal('25.0')
    
    def test_analyze_opportunities_filters_non_tradeable(
        self,
        analyzer,
        mock_research_engine,
        mock_projection_engine,
        mock_market_monitor
    ):
        """Test that non-tradeable securities are filtered out"""
        # Make verify_robinhood_tradeable return False
        analyzer.verify_robinhood_tradeable = Mock(return_value=False)
        
        opportunities = analyzer.analyze_opportunities(["XYZ"])
        
        assert len(opportunities) == 0
    
    def test_analyze_opportunities_filters_stale_data(
        self,
        analyzer,
        mock_research_engine,
        mock_projection_engine,
        mock_market_monitor
    ):
        """Test that stale data is filtered out"""
        # Create stale quote
        mock_quote = Quote(
            symbol="AAPL",
            price=Decimal('150.00'),
            exchange_timestamp=datetime.now() - timedelta(seconds=60),  # 60s old
            received_timestamp=datetime.now(),
            bid=Decimal('149.90'),
            ask=Decimal('150.10'),
            volume=1000000
        )
        mock_market_monitor.get_current_price.return_value = mock_quote
        
        opportunities = analyzer.analyze_opportunities(["AAPL"])
        
        assert len(opportunities) == 0
    
    def test_analyze_opportunities_filters_low_fundamental(
        self,
        analyzer,
        mock_research_engine,
        mock_projection_engine,
        mock_market_monitor
    ):
        """Test that low fundamental scores are filtered out"""
        mock_quote = Quote(
            symbol="ABC",
            price=Decimal('10.00'),
            exchange_timestamp=datetime.now(),
            received_timestamp=datetime.now(),
            bid=Decimal('9.90'),
            ask=Decimal('10.10'),
            volume=100000
        )
        mock_market_monitor.get_current_price.return_value = mock_quote
        
        # Weak fundamentals
        mock_context = MockCompanyContext(
            financial_data=MockFinancialData(
                revenue=Decimal('1000000'),
                earnings=Decimal('-100000'),  # Negative
                pe_ratio=Decimal('100'),  # Very high
                debt_to_equity=Decimal('3.0'),  # High debt
                free_cash_flow=Decimal('-10000'),  # Negative
                roe=Decimal('0.01')  # Very low
            )
        )
        mock_research_engine.get_company_context.return_value = mock_context
        
        opportunities = analyzer.analyze_opportunities(["ABC"])
        
        assert len(opportunities) == 0
    
    def test_analyze_opportunities_returns_top_5(
        self,
        analyzer,
        mock_research_engine,
        mock_projection_engine,
        mock_market_monitor
    ):
        """Test that only top 5 opportunities are returned"""
        # Setup mocks for 10 candidates
        mock_quote = Quote(
            symbol="TEST",
            price=Decimal('100.00'),
            exchange_timestamp=datetime.now(),
            received_timestamp=datetime.now(),
            bid=Decimal('99.90'),
            ask=Decimal('100.10'),
            volume=1000000
        )
        mock_market_monitor.get_current_price.return_value = mock_quote
        
        mock_context = MockCompanyContext(
            financial_data=MockFinancialData(
                revenue=Decimal('1000000000'),
                earnings=Decimal('100000000'),
                pe_ratio=Decimal('20'),
                debt_to_equity=Decimal('0.5'),
                free_cash_flow=Decimal('50000000'),
                roe=Decimal('0.20')
            ),
            news_sentiment=0.6
        )
        mock_research_engine.get_company_context.return_value = mock_context
        
        mock_projection = RealTimeProjection(
            symbol="TEST",
            projection_type="price_target",
            projected_value=Decimal('120.00'),
            confidence_lower=Decimal('110.00'),
            confidence_upper=Decimal('130.00'),
            confidence_level=0.8,
            projection_date=datetime.now() + timedelta(days=30)
        )
        mock_projection_engine.project_price_target.return_value = mock_projection
        
        # Analyze 10 candidates
        candidates = [f"STOCK{i}" for i in range(10)]
        opportunities = analyzer.analyze_opportunities(candidates)
        
        # Should return max 5
        assert len(opportunities) <= 5


class TestScoreCalculations:
    """Test score calculation methods"""
    
    def test_calculate_context_score(self, analyzer):
        """Test context score calculation"""
        context = GlobalContext(
            economic_factors=["Factor 1"],
            geopolitical_events=[],
            industry_dynamics=["Dynamic 1"],
            company_specifics=["Specific 1"],
            timing_rationale="Good timing",
            risk_factors=["Risk 1"]
        )
        
        score = analyzer._calculate_context_score(context)
        
        assert isinstance(score, ContextScore)
        assert 0.0 <= score.score <= 1.0
    
    def test_calculate_projection_score(self, analyzer):
        """Test projection score calculation"""
        projection = RealTimeProjection(
            symbol="AAPL",
            projection_type="price_target",
            projected_value=Decimal('180.00'),
            confidence_lower=Decimal('170.00'),
            confidence_upper=Decimal('190.00'),
            confidence_level=0.8,
            projection_date=datetime.now() + timedelta(days=30)
        )
        
        score = analyzer._calculate_projection_score(projection)
        
        assert isinstance(score, ProjectionScore)
        assert 0.0 <= score.score <= 1.0
    
    def test_calculate_projection_score_no_projection(self, analyzer):
        """Test projection score with no projection"""
        score = analyzer._calculate_projection_score(None)
        
        assert score.score == 0.5  # Default
