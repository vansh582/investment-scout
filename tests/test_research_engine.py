"""
Unit Tests for Research Engine

Tests data storage, retrieval, and context aggregation.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from decimal import Decimal

from src.utils.research_engine import ResearchEngine, CompanyContext, MarketSentiment
from src.models.investment_scout_models import (
    FinancialData, NewsArticle, GeopoliticalEvent, IndustryTrend, RealTimeProjection
)


def test_store_financial_data():
    """Test storing financial data"""
    mock_dm = Mock()
    engine = ResearchEngine(mock_dm)
    
    financial_data = FinancialData(
        symbol="AAPL",
        revenue=Decimal('394000000000'),
        earnings=Decimal('99800000000'),
        pe_ratio=Decimal('28.5'),
        debt_to_equity=Decimal('1.73'),
        free_cash_flow=Decimal('111000000000'),
        roe=Decimal('1.47'),
        updated_at=datetime.now()
    )
    
    engine.store_financial_data(financial_data)
    
    # Should call data manager
    mock_dm.store_financial_data.assert_called_once_with(financial_data)


def test_store_news_article():
    """Test storing news article"""
    mock_dm = Mock()
    engine = ResearchEngine(mock_dm)
    
    article = NewsArticle(
        title="Apple Reports Record Earnings",
        summary="Apple exceeded expectations with strong iPhone sales",
        source="Reuters",
        published_at=datetime.now(),
        url="https://example.com/article",
        sentiment=0.8
    )
    
    engine.store_news_article(article, symbols=["AAPL"])
    
    # Should call data manager
    mock_dm.store_news_article.assert_called_once_with(article, ["AAPL"])


def test_store_geopolitical_event():
    """Test storing geopolitical event"""
    mock_dm = Mock()
    engine = ResearchEngine(mock_dm)
    
    event = GeopoliticalEvent(
        event_type="policy",
        title="Fed Raises Interest Rates",
        description="Federal Reserve increases rates by 0.25%",
        affected_regions=["US"],
        affected_sectors=["Financial", "Technology"],
        impact_score=-0.3,
        event_date=datetime.now()
    )
    
    engine.store_geopolitical_event(event)
    
    # Should call data manager
    mock_dm.store_geopolitical_event.assert_called_once_with(event)


def test_store_industry_trend():
    """Test storing industry trend"""
    mock_dm = Mock()
    engine = ResearchEngine(mock_dm)
    
    trend = IndustryTrend(
        sector="Technology",
        industry="Semiconductors",
        trend_type="supply_chain",
        description="Chip shortage easing",
        impact_score=0.5,
        affected_companies=["NVDA", "AMD", "INTC"],
        timestamp=datetime.now()
    )
    
    engine.store_industry_trend(trend)
    
    # Should call data manager
    mock_dm.store_industry_trend.assert_called_once_with(trend)


def test_store_projection():
    """Test storing projection"""
    mock_dm = Mock()
    engine = ResearchEngine(mock_dm)
    
    projection = RealTimeProjection(
        symbol="AAPL",
        projection_type="price_target",
        projected_value=Decimal('180.00'),
        confidence_lower=Decimal('170.00'),
        confidence_upper=Decimal('190.00'),
        confidence_level=0.85,
        projection_date=datetime.now()
    )
    
    engine.store_projection(projection)
    
    # Should call data manager
    mock_dm.store_projection.assert_called_once_with(projection)


def test_get_company_context():
    """Test retrieving comprehensive company context"""
    mock_dm = Mock()
    
    # Mock financial data
    mock_dm.get_financial_data.return_value = {
        'symbol': 'AAPL',
        'revenue': Decimal('394000000000'),
        'earnings': Decimal('99800000000'),
        'pe_ratio': Decimal('28.5'),
        'debt_to_equity': Decimal('1.73'),
        'free_cash_flow': Decimal('111000000000'),
        'roe': Decimal('1.47'),
        'updated_at': datetime.now()
    }
    
    # Mock news data
    mock_dm.get_recent_news.return_value = [
        {
            'title': 'Apple Reports Strong Earnings',
            'summary': 'Q4 results beat expectations',
            'source': 'Reuters',
            'published_at': datetime.now(),
            'url': 'https://example.com/1',
            'sentiment': 0.8
        },
        {
            'title': 'iPhone Sales Surge',
            'summary': 'New model drives growth',
            'source': 'Bloomberg',
            'published_at': datetime.now(),
            'url': 'https://example.com/2',
            'sentiment': 0.6
        }
    ]
    
    engine = ResearchEngine(mock_dm)
    context = engine.get_company_context("AAPL", days=30)
    
    # Should return CompanyContext
    assert isinstance(context, CompanyContext)
    assert context.symbol == "AAPL"
    assert context.financial_data is not None
    assert len(context.recent_news) == 2
    
    # Should calculate average sentiment
    assert context.news_sentiment_avg == 0.7  # (0.8 + 0.6) / 2


def test_get_company_context_no_financial_data():
    """Test context retrieval when no financial data available"""
    mock_dm = Mock()
    mock_dm.get_financial_data.return_value = None
    mock_dm.get_recent_news.return_value = []
    
    engine = ResearchEngine(mock_dm)
    context = engine.get_company_context("UNKNOWN")
    
    # Should return context with None financial data
    assert context.financial_data is None
    assert len(context.recent_news) == 0
    assert context.news_sentiment_avg == 0.0


def test_get_market_sentiment():
    """Test overall market sentiment calculation"""
    mock_dm = Mock()
    
    # Mock news with various sentiments
    mock_dm.get_recent_news.return_value = [
        {'sentiment': 0.8, 'title': 'Positive news 1'},
        {'sentiment': 0.5, 'title': 'Positive news 2'},
        {'sentiment': -0.6, 'title': 'Negative news 1'},
        {'sentiment': -0.3, 'title': 'Negative news 2'},
        {'sentiment': 0.05, 'title': 'Neutral news'},
    ]
    
    engine = ResearchEngine(mock_dm)
    sentiment = engine.get_market_sentiment(days=7)
    
    # Should return MarketSentiment
    assert isinstance(sentiment, MarketSentiment)
    assert sentiment.total_articles == 5
    assert sentiment.positive_count == 2  # > 0.1
    assert sentiment.negative_count == 2  # < -0.1
    assert sentiment.neutral_count == 1  # between -0.1 and 0.1
    
    # Average sentiment: (0.8 + 0.5 - 0.6 - 0.3 + 0.05) / 5 = 0.09
    assert abs(sentiment.avg_sentiment - 0.09) < 0.01


def test_get_market_sentiment_no_data():
    """Test market sentiment with no data"""
    mock_dm = Mock()
    mock_dm.get_recent_news.return_value = []
    
    engine = ResearchEngine(mock_dm)
    sentiment = engine.get_market_sentiment(days=7)
    
    # Should return empty sentiment
    assert sentiment.total_articles == 0
    assert sentiment.avg_sentiment == 0.0
    assert sentiment.positive_count == 0
    assert sentiment.negative_count == 0


def test_calculate_sentiment_score_positive():
    """Test sentiment calculation for positive text"""
    engine = ResearchEngine(Mock())
    
    text = "Strong growth and profit beat expectations with success"
    score = engine.calculate_sentiment_score(text)
    
    # Should be positive
    assert score > 0


def test_calculate_sentiment_score_negative():
    """Test sentiment calculation for negative text"""
    engine = ResearchEngine(Mock())
    
    text = "Significant loss and decline with weak performance and risk"
    score = engine.calculate_sentiment_score(text)
    
    # Should be negative
    assert score < 0


def test_calculate_sentiment_score_neutral():
    """Test sentiment calculation for neutral text"""
    engine = ResearchEngine(Mock())
    
    text = "The company announced quarterly results today"
    score = engine.calculate_sentiment_score(text)
    
    # Should be neutral (no keywords)
    assert score == 0.0


def test_calculate_sentiment_score_mixed():
    """Test sentiment calculation for mixed text"""
    engine = ResearchEngine(Mock())
    
    text = "Strong growth but concerns about risk and decline"
    score = engine.calculate_sentiment_score(text)
    
    # Should be slightly negative (2 positive, 3 negative keywords)
    assert -1.0 <= score <= 1.0


def test_sentiment_score_range():
    """Test that sentiment scores are always in valid range"""
    engine = ResearchEngine(Mock())
    
    # Test various texts
    texts = [
        "growth profit success strong beat exceed",  # Very positive
        "loss decline fall weak miss concern risk",  # Very negative
        "neutral text without keywords",  # Neutral
        "growth and loss",  # Mixed
    ]
    
    for text in texts:
        score = engine.calculate_sentiment_score(text)
        assert -1.0 <= score <= 1.0, f"Score {score} out of range for text: {text}"
