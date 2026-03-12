"""Unit tests for ConfigurationManager"""

import os
import pytest
from datetime import time
from decimal import Decimal
from unittest.mock import patch

from src.utils.configuration_manager import (
    ConfigurationManager,
    ConfigurationError,
    CacheTTLConfig,
    PositionSizingConfig,
    AlertLimitsConfig,
    get_config,
    initialize_config
)


@pytest.fixture
def valid_env_vars():
    """Fixture providing valid environment variables"""
    return {
        'REDIS_URL': 'redis://localhost:6379/0',
        'DATABASE_URL': 'postgresql://user:pass@localhost:5432/testdb',
        'ROBINHOOD_USERNAME': 'test_user',
        'ROBINHOOD_PASSWORD': 'test_pass',
        'FINNHUB_API_KEY': 'test_finnhub_key',
        'TWELVE_DATA_API_KEY': 'test_twelve_data_key',
        'SENDGRID_API_KEY': 'test_sendgrid_key',
        'USER_EMAIL': 'user@example.com',
        'RECIPIENT_EMAILS': 'recipient1@example.com,recipient2@example.com',
        'ACTIVE_STOCK_TTL': '15',
        'WATCHLIST_STOCK_TTL': '60',
        'ROBINHOOD_TRADEABILITY_TTL': '86400',
        'COMPANY_INFO_TTL': '86400',
        'FINANCIAL_DATA_TTL': '21600',
        'NEWSLETTER_HOUR': '9',
        'NEWSLETTER_MINUTE': '0',
        'MAX_TRADING_ALERTS_PER_DAY': '3',
        'ALERT_GENERATION_TIMEOUT': '10',
        'ALERT_DELIVERY_TIMEOUT': '30',
        'LOW_RISK_MIN': '15',
        'LOW_RISK_MAX': '25',
        'MEDIUM_RISK_MIN': '8',
        'MEDIUM_RISK_MAX': '15',
        'HIGH_RISK_MIN': '1',
        'HIGH_RISK_MAX': '8',
        'ENVIRONMENT': 'development',
        'LOG_LEVEL': 'INFO'
    }


@pytest.fixture
def config_manager(valid_env_vars):
    """Fixture providing a ConfigurationManager with valid environment"""
    with patch.dict(os.environ, valid_env_vars, clear=True):
        return ConfigurationManager()


