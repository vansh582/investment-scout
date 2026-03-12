"""
Property-Based Tests for Investment Scout

Tests universal correctness properties using Hypothesis library.
Each property test runs 100+ iterations with generated test data.
"""

import json
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from hypothesis import given, strategies as st, settings
from src.models.investment_scout_models import (
    Quote, NewsArticle, GeopoliticalEvent, RealTimeProjection,
    InvestmentOpportunity, TradingAlert, GlobalContext, RiskLevel, SignalType
)


# Strategies for generating test data
symbols = st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=('Lu',)))
prices = st.decimals(min_value=Decimal('0.01'), max_value=Decimal('10000.00'), places=2)
volumes = st.integers(min_value=0, max_value=1000000000)
sentiments = st.floats(min_value=-1.0, max_value=1.0)
impact_scores = st.floats(min_value=-1.0, max_value=1.0)
position_sizes = st.decimals(min_value=Decimal('1.0'), max_value=Decimal('25.0'), places=2)


def generate_timestamp_pair(latency_seconds):
    """Generate exchange and received timestamps with specific latency"""
    received = datetime.now()
    exchange = received - timedelta(seconds=latency_seconds)
    return exchange, received


# Feature: investment-scout, Property 1: Data Timestamp Recording
@given(
    symbol=symbols,
    price=prices,
    volume=volumes
)
@settings(max_examples=100)
def test_property_1_data_timestamp_recording(symbol, price, volume):
    """
    Property 1: Data Timestamp Recording
    For any market data received, the Quote SHALL contain both valid 
    exchange_timestamp and received_timestamp.
    Validates: Requirements 1.4
    """
    exchange_ts, received_ts = generate_timestamp_pair(10)
    
    quote = Quote(
        symbol=symbol,
        price=price,
        exchange_timestamp=exchange_ts,
        received_timestamp=received_ts,
        bid=price - Decimal('0.01'),
        ask=price + Decimal('0.01'),
        volume=volume
    )
    
    # Property: Both timestamps must be present and valid
    assert quote.exchange_timestamp is not None
    assert quote.received_timestamp is not None
    assert isinstance(quote.exchange_timestamp, datetime)
    assert isinstance(quote.received_timestamp, datetime)


# Feature: investment-scout, Property 2: Latency Calculation Correctness
@given(
    symbol=symbols,
    price=prices,
    volume=volumes,
    latency_seconds=st.floats(min_value=0.0, max_value=120.0)
)
@settings(max_examples=100)
def test_property_2_latency_calculation_correctness(symbol, price, volume, latency_seconds):
    """
    Property 2: Latency Calculation Correctness
    For any Quote, the calculated latency SHALL equal the difference 
    between received_timestamp and exchange_timestamp.
    Validates: Requirements 1.5
    """
    exchange_ts, received_ts = generate_timestamp_pair(latency_seconds)
    
    quote = Quote(
        symbol=symbol,
        price=price,
        exchange_timestamp=exchange_ts,
        received_timestamp=received_ts,
        bid=price - Decimal('0.01'),
        ask=price + Decimal('0.01'),
        volume=volume
    )
    
    # Property: Latency must equal timestamp difference
    expected_latency = received_ts - exchange_ts
    assert quote.latency == expected_latency
    assert abs(quote.latency.total_seconds() - latency_seconds) < 0.1  # Allow small float precision error


