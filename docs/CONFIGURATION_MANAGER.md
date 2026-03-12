# Configuration Manager

## Overview

The `ConfigurationManager` is responsible for loading, validating, and providing access to all system configuration from environment variables. It ensures that all required credentials and settings are present and valid before the application starts.

## Features

- **Environment Variable Loading**: Loads all configuration from environment variables
- **Startup Validation**: Validates all required configuration at startup with descriptive error messages
- **Type Safety**: Provides strongly-typed access to configuration values
- **Credential Rotation**: Supports credential rotation without code changes
- **Default Values**: Provides sensible defaults for optional configuration
- **Comprehensive Validation**: Validates formats, ranges, and logical consistency

## Configuration Categories

### 1. Database Configuration

```python
config.redis_url          # Redis connection URL
config.database_url       # PostgreSQL connection URL
```

**Environment Variables:**
- `REDIS_URL` (required): Redis connection string
- `DATABASE_URL` (required): PostgreSQL connection string

**Example:**
```bash
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:password@localhost:5432/investment_scout
```

### 2. API Credentials

```python
config.robinhood_username      # Robinhood username
config.robinhood_password      # Robinhood password
config.finnhub_api_key         # Finnhub API key
config.twelve_data_api_key     # Twelve Data API key
config.sendgrid_api_key        # SendGrid API key
```

**Environment Variables:**
- `ROBINHOOD_USERNAME` (required)
- `ROBINHOOD_PASSWORD` (required)
- `FINNHUB_API_KEY` (required)
- `TWELVE_DATA_API_KEY` (required)
- `SENDGRID_API_KEY` (required)

**Security Note:** Credentials are never logged or displayed in plain text.

### 3. Email Configuration

```python
config.user_email              # User email address
config.recipient_emails        # List of recipient emails
config.newsletter_time         # Newsletter delivery time
```

**Environment Variables:**
- `USER_EMAIL` (required): Sender email address
- `RECIPIENT_EMAILS` (optional): Comma-separated list of recipients
- `NEWSLETTER_HOUR` (optional, default: 9): Newsletter hour (0-23)
- `NEWSLETTER_MINUTE` (optional, default: 0): Newsletter minute (0-59)

**Example:**
```bash
USER_EMAIL=sender@example.com
RECIPIENT_EMAILS=recipient1@example.com,recipient2@example.com
NEWSLETTER_HOUR=9
NEWSLETTER_MINUTE=0
```

### 4. Cache TTL Configuration

```python
config.active_stock_ttl        # Active stock cache TTL (seconds)
config.watchlist_stock_ttl     # Watchlist stock cache TTL (seconds)
config.cache_ttl_config        # Complete TTL configuration object
```

**Environment Variables:**
- `ACTIVE_STOCK_TTL` (optional, default: 15): Cache TTL for active stocks
- `WATCHLIST_STOCK_TTL` (optional, default: 60): Cache TTL for watchlist stocks
- `ROBINHOOD_TRADEABILITY_TTL` (optional, default: 86400): Tradeability cache TTL
- `COMPANY_INFO_TTL` (optional, default: 86400): Company info cache TTL
- `FINANCIAL_DATA_TTL` (optional, default: 21600): Financial data cache TTL

**Example:**
```bash
ACTIVE_STOCK_TTL=15
WATCHLIST_STOCK_TTL=60
ROBINHOOD_TRADEABILITY_TTL=86400
COMPANY_INFO_TTL=86400
FINANCIAL_DATA_TTL=21600
```

### 5. Alert Limits Configuration

```python
config.max_trading_alerts_per_day  # Maximum alerts per day
config.alert_limits_config         # Complete alert limits object
```

**Environment Variables:**
- `MAX_TRADING_ALERTS_PER_DAY` (optional, default: 3): Maximum trading alerts per day
- `ALERT_GENERATION_TIMEOUT` (optional, default: 10): Alert generation timeout (seconds)
- `ALERT_DELIVERY_TIMEOUT` (optional, default: 30): Alert delivery timeout (seconds)

