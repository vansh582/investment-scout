# Requirements Document

## Introduction

Investment Scout is an automated market intelligence system that monitors global stock markets worldwide and delivers two types of recommendations: (1) PRIMARY: Daily investment newsletters at 9 AM Eastern Time with highly selective long-term investment recommendations (1-5 opportunities), and (2) SECONDARY: Real-time trading alerts sent instantly when buy/sell opportunities are detected (limited to 2-3 per day due to capital constraints). The system operates 24/7, continuously scanning ALL global markets, geopolitical events, industry trends, and economic indicators in real-time. All recommendations are filtered to Robinhood-tradeable securities and designed for beginner investors with limited capital. The system uses only free API tiers (yfinance, Finnhub, Twelve Data) and ensures NO stale data enters analysis.

## Glossary

- **System**: The Investment Scout automated market intelligence system
- **Market_Monitor**: Component that continuously monitors stock markets worldwide and collects real-time quotes
- **Research_Engine**: Component that stores and manages financial data, news articles, economic indicators, geopolitical events, and industry research
- **Investment_Analyzer**: Component that analyzes data and generates long-term investment opportunities for daily newsletters
- **Trading_Analyzer**: Component that analyzes real-time data and generates instant buy/sell trading alerts
- **Projection_Engine**: Component that generates real-time forward-looking projections based on current data and trends
- **Geopolitical_Monitor**: Component that tracks and analyzes global political events, policy changes, and international relations
- **Industry_Analyzer**: Component that performs deep industry-level research and competitive analysis
- **Newsletter_Generator**: Component that creates daily email content from investment opportunities
- **Alert_Generator**: Component that creates instant trading alert emails
- **Email_Service**: Component that sends newsletters and trading alerts to subscribers
- **Data_Manager**: Component that manages Redis caching and PostgreSQL persistent storage
- **API_Client**: Components that interface with external data providers (yfinance, Finnhub, Twelve Data, Robinhood)
- **Quote**: Real-time market price data with timestamp tracking
- **Investment_Opportunity**: A recommended long-term investment with thesis, global context, and holding period of weeks to months
- **Trading_Alert**: An instant buy or sell recommendation for short-term trading with holding period of minutes to days
- **Newsletter**: Daily email at 9 AM containing market overview and 1-5 investment opportunities
- **Fresh_Data**: Market data with latency less than 30 seconds
- **Stale_Data**: Market data with latency exceeding 30 seconds
- **Active_Stock**: A stock currently being monitored for potential recommendation
- **Watchlist_Stock**: A stock being tracked but not actively analyzed
- **Robinhood_Tradeable**: Securities that can be traded on the Robinhood platform
- **Global_Market**: Any stock exchange worldwide including US, European, Asian, and emerging markets
- **Geopolitical_Event**: Political events, policy changes, elections, conflicts, trade agreements, or sanctions that impact markets
- **Industry_Trend**: Sector-specific developments, competitive dynamics, regulatory changes, or technological disruptions
- **Real_Time_Projection**: Forward-looking analysis based on current data, not historical patterns alone
- **Position_Size**: Recommended investment amount as percentage of total portfolio (1% to 25%)
- **Performance_Tracker**: Component that monitors and compares portfolio returns against S&P 500 benchmark
- **S&P_500_Benchmark**: Standard & Poor's 500 index used as performance comparison baseline
- **Free_Hosting_Platform**: Cloud hosting service with zero-cost tier (Heroku, Railway, Render, or equivalent)
- **Free_Data_Source**: Any API, RSS feed, or public data source accessible without payment

## Requirements

### Requirement 1: Real-Time Global Market Monitoring

**User Story:** As an investor, I want the system to continuously monitor ALL stock markets worldwide in real-time, so that I receive timely recommendations based on current global market conditions.

#### Acceptance Criteria

1. THE Market_Monitor SHALL operate continuously 24 hours per day, 7 days per week
2. THE Market_Monitor SHALL monitor ALL Global_Market exchanges including US, European, Asian, and emerging markets
3. THE Market_Monitor SHALL scan ALL available market data in real-time without gaps
4. WHEN market data is received, THE Market_Monitor SHALL record both exchange timestamp and system receipt timestamp
5. THE Market_Monitor SHALL calculate data latency as the difference between receipt time and exchange time
6. WHEN data latency exceeds 30 seconds, THE Market_Monitor SHALL flag the data as Stale_Data
7. THE Market_Monitor SHALL reject Stale_Data and exclude it from ALL analysis
8. THE Market_Monitor SHALL use dual TTL caching strategy: 15 seconds for Active_Stock, 60 seconds for Watchlist_Stock
9. THE Market_Monitor SHALL prioritize monitoring during active trading hours for each Global_Market timezone