# Feature: investment-scout, Property 3: Stale Data Flagging
@given(
    symbol=symbols,
    price=prices,
    volume=volumes,
    latency_seconds=st.floats(min_value=0.0, max_value=120.0)
)
@settings(max_examples=100)
def test_property_3_stale_data_flagging(symbol, price, volume, latency_seconds):
    """
    Property 3: Stale Data Flagging
    For any Quote where latency exceeds 30 seconds, is_fresh SHALL return False.
    For any Quote where latency is 30 seconds or less, is_fresh SHALL return True.
    Validates: Requirements 1.6
    """
    exchange_ts, received_ts = generate_timestamp_pair(latency_seconds)
    
    quote = Quote(
        symbol=symbol,
        price=price,
        exchange_timestamp=exchange_ts,
        received_timestamp=received_ts,
        bid=price - Decimal('0.01'),
        ask=price + Decimal('0.01'),
        volume=volume
    )
    
    # Property: is_fresh must correctly reflect 30-second threshold
    if latency_seconds > 30.0:
        assert not quote.is_fresh, f"Quote with {latency_seconds}s latency should be stale"
    else:
        assert quote.is_fresh, f"Quote with {latency_seconds}s latency should be fresh"


# Feature: investment-scout, Property 12: Sentiment Score Range
@given(
    sentiment=sentiments
)
@settings(max_examples=100)
def test_property_12_sentiment_score_range(sentiment):
    """
    Property 12: Sentiment Score Range
    For any news article, the sentiment score SHALL be between -1.0 and 1.0 inclusive.
    Validates: Requirements 8.9
    """
    article = NewsArticle(
        title="Test Article",
        summary="Test summary",
        source="Test Source",
        published_at=datetime.now(),
        url="https://example.com",
        sentiment=sentiment
    )
    
    # Property: Sentiment must be in valid range
    assert -1.0 <= article.sentiment <= 1.0


@given(
    invalid_sentiment=st.floats(min_value=-10.0, max_value=10.0).filter(
        lambda x: x < -1.0 or x > 1.0
    )
)
@settings(max_examples=100)
def test_property_12_sentiment_score_range_validation(invalid_sentiment):
    """Test that invalid sentiment scores are rejected"""
    with pytest.raises(ValueError, match="Sentiment score must be between -1.0 and 1.0"):
        NewsArticle(
            title="Test Article",
            summary="Test summary",
            source="Test Source",
            published_at=datetime.now(),
            url="https://example.com",
            sentiment=invalid_sentiment
        )


# Feature: investment-scout, Property 17: Geopolitical Impact Score Range
@given(
    impact_score=impact_scores
)
@settings(max_examples=100)
def test_property_17_geopolitical_impact_score_range(impact_score):
    """
    Property 17: Geopolitical Impact Score Range
    For any GeopoliticalEvent, the impact_score SHALL be between -1.0 and 1.0 inclusive.
    Validates: Requirements 13.4
    """
    event = GeopoliticalEvent(
        event_type="policy",
        title="Test Event",
        description="Test description",
        affected_regions=["US"],
        affected_sectors=["Technology"],
        impact_score=impact_score,
        event_date=datetime.now()
    )
    
    # Property: Impact score must be in valid range
    assert -1.0 <= event.impact_score <= 1.0


@given(
    invalid_impact=st.floats(min_value=-10.0, max_value=10.0).filter(
        lambda x: x < -1.0 or x > 1.0
    )
)
@settings(max_examples=100)
def test_property_17_geopolitical_impact_score_validation(invalid_impact):
    """Test that invalid impact scores are rejected"""
    with pytest.raises(ValueError, match="Impact score must be between -1.0 and 1.0"):
        GeopoliticalEvent(
            event_type="policy",
            title="Test Event",
            description="Test description",
            affected_regions=["US"],
            affected_sectors=["Technology"],
            impact_score=invalid_impact,
            event_date=datetime.now()
        )