**Example:**
```bash
MAX_TRADING_ALERTS_PER_DAY=3
ALERT_GENERATION_TIMEOUT=10
ALERT_DELIVERY_TIMEOUT=30
```

### 6. Position Sizing Configuration

```python
config.position_sizing_config  # Complete position sizing configuration
```

**Environment Variables:**
- `LOW_RISK_MIN` (optional, default: 15): Low risk minimum position size (%)
- `LOW_RISK_MAX` (optional, default: 25): Low risk maximum position size (%)
- `MEDIUM_RISK_MIN` (optional, default: 8): Medium risk minimum position size (%)
- `MEDIUM_RISK_MAX` (optional, default: 15): Medium risk maximum position size (%)
- `HIGH_RISK_MIN` (optional, default: 1): High risk minimum position size (%)
- `HIGH_RISK_MAX` (optional, default: 8): High risk maximum position size (%)

**Constraints:**
- All values must be between 1 and 25 (inclusive)
- MIN must be less than or equal to MAX for each risk level

**Example:**
```bash
LOW_RISK_MIN=15
LOW_RISK_MAX=25
MEDIUM_RISK_MIN=8
MEDIUM_RISK_MAX=15
HIGH_RISK_MIN=1
HIGH_RISK_MAX=8
```

### 7. Application Settings

```python
config.environment       # Application environment
config.log_level         # Logging level
config.is_production     # True if production environment
config.is_development    # True if development environment
```

**Environment Variables:**
- `ENVIRONMENT` (optional, default: development): Application environment
- `LOG_LEVEL` (optional, default: INFO): Logging level

**Example:**
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## Usage

### Basic Usage

```python
from src.utils.configuration_manager import initialize_config, ConfigurationError

try:
    # Initialize and validate configuration at startup
    config = initialize_config()
    
    # Access configuration values
    redis_url = config.redis_url
    api_key = config.finnhub_api_key
    
    # Use configuration objects
    ttl_config = config.cache_ttl_config
    print(f"Active stock TTL: {ttl_config.active_stock_ttl}s")
    
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    sys.exit(1)
```

### Startup Validation Pattern

```python
def main():
    """Application entry point"""
    try:
        # Validate configuration before starting
        config = initialize_config()
        
        # Configuration is valid - start application
        start_application(config)
        
    except ConfigurationError as e:
        # Configuration is invalid - fail fast
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
```

### Accessing Configuration

```python
# Get singleton instance
from src.utils.configuration_manager import get_config

config = get_config()

# Access individual values
redis_url = config.redis_url
api_key = config.finnhub_api_key

# Access configuration objects
cache_config = config.cache_ttl_config
alert_config = config.alert_limits_config
position_config = config.position_sizing_config
```

## Validation

The `validate_configuration()` method performs comprehensive validation:

### Required Fields Validation
- Checks that all required credentials are present
- Validates that values are not empty or whitespace-only

### Format Validation
- Email addresses must contain '@' symbol
- All recipient emails must be valid

### Range Validation
- TTL values must be positive integers
- Alert limits must be positive integers
- Position sizing must be between 1% and 25%

### Logical Consistency Validation
- MIN values must be ≤ MAX values for position sizing
- Newsletter time must be valid (0-23 hours, 0-59 minutes)

### Error Reporting
- Collects ALL validation errors (not just the first one)
- Provides descriptive error messages with field names
- Raises `ConfigurationError` with complete error list

**Example Error Message:**
```
Configuration validation failed:
  - Missing required configuration: REDIS_URL
  - Missing required configuration: FINNHUB_API_KEY
  - Invalid email format for USER_EMAIL: invalid_email
  - Invalid ACTIVE_STOCK_TTL: must be positive integer, got -5
  - LOW_RISK_MIN (20) cannot be greater than LOW_RISK_MAX (15)
```

## Credential Rotation

The ConfigurationManager supports credential rotation without code changes:

1. **Update Environment Variables**: Change credentials in `.env` file or environment
2. **Restart Application**: Restart the application process
3. **New Credentials Loaded**: New credentials are automatically loaded on startup

