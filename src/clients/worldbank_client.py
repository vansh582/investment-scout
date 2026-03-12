"""
World Bank API Client for Investment Scout

Free tier: Unlimited requests (no API key required)
Provides global economic data and development indicators.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict
from decimal import Decimal
import requests

from src.clients.base_api_client import BaseAPIClient


logger = logging.getLogger(__name__)


class WorldBankClient(BaseAPIClient):
    """
    World Bank client for global economic data.
    
    Free tier: Unlimited requests (no API key required)
    """
    
    def __init__(self):
        super().__init__(
            name="WorldBank",
            requests_per_minute=60,  # Self-imposed reasonable limit
            failure_threshold=5,
            circuit_timeout=60
        )
        self.base_url = "https://api.worldbank.org/v2"
    
    def get_indicator_data(
        self,
        country_code: str,
        indicator_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> List[Dict]:
        """
        Get indicator data for a country.
        
        Args:
            country_code: ISO country code (e.g., "US", "CN", "GB")
            indicator_code: World Bank indicator code (e.g., "NY.GDP.MKTP.CD")
            start_year: Start year
            end_year: End year
            
        Returns:
            List of data points with year and value
        """
        def _fetch():
            params = {
                'format': 'json',
                'per_page': 1000
            }
            
            if start_year:
                params['date'] = f"{start_year}:{end_year or datetime.now().year}"
            
            url = f"{self.base_url}/country/{country_code}/indicator/{indicator_code}"
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # World Bank API returns [metadata, data]
            if not isinstance(data, list) or len(data) < 2:
                raise ValueError("Invalid World Bank API response")
            
            results = []
            for item in data[1]:
                try:
                    value = item.get('value')
                    if value is None:
                        continue
                    
                    results.append({
                        'year': int(item.get('date', 0)),
                        'value': Decimal(str(value)),
                        'country': item.get('country', {}).get('value', country_code),
                        'indicator': item.get('indicator', {}).get('value', indicator_code)
                    })
                except Exception as e:
                    logger.warning(f"Error parsing World Bank data point: {e}")
                    continue
            
            logger.info(
                f"Retrieved {len(results)} data points for {indicator_code} "
                f"from World Bank"
            )
            return results
        
        try:
            return self.call_with_retry(_fetch)
        except Exception as e:
            logger.error(
                f"Failed to get indicator {indicator_code} for {country_code} "
                f"from World Bank: {e}"
            )
            return []
    
    def get_gdp(self, country_code: str, start_year: Optional[int] = None) -> List[Dict]:
        """Get GDP data for a country"""
        return self.get_indicator_data(
            country_code,
            'NY.GDP.MKTP.CD',  # GDP (current US$)
            start_year=start_year
        )
    
    def get_gdp_growth(self, country_code: str, start_year: Optional[int] = None) -> List[Dict]:
        """Get GDP growth rate for a country"""
        return self.get_indicator_data(
            country_code,
            'NY.GDP.MKTP.KD.ZG',  # GDP growth (annual %)
            start_year=start_year
        )
    
    def get_inflation(self, country_code: str, start_year: Optional[int] = None) -> List[Dict]:
        """Get inflation rate for a country"""
        return self.get_indicator_data(
            country_code,
            'FP.CPI.TOTL.ZG',  # Inflation, consumer prices (annual %)
            start_year=start_year
        )
    
    def get_unemployment(self, country_code: str, start_year: Optional[int] = None) -> List[Dict]:
        """Get unemployment rate for a country"""
        return self.get_indicator_data(
            country_code,
            'SL.UEM.TOTL.ZS',  # Unemployment, total (% of total labor force)
            start_year=start_year
        )
    
    def get_trade_balance(self, country_code: str, start_year: Optional[int] = None) -> List[Dict]:
        """Get trade balance for a country"""
        return self.get_indicator_data(
            country_code,
            'NE.RSB.GNFS.CD',  # External balance on goods and services (current US$)
            start_year=start_year
        )
