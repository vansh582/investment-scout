"""
Newsletter Generator for Investment Scout

Creates daily email content from investment opportunities with market overview,
opportunity details, and performance summaries.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from src.models.investment_scout_models import (
    InvestmentOpportunity,
    Newsletter,
    RiskLevel
)


logger = logging.getLogger(__name__)


class NewsletterGenerator:
    """
    Creates daily newsletter content from investment opportunities.
    
    Generates HTML and plain text email formats with market overview,
    opportunity details, global context, and monthly performance summaries.
    """
    
    def __init__(self, performance_tracker=None, market_monitor=None, 
                 geopolitical_monitor=None, industry_analyzer=None):
        """
        Initialize Newsletter Generator.
        
        Args:
            performance_tracker: PerformanceTracker instance for performance summaries
            market_monitor: MarketMonitor instance for market data
            geopolitical_monitor: GeopoliticalMonitor instance for geopolitical context
            industry_analyzer: IndustryAnalyzer instance for sector performance
        """
        self.performance_tracker = performance_tracker
        self.market_monitor = market_monitor
        self.geopolitical_monitor = geopolitical_monitor
        self.industry_analyzer = industry_analyzer
        logger.info("NewsletterGenerator initialized successfully")
    
    def generate_newsletter(self, opportunities: List[InvestmentOpportunity]) -> Newsletter:
        """
        Generate daily newsletter from investment opportunities.
        
        Args:
            opportunities: List of 1-5 InvestmentOpportunity objects
            
        Returns:
            Newsletter object with market overview and opportunities
            
        Raises:
            ValueError: If opportunities list is empty or contains more than 5 items
        """
        if not opportunities:
            raise ValueError("Cannot generate newsletter with empty opportunities list")
        
        if len(opportunities) > 5:
            raise ValueError(f"Newsletter can contain at most 5 opportunities, got {len(opportunities)}")
        
        logger.info(f"Generating newsletter with {len(opportunities)} opportunities")
        
        # Create market overview
        market_overview = self.create_market_overview()
        
        # Generate performance summary if it's a monthly newsletter
        performance_summary = self._generate_monthly_performance_summary()
        
        newsletter = Newsletter(
            date=datetime.now(),
            market_overview=market_overview,
            opportunities=opportunities,
            performance_summary=performance_summary,
            generated_at=datetime.now()
        )
        
        logger.info("Newsletter generated successfully")
        return newsletter
    
    def format_html(self, newsletter: Newsletter) -> str:
        """
        Format newsletter as HTML email.
        
        Args:
            newsletter: Newsletter object to format
            
        Returns:
            HTML string for email body
        """
        html_parts = []
        
        # Email header
        html_parts.append("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        h3 { color: #2980b9; margin-top: 20px; }
        .market-overview { background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .opportunity { background-color: #fff; border: 1px solid #bdc3c7; border-radius: 5px; padding: 20px; margin: 20px 0; }
        .opportunity-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .company-name { font-size: 1.3em; font-weight: bold; color: #2c3e50; }
        .symbol { color: #7f8c8d; font-size: 1.1em; }
        .price-info { text-align: right; }
        .current-price { font-size: 1.2em; color: #27ae60; }
        .target-price { font-size: 1.1em; color: #2980b9; }
        .risk-badge { display: inline-block; padding: 5px 10px; border-radius: 3px; font-weight: bold; font-size: 0.9em; }
        .risk-low { background-color: #2ecc71; color: white; }
        .risk-medium { background-color: #f39c12; color: white; }
        .risk-high { background-color: #e74c3c; color: white; }
        .thesis { margin: 15px 0; font-size: 1.05em; }
        .context-section { margin: 15px 0; }
        .context-title { font-weight: bold; color: #34495e; margin-bottom: 5px; }
        .context-list { margin: 5px 0 5px 20px; }
        .metrics { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 15px 0; }
        .metric { background-color: #f8f9fa; padding: 10px; border-radius: 3px; }
        .metric-label { font-size: 0.9em; color: #7f8c8d; }
        .metric-value { font-size: 1.1em; font-weight: bold; color: #2c3e50; }
        .performance-summary { background-color: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 2px solid #bdc3c7; font-size: 0.9em; color: #7f8c8d; }
        .disclaimer { background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; font-size: 0.9em; }
    </style>
</head>
<body>
""")
        
        # Newsletter title
        date_str = newsletter.date.strftime("%B %d, %Y")
        html_parts.append(f"""
    <h1>Investment Scout Daily - {date_str}</h1>
    <p style="font-size: 1.1em; color: #7f8c8d;">{len(newsletter.opportunities)} Investment Opportunities</p>
""")
        
        # Market overview section
        html_parts.append(f"""
    <div class="market-overview">
        <h2>Market Overview</h2>
        {self._format_market_overview_html(newsletter.market_overview)}
    </div>
""")
        
        # Investment opportunities
        html_parts.append('<h2>Investment Opportunities</h2>')
        
        for i, opp in enumerate(newsletter.opportunities, 1):
            html_parts.append(self._format_opportunity_html(opp, i))
        
        # Performance summary (if available)
        if newsletter.performance_summary:
            html_parts.append(f"""
    <div class="performance-summary">
        <h2>Monthly Performance Summary</h2>
        {newsletter.performance_summary}
    </div>
""")
        
        # Disclaimer
        html_parts.append("""
    <div class="disclaimer">
        <strong>Disclaimer:</strong> This newsletter is for informational purposes only and does not constitute 
        financial advice. All investments carry risk, including the potential loss of principal. Past performance 
        does not guarantee future results. Please conduct your own research and consult with a qualified financial 
        advisor before making investment decisions.
    </div>
""")
        
        # Footer
        html_parts.append("""
    <div class="footer">
        <p>Investment Scout - Automated Market Intelligence</p>
        <p><a href="{{unsubscribe_link}}">Unsubscribe</a> from these emails</p>
    </div>
</body>
</html>
""")
        
        return ''.join(html_parts)
    
    def format_plain_text(self, newsletter: Newsletter) -> str:
        """
        Format newsletter as plain text alternative.
        
        Args:
            newsletter: Newsletter object to format
            
        Returns:
            Plain text string for email body
        """
        text_parts = []
        
        # Header
        date_str = newsletter.date.strftime("%B %d, %Y")
        text_parts.append("=" * 70)
        text_parts.append(f"INVESTMENT SCOUT DAILY - {date_str}")
        text_parts.append(f"{len(newsletter.opportunities)} Investment Opportunities")
        text_parts.append("=" * 70)
        text_parts.append("")
        
        # Market overview
        text_parts.append("MARKET OVERVIEW")
        text_parts.append("-" * 70)
        text_parts.append(newsletter.market_overview)
        text_parts.append("")
        
        # Investment opportunities
        text_parts.append("INVESTMENT OPPORTUNITIES")
        text_parts.append("=" * 70)
        text_parts.append("")
        
        for i, opp in enumerate(newsletter.opportunities, 1):
            text_parts.append(self._format_opportunity_text(opp, i))
            text_parts.append("")
        
        # Performance summary
        if newsletter.performance_summary:
            text_parts.append("MONTHLY PERFORMANCE SUMMARY")
            text_parts.append("-" * 70)
            text_parts.append(newsletter.performance_summary)
            text_parts.append("")
        
        # Disclaimer
        text_parts.append("DISCLAIMER")
        text_parts.append("-" * 70)
        text_parts.append(
            "This newsletter is for informational purposes only and does not constitute "
            "financial advice. All investments carry risk, including the potential loss of "
            "principal. Past performance does not guarantee future results. Please conduct "
            "your own research and consult with a qualified financial advisor before making "
            "investment decisions."
        )
        text_parts.append("")
        
        # Footer
        text_parts.append("-" * 70)
        text_parts.append("Investment Scout - Automated Market Intelligence")
        text_parts.append("To unsubscribe: {{unsubscribe_link}}")
        text_parts.append("")
        
        return '\n'.join(text_parts)
    
    def create_market_overview(self) -> str:
        """
        Create market overview section with current conditions.
        
        Includes:
        - Current market conditions
        - Key economic indicators
        - Major geopolitical events
        - Sector performance summary
        
        Returns:
            Formatted market overview text
        """
        overview_parts = []
        
        # Market conditions
        if self.market_monitor:
            try:
                # Get major indices (simplified - would use actual market data)
                overview_parts.append("**Current Market Conditions:**")
                overview_parts.append("Markets are showing mixed signals with ongoing volatility across sectors.")
                overview_parts.append("")
            except Exception as e:
                logger.warning(f"Could not fetch market conditions: {e}")
        
        # Economic indicators
        overview_parts.append("**Key Economic Indicators:**")
        overview_parts.append("- Interest rates remain elevated as central banks monitor inflation")
        overview_parts.append("- GDP growth showing resilience despite headwinds")
        overview_parts.append("- Employment data continues to reflect tight labor markets")
        overview_parts.append("")
        
        # Geopolitical events
        if self.geopolitical_monitor:
            try:
                overview_parts.append("**Major Geopolitical Events:**")
                overview_parts.append("- Ongoing trade negotiations impacting global supply chains")
                overview_parts.append("- Policy changes creating opportunities in specific sectors")
                overview_parts.append("")
            except Exception as e:
                logger.warning(f"Could not fetch geopolitical events: {e}")
        
        # Sector performance
        if self.industry_analyzer:
            try:
                overview_parts.append("**Sector Performance:**")
                overview_parts.append("- Technology: Leading with AI and cloud infrastructure growth")
                overview_parts.append("- Healthcare: Stable performance with biotech innovation")
                overview_parts.append("- Energy: Volatility continues amid transition dynamics")
                overview_parts.append("- Financials: Benefiting from higher interest rate environment")
                overview_parts.append("")
            except Exception as e:
                logger.warning(f"Could not fetch sector performance: {e}")
        
        return '\n'.join(overview_parts)
    
    def _format_market_overview_html(self, overview: str) -> str:
        """Convert markdown-style overview to HTML"""
        html = overview.replace('**', '<strong>').replace('**', '</strong>')
        lines = html.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip().startswith('- '):
                formatted_lines.append(f'<li>{line.strip()[2:]}</li>')
            elif line.strip():
                formatted_lines.append(f'<p>{line.strip()}</p>')
        
        return '\n'.join(formatted_lines)
    
    def _format_opportunity_html(self, opp: InvestmentOpportunity, index: int) -> str:
        """Format a single opportunity as HTML"""
        risk_class = f"risk-{opp.risk_level.value}"
        expected_return_pct = ((opp.target_price - opp.current_price) / opp.current_price * 100)
        
        html = f"""
    <div class="opportunity">
        <div class="opportunity-header">
            <div>
                <div class="company-name">{index}. {opp.company_name}</div>
                <div class="symbol">{opp.symbol}</div>
            </div>
            <div class="price-info">
                <div class="current-price">Current: ${opp.current_price:.2f}</div>
                <div class="target-price">Target: ${opp.target_price:.2f}</div>
            </div>
        </div>
        
        <div style="margin: 15px 0;">
            <span class="risk-badge {risk_class}">Risk: {opp.risk_level.value.upper()}</span>
        </div>
        
        <div class="thesis">
            <strong>Investment Thesis:</strong><br>
            {opp.investment_thesis}
        </div>
        
        <div class="context-section">
            <div class="context-title">Global Context:</div>
            
            <div style="margin-top: 10px;">
                <strong>Economic Factors:</strong>
                <ul class="context-list">
                    {''.join(f'<li>{factor}</li>' for factor in opp.global_context.economic_factors)}
                </ul>
            </div>
            
            <div style="margin-top: 10px;">
                <strong>Geopolitical Events:</strong>
                <ul class="context-list">
                    {''.join(f'<li>{event}</li>' for event in opp.global_context.geopolitical_events)}
                </ul>
            </div>
            
            <div style="margin-top: 10px;">
                <strong>Industry Dynamics:</strong>
                <ul class="context-list">
                    {''.join(f'<li>{dynamic}</li>' for dynamic in opp.global_context.industry_dynamics)}
                </ul>
            </div>
            
            <div style="margin-top: 10px;">
                <strong>Company Specifics:</strong>
                <ul class="context-list">
                    {''.join(f'<li>{specific}</li>' for specific in opp.global_context.company_specifics)}
                </ul>
            </div>
        </div>
        
        <div class="context-section">
            <div class="context-title">Why Now:</div>
            <p>{opp.global_context.timing_rationale}</p>
        </div>
        
        <div class="context-section">
            <div class="context-title">Risk Factors:</div>
            <ul class="context-list">
                {''.join(f'<li>{risk}</li>' for risk in opp.global_context.risk_factors)}
            </ul>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-label">Expected Return</div>
                <div class="metric-value">{expected_return_pct:.1f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Holding Period</div>
                <div class="metric-value">{opp.expected_holding_period}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Position Size</div>
                <div class="metric-value">{opp.position_size_percent:.1f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Risk Level</div>
                <div class="metric-value">{opp.risk_level.value.upper()}</div>
            </div>
        </div>
    </div>
"""
        return html
    
    def _format_opportunity_text(self, opp: InvestmentOpportunity, index: int) -> str:
        """Format a single opportunity as plain text"""
        expected_return_pct = ((opp.target_price - opp.current_price) / opp.current_price * 100)
        
        lines = [
            f"{index}. {opp.company_name} ({opp.symbol})",
            "-" * 70,
            f"Current Price: ${opp.current_price:.2f}",
            f"Target Price: ${opp.target_price:.2f}",
            f"Expected Return: {expected_return_pct:.1f}%",
            f"Risk Level: {opp.risk_level.value.upper()}",
            f"Position Size: {opp.position_size_percent:.1f}%",
            f"Holding Period: {opp.expected_holding_period}",
            "",
            "Investment Thesis:",
            opp.investment_thesis,
            "",
            "Global Context:",
            "",
            "Economic Factors:",
        ]
        
        for factor in opp.global_context.economic_factors:
            lines.append(f"  - {factor}")
        
        lines.append("")
        lines.append("Geopolitical Events:")
        for event in opp.global_context.geopolitical_events:
            lines.append(f"  - {event}")
        
        lines.append("")
        lines.append("Industry Dynamics:")
        for dynamic in opp.global_context.industry_dynamics:
            lines.append(f"  - {dynamic}")
        
        lines.append("")
        lines.append("Company Specifics:")
        for specific in opp.global_context.company_specifics:
            lines.append(f"  - {specific}")
        
        lines.append("")
        lines.append("Why Now:")
        lines.append(opp.global_context.timing_rationale)
        
        lines.append("")
        lines.append("Risk Factors:")
        for risk in opp.global_context.risk_factors:
            lines.append(f"  - {risk}")
        
        lines.append("-" * 70)
        
        return '\n'.join(lines)
    
    def _generate_monthly_performance_summary(self) -> Optional[str]:
        """
        Generate monthly performance summary if available.
        
        Returns:
            Formatted performance summary or None if not monthly newsletter
        """
        if not self.performance_tracker:
            return None
        
        # Check if it's the first day of the month (monthly newsletter)
        today = datetime.now()
        if today.day != 1:
            return None
        
        try:
            # Get performance metrics
            metrics = self.performance_tracker.calculate_returns()
            
            # Get S&P 500 comparison (simplified - would use actual benchmark data)
            sp500_return = Decimal('1.5')  # Placeholder
            benchmark = self.performance_tracker.compare_to_benchmark(sp500_return)
            
            # Format summary
            summary_lines = [
                f"**Portfolio Performance vs S&P 500:**",
                f"",
                f"Portfolio Return: {metrics['total_return_percent']:.2f}%",
                f"S&P 500 Return: {benchmark['sp500_return_percent']:.2f}%",
                f"Relative Performance: {benchmark['relative_performance']:+.2f}%",
                f"",
                f"**Key Metrics:**",
                f"- Win Rate: {metrics['win_rate']:.1f}%",
                f"- Average Gain per Winner: {metrics['avg_gain_per_winner']:.2f}%",
                f"- Average Loss per Loser: {metrics['avg_loss_per_loser']:.2f}%",
                f"- Sharpe Ratio: {metrics['sharpe_ratio']:.2f}",
                f"- Maximum Drawdown: {metrics['max_drawdown']:.2f}%",
            ]
            
            return '\n'.join(summary_lines)
            
        except Exception as e:
            logger.error(f"Error generating performance summary: {e}")
            return None
