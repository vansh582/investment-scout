"""
Integration tests for Task 25: Component Wiring

Tests that all components are properly wired together in the main application.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os


@pytest.fixture
def mock_env():
    """Mock environment variables for testing"""
    env_vars = {
        'REDIS_URL': 'redis://localhost:6379',
        'POSTGRES_URL': 'postgresql://user:pass@localhost/testdb',
        'SENDGRID_API_KEY': 'test_sendgrid_key',
        'USER_EMAIL': 'test@example.com',
        'RECIPIENT_EMAILS': 'recipient@example.com',
        'ENVIRONMENT': 'test'
    }
    
    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture
def mock_components():
    """Mock all external dependencies"""
    with patch('src.main.DataManager') as mock_dm, \
         patch('src.main.YFinanceClient') as mock_yf, \
         patch('src.main.FinnhubClient') as mock_fh, \
         patch('src.main.TwelveDataClient') as mock_td, \
         patch('src.main.RobinhoodClient') as mock_rh, \
         patch('src.main.MarketMonitor') as mock_mm, \
         patch('src.main.ResearchEngine') as mock_re, \
         patch('src.main.GeopoliticalMonitor') as mock_gm, \
         patch('src.main.IndustryAnalyzer') as mock_ia, \
         patch('src.main.ProjectionEngine') as mock_pe, \
         patch('src.main.InvestmentAnalyzer') as mock_inv, \
         patch('src.main.TradingAnalyzer') as mock_ta, \
         patch('src.main.PerformanceTracker') as mock_pt, \
         patch('src.main.NewsletterGenerator') as mock_ng, \
         patch('src.main.AlertGenerator') as mock_ag, \
         patch('src.main.EmailService') as mock_es, \
         patch('src.main.Scheduler') as mock_sched, \
         patch('src.main.WebServer') as mock_ws, \
         patch('src.main.CredentialManager') as mock_cm:
        
        # Configure mocks
        mock_cm.return_value.get_credential.return_value = 'test_key'
        
        yield {
            'data_manager': mock_dm,
            'yfinance': mock_yf,
            'finnhub': mock_fh,
            'twelve_data': mock_td,
            'robinhood': mock_rh,
            'market_monitor': mock_mm,
            'research_engine': mock_re,
            'geopolitical_monitor': mock_gm,
            'industry_analyzer': mock_ia,
            'projection_engine': mock_pe,
            'investment_analyzer': mock_inv,
            'trading_analyzer': mock_ta,
            'performance_tracker': mock_pt,
            'newsletter_generator': mock_ng,
            'alert_generator': mock_ag,
            'email_service': mock_es,
            'scheduler': mock_sched,
            'web_server': mock_ws,
            'credential_manager': mock_cm
        }


def test_app_initialization(mock_env, mock_components):
    """Test that InvestmentScoutApp initializes all components"""
    from src.main import InvestmentScoutApp
    
    app = InvestmentScoutApp()
    
    # Mock configuration
    with patch('src.main.initialize_config') as mock_config:
        mock_config.return_value = Mock(
            environment='test',
            redis_url='redis://localhost:6379',
            postgres_url='postgresql://user:pass@localhost/testdb',
            max_trading_alerts_per_day=5,
            recipient_emails=['test@example.com'],
            is_development=True
        )
        
        # Initialize app
        result = app.initialize()
        
        # Verify initialization succeeded
        assert result is True
        
        # Verify all components were initialized
        assert app.credential_manager is not None
        assert app.data_manager is not None
        assert app.yfinance_client is not None
        assert app.robinhood_client is not None
        assert app.market_monitor is not None
        assert app.research_engine is not None
        assert app.geopolitical_monitor is not None
        assert app.industry_analyzer is not None
        assert app.projection_engine is not None
        assert app.investment_analyzer is not None
        assert app.trading_analyzer is not None
        assert app.performance_tracker is not None
        assert app.newsletter_generator is not None
        assert app.alert_generator is not None
        assert app.email_service is not None
        assert app.scheduler is not None
        assert app.web_server is not None


def test_market_monitor_wiring(mock_env, mock_components):
    """Test that Market Monitor is wired to API clients and Data Manager"""
    from src.main import InvestmentScoutApp
    
    app = InvestmentScoutApp()
    
    with patch('src.main.initialize_config') as mock_config:
        mock_config.return_value = Mock(
            environment='test',
            redis_url='redis://localhost:6379',
            postgres_url='postgresql://user:pass@localhost/testdb',
            max_trading_alerts_per_day=5,
            recipient_emails=['test@example.com'],
            is_development=True
        )
        
        app.initialize()
        
        # Verify Market Monitor was initialized with correct dependencies
        mock_components['market_monitor'].assert_called_once()
        call_kwargs = mock_components['market_monitor'].call_args[1]
        
        assert 'data_manager' in call_kwargs
        assert 'yfinance_client' in call_kwargs


def test_research_engine_wiring(mock_env, mock_components):
    """Test that Research Engine is wired to Data Manager"""
    from src.main import InvestmentScoutApp
    
    app = InvestmentScoutApp()
    
    with patch('src.main.initialize_config') as mock_config:
        mock_config.return_value = Mock(
            environment='test',
            redis_url='redis://localhost:6379',
            postgres_url='postgresql://user:pass@localhost/testdb',
            max_trading_alerts_per_day=5,
            recipient_emails=['test@example.com'],
            is_development=True
        )
        
        app.initialize()
        
        # Verify Research Engine was initialized with Data Manager
        mock_components['research_engine'].assert_called_once()
        call_kwargs = mock_components['research_engine'].call_args[1]
        
        assert 'data_manager' in call_kwargs


def test_investment_analyzer_wiring(mock_env, mock_components):
    """Test that Investment Analyzer is wired to Research Engine, Projection Engine, Market Monitor"""
    from src.main import InvestmentScoutApp
    
    app = InvestmentScoutApp()
    
    with patch('src.main.initialize_config') as mock_config:
        mock_config.return_value = Mock(
            environment='test',
            redis_url='redis://localhost:6379',
            postgres_url='postgresql://user:pass@localhost/testdb',
            max_trading_alerts_per_day=5,
            recipient_emails=['test@example.com'],
            is_development=True
        )
        
        app.initialize()
        
        # Verify Investment Analyzer was initialized with correct dependencies
        mock_components['investment_analyzer'].assert_called_once()
        call_kwargs = mock_components['investment_analyzer'].call_args[1]
        
        assert 'research_engine' in call_kwargs
        assert 'projection_engine' in call_kwargs
        assert 'market_monitor' in call_kwargs


def test_trading_analyzer_wiring(mock_env, mock_components):
    """Test that Trading Analyzer is wired to Data Manager and Research Engine"""
    from src.main import InvestmentScoutApp
    
    app = InvestmentScoutApp()
    
    with patch('src.main.initialize_config') as mock_config:
        mock_config.return_value = Mock(
            environment='test',
            redis_url='redis://localhost:6379',
            postgres_url='postgresql://user:pass@localhost/testdb',
            max_trading_alerts_per_day=5,
            recipient_emails=['test@example.com'],
            is_development=True
        )
        
        app.initialize()
        
        # Verify Trading Analyzer was initialized with correct dependencies
        mock_components['trading_analyzer'].assert_called_once()
        call_kwargs = mock_components['trading_analyzer'].call_args[1]
        
        assert 'data_manager' in call_kwargs
        assert 'research_engine' in call_kwargs
        assert 'max_alerts_per_day' in call_kwargs


def test_newsletter_generator_wiring(mock_env, mock_components):
    """Test that Newsletter Generator is wired to Performance Tracker and other components"""
    from src.main import InvestmentScoutApp
    
    app = InvestmentScoutApp()
    
    with patch('src.main.initialize_config') as mock_config:
        mock_config.return_value = Mock(
            environment='test',
            redis_url='redis://localhost:6379',
            postgres_url='postgresql://user:pass@localhost/testdb',
            max_trading_alerts_per_day=5,
            recipient_emails=['test@example.com'],
            is_development=True
        )
        
        app.initialize()
        
        # Verify Newsletter Generator was initialized with correct dependencies
        mock_components['newsletter_generator'].assert_called_once()
        call_kwargs = mock_components['newsletter_generator'].call_args[1]
        
        assert 'performance_tracker' in call_kwargs
        assert 'market_monitor' in call_kwargs
        assert 'geopolitical_monitor' in call_kwargs
        assert 'industry_analyzer' in call_kwargs


def test_email_service_wiring(mock_env, mock_components):
    """Test that Email Service is wired to Credential Manager"""
    from src.main import InvestmentScoutApp
    
    app = InvestmentScoutApp()
    
    with patch('src.main.initialize_config') as mock_config:
        mock_config.return_value = Mock(
            environment='test',
            redis_url='redis://localhost:6379',
            postgres_url='postgresql://user:pass@localhost/testdb',
            max_trading_alerts_per_day=5,
            recipient_emails=['test@example.com'],
            is_development=True
        )
        
        app.initialize()
        
        # Verify Email Service was initialized with Credential Manager
        mock_components['email_service'].assert_called_once()
        call_kwargs = mock_components['email_service'].call_args[1]
        
        assert 'credential_manager' in call_kwargs


def test_scheduler_wiring(mock_env, mock_components):
    """Test that Scheduler is wired to all component callbacks"""
    from src.main import InvestmentScoutApp
    
    app = InvestmentScoutApp()
    
    with patch('src.main.initialize_config') as mock_config:
        mock_config.return_value = Mock(
            environment='test',
            redis_url='redis://localhost:6379',
            postgres_url='postgresql://user:pass@localhost/testdb',
            max_trading_alerts_per_day=5,
            recipient_emails=['test@example.com'],
            is_development=True
        )
        
        app.initialize()
        
        # Verify Scheduler was initialized with all callbacks
        mock_components['scheduler'].assert_called_once()
        call_kwargs = mock_components['scheduler'].call_args[1]
        
        assert 'config' in call_kwargs
        assert 'investment_analyzer' in call_kwargs
        assert 'newsletter_generator' in call_kwargs
        assert 'market_monitor' in call_kwargs
        assert 'trading_analyzer' in call_kwargs
        assert 'performance_tracker' in call_kwargs
        assert 'geopolitical_monitor' in call_kwargs
        assert 'industry_analyzer' in call_kwargs
        assert 'projection_engine' in call_kwargs
        
        # Verify all callbacks are callable
        assert callable(call_kwargs['investment_analyzer'])
        assert callable(call_kwargs['market_monitor'])
        assert callable(call_kwargs['trading_analyzer'])
        assert callable(call_kwargs['performance_tracker'])
        assert callable(call_kwargs['geopolitical_monitor'])
        assert callable(call_kwargs['industry_analyzer'])
        assert callable(call_kwargs['projection_engine'])


def test_configuration_validation_at_startup(mock_env, mock_components):
    """Test that configuration is validated at startup"""
    from src.main import InvestmentScoutApp
    
    app = InvestmentScoutApp()
    
    # Test with invalid configuration
    with patch('src.main.initialize_config') as mock_config:
        from src.utils.configuration_manager import ConfigurationError
        mock_config.side_effect = ConfigurationError("Missing required configuration")
        
        result = app.initialize()
        
        # Verify initialization failed
        assert result is False


def test_graceful_shutdown(mock_env, mock_components):
    """Test that shutdown closes all connections gracefully"""
    from src.main import InvestmentScoutApp
    
    app = InvestmentScoutApp()
    
    with patch('src.main.initialize_config') as mock_config:
        mock_config.return_value = Mock(
            environment='test',
            redis_url='redis://localhost:6379',
            postgres_url='postgresql://user:pass@localhost/testdb',
            max_trading_alerts_per_day=5,
            recipient_emails=['test@example.com'],
            is_development=True
        )
        
        app.initialize()
        
        # Create mock instances
        app.market_monitor = Mock()
        app.data_manager = Mock()
        app.performance_tracker = Mock()
        app.scheduler = Mock()
        
        # Shutdown
        app.shutdown()
        
        # Verify all components were shut down
        app.market_monitor.stop_monitoring.assert_called_once()
        app.scheduler.stop.assert_called_once()
        app.data_manager.close.assert_called_once()
        app.performance_tracker.close.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