class TestConfigurationManagerLoading:
    """Tests for configuration loading"""
    
    def test_loads_database_urls(self, config_manager):
        """Test loading database URLs"""
        assert config_manager.redis_url == 'redis://localhost:6379/0'
        assert config_manager.database_url == 'postgresql://user:pass@localhost:5432/testdb'
    
    def test_loads_api_credentials(self, config_manager):
        """Test loading API credentials"""
        assert config_manager.robinhood_username == 'test_user'
        assert config_manager.robinhood_password == 'test_pass'
        assert config_manager.finnhub_api_key == 'test_finnhub_key'
        assert config_manager.twelve_data_api_key == 'test_twelve_data_key'
        assert config_manager.sendgrid_api_key == 'test_sendgrid_key'
    
    def test_loads_email_configuration(self, config_manager):
        """Test loading email configuration"""
        assert config_manager.user_email == 'user@example.com'
        assert config_manager.recipient_emails == ['recipient1@example.com', 'recipient2@example.com']
    
    def test_loads_cache_ttl_values(self, config_manager):
        """Test loading cache TTL values"""
        assert config_manager.active_stock_ttl == 15
        assert config_manager.watchlist_stock_ttl == 60
        
        ttl_config = config_manager.cache_ttl_config
        assert ttl_config.active_stock_ttl == 15
        assert ttl_config.watchlist_stock_ttl == 60
        assert ttl_config.robinhood_tradeability_ttl == 86400
        assert ttl_config.company_info_ttl == 86400
        assert ttl_config.financial_data_ttl == 21600
    
    def test_loads_newsletter_time(self, config_manager):
        """Test loading newsletter delivery time"""
        assert config_manager.newsletter_time == time(hour=9, minute=0)
    
    def test_loads_alert_limits(self, config_manager):
        """Test loading alert limits"""
        assert config_manager.max_trading_alerts_per_day == 3
        
        alert_config = config_manager.alert_limits_config
        assert alert_config.max_trading_alerts_per_day == 3
        assert alert_config.alert_generation_timeout_seconds == 10
        assert alert_config.alert_delivery_timeout_seconds == 30
    
    def test_loads_position_sizing_parameters(self, config_manager):
        """Test loading position sizing parameters"""
        position_config = config_manager.position_sizing_config
        assert position_config.low_risk_min == Decimal('15')
        assert position_config.low_risk_max == Decimal('25')
        assert position_config.medium_risk_min == Decimal('8')
        assert position_config.medium_risk_max == Decimal('15')
        assert position_config.high_risk_min == Decimal('1')
        assert position_config.high_risk_max == Decimal('8')
    
    def test_loads_application_settings(self, config_manager):
        """Test loading application settings"""
        assert config_manager.environment == 'development'
        assert config_manager.log_level == 'INFO'
        assert config_manager.is_development is True
        assert config_manager.is_production is False
    
    def test_default_values_when_optional_missing(self, valid_env_vars):
        """Test default values are used when optional config is missing"""
        # Remove optional config
        env_without_optional = valid_env_vars.copy()
        del env_without_optional['ACTIVE_STOCK_TTL']
        del env_without_optional['NEWSLETTER_HOUR']
        del env_without_optional['ENVIRONMENT']
        
        with patch.dict(os.environ, env_without_optional, clear=True):
            config = ConfigurationManager()
            assert config.active_stock_ttl == 15  # default
            assert config.newsletter_time == time(hour=9, minute=0)  # default
            assert config.environment == 'development'  # default
    
    def test_recipient_emails_empty_string(self, valid_env_vars):
        """Test recipient emails handles empty string"""
        env = valid_env_vars.copy()
        env['RECIPIENT_EMAILS'] = ''
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            assert config.recipient_emails == []
    
    def test_recipient_emails_with_spaces(self, valid_env_vars):
        """Test recipient emails strips whitespace"""
        env = valid_env_vars.copy()
        env['RECIPIENT_EMAILS'] = ' email1@test.com , email2@test.com '
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            assert config.recipient_emails == ['email1@test.com', 'email2@test.com']


