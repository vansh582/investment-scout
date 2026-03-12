"""yfinance client for primary market data (free, unlimited)"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict
import yfinance as yf
import pandas as pd

from ..models import Quote, FinancialData


logger = logging.getLogger(__name__)


class YFinanceClient:
    """Client for Yahoo Finance data via yfinance library"""
    
    def __init__(self):
        """Initialize yfinance client"""
        pass
    
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """
        Get current quote for a symbol
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            Quote object or None if error
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or 'regularMarketPrice' not in info:
                logger.warning(f"No quote data available for {symbol}")
                return None
            
            # Get current price
            price = Decimal(str(info.get('regularMarketPrice', 0)))
            bid = Decimal(str(info.get('bid', price)))
            ask = Decimal(str(info.get('ask', price)))
            volume = info.get('volume', 0)
            
            # Timestamps
            received_timestamp = datetime.now()
            # Yahoo Finance doesn't provide exact exchange timestamp, use current time
            exchange_timestamp = received_timestamp
            
            quote = Quote(
                symbol=symbol,
                price=price,
                exchange_timestamp=exchange_timestamp,
                received_timestamp=received_timestamp,
                bid=bid,
                ask=ask,
                volume=volume
            )
            
            logger.debug(f"Retrieved quote for {symbol}: ${price}")
            return quote
        
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """
        Get historical price data
        
        Args:
            symbol: Stock ticker symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
        Returns:
            DataFrame with historical data or None if error
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                logger.warning(f"No historical data available for {symbol}")
                return None
            
            logger.debug(f"Retrieved {len(hist)} historical data points for {symbol}")
            return hist
        
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return None
    
    def get_financial_statements(self, symbol: str) -> Optional[FinancialData]:
        """
        Get financial statements and fundamental data
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            FinancialData object or None if error
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                logger.warning(f"No financial data available for {symbol}")
                return None
            
            # Extract financial metrics
            revenue = Decimal(str(info.get('totalRevenue', 0)))
            earnings = Decimal(str(info.get('netIncomeToCommon', 0)))
            pe_ratio = Decimal(str(info.get('trailingPE', 0)))
            debt_to_equity = Decimal(str(info.get('debtToEquity', 0)))
            free_cash_flow = Decimal(str(info.get('freeCashflow', 0)))
            roe = Decimal(str(info.get('returnOnEquity', 0)))
            
            financial_data = FinancialData(
                symbol=symbol,
                revenue=revenue,
                earnings=earnings,
                pe_ratio=pe_ratio,
                debt_to_equity=debt_to_equity,
                free_cash_flow=free_cash_flow,
                roe=roe,
                updated_at=datetime.now()
            )
            
            logger.debug(f"Retrieved financial data for {symbol}")
            return financial_data
        
        except Exception as e:
            logger.error(f"Error getting financial statements for {symbol}: {e}")
            return None
    
    def get_company_info(self, symbol: str) -> Optional[Dict]:
        """
        Get company information
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            Dictionary with company info or None if error
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                logger.warning(f"No company info available for {symbol}")
                return None
            
            company_info = {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'description': info.get('longBusinessSummary', ''),
                'website': info.get('website', ''),
                'market_cap': info.get('marketCap', 0),
                'average_volume': info.get('averageVolume', 0),
            }
            
            logger.debug(f"Retrieved company info for {symbol}")
            return company_info
        
        except Exception as e:
            logger.error(f"Error getting company info for {symbol}: {e}")
            return None
