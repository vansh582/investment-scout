"""
Research Engine for Investment Scout

Centralized storage and retrieval of all research data including:
- Financial data
- News articles with sentiment
- Geopolitical events
- Industry trends
- Real-time projections
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.utils.data_manager_scout import DataManager
from src.models.investment_scout_models import (
    FinancialData, NewsArticle, GeopoliticalEvent,
    IndustryTrend, RealTimeProjection
)


logger = logging.getLogger(__name__)


@dataclass
class CompanyContext:
    """Comprehensive company context for analysis"""
    symbol: str
    financial_data: Optional[FinancialData]
    recent_news: List[NewsArticle]
    relevant_geo_events: List[GeopoliticalEvent]
    industry_trends: List[IndustryTrend]
    projections: List[RealTimeProjection]
    news_sentiment_avg: float
    geo_impact_avg: float


@dataclass
class MarketSentiment:
    """Overall market sentiment analysis"""
    period_days: int
    total_articles: int
    avg_sentiment: float
    positive_count: int
    negative_count: int
    neutral_count: int
    top_topics: List[str]


class ResearchEngine:
    """
    Centralized research data storage and retrieval.
    
    Aggregates data from multiple sources and provides
    comprehensive context for investment analysis.
    """
    
    def __init__(self, data_manager: DataManager):
        """
        Initialize Research Engine.
        
        Args:
            data_manager: Data manager for storage operations
        """
        self.data_manager = data_manager
        logger.info("ResearchEngine initialized")
    
    def store_financial_data(self, financial_data: FinancialData) -> None:
        """
        Store company financial data.
        
        Args:
            financial_data: FinancialData object to store
        """
        try:
            self.data_manager.store_financial_data(financial_data)
            logger.debug(f"Stored financial data for {financial_data.symbol}")
        except Exception as e:
            logger.error(f"Failed to store financial data: {e}")
    
    def store_news_article(self, article: NewsArticle, symbols: List[str] = None) -> None:
        """
        Store news article with sentiment.
        
        Args:
            article: NewsArticle object to store
            symbols: Related stock symbols
        """
        try:
            self.data_manager.store_news_article(article, symbols)
            logger.debug(f"Stored news article: {article.title[:50]}")
        except Exception as e:
            logger.error(f"Failed to store news article: {e}")
    
    def store_geopolitical_event(self, event: GeopoliticalEvent) -> None:
        """
        Store geopolitical event.
        
        Args:
            event: GeopoliticalEvent object to store
        """
        try:
            self.data_manager.store_geopolitical_event(event)
            logger.debug(f"Stored geopolitical event: {event.title[:50]}")
        except Exception as e:
            logger.error(f"Failed to store geopolitical event: {e}")
    
    def store_industry_trend(self, trend: IndustryTrend) -> None:
        """
        Store industry trend.
        
        Args:
            trend: IndustryTrend object to store
        """
        try:
            self.data_manager.store_industry_trend(trend)
            logger.debug(f"Stored industry trend for {trend.sector}/{trend.industry}")
        except Exception as e:
            logger.error(f"Failed to store industry trend: {e}")
    
    def store_projection(self, projection: RealTimeProjection) -> None:
        """
        Store real-time projection.
        
        Args:
            projection: RealTimeProjection object to store
        """
        try:
            self.data_manager.store_projection(projection)
            logger.debug(f"Stored projection for {projection.symbol}")
        except Exception as e:
            logger.error(f"Failed to store projection: {e}")
    
    def get_company_context(self, symbol: str, days: int = 30) -> CompanyContext:
        """
        Get comprehensive company context for analysis.
        
        Args:
            symbol: Stock symbol
            days: Number of days to look back
            
        Returns:
            CompanyContext with all relevant data
        """
        # Get financial data
        financial_data_dict = self.data_manager.get_financial_data(symbol)
        financial_data = None
        if financial_data_dict:
            financial_data = FinancialData(
                symbol=financial_data_dict['symbol'],
                revenue=financial_data_dict['revenue'],
                earnings=financial_data_dict['earnings'],
                pe_ratio=financial_data_dict['pe_ratio'],
                debt_to_equity=financial_data_dict['debt_to_equity'],
                free_cash_flow=financial_data_dict['free_cash_flow'],
                roe=financial_data_dict['roe'],
                updated_at=financial_data_dict['updated_at']
            )
        
        # Get recent news
        news_dicts = self.data_manager.get_recent_news(days=days, symbols=[symbol])
        recent_news = []
        for news_dict in news_dicts:
            try:
                article = NewsArticle(
                    title=news_dict['title'],
                    summary=news_dict['summary'],
                    source=news_dict['source'],
                    published_at=news_dict['published_at'],
                    url=news_dict['url'],
                    sentiment=float(news_dict['sentiment']) if news_dict.get('sentiment') else None
                )
                recent_news.append(article)
            except Exception as e:
                logger.warning(f"Error parsing news article: {e}")
        
        # Calculate average news sentiment
        sentiments = [a.sentiment for a in recent_news if a.sentiment is not None]
        news_sentiment_avg = sum(sentiments) / len(sentiments) if sentiments else 0.0
        
        # Get relevant geopolitical events (placeholder - would need sector mapping)
        relevant_geo_events = []
        geo_impact_avg = 0.0
        
        # Get industry trends (placeholder - would need sector mapping)
        industry_trends = []
        
        # Get projections
        projections = []
        
        context = CompanyContext(
            symbol=symbol,
            financial_data=financial_data,
            recent_news=recent_news,
            relevant_geo_events=relevant_geo_events,
            industry_trends=industry_trends,
            projections=projections,
            news_sentiment_avg=news_sentiment_avg,
            geo_impact_avg=geo_impact_avg
        )
        
        logger.debug(
            f"Retrieved context for {symbol}: "
            f"{len(recent_news)} news, sentiment {news_sentiment_avg:.2f}"
        )
        
        return context
    
    def get_market_sentiment(self, days: int = 7) -> MarketSentiment:
        """
        Get overall market sentiment analysis.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            MarketSentiment with aggregated data
        """
        # Get all recent news
        news_dicts = self.data_manager.get_recent_news(days=days)
        
        total_articles = len(news_dicts)
        sentiments = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for news_dict in news_dicts:
            sentiment = news_dict.get('sentiment')
            if sentiment is not None:
                sentiment_val = float(sentiment)
                sentiments.append(sentiment_val)
                
                if sentiment_val > 0.1:
                    positive_count += 1
                elif sentiment_val < -0.1:
                    negative_count += 1
                else:
                    neutral_count += 1
        
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
        
        # Extract top topics (simplified - would use NLP in production)
        top_topics = []
        
        market_sentiment = MarketSentiment(
            period_days=days,
            total_articles=total_articles,
            avg_sentiment=avg_sentiment,
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count,
            top_topics=top_topics
        )
        
        logger.debug(
            f"Market sentiment ({days}d): {total_articles} articles, "
            f"avg sentiment {avg_sentiment:.2f}"
        )
        
        return market_sentiment
    
    def get_sector_news(self, sector: str, days: int = 7) -> List[NewsArticle]:
        """
        Get news articles related to a specific sector.
        
        Args:
            sector: Sector name (e.g., 'Technology', 'Healthcare')
            days: Number of days to look back
            
        Returns:
            List of relevant NewsArticle objects
        """
        # This would require sector-to-symbol mapping
        # For now, return empty list as placeholder
        logger.debug(f"Retrieving news for sector {sector}")
        return []
    
    def get_geopolitical_events(
        self,
        days: int = 30,
        event_types: List[str] = None,
        regions: List[str] = None
    ) -> List[GeopoliticalEvent]:
        """
        Get geopolitical events with optional filtering.
        
        Args:
            days: Number of days to look back
            event_types: Filter by event types
            regions: Filter by affected regions
            
        Returns:
            List of GeopoliticalEvent objects
        """
        # This would require database query with filters
        # Placeholder for now
        logger.debug(f"Retrieving geopolitical events ({days}d)")
        return []
    
    def get_industry_trends(
        self,
        sector: str = None,
        industry: str = None,
        days: int = 30
    ) -> List[IndustryTrend]:
        """
        Get industry trends with optional filtering.
        
        Args:
            sector: Filter by sector
            industry: Filter by industry
            days: Number of days to look back
            
        Returns:
            List of IndustryTrend objects
        """
        # This would require database query with filters
        # Placeholder for now
        logger.debug(f"Retrieving industry trends for {sector}/{industry}")
        return []
    
    def calculate_sentiment_score(self, text: str) -> float:
        """
        Calculate sentiment score for text.
        
        This is a placeholder - would use NLP library in production
        (e.g., VADER, TextBlob, or transformer models).
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment score from -1.0 to 1.0
        """
        # Placeholder implementation
        # In production, would use:
        # - VADER (vaderSentiment)
        # - TextBlob
        # - Transformers (FinBERT for financial text)
        
        # Simple keyword-based approach for now
        positive_keywords = ['growth', 'profit', 'gain', 'success', 'strong', 'beat', 'exceed']
        negative_keywords = ['loss', 'decline', 'fall', 'weak', 'miss', 'concern', 'risk']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_keywords if word in text_lower)
        negative_count = sum(1 for word in negative_keywords if word in text_lower)
        
        total = positive_count + negative_count
        if total == 0:
            return 0.0
        
        score = (positive_count - negative_count) / total
        
        # Clamp to [-1.0, 1.0]
        return max(-1.0, min(1.0, score))