# Feature: investment-scout, Property 18: Projection Confidence Intervals
@given(
    symbol=symbols,
    projected_value=prices,
    confidence_level=st.floats(min_value=0.0, max_value=1.0)
)
@settings(max_examples=100)
def test_property_18_projection_confidence_intervals(symbol, projected_value, confidence_level):
    """
    Property 18: Projection Confidence Intervals
    For any RealTimeProjection, confidence_lower <= projected_value <= confidence_upper.
    Validates: Requirements 15.4
    """
    # Generate valid confidence bounds
    margin = projected_value * Decimal('0.1')  # 10% margin
    confidence_lower = projected_value - margin
    confidence_upper = projected_value + margin
    
    projection = RealTimeProjection(
        symbol=symbol,
        projection_type="price_target",
        projected_value=projected_value,
        confidence_lower=confidence_lower,
        confidence_upper=confidence_upper,
        confidence_level=confidence_level,
        projection_date=datetime.now()
    )
    
    # Property: Confidence interval must contain projected value
    assert projection.confidence_lower <= projection.projected_value <= projection.confidence_upper


@given(
    symbol=symbols,
    projected_value=prices
)
@settings(max_examples=100)
def test_property_18_projection_confidence_intervals_validation(symbol, projected_value):
    """Test that invalid confidence intervals are rejected"""
    # Create invalid interval where projected_value is outside bounds
    confidence_lower = projected_value + Decimal('10.0')
    confidence_upper = projected_value + Decimal('20.0')
    
    with pytest.raises(ValueError, match="Confidence interval invalid"):
        RealTimeProjection(
            symbol=symbol,
            projection_type="price_target",
            projected_value=projected_value,
            confidence_lower=confidence_lower,
            confidence_upper=confidence_upper,
            confidence_level=0.95,
            projection_date=datetime.now()
        )


# Feature: investment-scout, Property 8: Position Size Range Constraint
@given(
    symbol=symbols,
    price=prices,
    position_size=position_sizes
)
@settings(max_examples=100)
def test_property_8_position_size_range_constraint_investment(symbol, price, position_size):
    """
    Property 8: Position Size Range Constraint (InvestmentOpportunity)
    For any InvestmentOpportunity, position_size SHALL be between 1% and 25% inclusive.
    Validates: Requirements 4.8
    """
    opportunity = InvestmentOpportunity(
        symbol=symbol,
        company_name="Test Company",
        current_price=price,
        target_price=price * Decimal('1.2'),
        position_size_percent=position_size,
        investment_thesis="Test thesis",
        global_context=GlobalContext(
            economic_factors=[],
            geopolitical_events=[],
            industry_dynamics=[],
            company_specifics=[],
            timing_rationale="Test",
            risk_factors=[]
        ),
        expected_return=Decimal('20.0'),
        risk_level=RiskLevel.MEDIUM,
        expected_holding_period="3-6 months",
        data_timestamp=datetime.now()
    )
    
    # Property: Position size must be in valid range
    assert Decimal('1.0') <= opportunity.position_size_percent <= Decimal('25.0')


@given(
    symbol=symbols,
    price=prices,
    position_size=position_sizes
)
@settings(max_examples=100)
def test_property_8_position_size_range_constraint_trading(symbol, price, position_size):
    """
    Property 8: Position Size Range Constraint (TradingAlert)
    For any TradingAlert, position_size SHALL be between 1% and 25% inclusive.
    Validates: Requirements 4.8
    """
    alert = TradingAlert(
        symbol=symbol,
        company_name="Test Company",
        signal_type=SignalType.BUY,
        current_price=price,
        entry_price=price,
        target_price=price * Decimal('1.1'),
        stop_loss=price * Decimal('0.95'),
        position_size_percent=position_size,
        rationale="Test rationale",
        expected_holding_period="1-3 days",
        data_timestamp=datetime.now()
    )
    
    # Property: Position size must be in valid range
    assert Decimal('1.0') <= alert.position_size_percent <= Decimal('25.0')


