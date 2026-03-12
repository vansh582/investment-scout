"""
YFinance API Client for Investment Scout

Primary data source for market quotes and financial data.
Free tier with unlimited requests.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
import yfinance as yf

from src.clients.base_api_client import BaseAPIClient
from src.models.investment_scout_models import Quote, FinancialData


logger = logging.getLogger(__name__)


class YFinanceClient(BaseAPIClient):
    """
    YFinance client for market data and company financials.
    
    Primary data source with unlimited free tier.
    """
    
    def __init__(self):
        # YFinance has no official rate limit, but we'll be conservative
        super().__init__(
            name="YFinance",
            requests_per_minute=120,  # Conservative limit
            failure_threshold=5,
            circuit_timeout=60
        )
    
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """
        Get real-time quote for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            
        Returns:
            Quote object or None if failed
        """
        def _fetch():
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get current price data
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            bid = info.get('bid')
            ask = info.get('ask')
            volume = info.get('volume') or info.get('regularMarketVolume')
            
            if current_price is None:
                raise ValueError(f"No price data available for {symbol}")
            
            # YFinance doesn't provide exchange timestamp, use current time
            # This is a limitation but acceptable for free tier
            now = datetime.now()
            
            return Quote(
                symbol=symbol,
                price=Decimal(str(current_price)),
                bid=Decimal(str(bid)) if bid else Decimal(str(current_price)),
                ask=Decimal(str(ask)) if ask else Decimal(str(current_price)),
                volume=volume or 0,
                exchange_timestamp=now,  # Approximation
                received_timestamp=now
            )
        
        try:
            return self.call_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol} from YFinance: {e}")
            return None
    
    def get_financial_data(self, symbol: str) -> Optional[FinancialData]:
        """
        Get company financial data.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            FinancialData object or None if failed
        """
        def _fetch():
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extract financial metrics
            revenue = info.get('totalRevenue')
            earnings = info.get('netIncomeToCommon')
            pe_ratio = info.get('trailingPE')
            debt_to_equity = info.get('debtToEquity')
            free_cash_flow = info.get('freeCashflow')
            roe = info.get('returnOnEquity')
            
            # Validate we have at least some data
            if not any([revenue, earnings, pe_ratio]):
                raise ValueError(f"Insufficient financial data for {symbol}")
            
            return FinancialData(
                symbol=symbol,
                revenue=Decimal(str(revenue)) if revenue else Decimal('0'),
                earnings=Decimal(str(earnings)) if earnings else Decimal('0'),
                pe_ratio=Decimal(str(pe_ratio)) if pe_ratio else Decimal('0'),
                debt_to_equity=Decimal(str(debt_to_equity)) if debt_to_equity else Decimal('0'),
                free_cash_flow=Decimal(str(free_cash_flow)) if free_cash_flow else Decimal('0'),
                roe=Decimal(str(roe)) if roe else Decimal('0'),
                updated_at=datetime.now()
            )
        
        try:
            return self.call_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Failed to get financial data for {symbol} from YFinance: {e}")
            return None
    
    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get general company information.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with company info or None if failed
        """
        def _fetch():
            ticker = yf.Ticker(symbol)
            return ticker.info
        
        try:
            return self.call_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Failed to get company info for {symbol} from YFinance: {e}")
            return None
