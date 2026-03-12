# Email Service Documentation

## Overview

The EmailService component delivers newsletters and trading alerts via SendGrid free tier (100 emails/day). It implements robust retry logic with exponential backoff and ensures delivery timing constraints are met.

## Features

- **SendGrid Integration**: Uses SendGrid free tier for email delivery
- **Retry Logic**: Exponential backoff (5s, 15s, 45s) for failed deliveries
- **Timing Constraints**: 
  - Newsletters delivered before 9:00 AM ET
  - Trading alerts delivered within 30 seconds
- **Comprehensive Logging**: All delivery attempts and final status logged
- **System Alerts**: Automatic alert if newsletter fails after all retries
- **Multi-recipient Support**: Send to multiple recipients in one call

## Architecture

```
EmailService
├── send_newsletter()      # Send daily newsletter
├── send_alert()          # Send trading alert
├── send_with_retry()     # Core retry logic
└── _send_system_alert()  # System failure notifications
```

## Usage

### Basic Setup

```python
from src.utils.email_service import EmailService
from src.utils.credential_manager import CredentialManager

# Initialize
credential_manager = CredentialManager()
email_service = EmailService(credential_manager)
```

### Send Newsletter

```python
from src.utils.newsletter_generator import NewsletterGenerator

# Generate newsletter content
newsletter_generator = NewsletterGenerator()
html_content = newsletter_generator.format_html(newsletter)
plain_text_content = newsletter_generator.format_plain_text(newsletter)

# Send newsletter
success = email_service.send_newsletter(
    html_content=html_content,
    plain_text_content=plain_text_content,
    recipients=["user@example.com"],
    subject="Investment Scout Daily - January 15, 2024"
)

if success:
    print("Newsletter delivered successfully")
else:
    print("Newsletter delivery failed after all retries")
```

### Send Trading Alert

```python
from src.utils.alert_generator import AlertGenerator

# Generate alert content
alert_generator = AlertGenerator()
html_content = alert_generator.format_alert_html(alert)
plain_text_content = alert_generator.format_alert_plain_text(alert)

# Send alert
success = email_service.send_alert(
    html_content=html_content,
    plain_text_content=plain_text_content,
    recipients=["user@example.com"],
    subject="🚨 Trading Alert: BUY TSLA"
)

if success:
    print("Alert delivered successfully")
else:
    print("Alert delivery failed")
```

## Retry Logic

### Exponential Backoff Strategy

The EmailService implements exponential backoff for failed deliveries:

1. **Initial Attempt**: Immediate
2. **Retry 1**: Wait 5 seconds
3. **Retry 2**: Wait 15 seconds  
4. **Retry 3**: Wait 45 seconds
5. **Total**: 4 attempts (initial + 3 retries)

### Example Retry Sequence

```
Attempt 1: [FAIL] → Wait 5s
Attempt 2: [FAIL] → Wait 15s
Attempt 3: [FAIL] → Wait 45s
Attempt 4: [SUCCESS] ✓
```

### Retry Behavior

```python
# Automatic retry with exponential backoff
result = email_service.send_with_retry(
    subject="Test Email",
    html_content="<html>Test</html>",
    plain_text_content="Test",
    recipients=["user@example.com"],
    max_retries=3  # Default: 3
)
```

## Timing Constraints

### Newsletter Delivery

- **Requirement**: Delivered before 9:00 AM Eastern Time
- **Behavior**: Logs warning if sent after deadline
- **Failure Handling**: Sends system alert if all retries fail

```python
# Newsletter timing check
et_tz = pytz.timezone('US/Eastern')
current_time_et = datetime.now(et_tz).time()
deadline = time(9, 0)  # 9:00 AM

if current_time_et >= deadline:
    logger.warning("Newsletter delivery attempted after 9:00 AM ET deadline")
```

### Trading Alert Delivery

- **Requirement**: Delivered within 30 seconds
- **Behavior**: Logs warning if exceeds 30 seconds
- **Failure Handling**: Logs error (no system alert for time-sensitive alerts)

```python
# Alert timing tracking
start_time = time.time()
success = email_service.send_alert(...)
elapsed_time = time.time() - start_time

if elapsed_time > 30:
    logger.warning(f"Alert delivery took {elapsed_time:.2f} seconds")
```

