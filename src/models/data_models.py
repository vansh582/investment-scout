"""Core data models and types for Investment Scout"""

from dataclasses import dataclass
from datetime import datetime, timedelta, date
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
    """Market quote with timestamp tracking"""
    symbol: str
    price: Decimal
    exchange_timestamp: datetime  # From exchange
    received_timestamp: datetime  # System receipt time
    bid: Decimal
    ask: Decimal
    volume: int
    
    @property
    def latency(self) -> timedelta:
        """Calculate data latency"""
        return self.received_timestamp - self.exchange_timestamp
    
    @property
    def is_fresh(self) -> bool:
        """Check if data is fresh (<30 seconds old)"""
        return self.latency.total_seconds() < 30.0


@dataclass
class Security:
    """Security information"""
    symbol: str
    name: str
    tradeable_on_robinhood: bool
    supports_fractional_shares: bool
    average_volume: int
    sector: str
    industry: str


@dataclass
class FinancialData:
    """Company financial data"""
    symbol: str
    revenue: Decimal
    earnings: Decimal
    pe_ratio: Decimal
    debt_to_equity: Decimal
    free_cash_flow: Decimal
    roe: Decimal  # Return on Equity
    updated_at: datetime


@dataclass
class NewsArticle:
    """News article with sentiment"""
    title: str
    summary: str
    source: str
    published_at: datetime
    url: str
    sentiment: Optional[float] = None  # -1.0 to 1.0


@dataclass
class GlobalContext:
    """Comprehensive global context for investment recommendations"""
    economic_factors: List[str]  # GDP growth, interest rates, inflation
    geopolitical_events: List[str]  # Trade policies, regulations, conflicts
    industry_dynamics: List[str]  # Sector trends, competitive landscape
    company_specifics: List[str]  # Recent news, earnings, product launches
    timing_rationale: str  # Why this opportunity is attractive RIGHT NOW
    risk_factors: List[str]  # Potential downsides and concerns
    
    def to_text(self) -> str:
        """Format global context for email display"""
        sections = []
        
        if self.economic_factors:
            sections.append("Economic Factors:\n" + "\n".join(f"- {f}" for f in self.economic_factors))
        
        if self.geopolitical_events:
            sections.append("Geopolitical Events:\n" + "\n".join(f"- {e}" for e in self.geopolitical_events))
        
        if self.industry_dynamics:
            sections.append("Industry Dynamics:\n" + "\n".join(f"- {d}" for d in self.industry_dynamics))
        
        if self.company_specifics:
            sections.append("Company Specifics:\n" + "\n".join(f"- {s}" for s in self.company_specifics))
        
        sections.append(f"Why Now:\n{self.timing_rationale}")
        
        if self.risk_factors:
            sections.append("Risk Factors:\n" + "\n".join(f"- {r}" for r in self.risk_factors))
        
        return "\n\n".join(sections)


@dataclass
class InvestmentOpportunity:
    """Long-term investment opportunity"""
    symbol: str
    company_name: str
    current_price: Decimal
    target_price: Decimal
    position_size_percent: Decimal  # 1-25%
    investment_thesis: str
    global_context: GlobalContext
    expected_return: Decimal
    risk_level: RiskLevel
    expected_holding_period: str  # "6-12 months", "1-2 years", etc.
    data_timestamp: datetime


@dataclass
class Newsletter:
    """Daily investment newsletter"""
    date: date
    market_overview: str
    opportunities: List[InvestmentOpportunity]
    generated_at: datetime
