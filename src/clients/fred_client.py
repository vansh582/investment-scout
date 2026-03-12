"""
FRED (Federal Reserve Economic Data) API Client for Investment Scout

Free tier: Unlimited requests with API key
Provides economic indicators from the Federal Reserve.
"""

import logging
from datetime import datetime, date
from typing import List, Optional, Dict
from decimal import Decimal
import requests

from src.clients.base_api_client import BaseAPIClient


logger = logging.getLogger(__name__)


class FREDClient(BaseAPIClient):
    """
    FRED client for economic indicators.
    
    Free tier: Unlimited requests (with reasonable rate limiting)
    """
    
    def __init__(self, api_key: str):
        super().__init__(
            name="FRED",
            requests_per_minute=60,  # Self-imposed reasonable limit
            failure_threshold=5,
            circuit_timeout=60
        )
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred"
    
    def get_series_observations(
        self,
        series_id: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Get observations for an economic data series.
        
        Args:
            series_id: FRED series ID (e.g., "GDP", "UNRATE", "DFF")
            from_date: Start date
            to_date: End date
            limit: Maximum number of observations
            
        Returns:
            List of observations with date and value
        """
        def _fetch():
            params = {
                'series_id': series_id,
                'api_key': self.api_key,
                'file_type': 'json',
                'limit': limit
            }
            
            if from_date:
                params['observation_start'] = from_date.isoformat()
            if to_date:
                params['observation_end'] = to_date.isoformat()
            
            response = requests.get(
                f"{self.base_url}/series/observations",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'error_message' in data:
                raise ValueError(f"FRED error: {data['error_message']}")
            
            observations = []
            for obs in data.get('observations', []):
                try:
                    value_str = obs.get('value', '.')
                    if value_str == '.':
                        # Missing data
                        continue
                    
                    observations.append({
                        'date': datetime.strptime(obs['date'], '%Y-%m-%d').date(),
                        'value': Decimal(value_str),
                        'series_id': series_id
                    })
                except Exception as e:
                    logger.warning(f"Error parsing FRED observation: {e}")
                    continue
            
            logger.info(f"Retrieved {len(observations)} observations for {series_id} from FRED")
            return observations
        
        try:
            return self.call_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Failed to get series {series_id} from FRED: {e}")
            return []
    
    def get_gdp(self, from_date: Optional[date] = None) -> List[Dict]:
        """Get GDP data"""
        return self.get_series_observations('GDP', from_date=from_date)
    
    def get_unemployment_rate(self, from_date: Optional[date] = None) -> List[Dict]:
        """Get unemployment rate data"""
        return self.get_series_observations('UNRATE', from_date=from_date)
    
    def get_federal_funds_rate(self, from_date: Optional[date] = None) -> List[Dict]:
        """Get federal funds rate data"""
        return self.get_series_observations('DFF', from_date=from_date)
    
    def get_inflation_rate(self, from_date: Optional[date] = None) -> List[Dict]:
        """Get CPI inflation rate data"""
        return self.get_series_observations('CPIAUCSL', from_date=from_date)
    
    def get_series_info(self, series_id: str) -> Optional[Dict]:
        """
        Get metadata about a data series.
        
        Args:
            series_id: FRED series ID
            
        Returns:
            Dictionary with series metadata
        """
        def _fetch():
            params = {
                'series_id': series_id,
                'api_key': self.api_key,
                'file_type': 'json'
            }
            
            response = requests.get(
                f"{self.base_url}/series",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'error_message' in data:
                raise ValueError(f"FRED error: {data['error_message']}")
            
            series_list = data.get('seriess', [])
            if series_list:
                return series_list[0]
            return None
        
        try:
            return self.call_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Failed to get series info for {series_id} from FRED: {e}")
            return None
