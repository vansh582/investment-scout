"""
Data Manager for Investment Scout

Manages Redis caching and PostgreSQL persistence with dual TTL strategy:
- Active stocks: 15-second TTL
- Watchlist stocks: 60-second TTL
"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
import redis
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import SimpleConnectionPool

from src.models.investment_scout_models import (
    Quote, FinancialData, NewsArticle, GeopoliticalEvent,
    IndustryTrend, RealTimeProjection
)


logger = logging.getLogger(__name__)


class DataManager:
    """
    Manages data caching and persistence for Investment Scout.
    
    Implements dual TTL caching strategy:
    - Active stocks: 15-second TTL (frequently monitored)
    - Watchlist stocks: 60-second TTL (less frequent monitoring)
    """
    
    ACTIVE_TTL = 15  # seconds
    WATCHLIST_TTL = 60  # seconds
    
    def __init__(self, redis_url: str, postgres_url: str, min_pool_size: int = 1, max_pool_size: int = 5):
        """
        Initialize Data Manager with Redis and PostgreSQL connections.
        
        Args:
            redis_url: Redis connection URL
            postgres_url: PostgreSQL connection URL
            min_pool_size: Minimum PostgreSQL connection pool size
            max_pool_size: Maximum PostgreSQL connection pool size
        """
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.pg_pool = SimpleConnectionPool(min_pool_size, max_pool_size, postgres_url)
        self._ensure_schema()
        logger.info("DataManager initialized successfully")
    
    def _ensure_schema(self):
        """Create database schema if it doesn't exist"""
        conn = self.pg_pool.getconn()
        try:
            with conn.cursor() as cur:
                # Financial data table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS financial_data (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        revenue NUMERIC(20, 2),
                        earnings NUMERIC(20, 2),
                        pe_ratio NUMERIC(10, 2),
                        debt_to_equity NUMERIC(10, 2),
                        free_cash_flow NUMERIC(20, 2),
                        roe NUMERIC(10, 4),
                        updated_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(symbol, updated_at)
                    )
                """)
                
                # News articles table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS news_articles (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        summary TEXT,
                        source VARCHAR(100),
                        published_at TIMESTAMP NOT NULL,
                        url TEXT,
                        sentiment NUMERIC(3, 2),
                        symbols TEXT[],
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(url)
                    )
                """)
                
                # Geopolitical events table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS geopolitical_events (
                        id SERIAL PRIMARY KEY,
                        event_type VARCHAR(50) NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        affected_regions TEXT[],
                        affected_sectors TEXT[],
                        impact_score NUMERIC(3, 2),
                        event_date TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Industry trends table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS industry_trends (
                        id SERIAL PRIMARY KEY,
                        sector VARCHAR(100) NOT NULL,
                        industry VARCHAR(100) NOT NULL,
                        trend_type VARCHAR(50),
                        description TEXT,
                        impact_score NUMERIC(3, 2),
                        affected_companies TEXT[],
                        timestamp TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Real-time projections table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS projections (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        projection_type VARCHAR(50),
                        projected_value NUMERIC(20, 2),
                        confidence_lower NUMERIC(20, 2),
                        confidence_upper NUMERIC(20, 2),
                        confidence_level NUMERIC(3, 2),
                        projection_date TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Historical quotes table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS historical_quotes (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        price NUMERIC(20, 6),
                        bid NUMERIC(20, 6),
                        ask NUMERIC(20, 6),
                        volume BIGINT,
                        exchange_timestamp TIMESTAMP NOT NULL,
                        received_timestamp TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for performance
                cur.execute("CREATE INDEX IF NOT EXISTS idx_financial_data_symbol ON financial_data(symbol)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_news_articles_published ON news_articles(published_at DESC)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_geopolitical_events_date ON geopolitical_events(event_date DESC)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_industry_trends_sector ON industry_trends(sector, timestamp DESC)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_projections_symbol ON projections(symbol, projection_date DESC)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_historical_quotes_symbol ON historical_quotes(symbol, exchange_timestamp DESC)")
                
                conn.commit()
                logger.info("Database schema ensured")
        finally:
            self.pg_pool.putconn(conn)
    
    def cache_quote(self, symbol: str, quote: Quote, is_active: bool = True) -> None:
        """
        Cache quote with appropriate TTL based on stock type.
        
        Args:
            symbol: Stock symbol
            quote: Quote object to cache
            is_active: True for active stocks (15s TTL), False for watchlist (60s TTL)
        """
        ttl = self.ACTIVE_TTL if is_active else self.WATCHLIST_TTL
        cache_key = f"quote:{symbol}"
        
        quote_data = {
            "symbol": quote.symbol,
            "price": str(quote.price),
            "bid": str(quote.bid),
            "ask": str(quote.ask),
            "volume": quote.volume,
            "exchange_timestamp": quote.exchange_timestamp.isoformat(),
            "received_timestamp": quote.received_timestamp.isoformat()
        }
        
        self.redis_client.setex(cache_key, ttl, json.dumps(quote_data))
        logger.debug(f"Cached quote for {symbol} with {ttl}s TTL")
    
    def get_cached_quote(self, symbol: str) -> Optional[Quote]:
        """
        Retrieve cached quote and validate freshness.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Quote object if cached and fresh, None otherwise
        """
        cache_key = f"quote:{symbol}"
        cached_data = self.redis_client.get(cache_key)
        
        if not cached_data:
            logger.debug(f"Cache miss for {symbol}")
            return None
        
        try:
            data = json.loads(cached_data)
            quote = Quote(
                symbol=data["symbol"],
                price=Decimal(data["price"]),
                bid=Decimal(data["bid"]),
                ask=Decimal(data["ask"]),
                volume=data["volume"],
                exchange_timestamp=datetime.fromisoformat(data["exchange_timestamp"]),
                received_timestamp=datetime.fromisoformat(data["received_timestamp"])
            )
            
            # Validate freshness before returning
            if not quote.is_fresh:
                logger.warning(f"Cached quote for {symbol} is stale (latency: {quote.latency.total_seconds()}s)")
                self.redis_client.delete(cache_key)
                return None
            
            logger.debug(f"Cache hit for {symbol}")
            return quote
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Error parsing cached quote for {symbol}: {e}")
            self.redis_client.delete(cache_key)
            return None
    
    def is_cache_valid(self, symbol: str) -> bool:
        """
        Check if cached data exists and is valid.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if cache exists and is fresh, False otherwise
        """
        quote = self.get_cached_quote(symbol)
        return quote is not None
    
    def store_historical_quote(self, quote: Quote) -> None:
        """
        Store quote in PostgreSQL for historical analysis.
        
        Args:
            quote: Quote object to store
        """
        conn = self.pg_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO historical_quotes 
                    (symbol, price, bid, ask, volume, exchange_timestamp, received_timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    quote.symbol,
                    quote.price,
                    quote.bid,
                    quote.ask,
                    quote.volume,
                    quote.exchange_timestamp,
                    quote.received_timestamp
                ))
                conn.commit()
                logger.debug(f"Stored historical quote for {quote.symbol}")
        except psycopg2.Error as e:
            logger.error(f"Error storing historical quote: {e}")
            conn.rollback()
        finally:
            self.pg_pool.putconn(conn)
    
    def store_financial_data(self, financial_data: FinancialData) -> None:
        """Store company financial data in PostgreSQL"""
        conn = self.pg_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO financial_data 
                    (symbol, revenue, earnings, pe_ratio, debt_to_equity, free_cash_flow, roe, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, updated_at) DO UPDATE SET
                        revenue = EXCLUDED.revenue,
                        earnings = EXCLUDED.earnings,
                        pe_ratio = EXCLUDED.pe_ratio,
                        debt_to_equity = EXCLUDED.debt_to_equity,
                        free_cash_flow = EXCLUDED.free_cash_flow,
                        roe = EXCLUDED.roe
                """, (
                    financial_data.symbol,
                    financial_data.revenue,
                    financial_data.earnings,
                    financial_data.pe_ratio,
                    financial_data.debt_to_equity,
                    financial_data.free_cash_flow,
                    financial_data.roe,
                    financial_data.updated_at
                ))
                conn.commit()
                logger.debug(f"Stored financial data for {financial_data.symbol}")
        except psycopg2.Error as e:
            logger.error(f"Error storing financial data: {e}")
            conn.rollback()
        finally:
            self.pg_pool.putconn(conn)
    
    def store_news_article(self, article: NewsArticle, symbols: List[str] = None) -> None:
        """Store news article with sentiment in PostgreSQL"""
        conn = self.pg_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO news_articles 
                    (title, summary, source, published_at, url, sentiment, symbols)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                """, (
                    article.title,
                    article.summary,
                    article.source,
                    article.published_at,
                    article.url,
                    article.sentiment,
                    symbols or []
                ))
                conn.commit()
                logger.debug(f"Stored news article: {article.title[:50]}")
        except psycopg2.Error as e:
            logger.error(f"Error storing news article: {e}")
            conn.rollback()
        finally:
            self.pg_pool.putconn(conn)
    
    def store_geopolitical_event(self, event: GeopoliticalEvent) -> None:
        """Store geopolitical event in PostgreSQL"""
        conn = self.pg_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO geopolitical_events 
                    (event_type, title, description, affected_regions, affected_sectors, impact_score, event_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    event.event_type,
                    event.title,
                    event.description,
                    event.affected_regions,
                    event.affected_sectors,
                    event.impact_score,
                    event.event_date
                ))
                conn.commit()
                logger.debug(f"Stored geopolitical event: {event.title[:50]}")
        except psycopg2.Error as e:
            logger.error(f"Error storing geopolitical event: {e}")
            conn.rollback()
        finally:
            self.pg_pool.putconn(conn)
    
    def store_industry_trend(self, trend: IndustryTrend) -> None:
        """Store industry trend in PostgreSQL"""
        conn = self.pg_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO industry_trends 
                    (sector, industry, trend_type, description, impact_score, affected_companies, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    trend.sector,
                    trend.industry,
                    trend.trend_type,
                    trend.description,
                    trend.impact_score,
                    trend.affected_companies,
                    trend.timestamp
                ))
                conn.commit()
                logger.debug(f"Stored industry trend for {trend.sector}/{trend.industry}")
        except psycopg2.Error as e:
            logger.error(f"Error storing industry trend: {e}")
            conn.rollback()
        finally:
            self.pg_pool.putconn(conn)
    
    def store_projection(self, projection: RealTimeProjection) -> None:
        """Store real-time projection in PostgreSQL"""
        conn = self.pg_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO projections 
                    (symbol, projection_type, projected_value, confidence_lower, confidence_upper, confidence_level, projection_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    projection.symbol,
                    projection.projection_type,
                    projection.projected_value,
                    projection.confidence_lower,
                    projection.confidence_upper,
                    projection.confidence_level,
                    projection.projection_date
                ))
                conn.commit()
                logger.debug(f"Stored projection for {projection.symbol}")
        except psycopg2.Error as e:
            logger.error(f"Error storing projection: {e}")
            conn.rollback()
        finally:
            self.pg_pool.putconn(conn)
    
    def get_historical_quotes(self, symbol: str, days: int = 30) -> List[Dict]:
        """Retrieve historical quotes for analysis"""
        conn = self.pg_pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM historical_quotes
                    WHERE symbol = %s 
                    AND exchange_timestamp >= NOW() - INTERVAL '%s days'
                    ORDER BY exchange_timestamp DESC
                """, (symbol, days))
                return cur.fetchall()
        finally:
            self.pg_pool.putconn(conn)
    
    def get_financial_data(self, symbol: str) -> Optional[Dict]:
        """Retrieve latest financial data for a symbol"""
        conn = self.pg_pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM financial_data
                    WHERE symbol = %s
                    ORDER BY updated_at DESC
                    LIMIT 1
                """, (symbol,))
                return cur.fetchone()
        finally:
            self.pg_pool.putconn(conn)
    
    def get_recent_news(self, days: int = 7, symbols: List[str] = None) -> List[Dict]:
        """Retrieve recent news articles"""
        conn = self.pg_pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if symbols:
                    cur.execute("""
                        SELECT * FROM news_articles
                        WHERE published_at >= NOW() - INTERVAL '%s days'
                        AND symbols && %s
                        ORDER BY published_at DESC
                    """, (days, symbols))
                else:
                    cur.execute("""
                        SELECT * FROM news_articles
                        WHERE published_at >= NOW() - INTERVAL '%s days'
                        ORDER BY published_at DESC
                    """, (days,))
                return cur.fetchall()
        finally:
            self.pg_pool.putconn(conn)
    
    def close(self):
        """Close all connections"""
        self.redis_client.close()
        self.pg_pool.closeall()
        logger.info("DataManager connections closed")
