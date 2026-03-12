"""
Integration test for Newsletter Generator

Demonstrates end-to-end newsletter generation with all components.
"""

import pytest
from datetime import datetime
from decimal import Decimal

from src.utils.newsletter_generator import NewsletterGenerator
from src.models.investment_scout_models import (
    InvestmentOpportunity,
    GlobalContext,
    RiskLevel
)


def test_complete_newsletter_generation():
    """Test complete newsletter generation workflow"""
    
    # Create sample opportunities
    opportunities = []
    
    # Opportunity 1: Low risk tech stock
    opp1 = InvestmentOpportunity(
        symbol="MSFT",
        company_name="Microsoft Corporation",
        current_price=Decimal("380.00"),
        target_price=Decimal("450.00"),
        position_size_percent=Decimal("20.0"),
        investment_thesis=(
            "Microsoft continues to dominate cloud computing with Azure growing at 30% annually. "
            "The company's AI integration across products positions it well for the next decade. "
            "Strong balance sheet and consistent cash flow generation provide downside protection."
        ),
        global_context=GlobalContext(
            economic_factors=[
                "Strong corporate IT spending despite economic uncertainty",
                "Cloud migration accelerating across industries",
                "AI investment driving enterprise software demand"
            ],
            geopolitical_events=[
                "US-China tech decoupling creating opportunities for US cloud providers",
                "European data sovereignty regulations favoring Azure"
            ],
            industry_dynamics=[
                "Cloud computing market growing at 20% CAGR",
                "AI integration becoming competitive necessity",
                "Enterprise software consolidation trend"
            ],
            company_specifics=[
                "Azure revenue up 30% YoY",
                "Office 365 Copilot driving subscription growth",
                "Gaming division showing strong momentum"
            ],
            timing_rationale=(
                "Recent pullback provides attractive entry point. Q4 earnings beat expectations "
                "and guidance raised. AI product launches accelerating revenue growth."
            ),
            risk_factors=[
                "Regulatory scrutiny on market dominance",
                "Competition from AWS and Google Cloud",
                "Macroeconomic headwinds affecting IT budgets"
            ]
        ),
        expected_return=Decimal("18.4"),
        risk_level=RiskLevel.LOW,
        expected_holding_period="12-18 months",
        data_timestamp=datetime.now()
    )
    opportunities.append(opp1)
    
    # Opportunity 2: Medium risk healthcare stock
    opp2 = InvestmentOpportunity(
        symbol="UNH",
        company_name="UnitedHealth Group",
        current_price=Decimal("520.00"),
        target_price=Decimal("600.00"),
        position_size_percent=Decimal("15.0"),
        investment_thesis=(
            "Leading healthcare insurer with diversified revenue streams. Optum division "
            "growing rapidly and improving margins. Aging demographics provide long-term tailwind."
        ),
        global_context=GlobalContext(
            economic_factors=[
                "Healthcare spending growing faster than GDP",
                "Medicare Advantage enrollment increasing",
                "Inflation driving premium increases"
            ],
            geopolitical_events=[
                "Healthcare reform debates creating uncertainty",
                "Drug pricing legislation impact unclear"
            ],
            industry_dynamics=[
                "Consolidation in healthcare services",
                "Value-based care models gaining traction",
                "Technology integration improving efficiency"
            ],
            company_specifics=[
                "Optum revenue growing 20% annually",
                "Medical loss ratio improving",
                "Strong member retention rates"
            ],
            timing_rationale=(
                "Stock undervalued relative to peers. Recent acquisition expanding capabilities. "
                "Open enrollment period showing strong growth."
            ),
            risk_factors=[
                "Regulatory changes to Medicare Advantage",
                "Political pressure on healthcare costs",
                "Integration risks from acquisitions"
            ]
        ),
        expected_return=Decimal("15.4"),
        risk_level=RiskLevel.MEDIUM,
        expected_holding_period="9-15 months",
        data_timestamp=datetime.now()
    )
    opportunities.append(opp2)
    
    # Opportunity 3: High risk growth stock
    opp3 = InvestmentOpportunity(
        symbol="PLTR",
        company_name="Palantir Technologies",
        current_price=Decimal("25.00"),
        target_price=Decimal("40.00"),
        position_size_percent=Decimal("5.0"),
        investment_thesis=(
            "AI platform gaining commercial traction after years of government focus. "
            "Recent profitability milestone and strong customer growth. High risk but "
            "significant upside if commercial adoption accelerates."
        ),
        global_context=GlobalContext(
            economic_factors=[
                "Enterprise AI spending accelerating",
                "Digital transformation budgets increasing",
                "Data analytics becoming strategic priority"
            ],
            geopolitical_events=[
                "Government contracts expanding with geopolitical tensions",
                "Data sovereignty concerns driving domestic solutions"
            ],
            industry_dynamics=[
                "AI platform market highly competitive",
                "Large incumbents entering space",
                "Customer acquisition costs high"
            ],
            company_specifics=[
                "First profitable year achieved",
                "Commercial revenue growing 50% YoY",
                "Government contracts stable and growing"
            ],
            timing_rationale=(
                "Stock pulled back 30% from highs despite strong fundamentals. "
                "Recent commercial wins demonstrating product-market fit. "
                "AI hype cycle creating awareness."
            ),
            risk_factors=[
                "High valuation despite recent pullback",
                "Execution risk on commercial expansion",
                "Competition from established players",
                "Dependence on government contracts"
            ]
        ),
        expected_return=Decimal("60.0"),
        risk_level=RiskLevel.HIGH,
        expected_holding_period="6-12 months",
        data_timestamp=datetime.now()
    )
    opportunities.append(opp3)
    
    # Generate newsletter
    generator = NewsletterGenerator()
    newsletter = generator.generate_newsletter(opportunities)
    
    # Verify newsletter structure
    assert newsletter is not None
    assert len(newsletter.opportunities) == 3
    assert newsletter.market_overview
    assert newsletter.date
    
    # Generate HTML format
    html = generator.format_html(newsletter)
    assert html
    assert "MSFT" in html
    assert "UNH" in html
    assert "PLTR" in html
    assert "Microsoft Corporation" in html
    assert "Investment Scout Daily" in html
    assert "Market Overview" in html
    assert "Disclaimer" in html
    
    # Generate plain text format
    text = generator.format_plain_text(newsletter)
    assert text
    assert "MSFT" in text
    assert "UNH" in text
    assert "PLTR" in text
    assert "INVESTMENT SCOUT DAILY" in text
    assert "MARKET OVERVIEW" in text
    assert "DISCLAIMER" in text
    
    # Verify all opportunities have required fields
    for opp in newsletter.opportunities:
        assert opp.symbol
        assert opp.company_name
        assert opp.current_price > 0
        assert opp.target_price > opp.current_price
        assert 1 <= opp.position_size_percent <= 25
        assert opp.investment_thesis
        assert opp.global_context
        assert opp.expected_holding_period
        assert opp.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]
    
    print("\n" + "="*70)
    print("NEWSLETTER GENERATION SUCCESSFUL")
    print("="*70)
    print(f"Generated newsletter with {len(opportunities)} opportunities")
    print(f"HTML length: {len(html)} characters")
    print(f"Plain text length: {len(text)} characters")
    print("="*70)


if __name__ == "__main__":
    test_complete_newsletter_generation()
    print("\n✅ Integration test passed!")