### Requirement 2: Free API Integration

**User Story:** As a system operator, I want to use only free API tiers, so that the system operates without ongoing API costs.

#### Acceptance Criteria

1. THE System SHALL use yfinance API for market data collection
2. THE System SHALL use Finnhub free tier for company information and news
3. THE System SHALL use Twelve Data free tier for technical indicators
4. THE System SHALL use Robinhood API for security tradeability verification
5. THE System SHALL NOT exceed free tier rate limits for any API_Client
6. WHEN an API rate limit is approached, THE System SHALL throttle requests to stay within limits

### Requirement 3: Robinhood Security Filtering

**User Story:** As an investor using Robinhood, I want all recommendations to be tradeable on Robinhood, so that I can immediately act on recommendations.

#### Acceptance Criteria

1. WHEN evaluating a security, THE System SHALL verify the security is Robinhood_Tradeable
2. THE System SHALL exclude securities that are not Robinhood_Tradeable from recommendations
3. THE System SHALL verify fractional share support for each recommended security
4. THE System SHALL store tradeability information in the Data_Manager for caching

### Requirement 4: Long-Term Investment Analysis and Recommendations

**User Story:** As an investor with limited capital, I want comprehensive fundamental and momentum analysis with position sizing guidance, so that I receive high-quality long-term investment recommendations suitable for beginners.

#### Acceptance Criteria

1. THE Investment_Analyzer SHALL perform fundamental analysis using revenue, earnings, PE ratio, debt-to-equity, free cash flow, and ROE
2. THE Investment_Analyzer SHALL perform momentum analysis using price trends and volume patterns
3. THE Investment_Analyzer SHALL incorporate global context including economic factors, Geopolitical_Event data, Industry_Trend analysis, and company specifics
4. THE Investment_Analyzer SHALL generate 1 to 5 Investment_Opportunity recommendations per day for the Newsletter
5. WHEN generating recommendations, THE Investment_Analyzer SHALL use only Fresh_Data
6. THE Investment_Analyzer SHALL assign risk levels (LOW, MEDIUM, HIGH) to each Investment_Opportunity
7. THE Investment_Analyzer SHALL calculate expected returns and holding periods for each Investment_Opportunity
8. THE Investment_Analyzer SHALL provide Position_Size recommendations between 1% and 25% of portfolio based on risk level and capital constraints
9. THE Investment_Analyzer SHALL explain recommendations in beginner-friendly language without assuming investment knowledge
10. THE Investment_Analyzer SHALL prioritize Investment_Opportunity generation as the PRIMARY system function

### Requirement 5: Daily Newsletter Generation

**User Story:** As an investor, I want to receive a daily newsletter before 9 AM Eastern Time, so that I can review recommendations before market open.

#### Acceptance Criteria

1. THE Newsletter_Generator SHALL create one Newsletter per day
2. THE Newsletter_Generator SHALL schedule newsletter generation to complete before 9:00 AM Eastern Time (ET)
3. THE Newsletter SHALL include a market overview section
4. THE Newsletter SHALL include 1 to 5 Investment_Opportunity recommendations
5. THE Newsletter SHALL include global context for each Investment_Opportunity
6. THE Newsletter SHALL include investment thesis, expected return, risk level, and holding period for each recommendation
7. WHEN no suitable opportunities are found, THE Newsletter_Generator SHALL send a newsletter explaining market conditions

### Requirement 6: Email Delivery

**User Story:** As an investor, I want newsletters delivered to my email, so that I can access recommendations conveniently.

#### Acceptance Criteria

1. THE Email_Service SHALL deliver newsletters via email
2. THE Email_Service SHALL deliver newsletters before 9:00 AM Eastern Time (ET)
3. THE Email_Service SHALL format newsletters with HTML for readability
4. THE Email_Service SHALL include plain text alternative for email clients that don't support HTML
5. WHEN email delivery fails, THE Email_Service SHALL retry up to 3 times with exponential backoff
6. WHEN email delivery fails after retries, THE Email_Service SHALL log the failure for manual review