## System Alerts

When newsletter delivery fails after all retries, the EmailService automatically sends a system alert to the admin:

```python
# Automatic system alert on newsletter failure
if not success:
    email_service._send_system_alert(
        "Newsletter Delivery Failure",
        f"Failed to deliver newsletter to {len(recipients)} recipients"
    )
```

### System Alert Format

```
Subject: 🚨 Investment Scout System Alert: Newsletter Delivery Failure

Newsletter Delivery Failure

Failed to deliver newsletter to 5 recipients after 3 retry attempts

Timestamp: 2024-01-15T08:45:23.123456
```

## Logging

### Log Levels

- **INFO**: Normal operations (sending, successful delivery)
- **WARNING**: Timing violations, retries
- **ERROR**: Delivery failures
- **CRITICAL**: Newsletter failure after all retries

### Log Examples

```python
# Successful delivery
logger.info(
    "Email delivered successfully on attempt 1",
    extra={
        "status_code": 202,
        "attempt": 1,
        "recipients_count": 5
    }
)

# Retry attempt
logger.error(
    "Email delivery attempt 2 failed: Network timeout",
    extra={
        "attempt": 2,
        "error_type": "ConnectionError",
        "error_message": "Network timeout"
    }
)

# Final failure
logger.error(
    "Email delivery failed after 4 attempts",
    extra={
        "total_attempts": 4,
        "final_error": "SendGrid API error"
    }
)
```

## Configuration

### Environment Variables

Required environment variables in `.env`:

```bash
# SendGrid Configuration
SENDGRID_API_KEY=your_sendgrid_api_key_here
USER_EMAIL=your_email@example.com

# Optional: Override retry settings in code
# MAX_RETRIES=3
# RETRY_DELAYS=[5, 15, 45]
```

### SendGrid Free Tier Limits

- **Daily Limit**: 100 emails/day
- **Usage**: 1 newsletter + max 5 alerts = 6 emails/day
- **Headroom**: 94 emails/day available for testing/other uses

## Error Handling

### Network Errors

```python
try:
    response = self.client.send(message)
except ConnectionError as e:
    logger.error(f"Network error: {str(e)}")
    # Automatic retry with exponential backoff
```

### API Errors

```python
try:
    response = self.client.send(message)
except Exception as e:
    logger.error(f"SendGrid API error: {str(e)}")
    # Automatic retry with exponential backoff
```

### Rate Limit Errors

SendGrid free tier has generous limits, but if rate limiting occurs:

```python
# SendGrid returns 429 status code
# EmailService will retry after backoff delay
```

## Testing

### Unit Tests

Run the comprehensive test suite:

```bash
python3 -m pytest tests/test_email_service.py -v
```

### Test Coverage

- ✓ Initialization and credential retrieval
- ✓ Newsletter delivery success/failure
- ✓ Trading alert delivery success/failure
- ✓ Retry logic with exponential backoff
- ✓ Timing constraint validation
- ✓ System alert generation
- ✓ Multi-recipient support
- ✓ Error handling (network, API, rate limits)
- ✓ Comprehensive logging

### Mock Testing

```python
from unittest.mock import Mock, patch

# Mock SendGrid client
with patch('src.utils.email_service.SendGridAPIClient') as mock_sg:
    email_service = EmailService(credential_manager)
    email_service.client = Mock()
    
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 202
    email_service.client.send.return_value = mock_response
    
    # Test delivery
    success = email_service.send_newsletter(...)
    assert success is True
```

## Integration

### With Newsletter Generator

```python
from src.utils.newsletter_generator import NewsletterGenerator
from src.utils.email_service import EmailService

# Generate newsletter
newsletter_generator = NewsletterGenerator()
newsletter = newsletter_generator.generate_newsletter(opportunities)

# Format content
html_content = newsletter_generator.format_html(newsletter)
plain_text_content = newsletter_generator.format_plain_text(newsletter)

# Send via email service
email_service = EmailService(credential_manager)
email_service.send_newsletter(
    html_content=html_content,
    plain_text_content=plain_text_content,
    recipients=recipients,
    subject=f"Investment Scout Daily - {newsletter.date.strftime('%B %d, %Y')}"
)
```

