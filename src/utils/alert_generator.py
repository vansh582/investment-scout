"""
Alert Generator for Investment Scout

Creates instant trading alert emails for short-term buy/sell opportunities.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from src.models.investment_scout_models import TradingAlert, SignalType


logger = logging.getLogger(__name__)


class AlertGenerator:
    """
    Creates instant trading alert email content.
    
    Generates HTML and plain text email formats for real-time trading alerts
    with clear BUY/SELL actions, entry/exit levels, and beginner-friendly explanations.
    """
    
    def __init__(self):
        """Initialize Alert Generator."""
        logger.info("AlertGenerator initialized successfully")
    
    def generate_alert(self, alert: TradingAlert) -> str:
        """
        Generate alert email content from trading alert.
        
        Args:
            alert: TradingAlert object with opportunity details
            
        Returns:
            Formatted alert content string
            
        Raises:
            ValueError: If alert is None
        """
        if alert is None:
            raise ValueError("Cannot generate alert from None")
        
        logger.info(f"Generating {alert.signal_type.value.upper()} alert for {alert.symbol}")
        
        # Calculate expected gain/loss percentages
        expected_gain_pct = ((alert.target_price - alert.entry_price) / alert.entry_price * 100)
        max_loss_pct = ((alert.stop_loss - alert.entry_price) / alert.entry_price * 100)
        
        alert_parts = []
        
        # Action header
        action = alert.signal_type.value.upper()
        alert_parts.append(f"**ACTION: {action} {alert.symbol}**")
        alert_parts.append("")
        
        # Opportunity details
        alert_parts.append(f"**{alert.company_name} ({alert.symbol})**")
        alert_parts.append(f"Current Price: ${alert.current_price:.2f}")
        alert_parts.append("")
        
        # Entry/Exit levels
        alert_parts.append("**Trading Levels:**")
        alert_parts.append(f"- Entry Price: ${alert.entry_price:.2f}")
        alert_parts.append(f"- Target Price: ${alert.target_price:.2f} (Expected gain: {expected_gain_pct:+.1f}%)")
        alert_parts.append(f"- Stop Loss: ${alert.stop_loss:.2f} (Max loss: {max_loss_pct:.1f}%)")
        alert_parts.append(f"- Position Size: {alert.position_size_percent:.1f}% of portfolio")
        alert_parts.append(f"- Expected Holding Period: {alert.expected_holding_period}")
        alert_parts.append("")
        
        # Rationale
        alert_parts.append("**Why This Opportunity:**")
        alert_parts.append(alert.rationale)
        alert_parts.append("")
        
        # Risk factors
        alert_parts.append("**Important Reminders:**")
        alert_parts.append("- Always use stop loss orders to limit downside risk")
        alert_parts.append("- Only invest capital you can afford to lose")
        alert_parts.append("- Short-term trading carries higher risk than long-term investing")
        alert_parts.append("- Market conditions can change rapidly")
        alert_parts.append("")
        
        return '\n'.join(alert_parts)
    
    def format_alert_html(self, alert: TradingAlert) -> str:
        """
        Format trading alert as HTML email.
        
        Args:
            alert: TradingAlert object to format
            
        Returns:
            HTML string for email body
        """
        # Calculate percentages
        expected_gain_pct = ((alert.target_price - alert.entry_price) / alert.entry_price * 100)
        max_loss_pct = ((alert.stop_loss - alert.entry_price) / alert.entry_price * 100)
        
        # Determine action color
        action_color = "#27ae60" if alert.signal_type == SignalType.BUY else "#e74c3c"
        action = alert.signal_type.value.upper()
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 700px; margin: 0 auto; padding: 20px; }}
        .alert-header {{ background-color: {action_color}; color: white; padding: 20px; border-radius: 5px; text-align: center; margin-bottom: 20px; }}
        .alert-title {{ font-size: 2em; font-weight: bold; margin: 0; }}
        .alert-subtitle {{ font-size: 1.2em; margin: 10px 0 0 0; }}
        .company-info {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .company-name {{ font-size: 1.5em; font-weight: bold; color: #2c3e50; }}
        .symbol {{ color: #7f8c8d; font-size: 1.2em; }}
        .current-price {{ font-size: 1.3em; color: #2c3e50; margin-top: 10px; }}
        .trading-levels {{ background-color: #fff; border: 2px solid #3498db; border-radius: 5px; padding: 20px; margin: 20px 0; }}
        .level-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #ecf0f1; }}
        .level-row:last-child {{ border-bottom: none; }}
        .level-label {{ font-weight: bold; color: #34495e; }}
        .level-value {{ color: #2c3e50; font-size: 1.1em; }}
        .gain {{ color: #27ae60; font-weight: bold; }}
        .loss {{ color: #e74c3c; font-weight: bold; }}
        .rationale {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .rationale-title {{ font-size: 1.2em; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }}
        .reminders {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .reminders-title {{ font-size: 1.1em; font-weight: bold; color: #856404; margin-bottom: 10px; }}
        .reminders ul {{ margin: 5px 0; padding-left: 20px; }}
        .reminders li {{ margin: 5px 0; color: #856404; }}
        .disclaimer {{ background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0; font-size: 0.9em; color: #721c24; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 2px solid #bdc3c7; font-size: 0.9em; color: #7f8c8d; text-align: center; }}
    </style>
</head>
<body>
    <div class="alert-header">
        <div class="alert-title">🚨 TRADING ALERT</div>
        <div class="alert-subtitle">{action} {alert.symbol}</div>
    </div>
    
    <div class="company-info">
        <div class="company-name">{alert.company_name}</div>
        <div class="symbol">{alert.symbol}</div>
        <div class="current-price">Current Price: <strong>${alert.current_price:.2f}</strong></div>
    </div>
    
    <div class="trading-levels">
        <h2 style="margin-top: 0; color: #2c3e50;">Trading Levels</h2>
        
        <div class="level-row">
            <span class="level-label">Entry Price:</span>
            <span class="level-value">${alert.entry_price:.2f}</span>
        </div>
        
        <div class="level-row">
            <span class="level-label">Target Price:</span>
            <span class="level-value">${alert.target_price:.2f} <span class="gain">(+{expected_gain_pct:.1f}%)</span></span>
        </div>
        
        <div class="level-row">
            <span class="level-label">Stop Loss:</span>
            <span class="level-value">${alert.stop_loss:.2f} <span class="loss">({max_loss_pct:.1f}%)</span></span>
        </div>
        
        <div class="level-row">
            <span class="level-label">Position Size:</span>
            <span class="level-value">{alert.position_size_percent:.1f}% of portfolio</span>
        </div>
        
        <div class="level-row">
            <span class="level-label">Expected Holding Period:</span>
            <span class="level-value">{alert.expected_holding_period}</span>
        </div>
    </div>
    
    <div class="rationale">
        <div class="rationale-title">Why This Opportunity</div>
        <p>{alert.rationale}</p>
    </div>
    
    <div class="reminders">
        <div class="reminders-title">⚠️ Important Reminders</div>
        <ul>
            <li>Always use stop loss orders to limit downside risk</li>
            <li>Only invest capital you can afford to lose</li>
            <li>Short-term trading carries higher risk than long-term investing</li>
            <li>Market conditions can change rapidly</li>
        </ul>
    </div>
    
    <div class="disclaimer">
        <strong>Disclaimer:</strong> This trading alert is for informational purposes only and does not constitute 
        financial advice. Trading involves substantial risk of loss and is not suitable for all investors. 
        Past performance does not guarantee future results. Please conduct your own research and consult with 
        a qualified financial advisor before making trading decisions.
    </div>
    
    <div class="footer">
        <p>Investment Scout - Real-Time Trading Alerts</p>
        <p>Generated at {alert.data_timestamp.strftime("%Y-%m-%d %H:%M:%S")} ET</p>
    </div>
</body>
</html>
"""
        
        logger.info(f"HTML alert formatted for {alert.symbol}")
        return html
    
    def format_alert_plain_text(self, alert: TradingAlert) -> str:
        """
        Format trading alert as plain text alternative.
        
        Args:
            alert: TradingAlert object to format
            
        Returns:
            Plain text string for email body
        """
        # Calculate percentages
        expected_gain_pct = ((alert.target_price - alert.entry_price) / alert.entry_price * 100)
        max_loss_pct = ((alert.stop_loss - alert.entry_price) / alert.entry_price * 100)
        
        action = alert.signal_type.value.upper()
        
        lines = [
            "=" * 70,
            "🚨 TRADING ALERT",
            f"{action} {alert.symbol}",
            "=" * 70,
            "",
            f"{alert.company_name} ({alert.symbol})",
            f"Current Price: ${alert.current_price:.2f}",
            "",
            "TRADING LEVELS",
            "-" * 70,
            f"Entry Price:            ${alert.entry_price:.2f}",
            f"Target Price:           ${alert.target_price:.2f} (+{expected_gain_pct:.1f}%)",
            f"Stop Loss:              ${alert.stop_loss:.2f} ({max_loss_pct:.1f}%)",
            f"Position Size:          {alert.position_size_percent:.1f}% of portfolio",
            f"Expected Holding:       {alert.expected_holding_period}",
            "",
            "WHY THIS OPPORTUNITY",
            "-" * 70,
            alert.rationale,
            "",
            "⚠️ IMPORTANT REMINDERS",
            "-" * 70,
            "- Always use stop loss orders to limit downside risk",
            "- Only invest capital you can afford to lose",
            "- Short-term trading carries higher risk than long-term investing",
            "- Market conditions can change rapidly",
            "",
            "DISCLAIMER",
            "-" * 70,
            "This trading alert is for informational purposes only and does not constitute",
            "financial advice. Trading involves substantial risk of loss and is not suitable",
            "for all investors. Past performance does not guarantee future results. Please",
            "conduct your own research and consult with a qualified financial advisor before",
            "making trading decisions.",
            "",
            "-" * 70,
            "Investment Scout - Real-Time Trading Alerts",
            f"Generated at {alert.data_timestamp.strftime('%Y-%m-%d %H:%M:%S')} ET",
            ""
        ]
        
        logger.info(f"Plain text alert formatted for {alert.symbol}")
        return '\n'.join(lines)