### Requirement 7: Data Caching and Storage

**User Story:** As a system operator, I want efficient data caching and persistent storage, so that the system performs well and maintains historical data for analysis.

#### Acceptance Criteria

1. THE Data_Manager SHALL cache Quote data in Redis with appropriate TTL
2. THE Data_Manager SHALL use 15-second TTL for Active_Stock quotes
3. THE Data_Manager SHALL use 60-second TTL for Watchlist_Stock quotes
4. THE Data_Manager SHALL store historical Quote data in PostgreSQL
5. THE Data_Manager SHALL store financial data, news articles, and economic indicators in PostgreSQL
6. WHEN retrieving cached data, THE Data_Manager SHALL validate data freshness before returning
7. THE Data_Manager SHALL provide historical data retrieval for analysis periods up to 365 days

### Requirement 8: Research Data Management

**User Story:** As an analyst, I want comprehensive storage of financial data, news, geopolitical events, and industry research, so that investment analysis has access to complete historical and real-time context.

#### Acceptance Criteria

1. THE Research_Engine SHALL store company financial data including revenue, earnings, PE ratio, debt-to-equity, free cash flow, and ROE
2. THE Research_Engine SHALL store news articles with title, summary, source, publication date, URL, and sentiment score
3. THE Research_Engine SHALL store economic indicators including GDP growth, interest rates, and inflation data
4. THE Research_Engine SHALL store Geopolitical_Event data with event type, affected regions, impact scores, and timestamps
5. THE Research_Engine SHALL store Industry_Trend data with sector classifications, competitive analysis, and regulatory changes
6. THE Research_Engine SHALL store Real_Time_Projection data with confidence intervals and update timestamps
7. THE Research_Engine SHALL update financial data when new quarterly or annual reports are available
8. THE Research_Engine SHALL collect news articles, geopolitical events, and industry data continuously in real-time throughout the day
9. THE Research_Engine SHALL calculate sentiment scores for news articles ranging from -1.0 (negative) to 1.0 (positive)
10. THE Research_Engine SHALL maintain historical data for ALL data types for analysis periods up to 365 days

### Requirement 9: Credential Management

**User Story:** As a system operator, I want secure credential management, so that API keys and passwords are protected.

#### Acceptance Criteria

1. THE System SHALL store API keys and credentials in environment variables
2. THE System SHALL NOT log or display credentials in plain text
3. THE System SHALL validate that all required credentials are present at startup
4. WHEN required credentials are missing, THE System SHALL fail startup with a descriptive error message
5. THE System SHALL support credential rotation without code changes

### Requirement 10: Error Handling and Resilience

**User Story:** As a system operator, I want robust error handling, so that temporary failures don't crash the system.

#### Acceptance Criteria

1. WHEN an API_Client encounters a network error, THE System SHALL retry the request up to 3 times with exponential backoff
2. WHEN an API_Client encounters a rate limit error, THE System SHALL wait and retry after the rate limit reset time
3. WHEN the Data_Manager loses connection to Redis, THE System SHALL attempt to reconnect every 30 seconds
4. WHEN the Data_Manager loses connection to PostgreSQL, THE System SHALL attempt to reconnect every 30 seconds
5. WHEN a component encounters an unrecoverable error, THE System SHALL log the error with full context and continue operating other components
6. THE System SHALL log all errors with timestamp, component name, error type, and error message

### Requirement 11: Logging and Monitoring

**User Story:** As a system operator, I want comprehensive logging, so that I can monitor system health and troubleshoot issues.

#### Acceptance Criteria

1. THE System SHALL log all component startup and shutdown events
2. THE System SHALL log all API requests with timestamp, endpoint, and response status
3. THE System SHALL log all data freshness violations with symbol and latency
4. THE System SHALL log all newsletter generation events with timestamp and number of opportunities
5. THE System SHALL log all email delivery events with timestamp and delivery status
6. THE System SHALL use structured logging with consistent format across all components
7. THE System SHALL support configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Requirement 12: Real-Time Trading Alert System

**User Story:** As a trader with limited capital, I want instant email alerts when to buy or sell stocks for short-term trading, so that I can capitalize on time-sensitive opportunities.

#### Acceptance Criteria

