"""
Investment Scout Data Models

Core data models for the Investment Scout system including Quote, FinancialData,
NewsArticle, GeopoliticalEvent, IndustryTrend, RealTimeProjection, InvestmentOpportunity,
TradingAlert, Newsletter, and PerformanceMetrics.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import List, Optional


class RiskLevel(Enum):
    """Risk level classification for investment opportunities"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SignalType(Enum):
    """Trading signal type"""
    BUY = "buy"
    SELL = "sell"


@dataclass
class Quote:
    """Real-time market price data with timestamp tracking"""
    symbol: str
    price: Decimal
    exchange_timestamp: datetime
    received_timestamp: datetime
    bid: Decimal
    ask: Decimal
    volume: int
    
    @property
    def latency(self) -> timedelta:
        """Calculate data latency as difference between receipt and exchange time"""
        return self.received_timestamp - self.exchange_timestamp
    
    @property
    def is_fresh(self) -> bool:
        """Validate data freshness - must be 30 seconds or less"""
        return self.latency.total_seconds() <= 30.0


@dataclass
class FinancialData:
    """Company financial data"""
    symbol: str
    revenue: Decimal
    earnings: Decimal
    pe_ratio: Decimal
    debt_to_equity: Decimal
    free_cash_flow: Decimal
    roe: Decimal
    updated_at: datetime


@dataclass
class NewsArticle:
    """News article with sentiment analysis"""
    title: str
    summary: str
    source: str
    published_at: datetime
    url: str
    sentiment: Optional[float] = None  # -1.0 to 1.0
    
    def __post_init__(self):
        """Validate sentiment score range"""
        if self.sentiment is not None:
            if not -1.0 <= self.sentiment <= 1.0:
                raise ValueError(f"Sentiment score must be between -1.0 and 1.0, got {self.sentiment}")


@dataclass
class GeopoliticalEvent:
    """Geopolitical event with impact analysis"""
    event_type: str  # 'election', 'policy', 'conflict', 'trade', 'sanction'
    title: str
    description: str
    affected_regions: List[str]
    affected_sectors: List[str]
    impact_score: float  # -1.0 to 1.0
    event_date: datetime
    
    def __post_init__(self):
        """Validate impact score range"""
        if not -1.0 <= self.impact_score <= 1.0:
            raise ValueError(f"Impact score must be between -1.0 and 1.0, got {self.impact_score}")


@dataclass
class IndustryTrend:
    """Industry trend analysis"""
    sector: str
    industry: str
    trend_type: str  # 'regulatory', 'technological', 'competitive', 'supply_chain'
    description: str
    impact_score: float
    affected_companies: List[str]
    timestamp: datetime


@dataclass
class RealTimeProjection:
    """Forward-looking projection with confidence intervals"""
    symbol: str
    projection_type: str  # 'revenue', 'earnings', 'price_target'
    projected_value: Decimal
    confidence_lower: Decimal
    confidence_upper: Decimal
    confidence_level: float  # 0.0 to 1.0
    projection_date: datetime
    
    def __post_init__(self):
        """Validate confidence interval ordering"""
        if not (self.confidence_lower <= self.projected_value <= self.confidence_upper):
            raise ValueError(
                f"Confidence interval invalid: {self.confidence_lower} <= "
                f"{self.projected_value} <= {self.confidence_upper}"
            )


@dataclass
class GlobalContext:
    """Global context for investment opportunities"""
    economic_factors: List[str]
    geopolitical_events: List[str]
    industry_dynamics: List[str]
    company_specifics: List[str]
    timing_rationale: str
    risk_factors: List[str]


@dataclass
class InvestmentOpportunity:
    """Long-term investment opportunity recommendation"""
    symbol: str
    company_name: str
    current_price: Decimal
    target_price: Decimal
    position_size_percent: Decimal  # 1-25%
    investment_thesis: str
    global_context: GlobalContext
    expected_return: Decimal
    risk_level: RiskLevel
    expected_holding_period: str
    data_timestamp: datetime
    
    def __post_init__(self):
        """Validate position size range"""
        if not (Decimal('1.0') <= self.position_size_percent <= Decimal('25.0')):
            raise ValueError(
                f"Position size must be between 1% and 25%, got {self.position_size_percent}%"
            )


@dataclass
class TradingAlert:
    """Short-term trading alert"""
    symbol: str
    company_name: str
    signal_type: SignalType
    current_price: Decimal
    entry_price: Decimal
    target_price: Decimal
    stop_loss: Decimal
    position_size_percent: Decimal
    rationale: str
    expected_holding_period: str
    data_timestamp: datetime
    
    def __post_init__(self):
        """Validate position size range"""
        if not (Decimal('1.0') <= self.position_size_percent <= Decimal('25.0')):
            raise ValueError(
                f"Position size must be between 1% and 25%, got {self.position_size_percent}%"
            )


@dataclass
class Newsletter:
    """Daily investment newsletter"""
    date: datetime
    market_overview: str
    opportunities: List[InvestmentOpportunity]
    performance_summary: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class PerformanceMetrics:
    """Portfolio performance metrics"""
    total_return_percent: Decimal
    annualized_return: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    win_rate: Decimal
    avg_gain_per_winner: Decimal
    loss_rate: Decimal
    avg_loss_per_loser: Decimal
    sp500_return_percent: Decimal
    relative_performance: Decimal
