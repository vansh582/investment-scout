"""Secure credential management for API keys and secrets"""

import os
from typing import Optional
from dotenv import load_dotenv


class CredentialManager:
    """Manages secure storage and retrieval of API credentials"""
    
    def __init__(self):
        """Initialize credential manager and load environment variables"""
        load_dotenv()
        self._credentials = {}
        self._load_credentials()
    
    def _load_credentials(self):
        """Load credentials from environment variables"""
        # Robinhood credentials
        self._credentials['robinhood_username'] = os.getenv('ROBINHOOD_USERNAME')
        self._credentials['robinhood_password'] = os.getenv('ROBINHOOD_PASSWORD')
        
        # API keys
        self._credentials['finnhub_api_key'] = os.getenv('FINNHUB_API_KEY')
        self._credentials['twelve_data_api_key'] = os.getenv('TWELVE_DATA_API_KEY')
        self._credentials['sendgrid_api_key'] = os.getenv('SENDGRID_API_KEY')
        
        # Email configuration
        self._credentials['user_email'] = os.getenv('USER_EMAIL')
        
        # Database URLs
        self._credentials['database_url'] = os.getenv('DATABASE_URL')
        self._credentials['redis_url'] = os.getenv('REDIS_URL')
    
    def get_credential(self, service: str) -> Optional[str]:
        """
        Get credential for a specific service
        
        Args:
            service: Service name (e.g., 'finnhub_api_key', 'robinhood_username')
        
        Returns:
            Credential value or None if not found
        """
        return self._credentials.get(service)
    
    def validate_credential(self, service: str) -> bool:
        """
        Validate that a credential exists and is not empty
        
        Args:
            service: Service name to validate
        
        Returns:
            True if credential exists and is not empty, False otherwise
        """
        credential = self.get_credential(service)
        return credential is not None and len(credential.strip()) > 0
    
    def validate_all_required(self) -> tuple[bool, list[str]]:
        """
        Validate all required credentials are present
        
        Returns:
            Tuple of (all_valid, missing_credentials)
        """
        required_credentials = [
            'robinhood_username',
            'robinhood_password',
            'finnhub_api_key',
            'twelve_data_api_key',
            'sendgrid_api_key',
            'user_email',
            'database_url',
            'redis_url',
        ]
        
        missing = []
        for cred in required_credentials:
            if not self.validate_credential(cred):
                missing.append(cred)
        
        return len(missing) == 0, missing
    
    def rotate_credential(self, service: str, new_credential: str):
        """
        Rotate a credential (update with new value)
        
        Args:
            service: Service name
            new_credential: New credential value
        
        Note:
            This updates the in-memory credential only.
            For persistent rotation, update the .env file or secrets manager.
        """
        self._credentials[service] = new_credential


# Global credential manager instance
credential_manager = CredentialManager()