@given(
    symbol=symbols,
    price=prices,
    invalid_position_size=st.decimals(min_value=Decimal('0.0'), max_value=Decimal('100.0'), places=2).filter(
        lambda x: x < Decimal('1.0') or x > Decimal('25.0')
    )
)
@settings(max_examples=100)
def test_property_8_position_size_validation(symbol, price, invalid_position_size):
    """Test that invalid position sizes are rejected"""
    with pytest.raises(ValueError, match="Position size must be between 1% and 25%"):
        InvestmentOpportunity(
            symbol=symbol,
            company_name="Test Company",
            current_price=price,
            target_price=price * Decimal('1.2'),
            position_size_percent=invalid_position_size,
            investment_thesis="Test thesis",
            global_context=GlobalContext(
                economic_factors=[],
                geopolitical_events=[],
                industry_dynamics=[],
                company_specifics=[],
                timing_rationale="Test",
                risk_factors=[]
            ),
            expected_return=Decimal('20.0'),
            risk_level=RiskLevel.MEDIUM,
            expected_holding_period="3-6 months",
            data_timestamp=datetime.now()
        )



# Additional imports for Data Manager tests
from unittest.mock import Mock, patch, MagicMock
from src.utils.data_manager_scout import DataManager


# Feature: investment-scout, Property 5: Dual TTL Caching Strategy
@given(
    symbol=symbols,
    price=prices,
    volume=volumes,
    is_active=st.booleans()
)
@settings(max_examples=100)
def test_property_5_dual_ttl_caching_strategy(symbol, price, volume, is_active):
    """
    Property 5: Dual TTL Caching Strategy
    For any cached Quote, if Active_Stock then TTL=15s, if Watchlist_Stock then TTL=60s.
    Validates: Requirements 1.8, 7.2, 7.3
    """
    exchange_ts, received_ts = generate_timestamp_pair(5)
    
    quote = Quote(
        symbol=symbol,
        price=price,
        exchange_timestamp=exchange_ts,
        received_timestamp=received_ts,
        bid=price - Decimal('0.01'),
        ask=price + Decimal('0.01'),
        volume=volume
    )
    
    # Mock Redis client
    with patch('src.utils.data_manager_scout.redis.from_url') as mock_redis:
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client
        
        # Mock PostgreSQL pool
        with patch('src.utils.data_manager_scout.SimpleConnectionPool') as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool.return_value = mock_pool_instance
            
            # Mock connection for schema creation
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value.__exit__.return_value = None
            mock_pool_instance.getconn.return_value = mock_conn
            
            dm = DataManager("redis://localhost", "postgresql://localhost")
            dm.cache_quote(symbol, quote, is_active=is_active)
            
            # Property: TTL must match stock type
            expected_ttl = DataManager.ACTIVE_TTL if is_active else DataManager.WATCHLIST_TTL
            
            # Verify setex was called with correct TTL
            assert mock_redis_client.setex.called
            call_args = mock_redis_client.setex.call_args
            actual_ttl = call_args[0][1]  # Second argument is TTL
            
            assert actual_ttl == expected_ttl, f"Expected TTL {expected_ttl}s, got {actual_ttl}s"