**Example:**
```bash
# Before rotation
FINNHUB_API_KEY=old_key_12345

# After rotation
FINNHUB_API_KEY=new_key_67890

# Restart application - new key is used
```

**Security Best Practices:**
- Store credentials in environment variables, not in code
- Use `.env` file for local development (add to `.gitignore`)
- Use platform-specific secret management in production (Heroku Config Vars, etc.)
- Rotate credentials regularly
- Never commit credentials to version control

## Configuration Objects

### CacheTTLConfig

```python
@dataclass
class CacheTTLConfig:
    active_stock_ttl: int              # seconds
    watchlist_stock_ttl: int           # seconds
    robinhood_tradeability_ttl: int    # seconds
    company_info_ttl: int              # seconds
    financial_data_ttl: int            # seconds
```

### PositionSizingConfig

```python
@dataclass
class PositionSizingConfig:
    low_risk_min: Decimal
    low_risk_max: Decimal
    medium_risk_min: Decimal
    medium_risk_max: Decimal
    high_risk_min: Decimal
    high_risk_max: Decimal
```

### AlertLimitsConfig

```python
@dataclass
class AlertLimitsConfig:
    max_trading_alerts_per_day: int
    alert_generation_timeout_seconds: int
    alert_delivery_timeout_seconds: int
```

## Error Handling

### ConfigurationError

Raised when configuration is invalid or missing.

```python
from src.utils.configuration_manager import ConfigurationError

try:
    config = initialize_config()
except ConfigurationError as e:
    # Handle configuration error
    print(f"Configuration error: {e}")
    sys.exit(1)
```

## Testing

### Unit Tests

Comprehensive unit tests are provided in `tests/test_configuration_manager.py`:

- Configuration loading tests
- Validation tests (missing, invalid, out-of-range values)
- Edge case tests (boundary values, empty strings, whitespace)
- Global instance management tests
- Credential rotation support tests

**Run tests:**
```bash
python3 -m pytest tests/test_configuration_manager.py -v
```

### Test Coverage

- ✓ Loading all configuration categories
- ✓ Default values for optional configuration
- ✓ Validation of required fields
- ✓ Format validation (emails, etc.)
- ✓ Range validation (TTLs, position sizing)
- ✓ Logical consistency validation
- ✓ Multiple error collection
- ✓ Edge cases and boundary values
- ✓ Credential rotation support

## Example

See `examples/configuration_demo.py` for a complete demonstration of:
- Basic configuration usage
- Validation error handling
- Credential rotation
- Startup validation pattern

**Run demo:**
```bash
python3 examples/configuration_demo.py
```

## Requirements Satisfied

This implementation satisfies the following requirements:

- **Requirement 9.1**: Store API keys and credentials in environment variables
- **Requirement 9.2**: Never log or display credentials in plain text
- **Requirement 9.3**: Validate all required credentials at startup
- **Requirement 9.4**: Fail startup with descriptive error messages for missing credentials
- **Requirement 9.5**: Support credential rotation without code changes
- **Requirement 16.1**: Read configuration from environment variables
- **Requirement 16.2**: Support configuration for Redis URL, PostgreSQL URL, and API credentials
- **Requirement 16.3**: Support configuration for cache TTL values
- **Requirement 16.4**: Support configuration for newsletter delivery time
- **Requirement 16.5**: Support configuration for recipient email addresses
- **Requirement 16.6**: Support configuration for trading alert frequency limits
- **Requirement 16.7**: Support configuration for position sizing parameters
- **Requirement 16.8**: Validate all configuration values at startup
- **Requirement 16.9**: Fail startup with descriptive error messages for invalid configuration

## Best Practices

1. **Always validate at startup**: Call `initialize_config()` at application startup
2. **Fail fast**: Exit immediately if configuration is invalid
3. **Use .env file**: Store configuration in `.env` file for local development
4. **Never commit credentials**: Add `.env` to `.gitignore`
5. **Use platform secrets**: Use Heroku Config Vars or similar in production
6. **Rotate regularly**: Rotate credentials regularly for security
7. **Document requirements**: Keep `.env.example` up to date with all required variables
8. **Test configuration**: Write tests for configuration-dependent code