class TestConfigurationValidation:
    """Tests for configuration validation"""
    
    def test_validation_passes_with_valid_config(self, config_manager):
        """Test validation passes with all valid configuration"""
        # Should not raise any exception
        config_manager.validate_configuration()
    
    def test_validation_fails_missing_redis_url(self, valid_env_vars):
        """Test validation fails when REDIS_URL is missing"""
        env = valid_env_vars.copy()
        del env['REDIS_URL']
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            with pytest.raises(ConfigurationError) as exc_info:
                config.validate_configuration()
            assert 'REDIS_URL' in str(exc_info.value)
    
    def test_validation_fails_missing_database_url(self, valid_env_vars):
        """Test validation fails when DATABASE_URL is missing"""
        env = valid_env_vars.copy()
        del env['DATABASE_URL']
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            with pytest.raises(ConfigurationError) as exc_info:
                config.validate_configuration()
            assert 'DATABASE_URL' in str(exc_info.value)
    
    def test_validation_fails_missing_api_credentials(self, valid_env_vars):
        """Test validation fails when API credentials are missing"""
        credentials = [
            'ROBINHOOD_USERNAME',
            'ROBINHOOD_PASSWORD',
            'FINNHUB_API_KEY',
            'TWELVE_DATA_API_KEY',
            'SENDGRID_API_KEY'
        ]
        
        for credential in credentials:
            env = valid_env_vars.copy()
            del env[credential]
            
            with patch.dict(os.environ, env, clear=True):
                config = ConfigurationManager()
                with pytest.raises(ConfigurationError) as exc_info:
                    config.validate_configuration()
                assert credential in str(exc_info.value)
    
    def test_validation_fails_missing_user_email(self, valid_env_vars):
        """Test validation fails when USER_EMAIL is missing"""
        env = valid_env_vars.copy()
        del env['USER_EMAIL']
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            with pytest.raises(ConfigurationError) as exc_info:
                config.validate_configuration()
            assert 'USER_EMAIL' in str(exc_info.value)
    
    def test_validation_fails_invalid_user_email_format(self, valid_env_vars):
        """Test validation fails with invalid email format"""
        env = valid_env_vars.copy()
        env['USER_EMAIL'] = 'invalid_email'
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            with pytest.raises(ConfigurationError) as exc_info:
                config.validate_configuration()
            assert 'Invalid email format' in str(exc_info.value)
    
    def test_validation_fails_invalid_recipient_email_format(self, valid_env_vars):
        """Test validation fails with invalid recipient email format"""
        env = valid_env_vars.copy()
        env['RECIPIENT_EMAILS'] = 'valid@example.com,invalid_email'
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            with pytest.raises(ConfigurationError) as exc_info:
                config.validate_configuration()
            assert 'Invalid recipient email format' in str(exc_info.value)
    
    def test_validation_fails_negative_ttl(self, valid_env_vars):
        """Test validation fails with negative TTL values"""
        env = valid_env_vars.copy()
        env['ACTIVE_STOCK_TTL'] = '-5'
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            with pytest.raises(ConfigurationError) as exc_info:
                config.validate_configuration()
            assert 'ACTIVE_STOCK_TTL' in str(exc_info.value)
            assert 'must be positive' in str(exc_info.value)
    
    def test_validation_fails_zero_ttl(self, valid_env_vars):
        """Test validation fails with zero TTL values"""
        env = valid_env_vars.copy()
        env['WATCHLIST_STOCK_TTL'] = '0'
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            with pytest.raises(ConfigurationError) as exc_info:
                config.validate_configuration()
            assert 'WATCHLIST_STOCK_TTL' in str(exc_info.value)
    
    def test_validation_fails_negative_alert_limit(self, valid_env_vars):
        """Test validation fails with negative alert limit"""
        env = valid_env_vars.copy()
        env['MAX_TRADING_ALERTS_PER_DAY'] = '-1'
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            with pytest.raises(ConfigurationError) as exc_info:
                config.validate_configuration()
            assert 'MAX_TRADING_ALERTS_PER_DAY' in str(exc_info.value)
    
    def test_validation_fails_position_size_out_of_range(self, valid_env_vars):
        """Test validation fails with position size outside 1-25% range"""
        env = valid_env_vars.copy()
        env['LOW_RISK_MIN'] = '0'  # Below minimum
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            with pytest.raises(ConfigurationError) as exc_info:
                config.validate_configuration()
            assert 'LOW_RISK_MIN' in str(exc_info.value)
            assert 'between 1 and 25' in str(exc_info.value)
        
        env['LOW_RISK_MAX'] = '30'  # Above maximum
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            with pytest.raises(ConfigurationError) as exc_info:
                config.validate_configuration()
            assert 'LOW_RISK_MAX' in str(exc_info.value)
    
    def test_validation_fails_min_greater_than_max(self, valid_env_vars):
        """Test validation fails when min > max for position sizing"""
        env = valid_env_vars.copy()
        env['LOW_RISK_MIN'] = '20'
        env['LOW_RISK_MAX'] = '15'
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            with pytest.raises(ConfigurationError) as exc_info:
                config.validate_configuration()
            assert 'LOW_RISK_MIN' in str(exc_info.value)
            assert 'cannot be greater than' in str(exc_info.value)
    
    def test_validation_collects_multiple_errors(self, valid_env_vars):
        """Test validation collects all errors, not just the first one"""
        env = valid_env_vars.copy()
        del env['REDIS_URL']
        del env['DATABASE_URL']
        env['USER_EMAIL'] = 'invalid_email'
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            with pytest.raises(ConfigurationError) as exc_info:
                config.validate_configuration()
            error_message = str(exc_info.value)
            assert 'REDIS_URL' in error_message
            assert 'DATABASE_URL' in error_message
            assert 'Invalid email format' in error_message