### With Alert Generator

```python
from src.utils.alert_generator import AlertGenerator
from src.utils.email_service import EmailService

# Generate alert
alert_generator = AlertGenerator()
html_content = alert_generator.format_alert_html(alert)
plain_text_content = alert_generator.format_alert_plain_text(alert)

# Send via email service
email_service = EmailService(credential_manager)
email_service.send_alert(
    html_content=html_content,
    plain_text_content=plain_text_content,
    recipients=recipients,
    subject=f"🚨 Trading Alert: {alert.signal_type.value.upper()} {alert.symbol}"
)
```

## Performance

### Delivery Times

- **Newsletter**: Typically 1-3 seconds (without retries)
- **Trading Alert**: Typically 1-2 seconds (without retries)
- **With Retries**: Up to 65 seconds (initial + 5s + 15s + 45s)

### Memory Usage

- **Minimal**: ~1-2 MB per email operation
- **No Caching**: Emails sent immediately, not stored

### Throughput

- **Sequential**: 1 email at a time
- **Daily Capacity**: 100 emails (SendGrid free tier)
- **Typical Usage**: 6 emails/day (1 newsletter + 5 alerts max)

## Best Practices

### 1. Always Use Both HTML and Plain Text

```python
# Good: Provide both formats
email_service.send_newsletter(
    html_content=html_content,
    plain_text_content=plain_text_content,
    recipients=recipients,
    subject=subject
)

# Bad: Only HTML (some clients don't support it)
email_service.send_newsletter(
    html_content=html_content,
    plain_text_content="",  # Empty!
    recipients=recipients,
    subject=subject
)
```

### 2. Handle Failures Gracefully

```python
success = email_service.send_newsletter(...)

if not success:
    # Log for manual review
    logger.error("Newsletter delivery failed - manual intervention required")
    
    # Store newsletter in database for later retry
    db.store_failed_newsletter(newsletter)
```

### 3. Monitor SendGrid Usage

```python
# Track daily email count
daily_count = db.get_email_count_today()

if daily_count >= 95:  # Near limit
    logger.warning(f"Approaching SendGrid daily limit: {daily_count}/100")
```

### 4. Test Before Production

```python
# Test with your own email first
test_recipients = [credential_manager.get_credential('user_email')]

success = email_service.send_newsletter(
    html_content=html_content,
    plain_text_content=plain_text_content,
    recipients=test_recipients,
    subject="TEST: " + subject
)
```

## Troubleshooting

### Issue: Emails Not Sending

**Check:**
1. SendGrid API key is valid
2. API key has send permissions
3. From email is verified in SendGrid
4. No rate limiting (check SendGrid dashboard)

### Issue: Emails Going to Spam

**Solutions:**
1. Verify sender domain in SendGrid
2. Set up SPF/DKIM records
3. Use consistent from address
4. Avoid spam trigger words in subject

### Issue: Slow Delivery

**Check:**
1. Network latency
2. SendGrid API status
3. Retry delays (expected for failures)

### Issue: Newsletter After 9 AM

**Solutions:**
1. Start newsletter generation earlier (8:00 AM)
2. Optimize opportunity analysis
3. Pre-generate content at 8:30 AM

## Future Enhancements

### Planned Features

1. **Batch Sending**: Send to multiple recipients more efficiently
2. **Template Support**: Use SendGrid templates for consistent branding
3. **Delivery Tracking**: Track open rates and click rates
4. **Unsubscribe Management**: Handle unsubscribe requests
5. **A/B Testing**: Test different subject lines and content

### Potential Improvements

1. **Async Sending**: Non-blocking email delivery
2. **Queue System**: Queue emails for batch processing
3. **Retry Strategies**: Configurable retry delays
4. **Fallback Providers**: Use alternative email services if SendGrid fails

## Related Documentation

- [Newsletter Generator](NEWSLETTER_GENERATOR.md)
- [Alert Generator](ALERT_GENERATOR.md)
- [Credential Manager](../src/utils/credential_manager.py)
- [SendGrid API Documentation](https://docs.sendgrid.com/)

## Support

For issues or questions:
1. Check logs for error details
2. Verify SendGrid configuration
3. Review test suite for examples
4. Check SendGrid dashboard for delivery status
