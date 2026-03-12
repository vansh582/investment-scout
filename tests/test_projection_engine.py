"""
Unit tests for ProjectionEngine
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass

from src.utils.projection_engine import ProjectionEngine
from src.models.investment_scout_models import RealTimeProjection, FinancialData


@dataclass
class MockFinancialData:
    """Mock financial data for testing"""
    revenue: Decimal
    earnings: Decimal
    pe_ratio: Decimal
    debt_to_equity: Decimal
    free_cash_flow: Decimal
    roe: Decimal
    updated_at: datetime


@dataclass
class MockCompanyContext:
    """Mock company context for testing"""
    financial_data: MockFinancialData
    news_sentiment: float
    news_count: int = 5


@pytest.fixture
def mock_research_engine():
    """Create mock research engine"""
    engine = Mock()
    engine.get_company_context = Mock()
    engine.store_projection = Mock()
    return engine


@pytest.fixture
def engine(mock_research_engine):
    """Create ProjectionEngine instance"""
    return ProjectionEngine(mock_research_engine)


class TestRevenueProjection:
    """Test revenue projection functionality"""
    
    def test_project_revenue_success(self, engine, mock_research_engine):
        """Test successful revenue projection"""
        mock_context = MockCompanyContext(
            financial_data=MockFinancialData(
                revenue=Decimal('1000000000'),
                earnings=Decimal('100000000'),
                pe_ratio=Decimal('20'),
                debt_to_equity=Decimal('0.5'),
                free_cash_flow=Decimal('50000000'),
                roe=Decimal('0.15'),
                updated_at=datetime.now()
            ),
            news_sentiment=0.5,
            news_count=10
        )
        mock_research_engine.get_company_context.return_value = mock_context
        
        projection = engine.project_revenue("AAPL")
        
        assert projection is not None
        assert isinstance(projection, RealTimeProjection)
        assert projection.symbol == "AAPL"
        assert projection.projection_type == "revenue"
        assert projection.projected_value > Decimal('1000000000')  # Should be higher due to positive sentiment
        assert projection.confidence_lower < projection.projected_value
        assert projection.confidence_upper > projection.projected_value
        assert 0.0 <= projection.confidence_level <= 1.0
    
    def test_project_revenue_no_data(self, engine, mock_research_engine):
        """Test revenue projection with no data"""
        mock_research_engine.get_company_context.return_value = None
        
        projection = engine.project_revenue("XYZ")
        
        assert projection is None
    
    def test_project_revenue_no_financial_data(self, engine, mock_research_engine):
        """Test revenue projection with no financial data"""
        mock_context = MockCompanyContext(
            financial_data=None,
            news_sentiment=0.5
        )
        mock_research_engine.get_company_context.return_value = mock_context
        
        projection = engine.project_revenue("XYZ")
        
        assert projection is None
    
    def test_project_revenue_negative_sentiment(self, engine, mock_research_engine):
        """Test revenue projection with negative sentiment"""
        mock_context = MockCompanyContext(
            financial_data=MockFinancialData(
                revenue=Decimal('1000000000'),
                earnings=Decimal('100000000'),
                pe_ratio=Decimal('20'),
                debt_to_equity=Decimal('0.5'),
                free_cash_flow=Decimal('50000000'),
                roe=Decimal('0.15'),
                updated_at=datetime.now()
            ),
            news_sentiment=-0.5,
            news_count=10
        )
        mock_research_engine.get_company_context.return_value = mock_context
        
        projection = engine.project_revenue("ABC")
        
        assert projection is not None
        # With negative sentiment (-0.5 * 0.10 = -0.05) and baseline growth (0.05),
        # the net growth is 0, so projection equals current revenue
        assert projection.projected_value == Decimal('1000000000')


class TestEarningsProjection:
    """Test earnings projection functionality"""
    
    def test_project_earnings_success(self, engine, mock_research_engine):
        """Test successful earnings projection"""
        mock_context = MockCompanyContext(
            financial_data=MockFinancialData(
                revenue=Decimal('1000000000'),
                earnings=Decimal('100000000'),
                pe_ratio=Decimal('20'),
                debt_to_equity=Decimal('0.5'),
                free_cash_flow=Decimal('50000000'),
                roe=Decimal('0.15'),
                updated_at=datetime.now()
            ),
            news_sentiment=0.6,
            news_count=15
        )
        mock_research_engine.get_company_context.return_value = mock_context
        
        projection = engine.project_earnings("MSFT")
        
        assert projection is not None
        assert isinstance(projection, RealTimeProjection)
        assert projection.symbol == "MSFT"
        assert projection.projection_type == "earnings"
        assert projection.projected_value > Decimal('100000000')
        assert projection.confidence_lower < projection.projected_value
        assert projection.confidence_upper > projection.projected_value
    
    def test_project_earnings_no_data(self, engine, mock_research_engine):
        """Test earnings projection with no data"""
        mock_research_engine.get_company_context.return_value = None
        
        projection = engine.project_earnings("XYZ")
        
        assert projection is None


class TestPriceProjection:
    """Test price target projection functionality"""
    
    def test_project_price_target_success(self, engine, mock_research_engine):
        """Test successful price target projection"""
        mock_context = MockCompanyContext(
            financial_data=MockFinancialData(
                revenue=Decimal('1000000000'),
                earnings=Decimal('100000000'),
                pe_ratio=Decimal('20'),
                debt_to_equity=Decimal('0.5'),
                free_cash_flow=Decimal('50000000'),
                roe=Decimal('0.15'),
                updated_at=datetime.now()
            ),
            news_sentiment=0.4,
            news_count=8
        )
        mock_research_engine.get_company_context.return_value = mock_context
        
        current_price = Decimal('150.00')
        projection = engine.project_price_target("GOOGL", current_price)
        
        assert projection is not None
        assert isinstance(projection, RealTimeProjection)
        assert projection.symbol == "GOOGL"
        assert projection.projection_type == "price_target"
        assert projection.projected_value > current_price  # Positive sentiment
        assert projection.confidence_lower < projection.projected_value
        assert projection.confidence_upper > projection.projected_value
    
    def test_project_price_target_negative_sentiment(self, engine, mock_research_engine):
        """Test price projection with negative sentiment"""
        mock_context = MockCompanyContext(
            financial_data=MockFinancialData(
                revenue=Decimal('1000000000'),
                earnings=Decimal('100000000'),
                pe_ratio=Decimal('20'),
                debt_to_equity=Decimal('0.5'),
                free_cash_flow=Decimal('50000000'),
                roe=Decimal('0.15'),
                updated_at=datetime.now()
            ),
            news_sentiment=-0.6,
            news_count=8
        )
        mock_research_engine.get_company_context.return_value = mock_context
        
        current_price = Decimal('150.00')
        projection = engine.project_price_target("ABC", current_price)
        
        assert projection is not None
        assert projection.projected_value < current_price  # Negative sentiment
    
    def test_project_price_target_no_data(self, engine, mock_research_engine):
        """Test price projection with no data"""
        mock_research_engine.get_company_context.return_value = None
        
        projection = engine.project_price_target("XYZ", Decimal('100.00'))
        
        assert projection is None


class TestGrowthRateCalculation:
    """Test growth rate calculation methods"""
    
    def test_calculate_revenue_growth_rate_positive(self, engine):
        """Test revenue growth rate with positive sentiment"""
        context = MockCompanyContext(
            financial_data=None,
            news_sentiment=0.8
        )
        
        growth_rate = engine._calculate_revenue_growth_rate(context)
        
        assert growth_rate > 0
        assert growth_rate <= 0.5  # Clamped to max 50%
    
    def test_calculate_revenue_growth_rate_negative(self, engine):
        """Test revenue growth rate with negative sentiment"""
        context = MockCompanyContext(
            financial_data=None,
            news_sentiment=-0.8
        )
        
        growth_rate = engine._calculate_revenue_growth_rate(context)
        
        assert growth_rate < 0
        assert growth_rate >= -0.5  # Clamped to min -50%
    
    def test_calculate_earnings_growth_rate(self, engine):
        """Test earnings growth rate calculation"""
        context = MockCompanyContext(
            financial_data=None,
            news_sentiment=0.5
        )
        
        growth_rate = engine._calculate_earnings_growth_rate(context)
        
        assert isinstance(growth_rate, float)
        assert -0.6 <= growth_rate <= 0.6
    
    def test_calculate_expected_return(self, engine):
        """Test expected return calculation"""
        context = MockCompanyContext(
            financial_data=None,
            news_sentiment=0.3
        )
        
        expected_return = engine._calculate_expected_return(context)
        
        assert isinstance(expected_return, float)
        assert -0.3 <= expected_return <= 0.3


class TestConfidenceCalculation:
    """Test confidence interval and level calculation"""
    
    def test_calculate_confidence_interval(self, engine):
        """Test confidence interval calculation"""
        context = MockCompanyContext(
            financial_data=None,
            news_sentiment=0.5,
            news_count=10
        )
        
        projected_value = Decimal('1000000')
        growth_rate = 0.15
        
        lower, upper = engine._calculate_confidence_interval(
            projected_value,
            growth_rate,
            context
        )
        
        assert lower < projected_value
        assert upper > projected_value
        assert isinstance(lower, Decimal)
        assert isinstance(upper, Decimal)
    
    def test_calculate_price_confidence_interval(self, engine):
        """Test price confidence interval calculation"""
        context = MockCompanyContext(
            financial_data=None,
            news_sentiment=0.5,
            news_count=10
        )
        
        projected_price = Decimal('150.00')
        expected_return = 0.10
        
        lower, upper = engine._calculate_price_confidence_interval(
            projected_price,
            expected_return,
            context
        )
        
        assert lower < projected_price
        assert upper > projected_price
        # Price intervals should be wider than revenue/earnings
        interval_width = upper - lower
        assert interval_width > Decimal('0')
    
    def test_calculate_uncertainty_high_data_quality(self, engine):
        """Test uncertainty with high data quality"""
        context = MockCompanyContext(
            financial_data=None,
            news_sentiment=0.5,
            news_count=15  # High news count
        )
        
        uncertainty = engine._calculate_uncertainty(0.10, context)
        
        assert 0.10 <= uncertainty <= 0.50
        assert uncertainty < 0.20  # Should be relatively low
    
    def test_calculate_uncertainty_low_data_quality(self, engine):
        """Test uncertainty with low data quality"""
        context = MockCompanyContext(
            financial_data=None,
            news_sentiment=0.5,
            news_count=2  # Low news count
        )
        
        uncertainty = engine._calculate_uncertainty(0.10, context)
        
        assert 0.10 <= uncertainty <= 0.50
        # Should be higher due to low data quality
    
    def test_calculate_confidence_level_high_quality(self, engine):
        """Test confidence level with high data quality"""
        context = MockCompanyContext(
            financial_data=None,
            news_sentiment=0.5,
            news_count=15
        )
        
        confidence = engine._calculate_confidence_level(context)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence >= 0.80  # Should be high
    
    def test_calculate_confidence_level_low_quality(self, engine):
        """Test confidence level with low data quality"""
        context = MockCompanyContext(
            financial_data=None,
            news_sentiment=0.5,
            news_count=2
        )
        
        confidence = engine._calculate_confidence_level(context)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence < 0.80  # Should be lower


class TestUpdateProjections:
    """Test batch projection updates"""
    
    def test_update_projections_success(self, engine, mock_research_engine):
        """Test updating projections for multiple symbols"""
        mock_context = MockCompanyContext(
            financial_data=MockFinancialData(
                revenue=Decimal('1000000000'),
                earnings=Decimal('100000000'),
                pe_ratio=Decimal('20'),
                debt_to_equity=Decimal('0.5'),
                free_cash_flow=Decimal('50000000'),
                roe=Decimal('0.15'),
                updated_at=datetime.now()
            ),
            news_sentiment=0.5,
            news_count=10
        )
        mock_research_engine.get_company_context.return_value = mock_context
        
        symbols = ["AAPL", "MSFT", "GOOGL"]
        engine.update_projections(symbols)
        
        # Should have called store_projection for each symbol (revenue + earnings)
        assert mock_research_engine.store_projection.call_count == 6  # 3 symbols * 2 projections
    
    def test_update_projections_with_errors(self, engine, mock_research_engine):
        """Test updating projections handles errors gracefully"""
        mock_context = MockCompanyContext(
            financial_data=MockFinancialData(
                revenue=Decimal('1000000000'),
                earnings=Decimal('100000000'),
                pe_ratio=Decimal('20'),
                debt_to_equity=Decimal('0.5'),
                free_cash_flow=Decimal('50000000'),
                roe=Decimal('0.15'),
                updated_at=datetime.now()
            ),
            news_sentiment=0.5,
            news_count=10
        )
        
        # Set up side effects: first symbol succeeds, second fails, third succeeds
        # Each symbol calls get_company_context twice (revenue + earnings)
        mock_research_engine.get_company_context.side_effect = [
            mock_context,  # AAPL revenue
            mock_context,  # AAPL earnings
            Exception("API Error"),  # MSFT revenue fails
            mock_context,  # GOOGL revenue
            mock_context   # GOOGL earnings
        ]
        
        symbols = ["AAPL", "MSFT", "GOOGL"]
        engine.update_projections(symbols)
        
        # Should have stored projections for AAPL and GOOGL only (2 symbols * 2 projections each)
        assert mock_research_engine.store_projection.call_count == 4
    
    def test_update_projections_empty_list(self, engine, mock_research_engine):
        """Test updating projections with empty symbol list"""
        engine.update_projections([])
        
        # Should not call store_projection
        assert mock_research_engine.store_projection.call_count == 0


class TestProjectionValidation:
    """Test projection validation and constraints"""
    
    def test_projection_date_in_future(self, engine, mock_research_engine):
        """Test that projection dates are in the future"""
        mock_context = MockCompanyContext(
            financial_data=MockFinancialData(
                revenue=Decimal('1000000000'),
                earnings=Decimal('100000000'),
                pe_ratio=Decimal('20'),
                debt_to_equity=Decimal('0.5'),
                free_cash_flow=Decimal('50000000'),
                roe=Decimal('0.15'),
                updated_at=datetime.now()
            ),
            news_sentiment=0.5,
            news_count=10
        )
        mock_research_engine.get_company_context.return_value = mock_context
        
        projection = engine.project_revenue("AAPL")
        
        assert projection.projection_date > datetime.now()
    
    def test_confidence_interval_ordering(self, engine, mock_research_engine):
        """Test that confidence intervals are properly ordered"""
        mock_context = MockCompanyContext(
            financial_data=MockFinancialData(
                revenue=Decimal('1000000000'),
                earnings=Decimal('100000000'),
                pe_ratio=Decimal('20'),
                debt_to_equity=Decimal('0.5'),
                free_cash_flow=Decimal('50000000'),
                roe=Decimal('0.15'),
                updated_at=datetime.now()
            ),
            news_sentiment=0.5,
            news_count=10
        )
        mock_research_engine.get_company_context.return_value = mock_context
        
        projection = engine.project_revenue("AAPL")
        
        # Confidence interval should be properly ordered
        assert projection.confidence_lower <= projection.projected_value <= projection.confidence_upper
