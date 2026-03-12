"""
Newsletter Generator Demo

Demonstrates newsletter generation with sample opportunities.
Run this to see example HTML and plain text output.
"""

from datetime import datetime
from decimal import Decimal

from src.utils.newsletter_generator import NewsletterGenerator
from src.models.investment_scout_models import (
    InvestmentOpportunity,
    GlobalContext,
    RiskLevel
)


def create_sample_opportunity():
    """Create a sample investment opportunity"""
    return InvestmentOpportunity(
        symbol="AAPL",
        company_name="Apple Inc.",
        current_price=Decimal("175.00"),
        target_price=Decimal("210.00"),
        position_size_percent=Decimal("18.0"),
        investment_thesis=(
            "Apple continues to demonstrate strong fundamentals with growing services revenue "
            "and ecosystem expansion. The company's transition to Apple Silicon has improved "
            "margins while the Vision Pro launch opens new growth avenues. Strong brand loyalty "
            "and cash generation provide downside protection."
        ),
        global_context=GlobalContext(
            economic_factors=[
                "Consumer spending remains resilient despite inflation concerns",
                "Premium product demand holding up well",
                "Services sector showing strong growth"
            ],
            geopolitical_events=[
                "US-China tensions creating supply chain diversification opportunities",
                "India manufacturing expansion reducing geopolitical risk"
            ],
            industry_dynamics=[
                "Smartphone market stabilizing after post-pandemic decline",
                "Wearables and services driving incremental growth",
                "AI integration becoming key differentiator"
            ],
            company_specifics=[
                "Services revenue at all-time high with 20% margins",
                "iPhone 15 cycle showing strong demand",
                "Vision Pro pre-orders exceeding expectations",
                "$90B+ annual buyback program supporting stock"
            ],
            timing_rationale=(
                "Recent 15% pullback from highs provides attractive entry point. "
                "Holiday quarter typically strong for Apple. New product launches "
                "creating positive momentum heading into 2024."
            ),
            risk_factors=[
                "China demand uncertainty amid economic slowdown",
                "Regulatory scrutiny on App Store practices",
                "High valuation relative to historical averages",
                "Mature smartphone market limiting growth"
            ]
        ),
        expected_return=Decimal("20.0"),
        risk_level=RiskLevel.MEDIUM,
        expected_holding_period="9-12 months",
        data_timestamp=datetime.now()
    )


def main():
    """Generate and display sample newsletter"""
    print("\n" + "="*80)
    print("NEWSLETTER GENERATOR DEMO")
    print("="*80)
    
    # Create sample opportunity
    opportunity = create_sample_opportunity()
    
    # Initialize generator
    generator = NewsletterGenerator()
    
    # Generate newsletter
    print("\n📧 Generating newsletter...")
    newsletter = generator.generate_newsletter([opportunity])
    
    print(f"✅ Newsletter generated successfully!")
    print(f"   Date: {newsletter.date.strftime('%B %d, %Y')}")
    print(f"   Opportunities: {len(newsletter.opportunities)}")
    
    # Generate HTML
    print("\n🌐 Generating HTML format...")
    html = generator.format_html(newsletter)
    print(f"✅ HTML generated: {len(html)} characters")
    
    # Generate plain text
    print("\n📄 Generating plain text format...")
    text = generator.format_plain_text(newsletter)
    print(f"✅ Plain text generated: {len(text)} characters")
    
    # Display plain text preview
    print("\n" + "="*80)
    print("PLAIN TEXT PREVIEW")
    print("="*80)
    print(text[:1000] + "...\n[truncated]")
    
    # Save outputs
    print("\n💾 Saving outputs...")
    with open("newsletter_sample.html", "w") as f:
        f.write(html)
    print("   ✅ Saved: newsletter_sample.html")
    
    with open("newsletter_sample.txt", "w") as f:
        f.write(text)
    print("   ✅ Saved: newsletter_sample.txt")
    
    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80)
    print("\nOpen newsletter_sample.html in a browser to see the formatted newsletter!")
    print()


if __name__ == "__main__":
    main()