1. THE Trading_Analyzer SHALL analyze real-time market data continuously to identify buy and sell trading opportunities
2. WHEN a buy opportunity is detected, THE Trading_Analyzer SHALL generate a Trading_Alert within 10 seconds
3. WHEN a sell opportunity is detected, THE Trading_Analyzer SHALL generate a Trading_Alert within 10 seconds
4. THE Alert_Generator SHALL create email content for each Trading_Alert with clear BUY or SELL action
5. THE Email_Service SHALL send Trading_Alert emails within 30 seconds of opportunity detection
6. THE Trading_Alert SHALL include entry price, target price, stop loss, expected holding period, and Position_Size recommendation
7. THE Trading_Alert SHALL explain the opportunity in beginner-friendly language
8. THE Trading_Analyzer SHALL use only Fresh_Data for trading decisions
9. THE Trading_Analyzer SHALL treat trading alerts as SECONDARY to daily Investment_Opportunity generation
10. THE Trading_Analyzer SHALL limit Trading_Alert frequency to 2-3 alerts per day maximum due to capital constraints

### Requirement 13: Geopolitical Event Monitoring and Integration

**User Story:** As an investor, I want the system to monitor and analyze geopolitical events worldwide, so that recommendations account for political risks and opportunities.

#### Acceptance Criteria

1. THE Geopolitical_Monitor SHALL track political events, elections, policy changes, conflicts, trade agreements, and sanctions worldwide
2. THE Geopolitical_Monitor SHALL collect Geopolitical_Event data from news sources in real-time
3. THE Geopolitical_Monitor SHALL analyze impact of each Geopolitical_Event on specific markets, industries, and securities
4. THE Geopolitical_Monitor SHALL assign impact scores to Geopolitical_Event data ranging from -1.0 (highly negative) to 1.0 (highly positive)
5. THE Investment_Analyzer SHALL incorporate Geopolitical_Event analysis into Investment_Opportunity recommendations
6. THE Trading_Analyzer SHALL incorporate Geopolitical_Event analysis into Trading_Alert generation
7. THE Newsletter SHALL include relevant Geopolitical_Event context for each recommendation
8. THE Geopolitical_Monitor SHALL update event impact assessments as situations evolve in real-time

### Requirement 14: Deep Industry-Level Research and Analysis

**User Story:** As an investor, I want comprehensive industry-level research, so that recommendations include competitive dynamics and sector trends.

#### Acceptance Criteria

1. THE Industry_Analyzer SHALL track Industry_Trend data for all major sectors and sub-sectors
2. THE Industry_Analyzer SHALL analyze competitive positioning, market share, and competitive advantages for companies
3. THE Industry_Analyzer SHALL monitor regulatory changes, technological disruptions, and supply chain dynamics by industry
4. THE Industry_Analyzer SHALL identify emerging industry leaders and declining incumbents
5. THE Industry_Analyzer SHALL store industry research data in the Research_Engine for historical analysis
6. THE Investment_Analyzer SHALL incorporate Industry_Trend analysis into Investment_Opportunity generation
7. THE Newsletter SHALL include industry context and competitive positioning for each recommendation
8. THE Industry_Analyzer SHALL update industry assessments continuously as new data becomes available

### Requirement 15: Real-Time Projection Capabilities

**User Story:** As an investor, I want forward-looking projections based on current trends, so that recommendations anticipate future performance rather than just analyzing history.

#### Acceptance Criteria

1. THE Projection_Engine SHALL generate Real_Time_Projection data for revenue, earnings, and price targets
2. THE Projection_Engine SHALL base projections on current trends, momentum, Industry_Trend data, and Geopolitical_Event impacts
3. THE Projection_Engine SHALL update projections continuously as new data becomes available
4. THE Projection_Engine SHALL calculate confidence intervals for each Real_Time_Projection
5. THE Investment_Analyzer SHALL incorporate Real_Time_Projection data into Investment_Opportunity recommendations
6. THE Trading_Analyzer SHALL incorporate Real_Time_Projection data into Trading_Alert generation
7. THE Newsletter SHALL include forward-looking projections with confidence levels for each recommendation
8. THE Projection_Engine SHALL NOT rely solely on historical patterns for projection generation

### Requirement 16: Configuration Management

**User Story:** As a system operator, I want flexible configuration, so that I can adjust system behavior without code changes.

#### Acceptance Criteria

