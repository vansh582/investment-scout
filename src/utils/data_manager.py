"""Data manager with Redis caching and PostgreSQL persistent storage"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
import redis
import psycopg2
from psycopg2.extras import RealDictCursor, Json

from ..models.data_models import Quote


logger = logging.getLogger(__name__)


class DataManager:
    """Manages data caching and persistent storage"""
    
    def __init__(
        self,
        redis_url: str,
        postgres_url: str,
        active_cache_ttl: int = 15,
        watchlist_cache_ttl: int = 60
    ):
        """
        Initialize data manager with Redis and PostgreSQL connections
        
        Args:
            redis_url: Redis connection URL
            postgres_url: PostgreSQL connection URL
            active_cache_ttl: Cache TTL in seconds for actively monitored stocks (default: 15)
            watchlist_cache_ttl: Cache TTL in seconds for watchlist stocks (default: 60)
        """
        self.active_cache_ttl = active_cache_ttl
        self.watchlist_cache_ttl = watchlist_cache_ttl
        
        # Initialize Redis connection
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        
        # Initialize PostgreSQL connection
        try:
            self.pg_conn = psycopg2.connect(postgres_url)
            self.pg_conn.autocommit = False
            logger.info("PostgreSQL connection established")
            self._init_database_schema()
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def _init_database_schema(self) -> None:
        """Initialize database schema if not exists"""
        with self.pg_conn.cursor() as cursor:
            # Create quotes table for historical data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quotes (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    price NUMERIC(20, 6) NOT NULL,
                    exchange_timestamp TIMESTAMP NOT NULL,
                    received_timestamp TIMESTAMP NOT NULL,
                    bid NUMERIC(20, 6),
                    ask NUMERIC(20, 6),
                    volume BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_symbol_timestamp 
                ON quotes (symbol, exchange_timestamp DESC)
            """)
            
            # Create historical_data table for aggregated data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historical_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    data_type VARCHAR(50) NOT NULL,
                    data JSONB NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_symbol_type_timestamp 
                ON historical_data (symbol, data_type, timestamp DESC)
            """)
            
            self.pg_conn.commit()
            logger.info("Database schema initialized")
    
    def cache_quote(
        self,
        symbol: str,
        quote: Quote,
        is_active: bool = True
    ) -> None:
        """
        Cache a quote in Redis with appropriate TTL
        
        Args:
            symbol: Stock symbol
            quote: Quote object to cache
            is_active: Whether this is an actively monitored stock (affects TTL)
        """
        try:
            # Determine TTL based on monitoring type
            ttl = self.active_cache_ttl if is_active else self.watchlist_cache_ttl
            
            # Serialize quote to JSON
            quote_data = {
                'symbol': quote.symbol,
                'price': str(quote.price),
                'exchange_timestamp': quote.exchange_timestamp.isoformat(),
                'received_timestamp': quote.received_timestamp.isoformat(),
                'bid': str(quote.bid),
                'ask': str(quote.ask),
                'volume': quote.volume
            }
            
            # Store in Redis with TTL
            cache_key = f"quote:{symbol}"
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(quote_data)
            )
            
            logger.debug(f"Cached quote for {symbol} with TTL {ttl}s")
        except Exception as e:
            logger.error(f"Failed to cache quote for {symbol}: {e}")
    
    def get_cached_quote(self, symbol: str) -> Optional[Quote]:
        """
        Retrieve a cached quote from Redis
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Quote object if found and valid, None otherwise
        """
        try:
            cache_key = f"quote:{symbol}"
            cached_data = self.redis_client.get(cache_key)
            
            if not cached_data:
                logger.debug(f"No cached quote found for {symbol}")
                return None
            
            # Deserialize quote from JSON
            quote_data = json.loads(cached_data)
            quote = Quote(
                symbol=quote_data['symbol'],
                price=Decimal(quote_data['price']),
                exchange_timestamp=datetime.fromisoformat(quote_data['exchange_timestamp']),
                received_timestamp=datetime.fromisoformat(quote_data['received_timestamp']),
                bid=Decimal(quote_data['bid']),
                ask=Decimal(quote_data['ask']),
                volume=quote_data['volume']
            )
            
            logger.debug(f"Retrieved cached quote for {symbol}")
            return quote
        except Exception as e:
            logger.error(f"Failed to retrieve cached quote for {symbol}: {e}")
            return None
    
    def store_historical_data(
        self,
        symbol: str,
        data_type: str,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Store historical data in PostgreSQL
        
        Args:
            symbol: Stock symbol
            data_type: Type of data (e.g., 'price_history', 'financials', 'news')
            data: Data to store as dictionary
            timestamp: Timestamp for the data (defaults to now)
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            with self.pg_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO historical_data (symbol, data_type, data, timestamp)
                    VALUES (%s, %s, %s, %s)
                """, (symbol, data_type, Json(data), timestamp))
            
            self.pg_conn.commit()
            logger.debug(f"Stored historical data for {symbol} (type: {data_type})")
        except Exception as e:
            self.pg_conn.rollback()
            logger.error(f"Failed to store historical data for {symbol}: {e}")
    
    def get_historical_data(
        self,
        symbol: str,
        data_type: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical data from PostgreSQL
        
        Args:
            symbol: Stock symbol
            data_type: Type of data to retrieve
            days: Number of days of history to retrieve
            
        Returns:
            List of historical data records
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT symbol, data_type, data, timestamp, created_at
                    FROM historical_data
                    WHERE symbol = %s
                      AND data_type = %s
                      AND timestamp >= %s
                    ORDER BY timestamp DESC
                """, (symbol, data_type, cutoff_date))
                
                results = cursor.fetchall()
            
            logger.debug(f"Retrieved {len(results)} historical records for {symbol} (type: {data_type})")
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Failed to retrieve historical data for {symbol}: {e}")
            return []
    
    def is_cache_valid(self, symbol: str) -> bool:
        """
        Check if cached data for a symbol is still valid
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if cache exists and is valid, False otherwise
        """
        try:
            cache_key = f"quote:{symbol}"
            ttl = self.redis_client.ttl(cache_key)
            
            # TTL returns -2 if key doesn't exist, -1 if no expiry, positive number for remaining seconds
            is_valid = ttl > 0
            
            logger.debug(f"Cache validity for {symbol}: {is_valid} (TTL: {ttl}s)")
            return is_valid
        except Exception as e:
            logger.error(f"Failed to check cache validity for {symbol}: {e}")
            return False
    
    def store_quote_history(self, quote: Quote) -> None:
        """
        Store a quote in PostgreSQL for historical tracking
        
        Args:
            quote: Quote object to store
        """
        try:
            with self.pg_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO quotes (
                        symbol, price, exchange_timestamp, received_timestamp,
                        bid, ask, volume
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    quote.symbol,
                    quote.price,
                    quote.exchange_timestamp,
                    quote.received_timestamp,
                    quote.bid,
                    quote.ask,
                    quote.volume
                ))
            
            self.pg_conn.commit()
            logger.debug(f"Stored quote history for {quote.symbol}")
        except Exception as e:
            self.pg_conn.rollback()
            logger.error(f"Failed to store quote history for {quote.symbol}: {e}")
    
    def get_quote_history(
        self,
        symbol: str,
        days: int = 30
    ) -> List[Quote]:
        """
        Retrieve quote history from PostgreSQL
        
        Args:
            symbol: Stock symbol
            days: Number of days of history to retrieve
            
        Returns:
            List of Quote objects
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT symbol, price, exchange_timestamp, received_timestamp,
                           bid, ask, volume
                    FROM quotes
                    WHERE symbol = %s
                      AND exchange_timestamp >= %s
                    ORDER BY exchange_timestamp DESC
                """, (symbol, cutoff_date))
                
                results = cursor.fetchall()
            
            quotes = [
                Quote(
                    symbol=row['symbol'],
                    price=Decimal(str(row['price'])),
                    exchange_timestamp=row['exchange_timestamp'],
                    received_timestamp=row['received_timestamp'],
                    bid=Decimal(str(row['bid'])) if row['bid'] else Decimal('0'),
                    ask=Decimal(str(row['ask'])) if row['ask'] else Decimal('0'),
                    volume=row['volume']
                )
                for row in results
            ]
            
            logger.debug(f"Retrieved {len(quotes)} quote history records for {symbol}")
            return quotes
        except Exception as e:
            logger.error(f"Failed to retrieve quote history for {symbol}: {e}")
            return []
    
    def close(self) -> None:
        """Close database connections"""
        try:
            if self.redis_client:
                self.redis_client.close()
                logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
        
        try:
            if self.pg_conn:
                self.pg_conn.close()
                logger.info("PostgreSQL connection closed")
        except Exception as e:
            logger.error(f"Error closing PostgreSQL connection: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
