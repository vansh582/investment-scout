"""
Email Service Demo

Demonstrates how to use EmailService to send newsletters and trading alerts.
"""

import os
import sys
from datetime import datetime
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.email_service import EmailService
from src.utils.credential_manager import CredentialManager
from src.utils.newsletter_generator import NewsletterGenerator
from src.utils.alert_generator import AlertGenerator
from src.models.investment_scout_models import (
    Newsletter, InvestmentOpportunity, TradingAlert,
    GlobalContext, RiskLevel, SignalType
)


def demo_newsletter_delivery():
    """Demonstrate newsletter delivery"""
    print("=" * 60)
    print("Newsletter Delivery Demo")
    print("=" * 60)
    
    # Initialize services
    credential_manager = CredentialManager()
    email_service = EmailService(credential_manager)
    newsletter_generator = NewsletterGenerator()
    
    # Create sample opportunity
    opportunity = InvestmentOpportunity(
        symbol="AAPL",
        company_name="Apple Inc.",
        current_price=Decimal("175.50"),
        target_price=Decimal("200.00"),
        position_size_percent=Decimal("15.0"),
        investment_thesis="Strong iPhone demand and services growth",
        global_context=GlobalContext(
            economic_factors=["Strong consumer spending", "Low unemployment"],
            geopolitical_events=["US-China trade stabilization"],
            industry_dynamics=["AI integration in consumer devices"],
            company_specifics=["Record Q4 earnings", "New product launches"],
            timing_rationale="Post-earnings dip presents buying opportunity",
            risk_factors=["Supply chain disruptions", "Regulatory scrutiny"]
        ),
        expected_return=Decimal("14.0"),
        risk_level=RiskLevel.LOW,
        expected_holding_period="6-12 months",
        data_timestamp=datetime.now()
    )
    
    # Create newsletter
    newsletter = Newsletter(
        date=datetime.now(),
        market_overview="Markets showing strength with tech sector leading gains.",
        opportunities=[opportunity],
        performance_summary="Portfolio up 12% vs S&P 500 up 8% YTD",
        generated_at=datetime.now()
    )
    
    # Generate email content
    html_content = newsletter_generator.format_html(newsletter)
    plain_text_content = newsletter_generator.format_plain_text(newsletter)
    
    print("\nNewsletter Content Generated:")
    print(f"- Opportunities: {len(newsletter.opportunities)}")
    print(f"- HTML length: {len(html_content)} chars")
    print(f"- Plain text length: {len(plain_text_content)} chars")
    
    # Send newsletter (commented out to avoid actual sending)
    # recipients = [credential_manager.get_credential('user_email')]
    # success = email_service.send_newsletter(
    #     html_content=html_content,
    #     plain_text_content=plain_text_content,
    #     recipients=recipients,
    #     subject=f"Investment Scout Daily - {newsletter.date.strftime('%B %d, %Y')}"
    # )
    # print(f"\nNewsletter delivery: {'SUCCESS' if success else 'FAILED'}")
    
    print("\n✓ Newsletter delivery demo complete (actual sending commented out)")


def demo_alert_delivery():
    """Demonstrate trading alert delivery"""
    print("\n" + "=" * 60)
    print("Trading Alert Delivery Demo")
    print("=" * 60)
    
    # Initialize services
    credential_manager = CredentialManager()
    email_service = EmailService(credential_manager)
    alert_generator = AlertGenerator()
    
    # Create sample trading alert
    alert = TradingAlert(
        symbol="TSLA",
        company_name="Tesla Inc.",
        signal_type=SignalType.BUY,
        current_price=Decimal("245.00"),
        entry_price=Decimal("245.00"),
        target_price=Decimal("270.00"),
        stop_loss=Decimal("235.00"),
        position_size_percent=Decimal("10.0"),
        rationale="Breakout above resistance with strong volume confirmation",
        expected_holding_period="3-7 days",
        data_timestamp=datetime.now()
    )
    
    # Generate alert content
    html_content = alert_generator.format_alert_html(alert)
    plain_text_content = alert_generator.format_alert_plain_text(alert)
    
    print("\nTrading Alert Content Generated:")
    print(f"- Signal: {alert.signal_type.value.upper()}")
    print(f"- Symbol: {alert.symbol}")
    print(f"- Entry: ${alert.entry_price}")
    print(f"- Target: ${alert.target_price}")
    print(f"- Stop Loss: ${alert.stop_loss}")
    print(f"- HTML length: {len(html_content)} chars")
    print(f"- Plain text length: {len(plain_text_content)} chars")
    
    # Send alert (commented out to avoid actual sending)
    # recipients = [credential_manager.get_credential('user_email')]
    # success = email_service.send_alert(
    #     html_content=html_content,
    #     plain_text_content=plain_text_content,
    #     recipients=recipients,
    #     subject=f"🚨 Trading Alert: {alert.signal_type.value.upper()} {alert.symbol}"
    # )
    # print(f"\nAlert delivery: {'SUCCESS' if success else 'FAILED'}")
    
    print("\n✓ Trading alert delivery demo complete (actual sending commented out)")


def demo_retry_logic():
    """Demonstrate retry logic"""
    print("\n" + "=" * 60)
    print("Retry Logic Demo")
    print("=" * 60)
    
    print("\nRetry Strategy:")
    print("- Initial attempt: Immediate")
    print("- Retry 1: Wait 5 seconds")
    print("- Retry 2: Wait 15 seconds")
    print("- Retry 3: Wait 45 seconds")
    print("- Total attempts: 4 (initial + 3 retries)")
    
    print("\nDelivery Requirements:")
    print("- Newsletters: Must be delivered before 9:00 AM ET")
    print("- Trading Alerts: Must be delivered within 30 seconds")
    
    print("\nError Handling:")
    print("- Network errors: Retry with exponential backoff")
    print("- API errors: Retry with exponential backoff")
    print("- Newsletter failure: Send system alert after all retries")
    print("- Alert failure: Log error (time-sensitive, no system alert)")
    
    print("\n✓ Retry logic demo complete")


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("EMAIL SERVICE DEMONSTRATION")
    print("=" * 60)
    
    try:
        demo_newsletter_delivery()
        demo_alert_delivery()
        demo_retry_logic()
        
        print("\n" + "=" * 60)
        print("All demos completed successfully!")
        print("=" * 60)
        
        print("\nTo enable actual email sending:")
        print("1. Set up SendGrid account and get API key")
        print("2. Add SENDGRID_API_KEY to .env file")
        print("3. Add USER_EMAIL to .env file")
        print("4. Uncomment the email sending code in the demos")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
