"""
Demo script showing how to use ConfigurationManager

This script demonstrates:
1. Loading configuration from environment variables
2. Validating configuration at startup
3. Accessing configuration values
4. Handling configuration errors
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.configuration_manager import (
    ConfigurationManager,
    ConfigurationError,
    initialize_config
)


def demo_basic_usage():
    """Demonstrate basic configuration usage"""
    print("=" * 60)
    print("Demo 1: Basic Configuration Usage")
    print("=" * 60)
    
    try:
        # Initialize and validate configuration
        config = initialize_config()
        
        print("\n✓ Configuration loaded and validated successfully!")
        
        # Access database configuration
        print(f"\nDatabase Configuration:")
        print(f"  Redis URL: {config.redis_url}")
        print(f"  Database URL: {config.database_url}")
        
        # Access email configuration
        print(f"\nEmail Configuration:")
        print(f"  User Email: {config.user_email}")
        print(f"  Recipients: {', '.join(config.recipient_emails)}")
        print(f"  Newsletter Time: {config.newsletter_time}")
        
        # Access cache TTL configuration
        print(f"\nCache TTL Configuration:")
        ttl_config = config.cache_ttl_config
        print(f"  Active Stock TTL: {ttl_config.active_stock_ttl}s")
        print(f"  Watchlist Stock TTL: {ttl_config.watchlist_stock_ttl}s")
        
        # Access alert limits
        print(f"\nAlert Limits:")
        alert_config = config.alert_limits_config
        print(f"  Max Alerts Per Day: {alert_config.max_trading_alerts_per_day}")
        print(f"  Generation Timeout: {alert_config.alert_generation_timeout_seconds}s")
        print(f"  Delivery Timeout: {alert_config.alert_delivery_timeout_seconds}s")
        
        # Access position sizing
        print(f"\nPosition Sizing Configuration:")
        position_config = config.position_sizing_config
        print(f"  Low Risk: {position_config.low_risk_min}% - {position_config.low_risk_max}%")
        print(f"  Medium Risk: {position_config.medium_risk_min}% - {position_config.medium_risk_max}%")
        print(f"  High Risk: {position_config.high_risk_min}% - {position_config.high_risk_max}%")
        
        # Access application settings
        print(f"\nApplication Settings:")
        print(f"  Environment: {config.environment}")
        print(f"  Log Level: {config.log_level}")
        print(f"  Is Production: {config.is_production}")
        print(f"  Is Development: {config.is_development}")
        
    except ConfigurationError as e:
        print(f"\n✗ Configuration Error:")
        print(f"{e}")
        return False
    
    return True


def demo_validation_errors():
    """Demonstrate configuration validation errors"""
    print("\n" + "=" * 60)
    print("Demo 2: Configuration Validation Errors")
    print("=" * 60)
    
    # Save original environment
    original_redis_url = os.environ.get('REDIS_URL')
    
    try:
        # Remove required configuration
        if 'REDIS_URL' in os.environ:
            del os.environ['REDIS_URL']
        
        # Try to initialize - should fail
        config = ConfigurationManager()
        config.validate_configuration()
        
        print("\n✗ Validation should have failed but didn't!")
        
    except ConfigurationError as e:
        print("\n✓ Validation correctly detected missing configuration:")
        print(f"\n{e}")
    
    finally:
        # Restore original environment
        if original_redis_url:
            os.environ['REDIS_URL'] = original_redis_url


def demo_credential_rotation():
    """Demonstrate credential rotation support"""
    print("\n" + "=" * 60)
    print("Demo 3: Credential Rotation Support")
    print("=" * 60)
    
    print("\nConfiguration is loaded from environment variables.")
    print("To rotate credentials without code changes:")
    print("  1. Update environment variables (e.g., in .env file)")
    print("  2. Restart the application")
    print("  3. New credentials are automatically loaded")
    
    print("\nExample:")
    print("  # Old credential")
    print("  FINNHUB_API_KEY=old_key_12345")
    print()
    print("  # Update to new credential")
    print("  FINNHUB_API_KEY=new_key_67890")
    print()
    print("  # Restart application - new key is used")
    
    print("\n✓ No code changes required for credential rotation!")


def demo_startup_validation():
    """Demonstrate startup validation pattern"""
    print("\n" + "=" * 60)
    print("Demo 4: Startup Validation Pattern")
    print("=" * 60)
    
    print("\nRecommended pattern for application startup:")
    print("""
def main():
    try:
        # Initialize and validate configuration at startup
        config = initialize_config()
        
        # If we get here, configuration is valid
        print("Starting Investment Scout...")
        
        # Start application components
        # market_monitor = MarketMonitor(config)
        # data_manager = DataManager(config)
        # ...
        
    except ConfigurationError as e:
        # Configuration is invalid - fail fast with descriptive error
        print(f"Configuration Error: {e}")
        sys.exit(1)
    
    except Exception as e:
        # Other startup errors
        print(f"Startup Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
    """)
    
    print("✓ This pattern ensures invalid configuration is caught at startup")
    print("  rather than during operation!")


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("ConfigurationManager Demo")
    print("=" * 60)
    
    # Check if .env file exists
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
    if not os.path.exists(env_file):
        print("\n⚠ Warning: .env file not found")
        print("  Copy .env.example to .env and fill in your credentials")
        print("  to run this demo with real configuration.")
        print("\n  For now, the demo will show validation errors.")
    
    # Run demos
    success = demo_basic_usage()
    
    if success:
        demo_validation_errors()
        demo_credential_rotation()
        demo_startup_validation()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
