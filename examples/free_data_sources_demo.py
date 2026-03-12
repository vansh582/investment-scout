"""
Free Data Sources Demo

Demonstrates the usage of free data source integration for Investment Scout.
Shows how to fetch news, economic indicators, and handle failover.
"""

import os
from datetime import date, timedelta
from dotenv import load_dotenv

from src.utils.free_data_source_manager import FreeDataSourceManager


def main():
    """Demonstrate free data source integration"""
    
    # Load environment variables
    load_dotenv()
    
    # Initialize manager with API keys
    manager = FreeDataSourceManager(
        newsapi_key=os.getenv('NEWSAPI_KEY'),
        alphavantage_key=os.getenv('ALPHAVANTAGE_KEY'),
        fred_key=os.getenv('FRED_API_KEY')
    )
    
    print("=" * 80)
    print("Free Data Source Integration Demo")
    print("=" * 80)
    
    # 1. Get Market News
    print("\n1. Fetching Market News (with automatic failover)...")
    print("-" * 80)
    
    articles = manager.get_market_news(
        from_date=date.today() - timedelta(days=7),
        max_articles=10
    )
    
    print(f"Retrieved {len(articles)} articles from multiple sources:")
    for i, article in enumerate(articles[:5], 1):
        print(f"\n{i}. {article.title}")
        print(f"   Source: {article.source}")
        print(f"   Published: {article.published_at}")
        if article.sentiment is not None:
            print(f"   Sentiment: {article.sentiment:.2f}")
    
    # 2. Get Company News
    print("\n\n2. Fetching Company-Specific News...")
    print("-" * 80)
    
    company_articles = manager.get_company_news(
        symbol='AAPL',
        company_name='Apple Inc.',
        max_articles=5
    )
    
    print(f"Retrieved {len(company_articles)} articles about Apple:")
    for i, article in enumerate(company_articles, 1):
        print(f"\n{i}. {article.title}")
        print(f"   Source: {article.source}")
        if article.sentiment is not None:
            sentiment_label = "Bullish" if article.sentiment > 0 else "Bearish"
            print(f"   Sentiment: {sentiment_label} ({article.sentiment:.2f})")
    
    # 3. Get Economic Indicators
    print("\n\n3. Fetching Economic Indicators...")
    print("-" * 80)
    
    indicators = manager.get_economic_indicators(
        country_code='US',
        from_date=date.today() - timedelta(days=365)
    )
    
    print("US Economic Indicators:")
    for indicator_name, data in indicators.items():
        if data:
            latest = data[0]
            print(f"\n{indicator_name.upper()}:")
            print(f"  Latest Value: {latest['value']}")
            print(f"  Date: {latest.get('date', latest.get('year', 'N/A'))}")
    
    # 4. Usage Report
    print("\n\n4. API Usage Report...")
    print("-" * 80)
    
    report = manager.get_usage_report()
    
    print("\nCurrent API Usage:")
    for source, stats in report.items():
        print(f"\n{source.upper()}:")
        print(f"  Used: {stats['usage']}/{stats['limit']}")
        print(f"  Remaining: {stats['remaining']}")
        print(f"  Percentage: {stats['percentage']:.1f}%")
    
    # 5. Demonstrate Failover
    print("\n\n5. Failover Demonstration...")
    print("-" * 80)
    print("The system automatically tries multiple sources:")
    print("  Market News: RSS → NewsAPI → Alpha Vantage")
    print("  Company News: Alpha Vantage → NewsAPI")
    print("  Economic Data: FRED → World Bank")
    print("\nIf one source fails or reaches its limit, the next is tried automatically.")
    
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
