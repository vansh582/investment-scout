"""Configuration management for Investment Scout system"""

import os
from dataclasses import dataclass
from datetime import time
from decimal import Decimal
from typing import List, Optional
from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing"""
    pass


@dataclass
class CacheTTLConfig:
    """Cache TTL configuration"""
    active_stock_ttl: int  # seconds
    watchlist_stock_ttl: int  # seconds
    robinhood_tradeability_ttl: int  # seconds
    company_info_ttl: int  # seconds
    financial_data_ttl: int  # seconds


@dataclass
class PositionSizingConfig:
    """Position sizing parameters"""
    low_risk_min: Decimal
    low_risk_max: Decimal
    medium_risk_min: Decimal
    medium_risk_max: Decimal
    high_risk_min: Decimal
    high_risk_max: Decimal


@dataclass
class AlertLimitsConfig:
    """Alert frequency limits"""
    max_trading_alerts_per_day: int
    alert_generation_timeout_seconds: int
    alert_delivery_timeout_seconds: int


class ConfigurationManager:
    """Manages all system configuration from environment variables"""
    
    def __init__(self):
        """Initialize configuration manager and load environment variables"""
        load_dotenv()
        self._config = {}
        self._load_configuration()
    
    def _load_configuration(self):
        """Load all configuration from environment variables"""
        # Database URLs
        self._config['redis_url'] = os.getenv('REDIS_URL')
        self._config['database_url'] = os.getenv('DATABASE_URL')
        
        # API Credentials
        self._config['robinhood_username'] = os.getenv('ROBINHOOD_USERNAME')
        self._config['robinhood_password'] = os.getenv('ROBINHOOD_PASSWORD')
        self._config['finnhub_api_key'] = os.getenv('FINNHUB_API_KEY')
        self._config['twelve_data_api_key'] = os.getenv('TWELVE_DATA_API_KEY')
        self._config['sendgrid_api_key'] = os.getenv('SENDGRID_API_KEY')
        
        # Email Configuration
        self._config['user_email'] = os.getenv('USER_EMAIL')
        recipient_emails = os.getenv('RECIPIENT_EMAILS', '')
        self._config['recipient_emails'] = [
            email.strip() for email in recipient_emails.split(',') if email.strip()
        ] if recipient_emails else []
        
        # Cache TTL values (with defaults)
        self._config['active_stock_ttl'] = int(os.getenv('ACTIVE_STOCK_TTL', '15'))
        self._config['watchlist_stock_ttl'] = int(os.getenv('WATCHLIST_STOCK_TTL', '60'))
        self._config['robinhood_tradeability_ttl'] = int(os.getenv('ROBINHOOD_TRADEABILITY_TTL', '86400'))  # 24h
        self._config['company_info_ttl'] = int(os.getenv('COMPANY_INFO_TTL', '86400'))  # 24h
        self._config['financial_data_ttl'] = int(os.getenv('FINANCIAL_DATA_TTL', '21600'))  # 6h
        
        # Newsletter delivery time (default 9:00 AM ET)
        newsletter_hour = int(os.getenv('NEWSLETTER_HOUR', '9'))
        newsletter_minute = int(os.getenv('NEWSLETTER_MINUTE', '0'))
        self._config['newsletter_time'] = time(hour=newsletter_hour, minute=newsletter_minute)
        
        # Alert limits
        self._config['max_trading_alerts_per_day'] = int(os.getenv('MAX_TRADING_ALERTS_PER_DAY', '3'))
        self._config['alert_generation_timeout'] = int(os.getenv('ALERT_GENERATION_TIMEOUT', '10'))
        self._config['alert_delivery_timeout'] = int(os.getenv('ALERT_DELIVERY_TIMEOUT', '30'))
        
        # Position sizing parameters (percentages as decimals)
        self._config['low_risk_min'] = Decimal(os.getenv('LOW_RISK_MIN', '15'))
        self._config['low_risk_max'] = Decimal(os.getenv('LOW_RISK_MAX', '25'))
        self._config['medium_risk_min'] = Decimal(os.getenv('MEDIUM_RISK_MIN', '8'))
        self._config['medium_risk_max'] = Decimal(os.getenv('MEDIUM_RISK_MAX', '15'))
        self._config['high_risk_min'] = Decimal(os.getenv('HIGH_RISK_MIN', '1'))
        self._config['high_risk_max'] = Decimal(os.getenv('HIGH_RISK_MAX', '8'))
        
        # Application settings
        self._config['environment'] = os.getenv('ENVIRONMENT', 'development')
        self._config['log_level'] = os.getenv('LOG_LEVEL', 'INFO')
    
    def validate_configuration(self) -> None:
        """
        Validate all required configuration values at startup.
        
        Raises:
            ConfigurationError: If any required configuration is missing or invalid
        """
        errors = []
        
        # Validate required credentials
        required_credentials = [
            ('redis_url', 'REDIS_URL'),
            ('database_url', 'DATABASE_URL'),
            ('sendgrid_api_key', 'SENDGRID_API_KEY'),
            ('user_email', 'USER_EMAIL'),
        ]
        
        # Optional credentials (warn if missing but don't fail)
        optional_credentials = [
            ('robinhood_username', 'ROBINHOOD_USERNAME'),
            ('robinhood_password', 'ROBINHOOD_PASSWORD'),
            ('finnhub_api_key', 'FINNHUB_API_KEY'),
            ('twelve_data_api_key', 'TWELVE_DATA_API_KEY'),
        ]
        
        for config_key, env_var in required_credentials:
            value = self._config.get(config_key)
            if not value or (isinstance(value, str) and not value.strip()):
                errors.append(f"Missing required configuration: {env_var}")
        
        # Validate email format (basic check)
        user_email = self._config.get('user_email', '')
        if user_email and '@' not in user_email:
            errors.append(f"Invalid email format for USER_EMAIL: {user_email}")
        
        # Validate recipient emails if provided
        for email in self._config.get('recipient_emails', []):
            if '@' not in email:
                errors.append(f"Invalid recipient email format: {email}")
        
        # Validate cache TTL values are positive
        ttl_configs = [
            ('active_stock_ttl', 'ACTIVE_STOCK_TTL'),
            ('watchlist_stock_ttl', 'WATCHLIST_STOCK_TTL'),
            ('robinhood_tradeability_ttl', 'ROBINHOOD_TRADEABILITY_TTL'),
            ('company_info_ttl', 'COMPANY_INFO_TTL'),
            ('financial_data_ttl', 'FINANCIAL_DATA_TTL'),
        ]
        
        for config_key, env_var in ttl_configs:
            value = self._config.get(config_key)
            if value is not None and value <= 0:
                errors.append(f"Invalid {env_var}: must be positive integer, got {value}")
        
        # Validate newsletter time
        newsletter_time = self._config.get('newsletter_time')
        if newsletter_time is None:
            errors.append("Invalid newsletter time configuration")
        
        # Validate alert limits are positive
        max_alerts = self._config.get('max_trading_alerts_per_day')
        if max_alerts is not None and max_alerts <= 0:
            errors.append(f"Invalid MAX_TRADING_ALERTS_PER_DAY: must be positive, got {max_alerts}")
        
        alert_gen_timeout = self._config.get('alert_generation_timeout')
        if alert_gen_timeout is not None and alert_gen_timeout <= 0:
            errors.append(f"Invalid ALERT_GENERATION_TIMEOUT: must be positive, got {alert_gen_timeout}")
        
        alert_delivery_timeout = self._config.get('alert_delivery_timeout')
        if alert_delivery_timeout is not None and alert_delivery_timeout <= 0:
            errors.append(f"Invalid ALERT_DELIVERY_TIMEOUT: must be positive, got {alert_delivery_timeout}")
        
        # Validate position sizing parameters
        position_configs = [
            ('low_risk_min', 'LOW_RISK_MIN', 1, 25),
            ('low_risk_max', 'LOW_RISK_MAX', 1, 25),
            ('medium_risk_min', 'MEDIUM_RISK_MIN', 1, 25),
            ('medium_risk_max', 'MEDIUM_RISK_MAX', 1, 25),
            ('high_risk_min', 'HIGH_RISK_MIN', 1, 25),
            ('high_risk_max', 'HIGH_RISK_MAX', 1, 25),
        ]
        
        for config_key, env_var, min_val, max_val in position_configs:
            value = self._config.get(config_key)
            if value is not None:
                if value < min_val or value > max_val:
                    errors.append(
                        f"Invalid {env_var}: must be between {min_val} and {max_val}, got {value}"
                    )
        
        # Validate position sizing ranges are logical
        low_min = self._config.get('low_risk_min', Decimal('0'))
        low_max = self._config.get('low_risk_max', Decimal('0'))
        if low_min > low_max:
            errors.append(f"LOW_RISK_MIN ({low_min}) cannot be greater than LOW_RISK_MAX ({low_max})")
        
        med_min = self._config.get('medium_risk_min', Decimal('0'))
        med_max = self._config.get('medium_risk_max', Decimal('0'))
        if med_min > med_max:
            errors.append(f"MEDIUM_RISK_MIN ({med_min}) cannot be greater than MEDIUM_RISK_MAX ({med_max})")
        
        high_min = self._config.get('high_risk_min', Decimal('0'))
        high_max = self._config.get('high_risk_max', Decimal('0'))
        if high_min > high_max:
            errors.append(f"HIGH_RISK_MIN ({high_min}) cannot be greater than HIGH_RISK_MAX ({high_max})")
        
        # If there are any errors, raise ConfigurationError with all messages
        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            raise ConfigurationError(error_message)

    
    # Database configuration getters
    @property
    def redis_url(self) -> str:
        """Get Redis URL"""
        return self._config['redis_url']
    
    @property
    def database_url(self) -> str:
        """Get PostgreSQL database URL"""
        return self._config['database_url']
    
    # API credentials getters
    @property
    def robinhood_username(self) -> str:
        """Get Robinhood username"""
        return self._config['robinhood_username']
    
    @property
    def robinhood_password(self) -> str:
        """Get Robinhood password"""
        return self._config['robinhood_password']
    
    @property
    def finnhub_api_key(self) -> str:
        """Get Finnhub API key"""
        return self._config['finnhub_api_key']
    
    @property
    def twelve_data_api_key(self) -> str:
        """Get Twelve Data API key"""
        return self._config['twelve_data_api_key']
    
    @property
    def sendgrid_api_key(self) -> str:
        """Get SendGrid API key"""
        return self._config['sendgrid_api_key']
    
    # Email configuration getters
    @property
    def user_email(self) -> str:
        """Get user email address"""
        return self._config['user_email']
    
    @property
    def recipient_emails(self) -> List[str]:
        """Get list of recipient email addresses"""
        return self._config['recipient_emails']
    
    @property
    def newsletter_time(self) -> time:
        """Get newsletter delivery time"""
        return self._config['newsletter_time']
    
    # Cache TTL configuration
    @property
    def cache_ttl_config(self) -> CacheTTLConfig:
        """Get cache TTL configuration"""
        return CacheTTLConfig(
            active_stock_ttl=self._config['active_stock_ttl'],
            watchlist_stock_ttl=self._config['watchlist_stock_ttl'],
            robinhood_tradeability_ttl=self._config['robinhood_tradeability_ttl'],
            company_info_ttl=self._config['company_info_ttl'],
            financial_data_ttl=self._config['financial_data_ttl']
        )
    
    @property
    def active_stock_ttl(self) -> int:
        """Get active stock cache TTL in seconds"""
        return self._config['active_stock_ttl']
    
    @property
    def watchlist_stock_ttl(self) -> int:
        """Get watchlist stock cache TTL in seconds"""
        return self._config['watchlist_stock_ttl']
    
    # Alert limits configuration
    @property
    def alert_limits_config(self) -> AlertLimitsConfig:
        """Get alert limits configuration"""
        return AlertLimitsConfig(
            max_trading_alerts_per_day=self._config['max_trading_alerts_per_day'],
            alert_generation_timeout_seconds=self._config['alert_generation_timeout'],
            alert_delivery_timeout_seconds=self._config['alert_delivery_timeout']
        )
    
    @property
    def max_trading_alerts_per_day(self) -> int:
        """Get maximum trading alerts per day"""
        return self._config['max_trading_alerts_per_day']
    
    # Position sizing configuration
    @property
    def position_sizing_config(self) -> PositionSizingConfig:
        """Get position sizing configuration"""
        return PositionSizingConfig(
            low_risk_min=self._config['low_risk_min'],
            low_risk_max=self._config['low_risk_max'],
            medium_risk_min=self._config['medium_risk_min'],
            medium_risk_max=self._config['medium_risk_max'],
            high_risk_min=self._config['high_risk_min'],
            high_risk_max=self._config['high_risk_max']
        )
    
    # Application settings
    @property
    def environment(self) -> str:
        """Get application environment (development, production, etc.)"""
        return self._config['environment']
    
    @property
    def log_level(self) -> str:
        """Get log level"""
        return self._config['log_level']
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self._config['environment'].lower() == 'production'
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self._config['environment'].lower() == 'development'


# Global configuration instance
_config_instance: Optional[ConfigurationManager] = None


def get_config() -> ConfigurationManager:
    """
    Get the global configuration instance.
    
    Returns:
        ConfigurationManager: The global configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigurationManager()
    return _config_instance


def initialize_config() -> ConfigurationManager:
    """
    Initialize and validate configuration at startup.
    
    Returns:
        ConfigurationManager: The initialized and validated configuration
        
    Raises:
        ConfigurationError: If configuration is invalid or missing
    """
    config = get_config()
    config.validate_configuration()
    return config
