"""
Base API Client with Circuit Breaker Pattern

Provides rate limiting, retry logic with exponential backoff, and circuit breaker
pattern for resilient API communication.
"""

import time
import logging
from typing import Optional, Callable, Any
from datetime import datetime, timedelta
from enum import Enum


logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for API resilience.
    
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: After timeout, allow one request to test recovery
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from function
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker entering HALF_OPEN state")
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. Last failure: {self.last_failure_time}"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return (datetime.now() - self.last_failure_time).total_seconds() > self.timeout
    
    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Circuit breaker recovered, returning to CLOSED state")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                logger.warning(
                    f"Circuit breaker OPENED after {self.failure_count} failures"
                )
                self.state = CircuitState.OPEN


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class RateLimiter:
    """
    Token bucket rate limiter for API request throttling.
    """
    
    def __init__(self, requests_per_minute: int):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests allowed per minute
        """
        self.requests_per_minute = requests_per_minute
        self.tokens = requests_per_minute
        self.last_refill = datetime.now()
        self.min_interval = 60.0 / requests_per_minute  # Seconds between requests
    
    def acquire(self) -> bool:
        """
        Attempt to acquire a token for making a request.
        
        Returns:
            True if token acquired, False if rate limit reached
        """
        self._refill_tokens()
        
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
    
    def wait_if_needed(self):
        """Block until a token is available"""
        while not self.acquire():
            time.sleep(0.1)  # Wait 100ms before checking again
    
    def _refill_tokens(self):
        """Refill tokens based on elapsed time"""
        now = datetime.now()
        elapsed = (now - self.last_refill).total_seconds()
        
        # Add tokens based on elapsed time
        tokens_to_add = elapsed * (self.requests_per_minute / 60.0)
        self.tokens = min(self.requests_per_minute, self.tokens + tokens_to_add)
        self.last_refill = now


class BaseAPIClient:
    """
    Base class for API clients with rate limiting, retry logic, and circuit breaker.
    """
    
    def __init__(
        self,
        name: str,
        requests_per_minute: int,
        failure_threshold: int = 5,
        circuit_timeout: int = 60
    ):
        """
        Initialize base API client.
        
        Args:
            name: Client name for logging
            requests_per_minute: Rate limit
            failure_threshold: Circuit breaker failure threshold
            circuit_timeout: Circuit breaker timeout in seconds
        """
        self.name = name
        self.rate_limiter = RateLimiter(requests_per_minute)
        self.circuit_breaker = CircuitBreaker(failure_threshold, circuit_timeout)
        logger.info(f"Initialized {name} client with {requests_per_minute} req/min limit")
    
    def call_with_retry(
        self,
        func: Callable,
        *args,
        max_retries: int = 3,
        backoff_base: float = 1.0,
        **kwargs
    ) -> Any:
        """
        Call function with exponential backoff retry logic.
        
        Retry delays: 1s, 3s, 9s (exponential backoff)
        
        Args:
            func: Function to call
            *args: Positional arguments
            max_retries: Maximum retry attempts
            backoff_base: Base delay for exponential backoff
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                # Wait for rate limit
                self.rate_limiter.wait_if_needed()
                
                # Execute with circuit breaker protection
                result = self.circuit_breaker.call(func, *args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"{self.name}: Request succeeded on attempt {attempt + 1}")
                
                return result
                
            except CircuitBreakerOpenError as e:
                logger.error(f"{self.name}: Circuit breaker is open, skipping retries")
                raise
                
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries:
                    delay = backoff_base * (3 ** attempt)  # 1s, 3s, 9s
                    logger.warning(
                        f"{self.name}: Request failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {delay}s: {str(e)}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"{self.name}: Request failed after {max_retries + 1} attempts: {str(e)}"
                    )
        
        raise last_exception
    
    def handle_rate_limit_error(self, reset_time: Optional[datetime] = None):
        """
        Handle rate limit error by waiting until reset time.
        
        Args:
            reset_time: When rate limit resets (if known)
        """
        if reset_time:
            wait_seconds = (reset_time - datetime.now()).total_seconds()
            if wait_seconds > 0:
                logger.warning(
                    f"{self.name}: Rate limit hit, waiting {wait_seconds:.0f}s until reset"
                )
                time.sleep(wait_seconds)
        else:
            # Default wait if reset time unknown
            logger.warning(f"{self.name}: Rate limit hit, waiting 60s")
            time.sleep(60)