1. THE System SHALL read configuration from environment variables
2. THE System SHALL support configuration for Redis URL, PostgreSQL URL, and all API credentials
3. THE System SHALL support configuration for cache TTL values (active and watchlist)
4. THE System SHALL support configuration for newsletter delivery time (default 9:00 AM Eastern Time)
5. THE System SHALL support configuration for recipient email addresses
6. THE System SHALL support configuration for Trading_Alert frequency limits
7. THE System SHALL support configuration for Position_Size calculation parameters
8. THE System SHALL validate all configuration values at startup
9. WHEN configuration is invalid, THE System SHALL fail startup with descriptive error messages

### Requirement 17: Performance Benchmarking Against S&P 500

**User Story:** As an investor, I want the system's recommendations to outperform the S&P 500 index, so that I achieve better returns than passive index investing.

#### Acceptance Criteria

1. THE System SHALL track the performance of all Investment_Opportunity recommendations from entry to exit
2. THE System SHALL calculate cumulative portfolio return based on Position_Size recommendations and actual price movements
3. THE System SHALL compare portfolio performance against S&P 500 index returns over the same time period
4. THE System SHALL calculate performance metrics including total return, annualized return, Sharpe ratio, and maximum drawdown
5. THE System SHALL store performance data in PostgreSQL for historical analysis
6. THE Newsletter SHALL include monthly performance summary comparing portfolio returns to S&P 500 benchmark
7. THE System SHALL track win rate (percentage of profitable recommendations) and average gain per winning trade
8. THE System SHALL track loss rate and average loss per losing trade
9. WHEN portfolio performance trails S&P 500 by more than 5% over a 90-day period, THE System SHALL log a performance warning
10. THE System SHALL provide performance attribution analysis showing which Investment_Opportunity types contribute most to returns

### Requirement 18: Free Hosting Platform Deployment

**User Story:** As a system operator with budget constraints, I want the entire system deployable on free hosting platforms, so that I incur zero hosting costs.

#### Acceptance Criteria

1. THE System SHALL be deployable on free hosting platforms including Heroku free tier, Railway free tier, Render free tier, or equivalent services
2. THE System SHALL operate within free tier resource limits including memory, CPU, and storage constraints
3. THE System SHALL use free tier database services for PostgreSQL (such as ElephantSQL free tier, Supabase free tier, or Neon free tier)
4. THE System SHALL use free tier Redis services (such as Redis Cloud free tier or Upstash free tier)
5. THE System SHALL optimize memory usage to stay within 512 MB RAM limit typical of free hosting tiers
6. THE System SHALL handle platform sleep/wake cycles gracefully for platforms that sleep after inactivity
7. THE System SHALL NOT require paid add-ons, paid databases, or paid infrastructure services
8. THE System SHALL document deployment instructions for at least two different free hosting platforms
9. WHEN deployed on free hosting, THE System SHALL maintain all core functionality including real-time monitoring and email delivery
10. THE System SHALL use free email delivery services (such as SendGrid free tier, Mailgun free tier, or SMTP with free email providers)

### Requirement 19: Comprehensive Free Data Source Utilization

**User Story:** As a system operator, I want to maximize all available free data sources and APIs, so that the system gathers comprehensive market intelligence without incurring data costs.

#### Acceptance Criteria

1. THE System SHALL identify and integrate ALL available free-tier financial data APIs beyond yfinance, Finnhub, and Twelve Data
2. THE System SHALL use free news APIs (such as NewsAPI free tier, Alpha Vantage news, or RSS feeds) for market news collection
3. THE System SHALL use free economic data sources (such as FRED API, World Bank API, or IMF data) for economic indicators
4. THE System SHALL use free sentiment analysis tools or libraries for news sentiment scoring
5. THE System SHALL aggregate data from multiple free sources to maximize data coverage and redundancy
6. WHEN one free API source is unavailable, THE System SHALL fall back to alternative free sources for the same data type
7. THE System SHALL use web scraping with rate limiting for publicly available data when no free API exists
8. THE System SHALL respect robots.txt and terms of service for all data sources
9. THE System SHALL document all free data sources used with API limits and refresh rates
10. THE System SHALL monitor free tier usage across all APIs to prevent exceeding limits
11. THE System SHALL prioritize data sources with higher free tier limits when multiple sources provide equivalent data
12. THE System SHALL cache aggressively to minimize API calls and maximize free tier utilization efficiency

