"""
Alert Generator Demo

Demonstrates the AlertGenerator functionality with sample trading alerts.
"""

from datetime import datetime
from decimal import Decimal

from src.utils.alert_generator import AlertGenerator
from src.models.investment_scout_models import TradingAlert, SignalType


def main():
    """Generate sample trading alerts"""
    
    # Initialize generator
    generator = AlertGenerator()
    
    # Create sample BUY alert
    buy_alert = TradingAlert(
        symbol="AAPL",
        company_name="Apple Inc.",
        signal_type=SignalType.BUY,
        current_price=Decimal("150.00"),
        entry_price=Decimal("150.50"),
        target_price=Decimal("160.00"),
        stop_loss=Decimal("145.00"),
        position_size_percent=Decimal("5.0"),
        rationale="Strong breakout above resistance with high volume confirmation. "
                  "Positive earnings surprise and new product launch creating momentum. "
                  "Technical indicators showing bullish divergence.",
        expected_holding_period="2-5 days",
        data_timestamp=datetime.now()
    )
    
    # Create sample SELL alert
    sell_alert = TradingAlert(
        symbol="TSLA",
        company_name="Tesla Inc.",
        signal_type=SignalType.SELL,
        current_price=Decimal("250.00"),
        entry_price=Decimal("249.50"),
        target_price=Decimal("230.00"),
        stop_loss=Decimal("255.00"),
        position_size_percent=Decimal("3.0"),
        rationale="Breakdown below key support level with increasing selling pressure. "
                  "Negative news on production delays and regulatory concerns. "
                  "Overbought conditions reversing.",
        expected_holding_period="1-3 days",
        data_timestamp=datetime.now()
    )
    
    # Generate HTML for BUY alert
    print("=" * 80)
    print("BUY ALERT - HTML FORMAT")
    print("=" * 80)
    buy_html = generator.format_alert_html(buy_alert)
    with open("alert_buy_sample.html", "w") as f:
        f.write(buy_html)
    print("✓ HTML saved to alert_buy_sample.html")
    print()
    
    # Generate plain text for BUY alert
    print("=" * 80)
    print("BUY ALERT - PLAIN TEXT FORMAT")
    print("=" * 80)
    buy_text = generator.format_alert_plain_text(buy_alert)
    print(buy_text)
    with open("alert_buy_sample.txt", "w") as f:
        f.write(buy_text)
    print("✓ Plain text saved to alert_buy_sample.txt")
    print()
    
    # Generate HTML for SELL alert
    print("=" * 80)
    print("SELL ALERT - HTML FORMAT")
    print("=" * 80)
    sell_html = generator.format_alert_html(sell_alert)
    with open("alert_sell_sample.html", "w") as f:
        f.write(sell_html)
    print("✓ HTML saved to alert_sell_sample.html")
    print()
    
    # Generate plain text for SELL alert
    print("=" * 80)
    print("SELL ALERT - PLAIN TEXT FORMAT")
    print("=" * 80)
    sell_text = generator.format_alert_plain_text(sell_alert)
    print(sell_text)
    with open("alert_sell_sample.txt", "w") as f:
        f.write(sell_text)
    print("✓ Plain text saved to alert_sell_sample.txt")
    print()
    
    print("=" * 80)
    print("Demo completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
