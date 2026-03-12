# Alert Generator Documentation

## Overview

The `AlertGenerator` class creates instant trading alert emails for short-term buy/sell opportunities. It generates both HTML and plain text formats with clear action indicators, entry/exit levels, and beginner-friendly explanations.

## Features

- **Dual Format Support**: Generates both HTML and plain text email formats
- **Clear Action Indicators**: Prominent BUY/SELL signals with color coding
- **Complete Trading Information**: Entry price, target price, stop loss, position size
- **Risk Management**: Includes stop loss levels and risk reminders
- **Beginner-Friendly**: Clear explanations without assuming trading knowledge
- **Professional Styling**: Responsive HTML design with proper formatting
- **Compliance**: Includes comprehensive disclaimer

## Class: AlertGenerator

### Methods

#### `__init__()`
Initialize the Alert Generator.

```python
generator = AlertGenerator()
```

#### `generate_alert(alert: TradingAlert) -> str`
Generate alert email content from trading alert.

**Parameters:**
- `alert`: TradingAlert object with opportunity details

**Returns:**
- Formatted alert content string

**Raises:**
- `ValueError`: If alert is None

**Example:**
```python
content = generator.generate_alert(trading_alert)
```

#### `format_alert_html(alert: TradingAlert) -> str`
Format trading alert as HTML email.

**Parameters:**
- `alert`: TradingAlert object to format

**Returns:**
- HTML string for email body

**Features:**
- Responsive design (max-width: 700px)
- Color-coded action header (green for BUY, red for SELL)
- Styled trading levels section
- Professional typography and spacing
- Mobile-friendly layout

**Example:**
```python
html = generator.format_alert_html(trading_alert)
```

#### `format_alert_plain_text(alert: TradingAlert) -> str`
Format trading alert as plain text alternative.

**Parameters:**
- `alert`: TradingAlert object to format

**Returns:**
- Plain text string for email body

**Features:**
- Clear section separators
- Readable formatting with proper spacing
- All information from HTML version
- Works in any email client

**Example:**
```python
text = generator.format_alert_plain_text(trading_alert)
```

## Alert Structure

### HTML Format

1. **Alert Header**
   - 🚨 TRADING ALERT title
   - BUY/SELL action with symbol
   - Color-coded background (green/red)

2. **Company Information**
   - Company name and symbol
   - Current price

3. **Trading Levels**
   - Entry price
   - Target price with expected gain %
   - Stop loss with max loss %
   - Position size (% of portfolio)
   - Expected holding period

4. **Rationale**
   - Explanation of why this opportunity exists
   - Beginner-friendly language

5. **Important Reminders**
   - Risk management guidelines
   - Trading best practices

6. **Disclaimer**
   - Legal disclaimer about financial advice
   - Risk warnings

7. **Footer**
   - Generation timestamp
   - Investment Scout branding

### Plain Text Format

Same structure as HTML but with:
- ASCII separators (=, -)
- Left-aligned text
- Clear section headers
- Readable spacing

## Usage Example

```python
from datetime import datetime
from decimal import Decimal
from src.utils.alert_generator import AlertGenerator
from src.models.investment_scout_models import TradingAlert, SignalType

# Create generator
generator = AlertGenerator()

# Create trading alert
alert = TradingAlert(
    symbol="AAPL",
    company_name="Apple Inc.",
    signal_type=SignalType.BUY,
    current_price=Decimal("150.00"),
    entry_price=Decimal("150.50"),
    target_price=Decimal("160.00"),
    stop_loss=Decimal("145.00"),
    position_size_percent=Decimal("5.0"),
    rationale="Strong breakout above resistance with high volume confirmation.",
    expected_holding_period="2-5 days",
    data_timestamp=datetime.now()
)

# Generate HTML
html = generator.format_alert_html(alert)

# Generate plain text
text = generator.format_alert_plain_text(alert)

# Use in email service
email_service.send_alert(html, text, recipients)
```

## Design Principles

### 1. Clarity First
- Clear BUY/SELL action at the top
- All critical information prominently displayed
- No ambiguity about what to do

### 2. Risk Management
- Always includes stop loss
- Shows both potential gain and max loss
- Includes risk reminders
- Emphasizes position sizing

### 3. Beginner-Friendly
- Explains the opportunity in plain language
- No jargon without explanation
- Clear structure and formatting

### 4. Professional Presentation
- Clean, modern design
- Consistent styling
- Mobile-responsive
- Works across email clients

### 5. Compliance
- Comprehensive disclaimer
- Clear risk warnings
- Not presented as financial advice

## Color Coding

- **BUY Alerts**: Green (#27ae60)
- **SELL Alerts**: Red (#e74c3c)
- **Gains**: Green text
- **Losses**: Red text
- **Warnings**: Yellow background (#fff3cd)
- **Disclaimer**: Light red background (#f8d7da)

## Percentage Calculations

The generator automatically calculates:

**Expected Gain:**
```
(target_price - entry_price) / entry_price * 100
```

**Max Loss:**
```
(stop_loss - entry_price) / entry_price * 100
```

Both are displayed with appropriate +/- signs and color coding.

## Testing

Comprehensive test suite with 24 tests covering:
- Alert generation for BUY and SELL signals
- HTML formatting with styling
- Plain text formatting
- Percentage calculations
- Error handling
- Edge cases (min/max position sizes, various holding periods)
- Disclaimer inclusion
- Timestamp formatting

Run tests:
```bash
python3 -m pytest tests/test_alert_generator.py -v
```

## Requirements Validation

**Validates Requirements:**
- 12.4: Alert content generation with clear BUY/SELL action
- 12.6: Include entry, target, stop loss, position size, holding period
- 12.7: Beginner-friendly explanations

## Integration

The AlertGenerator integrates with:
- **TradingAnalyzer**: Receives TradingAlert objects
- **EmailService**: Provides HTML and plain text for delivery
- **Data Models**: Uses TradingAlert and SignalType from investment_scout_models

## Sample Output

See generated samples:
- `alert_buy_sample.html` - HTML BUY alert
- `alert_buy_sample.txt` - Plain text BUY alert
- `alert_sell_sample.html` - HTML SELL alert
- `alert_sell_sample.txt` - Plain text SELL alert

Generate samples:
```bash
PYTHONPATH=. python3 examples/alert_demo.py
```

## Future Enhancements

Potential improvements:
- Multi-language support
- Customizable templates
- Chart/graph embedding
- Historical performance context
- Related news links
- Social sentiment indicators
