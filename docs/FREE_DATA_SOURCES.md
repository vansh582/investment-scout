# Free Data Source Integration

## Overview

Task 24 implements comprehensive free data source integration for Investment Scout, expanding beyond the initial yfinance, Finnhub, and Twelve Data sources. This integration adds NewsAPI, Alpha Vantage, FRED, World Bank, RSS feeds, and web scraping capabilities.

## Implemented Data Sources

### 1. NewsAPI (News)
- **Free Tier**: 100 requests per day
- **Purpose**: Market news and company-specific news
- **Features**: 1000 results per request, multiple sources
- **Client**: `src/clients/newsapi_client.py`

### 2. Alpha Vantage (News with Sentiment)
- **Free Tier**: 25 requests per day (very limited)
- **Purpose**: News articles with sentiment analysis
- **Features**: Sentiment scores from -1 (bearish) to 1 (bullish)
- **Client**: `src/clients/alphavantage_client.py`

### 3. FRED API (Economic Indicators)
- **Free Tier**: Unlimited with API key
- **Purpose**: US economic data from Federal Reserve
- **Features**: GDP, unemployment, interest rates, inflation
- **Client**: `src/clients/fred_client.py`

### 4. World Bank API (Global Economic Data)
- **Free Tier**: Unlimited, no API key required
- **Purpose**: Global economic indicators
- **Features**: GDP, growth rates, inflation, unemployment by country
- **Client**: `src/clients/worldbank_client.py`

### 5. RSS Feeds (News)
- **Free Tier**: Unlimited
- **Purpose**: Financial news from various sources
- **Features**: Yahoo Finance, CNBC, Reuters, MarketWatch
- **Client**: `src/clients/rss_feed_client.py`

### 6. Web Scraper (Public Data)
- **Free Tier**: Self-imposed limit of 100 requests per day
- **Purpose**: Publicly available financial data
- **Features**: Robots.txt compliance, rate limiting
- **Client**: `src/clients/web_scraper_client.py`

## Free Data Source Manager

The `FreeDataSourceManager` (`src/utils/free_data_source_manager.py`) orchestrates all free data sources with:

### Key Features

1. **Multi-Source Aggregation** (Req 19.1, 19.5)
   - Combines data from multiple sources
   - Deduplicates articles
   - Returns comprehensive results

2. **Automatic Failover** (Req 19.6)
   - Primary → Secondary → Tertiary source chain
   - Example: RSS → NewsAPI → Alpha Vantage
   - Continues on failure

3. **Rate Limit Monitoring** (Req 19.10)
   - Tracks usage per source
   - Prevents exceeding free tier limits
   - Daily usage reset

4. **Aggressive Caching** (Req 19.12)
   - Minimizes API calls
   - Maximizes free tier efficiency
   - Usage statistics tracking

5. **Compliance** (Req 19.8)
   - Respects robots.txt
   - Follows terms of service
   - Conservative rate limiting

## Usage Examples

### Get Market News
```python
from src.utils.free_data_source_manager import FreeDataSourceManager

manager = FreeDataSourceManager(
    newsapi_key='your_key',
    alphavantage_key='your_key',
    fred_key='your_key'
)

# Get market news with automatic failover
articles = manager.get_market_news(max_articles=100)
```

### Get Company News
```python
# Get company-specific news with sentiment
articles = manager.get_company_news(
    symbol='AAPL',
    company_name='Apple Inc.',
    max_articles=50
)
```

### Get Economic Indicators
```python
# Get US economic indicators from FRED
indicators = manager.get_economic_indicators('US')
# Returns: gdp, unemployment, interest_rate, inflation

# Get global indicators from World Bank
indicators = manager.get_economic_indicators('CN')
# Returns: gdp, gdp_growth, inflation, unemployment
```

### Monitor Usage
```python
# Get usage report
report = manager.get_usage_report()
# Shows usage, limit, remaining, percentage for each source
```

## Failover Chains

### Market News Failover
1. **RSS Feeds** (unlimited, free)
2. **NewsAPI** (100/day)
3. **Alpha Vantage** (25/day, has sentiment)

### Company News Failover
1. **Alpha Vantage** (sentiment analysis)
2. **NewsAPI** (fallback)

### Economic Indicators Failover
1. **FRED** (US data, frequent updates)
2. **World Bank** (global data, annual)

## Rate Limits and Usage

| Source | Daily Limit | Usage Strategy |
|--------|-------------|----------------|
| NewsAPI | 100 | Conservative, 4/hour |
| Alpha Vantage | 25 | Very conservative, 1/hour |
| FRED | 1000 (self) | 60/minute |
| World Bank | 1000 (self) | 60/minute |
| RSS Feeds | 500 (self) | 30/minute |
| Web Scraper | 100 (self) | 10/minute |

## Testing

Run tests with:
```bash
python3 -m pytest tests/test_free_data_sources.py -v
```

Tests cover:
- Multi-source aggregation
- Failover logic
- Rate limit monitoring
- Caching efficiency
- Robots.txt compliance
- Usage tracking
- Deduplication

## Requirements Validation

✅ **19.1**: Integrated NewsAPI, Alpha Vantage, FRED, World Bank, RSS, web scraping
✅ **19.2**: NewsAPI and RSS feeds for market news
✅ **19.3**: FRED and World Bank for economic data
✅ **19.6**: Automatic failover across sources
✅ **19.7**: Web scraping with rate limiting
✅ **19.8**: Respects robots.txt and terms of service
✅ **19.10**: Monitors free tier usage
✅ **19.11**: Prioritizes higher limit sources
✅ **19.12**: Aggressive caching to maximize efficiency