# Feature: investment-scout, Property 11: Cache Freshness Validation
@given(
    symbol=symbols,
    price=prices,
    volume=volumes,
    latency_seconds=st.floats(min_value=0.0, max_value=120.0)
)
@settings(max_examples=100)
def test_property_11_cache_freshness_validation(symbol, price, volume, latency_seconds):
    """
    Property 11: Cache Freshness Validation
    For any cached data retrieval, if TTL exceeded, Data_Manager SHALL NOT return cached data.
    Validates: Requirements 7.6
    """
    exchange_ts, received_ts = generate_timestamp_pair(latency_seconds)
    
    quote = Quote(
        symbol=symbol,
        price=price,
        exchange_timestamp=exchange_ts,
        received_timestamp=received_ts,
        bid=price - Decimal('0.01'),
        ask=price + Decimal('0.01'),
        volume=volume
    )
    
    # Mock Redis client
    with patch('src.utils.data_manager_scout.redis.from_url') as mock_redis:
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client
        
        # Mock PostgreSQL pool
        with patch('src.utils.data_manager_scout.SimpleConnectionPool') as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool.return_value = mock_pool_instance
            
            # Mock connection for schema creation
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value.__exit__.return_value = None
            mock_pool_instance.getconn.return_value = mock_conn
            
            dm = DataManager("redis://localhost", "postgresql://localhost")
            
            # Simulate cached data
            cached_data = {
                "symbol": quote.symbol,
                "price": str(quote.price),
                "bid": str(quote.bid),
                "ask": str(quote.ask),
                "volume": quote.volume,
                "exchange_timestamp": quote.exchange_timestamp.isoformat(),
                "received_timestamp": quote.received_timestamp.isoformat()
            }
            mock_redis_client.get.return_value = json.dumps(cached_data)
            
            result = dm.get_cached_quote(symbol)
            
            # Property: Stale cached data must not be returned
            if latency_seconds > 30.0:
                # Stale data should be rejected and cache deleted
                assert result is None, f"Stale cached data (latency {latency_seconds}s) should not be returned"
                assert mock_redis_client.delete.called, "Stale cache should be deleted"
            else:
                # Fresh data should be returned
                assert result is not None, f"Fresh cached data (latency {latency_seconds}s) should be returned"
                assert result.symbol == symbol



# Additional imports for API client tests
import time
from src.clients.base_api_client import CircuitBreaker, RateLimiter, CircuitBreakerOpenError


# Feature: investment-scout, Property 6: Rate Limit Compliance
def test_property_6_rate_limit_compliance():
    """
    Property 6: Rate Limit Compliance
    For any API_Client over any time window, requests SHALL NOT exceed free tier rate limit.
    Validates: Requirements 2.5
    """
    # Test with 60 requests per minute limit
    rate_limiter = RateLimiter(requests_per_minute=60)
    
    # Property: Should allow up to rate limit
    successful_requests = 0
    for i in range(60):
        if rate_limiter.acquire():
            successful_requests += 1
    
    assert successful_requests == 60, "Should allow exactly rate limit requests"
    
    # Property: Should block additional requests
    assert not rate_limiter.acquire(), "Should block request exceeding rate limit"


# Feature: investment-scout, Property 10: Retry with Exponential Backoff
def test_property_10_retry_with_exponential_backoff():
    """
    Property 10: Retry with Exponential Backoff
    For any failed operation, system SHALL retry exactly 3 times with exponential backoff.
    Validates: Requirements 6.5, 10.1
    """
    from src.clients.base_api_client import BaseAPIClient
    
    client = BaseAPIClient("TestClient", requests_per_minute=60)
    
    attempt_count = 0
    attempt_times = []
    
    def failing_function():
        nonlocal attempt_count
        attempt_count += 1
        attempt_times.append(time.time())
        raise ValueError("Test failure")
    
    # Property: Should retry exactly 3 times (4 total attempts: 1 initial + 3 retries)
    try:
        client.call_with_retry(failing_function, max_retries=3, backoff_base=0.1)
    except ValueError:
        pass
    
    assert attempt_count == 4, f"Should attempt 4 times (1 + 3 retries), got {attempt_count}"
    
    # Property: Delays should follow exponential backoff pattern (approximately)
    if len(attempt_times) >= 3:
        delay1 = attempt_times[1] - attempt_times[0]
        delay2 = attempt_times[2] - attempt_times[1]
        delay3 = attempt_times[3] - attempt_times[2]
        
        # With backoff_base=0.1: delays should be ~0.1s, ~0.3s, ~0.9s
        assert 0.05 < delay1 < 0.2, f"First delay should be ~0.1s, got {delay1:.2f}s"
        assert 0.2 < delay2 < 0.5, f"Second delay should be ~0.3s, got {delay2:.2f}s"
        assert 0.7 < delay3 < 1.2, f"Third delay should be ~0.9s, got {delay3:.2f}s"