class TestConfigurationEdgeCases:
    """Tests for edge cases and boundary conditions"""
    
    def test_empty_string_treated_as_missing(self, valid_env_vars):
        """Test empty string values are treated as missing"""
        env = valid_env_vars.copy()
        env['REDIS_URL'] = ''
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            with pytest.raises(ConfigurationError) as exc_info:
                config.validate_configuration()
            assert 'REDIS_URL' in str(exc_info.value)
    
    def test_whitespace_only_treated_as_missing(self, valid_env_vars):
        """Test whitespace-only values are treated as missing"""
        env = valid_env_vars.copy()
        env['FINNHUB_API_KEY'] = '   '
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            with pytest.raises(ConfigurationError) as exc_info:
                config.validate_configuration()
            assert 'FINNHUB_API_KEY' in str(exc_info.value)
    
    def test_position_size_boundary_values(self, valid_env_vars):
        """Test position sizing at boundary values (1% and 25%)"""
        env = valid_env_vars.copy()
        env['HIGH_RISK_MIN'] = '1'
        env['LOW_RISK_MAX'] = '25'
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            config.validate_configuration()  # Should not raise
            assert config.position_sizing_config.high_risk_min == Decimal('1')
            assert config.position_sizing_config.low_risk_max == Decimal('25')
    
    def test_newsletter_time_edge_cases(self, valid_env_vars):
        """Test newsletter time at edge cases (midnight, 23:59)"""
        env = valid_env_vars.copy()
        env['NEWSLETTER_HOUR'] = '0'
        env['NEWSLETTER_MINUTE'] = '0'
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            assert config.newsletter_time == time(hour=0, minute=0)
        
        env['NEWSLETTER_HOUR'] = '23'
        env['NEWSLETTER_MINUTE'] = '59'
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            assert config.newsletter_time == time(hour=23, minute=59)
    
    def test_production_environment_detection(self, valid_env_vars):
        """Test production environment detection"""
        env = valid_env_vars.copy()
        env['ENVIRONMENT'] = 'production'
        
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            assert config.is_production is True
            assert config.is_development is False
        
        env['ENVIRONMENT'] = 'PRODUCTION'  # Case insensitive
        with patch.dict(os.environ, env, clear=True):
            config = ConfigurationManager()
            assert config.is_production is True


class TestGlobalConfigurationInstance:
    """Tests for global configuration instance management"""
    
    def test_get_config_returns_singleton(self, valid_env_vars):
        """Test get_config returns the same instance"""
        with patch.dict(os.environ, valid_env_vars, clear=True):
            # Reset global instance
            import src.utils.configuration_manager as config_module
            config_module._config_instance = None
            
            config1 = get_config()
            config2 = get_config()
            assert config1 is config2
    
    def test_initialize_config_validates(self, valid_env_vars):
        """Test initialize_config validates configuration"""
        with patch.dict(os.environ, valid_env_vars, clear=True):
            # Reset global instance
            import src.utils.configuration_manager as config_module
            config_module._config_instance = None
            
            config = initialize_config()
            assert config is not None
    
    def test_initialize_config_raises_on_invalid(self, valid_env_vars):
        """Test initialize_config raises ConfigurationError on invalid config"""
        env = valid_env_vars.copy()
        del env['REDIS_URL']
        
        with patch.dict(os.environ, env, clear=True):
            # Reset global instance
            import src.utils.configuration_manager as config_module
            config_module._config_instance = None
            
            with pytest.raises(ConfigurationError):
                initialize_config()


class TestCredentialRotationSupport:
    """Tests for credential rotation support"""
    
    def test_credentials_loaded_from_environment(self, valid_env_vars):
        """Test credentials are loaded from environment variables"""
        with patch.dict(os.environ, valid_env_vars, clear=True):
            config = ConfigurationManager()
            assert config.finnhub_api_key == 'test_finnhub_key'
    
    def test_new_instance_picks_up_changed_credentials(self, valid_env_vars):
        """Test new instance picks up changed environment variables"""
        with patch.dict(os.environ, valid_env_vars, clear=True):
            config1 = ConfigurationManager()
            assert config1.finnhub_api_key == 'test_finnhub_key'
        
        # Change environment variable
        env_changed = valid_env_vars.copy()
        env_changed['FINNHUB_API_KEY'] = 'new_rotated_key'
        
        with patch.dict(os.environ, env_changed, clear=True):
            config2 = ConfigurationManager()
            assert config2.finnhub_api_key == 'new_rotated_key'
    
    def test_credentials_not_logged_in_repr(self, config_manager):
        """Test credentials are not exposed in string representation"""
        config_str = str(config_manager)
        # Should not contain actual credential values
        assert 'test_pass' not in config_str
        assert 'test_finnhub_key' not in config_str
