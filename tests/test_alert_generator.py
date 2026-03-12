"""
Tests for Alert Generator

Tests alert generation, HTML formatting, and plain text formatting for trading alerts.
"""

import pytest
from datetime import datetime
from decimal import Decimal

from src.utils.alert_generator import AlertGenerator
from src.models.investment_scout_models import TradingAlert, SignalType


@pytest.fixture
def alert_generator():
    """Create AlertGenerator instance"""
    return AlertGenerator()


@pytest.fixture
def sample_buy_alert():
    """Create sample BUY trading alert"""
    return TradingAlert(
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
        data_timestamp=datetime(2024, 1, 15, 10, 30, 0)
    )


@pytest.fixture
def sample_sell_alert():
    """Create sample SELL trading alert"""
    return TradingAlert(
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
        data_timestamp=datetime(2024, 1, 15, 14, 45, 0)
    )


class TestAlertGenerator:
    """Test AlertGenerator class"""
    
    def test_initialization(self, alert_generator):
        """Test AlertGenerator initializes correctly"""
        assert alert_generator is not None
    
    def test_generate_alert_buy(self, alert_generator, sample_buy_alert):
        """Test generate_alert creates content for BUY alert"""
        content = alert_generator.generate_alert(sample_buy_alert)
        
        assert content is not None
        assert "BUY AAPL" in content
        assert "Apple Inc." in content
        assert "$150.00" in content
        assert "$150.50" in content
        assert "$160.00" in content
        assert "$145.00" in content
        assert "5.0%" in content
        assert "2-5 days" in content
        assert "Strong breakout" in content
    
    def test_generate_alert_sell(self, alert_generator, sample_sell_alert):
        """Test generate_alert creates content for SELL alert"""
        content = alert_generator.generate_alert(sample_sell_alert)
        
        assert content is not None
        assert "SELL TSLA" in content
        assert "Tesla Inc." in content
        assert "$250.00" in content
        assert "$249.50" in content
        assert "$230.00" in content
        assert "$255.00" in content
        assert "3.0%" in content
        assert "1-3 days" in content
        assert "Breakdown below" in content
    
    def test_generate_alert_none_raises_error(self, alert_generator):
        """Test generate_alert raises ValueError for None input"""
        with pytest.raises(ValueError, match="Cannot generate alert from None"):
            alert_generator.generate_alert(None)
    
    def test_generate_alert_includes_percentages(self, alert_generator, sample_buy_alert):
        """Test generate_alert includes expected gain and max loss percentages"""
        content = alert_generator.generate_alert(sample_buy_alert)
        
        # Expected gain: (160 - 150.50) / 150.50 = 6.3%
        assert "6.3%" in content or "+6.3%" in content
        
        # Max loss: (145 - 150.50) / 150.50 = -3.7%
        assert "3.7%" in content or "-3.7%" in content
    
    def test_generate_alert_includes_risk_reminders(self, alert_generator, sample_buy_alert):
        """Test generate_alert includes important risk reminders"""
        content = alert_generator.generate_alert(sample_buy_alert)
        
        assert "stop loss" in content.lower()
        assert "risk" in content.lower()
        assert "afford to lose" in content.lower()
    
    def test_format_alert_html_buy(self, alert_generator, sample_buy_alert):
        """Test format_alert_html creates valid HTML for BUY alert"""
        html = alert_generator.format_alert_html(sample_buy_alert)
        
        assert html is not None
        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "</html>" in html
        assert "BUY AAPL" in html
        assert "Apple Inc." in html
        assert "$150.00" in html
        assert "$150.50" in html
        assert "$160.00" in html
        assert "$145.00" in html
        assert "5.0%" in html
        assert "2-5 days" in html
        assert "Strong breakout" in html
    
    def test_format_alert_html_sell(self, alert_generator, sample_sell_alert):
        """Test format_alert_html creates valid HTML for SELL alert"""
        html = alert_generator.format_alert_html(sample_sell_alert)
        
        assert html is not None
        assert "<!DOCTYPE html>" in html
        assert "SELL TSLA" in html
        assert "Tesla Inc." in html
        assert "$250.00" in html
        assert "$249.50" in html
        assert "$230.00" in html
        assert "$255.00" in html
        assert "3.0%" in html
        assert "1-3 days" in html
        assert "Breakdown below" in html
    
    def test_format_alert_html_includes_styling(self, alert_generator, sample_buy_alert):
        """Test format_alert_html includes CSS styling"""
        html = alert_generator.format_alert_html(sample_buy_alert)
        
        assert "<style>" in html
        assert "</style>" in html
        assert "alert-header" in html
        assert "trading-levels" in html
        assert "rationale" in html
        assert "disclaimer" in html
    
    def test_format_alert_html_includes_disclaimer(self, alert_generator, sample_buy_alert):
        """Test format_alert_html includes disclaimer"""
        html = alert_generator.format_alert_html(sample_buy_alert)
        
        assert "Disclaimer" in html
        assert "informational purposes only" in html
        assert "not constitute financial advice" in html or "does not constitute" in html
        assert "risk" in html.lower()
    
    def test_format_alert_html_includes_timestamp(self, alert_generator, sample_buy_alert):
        """Test format_alert_html includes generation timestamp"""
        html = alert_generator.format_alert_html(sample_buy_alert)
        
        assert "2024-01-15" in html
        assert "10:30:00" in html
    
    def test_format_alert_html_color_coding_buy(self, alert_generator, sample_buy_alert):
        """Test format_alert_html uses green color for BUY alerts"""
        html = alert_generator.format_alert_html(sample_buy_alert)
        
        # Green color for BUY
        assert "#27ae60" in html
    
    def test_format_alert_html_color_coding_sell(self, alert_generator, sample_sell_alert):
        """Test format_alert_html uses red color for SELL alerts"""
        html = alert_generator.format_alert_html(sample_sell_alert)
        
        # Red color for SELL
        assert "#e74c3c" in html
    
    def test_format_alert_plain_text_buy(self, alert_generator, sample_buy_alert):
        """Test format_alert_plain_text creates plain text for BUY alert"""
        text = alert_generator.format_alert_plain_text(sample_buy_alert)
        
        assert text is not None
        assert "TRADING ALERT" in text
        assert "BUY AAPL" in text
        assert "Apple Inc." in text
        assert "$150.00" in text
        assert "$150.50" in text
        assert "$160.00" in text
        assert "$145.00" in text
        assert "5.0%" in text
        assert "2-5 days" in text
        assert "Strong breakout" in text
    
    def test_format_alert_plain_text_sell(self, alert_generator, sample_sell_alert):
        """Test format_alert_plain_text creates plain text for SELL alert"""
        text = alert_generator.format_alert_plain_text(sample_sell_alert)
        
        assert text is not None
        assert "TRADING ALERT" in text
        assert "SELL TSLA" in text
        assert "Tesla Inc." in text
        assert "$250.00" in text
        assert "$249.50" in text
        assert "$230.00" in text
        assert "$255.00" in text
        assert "3.0%" in text
        assert "1-3 days" in text
        assert "Breakdown below" in text
    
    def test_format_alert_plain_text_includes_sections(self, alert_generator, sample_buy_alert):
        """Test format_alert_plain_text includes all required sections"""
        text = alert_generator.format_alert_plain_text(sample_buy_alert)
        
        assert "TRADING LEVELS" in text
        assert "WHY THIS OPPORTUNITY" in text
        assert "IMPORTANT REMINDERS" in text
        assert "DISCLAIMER" in text
    
    def test_format_alert_plain_text_includes_disclaimer(self, alert_generator, sample_buy_alert):
        """Test format_alert_plain_text includes disclaimer"""
        text = alert_generator.format_alert_plain_text(sample_buy_alert)
        
        assert "informational purposes only" in text
        assert "not constitute" in text
        assert "financial advice" in text
        assert "risk" in text.lower()
    
    def test_format_alert_plain_text_includes_timestamp(self, alert_generator, sample_buy_alert):
        """Test format_alert_plain_text includes generation timestamp"""
        text = alert_generator.format_alert_plain_text(sample_buy_alert)
        
        assert "2024-01-15" in text
        assert "10:30:00" in text
    
    def test_format_alert_plain_text_readable_formatting(self, alert_generator, sample_buy_alert):
        """Test format_alert_plain_text uses readable formatting"""
        text = alert_generator.format_alert_plain_text(sample_buy_alert)
        
        # Check for separator lines
        assert "=" * 70 in text
        assert "-" * 70 in text
        
        # Check for proper line breaks
        lines = text.split('\n')
        assert len(lines) > 20  # Should have multiple lines
    
    def test_alert_with_small_position_size(self, alert_generator):
        """Test alert generation with minimum position size"""
        alert = TradingAlert(
            symbol="SPY",
            company_name="SPDR S&P 500 ETF",
            signal_type=SignalType.BUY,
            current_price=Decimal("450.00"),
            entry_price=Decimal("450.25"),
            target_price=Decimal("455.00"),
            stop_loss=Decimal("447.00"),
            position_size_percent=Decimal("1.0"),
            rationale="Market dip buying opportunity with strong support.",
            expected_holding_period="1-2 days",
            data_timestamp=datetime.now()
        )
        
        html = alert_generator.format_alert_html(alert)
        text = alert_generator.format_alert_plain_text(alert)
        
        assert "1.0%" in html
        assert "1.0%" in text
    
    def test_alert_with_large_position_size(self, alert_generator):
        """Test alert generation with maximum position size"""
        alert = TradingAlert(
            symbol="QQQ",
            company_name="Invesco QQQ Trust",
            signal_type=SignalType.BUY,
            current_price=Decimal("380.00"),
            entry_price=Decimal("380.50"),
            target_price=Decimal("395.00"),
            stop_loss=Decimal("375.00"),
            position_size_percent=Decimal("25.0"),
            rationale="High conviction tech sector breakout with strong momentum.",
            expected_holding_period="5-10 days",
            data_timestamp=datetime.now()
        )
        
        html = alert_generator.format_alert_html(alert)
        text = alert_generator.format_alert_plain_text(alert)
        
        assert "25.0%" in html
        assert "25.0%" in text
    
    def test_alert_with_short_holding_period(self, alert_generator):
        """Test alert with very short holding period"""
        alert = TradingAlert(
            symbol="NVDA",
            company_name="NVIDIA Corporation",
            signal_type=SignalType.BUY,
            current_price=Decimal("500.00"),
            entry_price=Decimal("500.50"),
            target_price=Decimal("510.00"),
            stop_loss=Decimal("495.00"),
            position_size_percent=Decimal("5.0"),
            rationale="Intraday momentum play on earnings catalyst.",
            expected_holding_period="Minutes to hours",
            data_timestamp=datetime.now()
        )
        
        content = alert_generator.generate_alert(alert)
        
        assert "Minutes to hours" in content
    
    def test_alert_with_long_rationale(self, alert_generator):
        """Test alert with lengthy rationale text"""
        long_rationale = (
            "This is a complex trading opportunity based on multiple factors. "
            "First, we're seeing a technical breakout above the 200-day moving average "
            "with strong volume confirmation. Second, recent earnings beat expectations "
            "by 15% with raised guidance for next quarter. Third, the sector is showing "
            "relative strength compared to the broader market. Fourth, institutional "
            "buying has increased significantly over the past week. Fifth, short interest "
            "has declined suggesting reduced bearish sentiment. All these factors combined "
            "create a compelling short-term trading opportunity with favorable risk/reward."
        )
        
        alert = TradingAlert(
            symbol="MSFT",
            company_name="Microsoft Corporation",
            signal_type=SignalType.BUY,
            current_price=Decimal("380.00"),
            entry_price=Decimal("380.50"),
            target_price=Decimal("395.00"),
            stop_loss=Decimal("375.00"),
            position_size_percent=Decimal("10.0"),
            rationale=long_rationale,
            expected_holding_period="3-7 days",
            data_timestamp=datetime.now()
        )
        
        html = alert_generator.format_alert_html(alert)
        text = alert_generator.format_alert_plain_text(alert)
        
        assert long_rationale in html
        assert long_rationale in text
    
    def test_percentage_calculations_accuracy(self, alert_generator):
        """Test that percentage calculations are accurate"""
        alert = TradingAlert(
            symbol="AMZN",
            company_name="Amazon.com Inc.",
            signal_type=SignalType.BUY,
            current_price=Decimal("150.00"),
            entry_price=Decimal("150.00"),
            target_price=Decimal("165.00"),  # +10%
            stop_loss=Decimal("142.50"),     # -5%
            position_size_percent=Decimal("8.0"),
            rationale="Test alert for percentage calculations.",
            expected_holding_period="3-5 days",
            data_timestamp=datetime.now()
        )
        
        html = alert_generator.format_alert_html(alert)
        text = alert_generator.format_alert_plain_text(alert)
        
        # Expected gain: (165 - 150) / 150 = 10%
        assert "10.0%" in html or "+10.0%" in html
        assert "10.0%" in text or "+10.0%" in text
        
        # Max loss: (142.50 - 150) / 150 = -5%
        assert "5.0%" in html or "-5.0%" in html
        assert "5.0%" in text or "-5.0%" in text