# Feature: investment-scout, Property 13: Rate Limit Error Handling
def test_property_13_rate_limit_error_handling():
    """
    Property 13: Rate Limit Error Handling
    For any API_Client encountering rate limit error, SHALL wait until reset time before retrying.
    Validates: Requirements 10.2
    """
    from src.clients.base_api_client import BaseAPIClient
    from datetime import datetime, timedelta
    
    client = BaseAPIClient("TestClient", requests_per_minute=60)
    
    # Property: Should wait until reset time
    reset_time = datetime.now() + timedelta(seconds=0.5)
    start_time = time.time()
    
    client.handle_rate_limit_error(reset_time)
    
    elapsed = time.time() - start_time
    
    # Should have waited approximately 0.5 seconds
    assert 0.4 < elapsed < 0.7, f"Should wait ~0.5s for rate limit reset, waited {elapsed:.2f}s"


# Feature: investment-scout, Property 23: API Failover Chain
def test_property_23_api_failover_chain():
    """
    Property 23: API Failover Chain
    For any data request where primary source unavailable, SHALL fall back to next source.
    Validates: Requirements 19.6
    """
    # This property is tested at integration level with Market Monitor
    # Here we test the circuit breaker mechanism that enables failover
    
    circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=1)
    
    def failing_function():
        raise ValueError("Service unavailable")
    
    # Property: Circuit should open after threshold failures
    for i in range(3):
        try:
            circuit_breaker.call(failing_function)
        except ValueError:
            pass
    
    # Circuit should now be OPEN
    from src.clients.base_api_client import CircuitState
    assert circuit_breaker.state == CircuitState.OPEN, "Circuit should be OPEN after threshold failures"
    
    # Property: Should reject requests when circuit is OPEN
    try:
        circuit_breaker.call(failing_function)
        assert False, "Should raise CircuitBreakerOpenError"
    except CircuitBreakerOpenError:
        pass  # Expected



# Additional imports for Performance Tracker tests
from src.utils.performance_tracker import PerformanceTracker


# Feature: investment-scout, Property 20: Performance Tracking Completeness
@given(
    symbol=symbols,
    price=prices,
    position_size=position_sizes
)
@settings(max_examples=100)
def test_property_20_performance_tracking_completeness(symbol, price, position_size):
    """
    Property 20: Performance Tracking Completeness
    For any InvestmentOpportunity recommended, PerformanceTracker SHALL create
    a tracking record with entry_price, entry_date, and status.
    Validates: Requirements 17.1
    """
    opportunity = InvestmentOpportunity(
        symbol=symbol,
        company_name="Test Company",
        current_price=price,
        target_price=price * Decimal('1.2'),
        position_size_percent=position_size,
        investment_thesis="Test thesis",
        global_context=GlobalContext(
            economic_factors=[],
            geopolitical_events=[],
            industry_dynamics=[],
            company_specifics=[],
            timing_rationale="Test",
            risk_factors=[]
        ),
        expected_return=Decimal('20.0'),
        risk_level=RiskLevel.MEDIUM,
        expected_holding_period="3-6 months",
        data_timestamp=datetime.now()
    )
    
    # Mock PostgreSQL pool
    with patch('src.utils.performance_tracker.SimpleConnectionPool') as mock_pool:
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance
        
        # Mock connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_pool_instance.getconn.return_value = mock_conn
        
        tracker = PerformanceTracker("postgresql://localhost")
        tracker.track_recommendation(opportunity)
        
        # Property: Must insert tracking record with required fields
        assert mock_cursor.execute.called
        call_args = mock_cursor.execute.call_args[0]
        
        # Verify INSERT statement
        assert 'INSERT INTO recommendations' in call_args[0]
        
        # Verify required fields are present
        values = call_args[1]
        assert values[0] == symbol  # symbol
        assert values[1] == 'investment'  # recommendation_type
        assert values[2] == price  # entry_price
        assert values[3] == opportunity.data_timestamp  # entry_date
        assert values[4] == position_size  # position_size_percent
        assert values[6] == 'open'  # status


# Feature: investment-scout, Property 21: Portfolio Return Calculation
@given(
    num_positions=st.integers(min_value=1, max_value=10),
    seed=st.integers(min_value=0, max_value=1000000)
)
@settings(max_examples=100)
def test_property_21_portfolio_return_calculation(num_positions, seed):
    """
    Property 21: Portfolio Return Calculation
    For any set of tracked recommendations, calculated cumulative portfolio return
    SHALL equal weighted sum of individual returns based on Position_Size percentages.
    Validates: Requirements 17.2
    """
    import random
    random.seed(seed)
    
    # Generate random positions
    positions = []
    expected_total_return = Decimal('0')
    
    for i in range(num_positions):
        return_pct = Decimal(str(random.uniform(-50.0, 100.0)))
        position_size = Decimal(str(random.uniform(1.0, 25.0)))
        
        weighted_return = (return_pct * position_size) / Decimal('100')
        expected_total_return += weighted_return
        
        positions.append({
            'symbol': f'SYM{i}',
            'entry_price': Decimal('100.00'),
            'entry_date': datetime.now() - timedelta(days=30),
            'exit_price': Decimal('100.00') * (Decimal('1') + return_pct / Decimal('100')),
            'exit_date': datetime.now(),
            'position_size_percent': position_size,
            'return_percent': return_pct,
            'status': 'closed'
        })
    
    # Mock PostgreSQL pool
    with patch('src.utils.performance_tracker.SimpleConnectionPool') as mock_pool:
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance
        
        # Mock connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_pool_instance.getconn.return_value = mock_conn
        
        # Mock fetchall to return our positions
        mock_cursor.fetchall.return_value = positions
        
        tracker = PerformanceTracker("postgresql://localhost")
        metrics = tracker.calculate_returns()
        
        # Property: Total return must equal weighted sum
        actual_total_return = metrics['total_return_percent']
        
        # Allow small floating point precision error
        assert abs(actual_total_return - expected_total_return) < Decimal('0.01'), \
            f"Expected {expected_total_return}, got {actual_total_return}"


# Additional imports for Market Monitor tests
from src.utils.market_monitor import MarketMonitor


# Feature: investment-scout, Property 4: Fresh Data Usage in Analysis
@given(
    symbol=symbols,
    price=prices,
    volume=volumes,
    latency_seconds=st.floats(min_value=0.0, max_value=120.0)
)
@settings(max_examples=100)
def test_property_4_fresh_data_usage_in_analysis(symbol, price, volume, latency_seconds):
    """
    Property 4: Fresh Data Usage in Analysis
    For any analysis operation, all Quote data SHALL have is_fresh=True,
    and any Quote with is_fresh=False SHALL be rejected.
    Validates: Requirements 1.7, 4.5, 12.8
    """
    exchange_ts, received_ts = generate_timestamp_pair(latency_seconds)
    
    quote = Quote(
        symbol=symbol,
        price=price,
        exchange_timestamp=exchange_ts,
        received_timestamp=received_ts,
        bid=price - Decimal('0.01'),
        ask=price + Decimal('0.01'),
        volume=volume
    )
    
    # Mock dependencies
    mock_dm = Mock()
    mock_yf = Mock()
    mock_yf.get_quote.return_value = quote
    
    monitor = MarketMonitor(mock_dm, mock_yf)
    
    # Property: Market Monitor must validate freshness
    is_fresh = monitor.is_data_fresh(quote)
    
    if latency_seconds > 30.0:
        # Stale data must be rejected
        assert not is_fresh, f"Quote with {latency_seconds}s latency should be rejected"
        assert not quote.is_fresh
    else:
        # Fresh data must be accepted
        assert is_fresh, f"Quote with {latency_seconds}s latency should be accepted"
        assert quote.is_fresh
