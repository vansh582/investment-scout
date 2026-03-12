# Implementation Plan: Investment Scout

## Overview

This implementation plan breaks down the Investment Scout system into discrete, testable tasks. The system operates on free hosting (512 MB RAM) using only free-tier APIs (yfinance, Finnhub, Twelve Data) to deliver:
1. PRIMARY: Daily 9 AM ET newsletter with 1-5 long-term investment opportunities
2. SECONDARY: 2-3 real-time trading alerts per day

The implementation prioritizes data freshness (<30s latency), free-tier optimization, multi-source resilience, and performance tracking against S&P 500.

## Tasks

- [x] 1. Set up core data models and validation
  - Create Quote, FinancialData, NewsArticle, GeopoliticalEvent, IndustryTrend, RealTimeProjection data classes
  - Implement timestamp tracking and latency calculation in Quote model
  - Implement is_fresh property validation (<30s latency)
  - Create InvestmentOpportunity and TradingAlert models with position sizing
  - Create GlobalContext, PerformanceMetrics, Newsletter models
  - _Requirements: 1.4, 1.5, 1.6, 4.8, 8.9, 13.4, 15.4_

- [ ]* 1.1 Write property test for data timestamp recording
  - **Property 1: Data Timestamp Recording**
  - **Validates: Requirements 1.4**

- [ ]* 1.2 Write property test for latency calculation correctness
  - **Property 2: Latency Calculation Correctness**
  - **Validates: Requirements 1.5**

- [ ]* 1.3 Write property test for stale data flagging
  - **Property 3: Stale Data Flagging**
  - **Validates: Requirements 1.6**

- [ ]* 1.4 Write property test for sentiment score range
  - **Property 12: Sentiment Score Range**
  - **Validates: Requirements 8.9**

- [ ]* 1.5 Write property test for geopolitical impact score range
  - **Property 17: Geopolitical Impact Score Range**
  - **Validates: Requirements 13.4**

- [ ]* 1.6 Write property test for projection confidence intervals
  - **Property 18: Projection Confidence Intervals**
  - **Validates: Requirements 15.4**

- [ ]* 1.7 Write property test for position size range constraint
  - **Property 8: Position Size Range Constraint**
  - **Validates: Requirements 4.8**

- [x] 2. Implement Data Manager with Redis and PostgreSQL
  - Create DataManager class with Redis caching and PostgreSQL persistence
  - Implement dual TTL caching: 15s for active stocks, 60s for watchlist stocks
  - Implement cache_quote() with TTL-based expiration
  - Implement get_cached_quote() with freshness validation
  - Implement store_historical_data() for PostgreSQL persistence
  - Implement get_historical_data() for retrieval
  - Create PostgreSQL schema for financial_data, news_articles, geopolitical_events, industry_trends, projections tables
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 8.1-8.6_

- [ ]* 2.1 Write property test for dual TTL caching strategy
  - **Property 5: Dual TTL Caching Strategy**
  - **Validates: Requirements 1.8, 7.2, 7.3**

- [ ]* 2.2 Write property test for cache freshness validation
  - **Property 11: Cache Freshness Validation**
  - **Validates: Requirements 7.6**

- [x] 3. Implement API clients with rate limiting and failover
  - Create base APIClient class with circuit breaker pattern
  - Implement YFinanceClient for market data and financials
  - Implement FinnhubClient for company info and news
  - Implement TwelveDataClient for technical indicators
  - Implement RobinhoodClient for tradeability verification
  - Add rate limit tracking and throttling for each client
  - Implement retry logic with exponential backoff (1s, 3s, 9s)
  - Cache Robinhood tradeability results for 24h
  - _Requirements: 2.1-2.6, 3.1-3.4, 10.1, 10.2_

- [ ]* 3.1 Write property test for rate limit compliance
  - **Property 6: Rate Limit Compliance**
  - **Validates: Requirements 2.5**

- [ ]* 3.2 Write property test for retry with exponential backoff
  - **Property 10: Retry with Exponential Backoff**
  - **Validates: Requirements 6.5, 10.1**

- [ ]* 3.3 Write property test for rate limit error handling
  - **Property 13: Rate Limit Error Handling**
  - **Validates: Requirements 10.2**

- [ ]* 3.4 Write property test for API failover chain
  - **Property 23: API Failover Chain**
  - **Validates: Requirements 19.6**

- [x] 4. Implement Market Monitor with continuous polling
  - Create MarketMonitor class with 24/7 monitoring capability
  - Implement start_monitoring() to begin continuous polling
  - Implement poll_market_data() with 15s interval for active stocks, 60s for watchlist
  - Implement get_current_price() with failover chain: yfinance → Finnhub → Twelve Data → cache
  - Implement is_data_fresh() validation rejecting >30s latency
  - Record exchange_timestamp and received_timestamp for all quotes
  - Implement update_watchlist() for dynamic symbol management
  - Log all data freshness violations
  - _Requirements: 1.1-1.9, 10.3_

- [ ]* 4.1 Write property test for fresh data usage in analysis
  - **Property 4: Fresh Data Usage in Analysis**
  - **Validates: Requirements 1.7, 4.5, 12.8**

- [ ]* 4.2 Write unit tests for Market Monitor
  - Test failover chain execution
  - Test stale data rejection
  - Test dual TTL polling intervals
  - _Requirements: 1.6, 1.7, 1.8_

- [x] 5. Implement Research Engine for data aggregation
  - Create ResearchEngine class for centralized data storage
  - Implement store_financial_data() for company financials
  - Implement store_news_article() with sentiment scoring
  - Implement store_geopolitical_event() with impact analysis
  - Implement store_industry_trend() for sector research
  - Implement store_projection() for forward-looking data
  - Implement get_company_context() for comprehensive retrieval
  - Implement get_market_sentiment() for overall market analysis
  - _Requirements: 8.1-8.10_

- [ ]* 5.1 Write unit tests for Research Engine
  - Test data storage and retrieval
  - Test sentiment score calculation
  - Test context aggregation
  - _Requirements: 8.1-8.10_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement Geopolitical Monitor
  - Create GeopoliticalMonitor class for event tracking
  - Implement collect_events() from news APIs and RSS feeds
  - Implement analyze_impact() to score event impact (-1.0 to 1.0)
  - Implement get_affected_securities() to identify impacted stocks
  - Implement calculate_impact_score() with validation
  - Track elections, policy changes, conflicts, trade agreements, sanctions
  - Store events in Research Engine
  - _Requirements: 13.1-13.8_

- [ ]* 7.1 Write unit tests for Geopolitical Monitor
  - Test event collection and parsing
  - Test impact score calculation
  - Test affected securities identification
  - _Requirements: 13.1-13.4_

- [x] 8. Implement Industry Analyzer
  - Create IndustryAnalyzer class for sector research
  - Implement analyze_sector() for sector trends and outlook
  - Implement analyze_competitive_position() for company positioning
  - Implement detect_disruptions() for regulatory/technological changes
  - Implement identify_leaders() for emerging sector leaders
  - Track competitive positioning, regulatory changes, tech disruptions, supply chain
  - Store trends in Research Engine
  - _Requirements: 14.1-14.8_

- [ ]* 8.1 Write unit tests for Industry Analyzer
  - Test sector analysis
  - Test competitive positioning
  - Test disruption detection
  - _Requirements: 14.1-14.5_

- [x] 9. Implement Projection Engine
  - Create ProjectionEngine class for forward-looking analysis
  - Implement project_revenue() with confidence intervals
  - Implement project_earnings() with confidence intervals
  - Implement project_price_target() with confidence intervals
  - Implement update_projections() for continuous updates
  - Base projections on current trends, industry data, geopolitical impacts
  - Validate confidence_lower ≤ projected_value ≤ confidence_upper
  - Store projections in Research Engine
  - _Requirements: 15.1-15.8_

- [ ]* 9.1 Write unit tests for Projection Engine
  - Test projection generation
  - Test confidence interval validation
  - Test continuous updates
  - _Requirements: 15.1-15.4_

- [x] 10. Implement Investment Analyzer (PRIMARY function)
  - Create InvestmentAnalyzer class for long-term opportunity generation
  - Implement analyze_opportunities() to generate 1-5 daily recommendations
  - Implement perform_fundamental_analysis() using revenue, earnings, PE, debt, FCF, ROE
  - Implement perform_momentum_analysis() using price trends and volume
  - Implement build_global_context() aggregating economic, geopolitical, industry, company data
  - Implement calculate_position_size() based on risk level (LOW: 15-25%, MEDIUM: 8-15%, HIGH: 1-8%)
  - Implement verify_robinhood_tradeable() with 24h caching
  - Implement scoring formula: Fundamental (40%) + Momentum (30%) + Context (20%) + Projection (10%)
  - Generate beginner-friendly investment thesis for each opportunity
  - Use only fresh data (<30s latency) for all analysis
  - _Requirements: 3.1-3.4, 4.1-4.10_

- [ ]* 10.1 Write property test for Robinhood tradeability filtering
  - **Property 7: Robinhood Tradeability Filtering**
  - **Validates: Requirements 3.1, 3.2**

- [ ]* 10.2 Write property test for newsletter opportunity count
  - **Property 9: Newsletter Opportunity Count**
  - **Validates: Requirements 5.4**

- [ ]* 10.3 Write unit tests for Investment Analyzer
  - Test fundamental analysis scoring
  - Test momentum analysis
  - Test position sizing by risk level
  - Test opportunity ranking
  - _Requirements: 4.1-4.8_

- [x] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Implement Trading Analyzer (SECONDARY function)
  - Create TradingAnalyzer class for real-time trading alerts
  - Implement analyze_real_time() to detect opportunities from fresh quotes
  - Implement detect_buy_signal() for breakouts, oversold bounces, positive catalysts
  - Implement detect_sell_signal() for breakdowns, overbought reversals, negative news
  - Implement calculate_entry_exit() for entry, target, stop loss levels
  - Implement check_alert_limit() to enforce max 3 alerts per day
  - Generate alerts within 10 seconds of opportunity detection
  - Require volume confirmation and fresh data (<30s)
  - Include risk management with stop loss and target price
  - _Requirements: 12.1-12.10_

- [ ]* 12.1 Write property test for trading alert generation timing
  - **Property 14: Trading Alert Generation Timing**
  - **Validates: Requirements 12.2, 12.3**

- [ ]* 12.2 Write property test for trading alert frequency limit
  - **Property 16: Trading Alert Frequency Limit**
  - **Validates: Requirements 12.10**

- [ ]* 12.3 Write unit tests for Trading Analyzer
  - Test buy signal detection
  - Test sell signal detection
  - Test alert frequency limiting
  - Test entry/exit calculation
  - _Requirements: 12.1-12.7_

- [x] 13. Implement Performance Tracker
  - Create PerformanceTracker class for portfolio monitoring
  - Implement track_recommendation() to start tracking entries
  - Implement update_positions() for continuous value updates
  - Implement calculate_returns() for portfolio metrics
  - Implement compare_to_benchmark() for S&P 500 comparison
  - Implement generate_attribution() for contribution analysis
  - Track total return, annualized return, Sharpe ratio, max drawdown
  - Track win rate, avg gain per winner, loss rate, avg loss per loser
  - Create recommendations and performance_snapshots tables
  - Log warning when trailing S&P 500 by >5% over 90 days
  - _Requirements: 17.1-17.10_

- [ ]* 13.1 Write property test for performance tracking completeness
  - **Property 20: Performance Tracking Completeness**
  - **Validates: Requirements 17.1**

- [ ]* 13.2 Write property test for portfolio return calculation
  - **Property 21: Portfolio Return Calculation**
  - **Validates: Requirements 17.2**

- [ ]* 13.3 Write unit tests for Performance Tracker
  - Test return calculation
  - Test S&P 500 comparison
  - Test win/loss rate calculation
  - Test attribution analysis
  - _Requirements: 17.1-17.8_

- [x] 14. Implement Newsletter Generator
  - Create NewsletterGenerator class for daily email content
  - Implement generate_newsletter() to create Newsletter from opportunities
  - Implement format_html() for HTML email formatting
  - Implement format_plain_text() for plain text alternative
  - Implement create_market_overview() for market conditions summary
  - Include market overview, economic indicators, geopolitical events, sector performance
  - Format each opportunity with: company, price, target, thesis, global context, timing, risk, return, holding period, position size
  - Include monthly performance summary comparing to S&P 500
  - Add disclaimer and unsubscribe link
  - _Requirements: 5.1-5.7, 6.3, 6.4_

- [ ]* 14.1 Write unit tests for Newsletter Generator
  - Test HTML formatting
  - Test plain text formatting
  - Test market overview generation
  - Test opportunity formatting
  - _Requirements: 5.3-5.7_

- [x] 15. Implement Alert Generator
  - Create AlertGenerator class for trading alert emails
  - Implement generate_alert() to create alert content
  - Implement format_alert_html() for HTML formatting
  - Implement format_alert_plain_text() for plain text alternative
  - Include: action (BUY/SELL), symbol, current price, entry, target, stop loss, position size
  - Include: rationale, context, risk factors, expected holding period
  - Add disclaimer
  - _Requirements: 12.4, 12.6, 12.7_

- [ ]* 15.1 Write unit tests for Alert Generator
  - Test alert content generation
  - Test HTML formatting
  - Test plain text formatting
  - _Requirements: 12.4, 12.6_

- [x] 16. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 17. Implement Email Service with retry logic
  - Create EmailService class using SendGrid free tier
  - Implement send_newsletter() for daily newsletter delivery
  - Implement send_alert() for trading alert delivery
  - Implement send_with_retry() with exponential backoff (5s, 15s, 45s)
  - Deliver newsletters before 9:00 AM ET
  - Deliver alerts within 30 seconds of generation
  - Log all delivery attempts and final status
  - Send system alert if newsletter fails after all retries
  - _Requirements: 6.1, 6.2, 6.5, 6.6, 12.5_

- [ ]* 17.1 Write property test for trading alert delivery timing
  - **Property 15: Trading Alert Delivery Timing**
  - **Validates: Requirements 12.5**

- [ ]* 17.2 Write unit tests for Email Service
  - Test successful delivery
  - Test retry logic
  - Test failure after max retries
  - Test timing constraints
  - _Requirements: 6.1-6.6_

- [x] 18. Implement Configuration Manager
  - Create ConfigurationManager class for environment variable management
  - Load Redis URL, PostgreSQL URL, API credentials from environment
  - Load cache TTL values, newsletter time, recipient emails, alert limits
  - Load position sizing parameters
  - Implement validate_configuration() at startup
  - Fail startup with descriptive errors for missing/invalid config
  - Support credential rotation without code changes
  - _Requirements: 9.1-9.5, 16.1-16.9_

- [ ]* 18.1 Write property test for configuration validation at startup
  - **Property 19: Configuration Validation at Startup**
  - **Validates: Requirements 16.8, 16.9**

- [ ]* 18.2 Write unit tests for Configuration Manager
  - Test configuration loading
  - Test validation logic
  - Test startup failure scenarios
  - _Requirements: 16.1-16.9_

- [-] 19. Implement Logging System
  - Create structured logging with JSON format
  - Implement log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - Log component startup/shutdown events
  - Log all API requests with provider, endpoint, status, latency
  - Log data freshness violations with symbol and latency
  - Log failover events
  - Log newsletter and alert generation/delivery
  - Log performance metric updates
  - Log database connection status changes
  - Log memory usage warnings
  - Log all errors with full stack traces
  - _Requirements: 10.5, 10.6, 11.1-11.7_

- [ ]* 19.1 Write unit tests for Logging System
  - Test structured log format
  - Test log level filtering
  - Test critical event logging
  - _Requirements: 11.1-11.7_

- [x] 20. Implement Error Handling and Resilience
  - Implement CircuitBreaker pattern for API clients
  - Implement graceful degradation for component failures
  - Handle network errors with retry and failover
  - Handle rate limit errors with wait and retry
  - Handle database connection errors with reconnection attempts
  - Handle memory pressure with aggressive cleanup
  - Queue writes in memory (max 1000) during PostgreSQL outage
  - Continue with degraded service during Redis outage
  - _Requirements: 10.1-10.6_

- [ ]* 20.1 Write unit tests for Error Handling
  - Test circuit breaker pattern
  - Test graceful degradation
  - Test reconnection logic
  - Test memory pressure handling
  - _Requirements: 10.1-10.5_

- [x] 21. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 22. Implement Scheduler and Orchestration
  - Create Scheduler class for task orchestration
  - Schedule Investment Analyzer to run at 8:30 AM ET daily
  - Schedule Newsletter Generator to complete before 9:00 AM ET
  - Schedule Market Monitor for continuous 24/7 operation
  - Schedule Trading Analyzer for real-time monitoring (15s intervals)
  - Schedule Performance Tracker updates (daily)
  - Schedule Geopolitical Monitor updates (every 6 hours)
  - Schedule Industry Analyzer updates (daily)
  - Schedule Projection Engine updates (hourly)
  - Implement wake-up handling for free hosting sleep cycles
  - Use external cron service (cron-job.org) to ping every 25 minutes
  - _Requirements: 1.1, 5.2, 12.1_

- [ ]* 22.1 Write unit tests for Scheduler
  - Test task scheduling
  - Test timing constraints
  - Test wake-up handling
  - _Requirements: 1.1, 5.2_

- [x] 23. Implement Memory Optimization
  - Implement aggressive cache eviction in Redis
  - Implement lazy loading for historical data
  - Implement streaming processing for large datasets
  - Limit active watchlist to 100-200 stocks
  - Monitor memory usage and trigger cleanup at 400 MB
  - Use lightweight libraries where possible
  - Optimize data structures for memory efficiency
  - _Requirements: 18.5_

- [ ]* 23.1 Write property test for memory usage constraint
  - **Property 22: Memory Usage Constraint**
  - **Validates: Requirements 18.5**

- [ ]* 23.2 Write unit tests for Memory Optimization
  - Test cache eviction
  - Test lazy loading
  - Test memory monitoring
  - _Requirements: 18.5_

- [x] 24. Implement Free Data Source Integration
  - Integrate NewsAPI free tier for market news
  - Integrate Alpha Vantage news API
  - Integrate FRED API for economic indicators
  - Integrate World Bank API for global economic data
  - Set up RSS feed parsing for additional news sources
  - Implement web scraping with rate limiting for public data
  - Respect robots.txt and terms of service
  - Implement failover across multiple free sources
  - Monitor free tier usage to prevent limit violations
  - Cache aggressively to maximize free tier efficiency
  - _Requirements: 19.1-19.12_

- [ ]* 24.1 Write unit tests for Free Data Source Integration
  - Test multi-source aggregation
  - Test failover logic
  - Test rate limit monitoring
  - Test caching efficiency
  - _Requirements: 19.1-19.11_

- [x] 25. Integration and Wiring
  - Wire Market Monitor to API clients and Data Manager
  - Wire Research Engine to Data Manager
  - Wire Investment Analyzer to Research Engine, Projection Engine, Robinhood Client
  - Wire Trading Analyzer to Market Monitor, Research Engine
  - Wire Newsletter Generator to Investment Analyzer
  - Wire Alert Generator to Trading Analyzer
  - Wire Email Service to Newsletter Generator and Alert Generator
  - Wire Performance Tracker to Investment Analyzer and Trading Analyzer
  - Wire Scheduler to all components
  - Create main application entry point
  - Implement startup sequence with configuration validation
  - _Requirements: All_

- [ ]* 25.1 Write integration tests
  - Test end-to-end newsletter generation flow
  - Test real-time alert flow
  - Test multi-provider failover
  - Test database persistence
  - Test performance tracking
  - _Requirements: All_

- [x] 26. Deployment Configuration
  - Create requirements.txt with all dependencies
  - Create Dockerfile for containerized deployment
  - Create docker-compose.yml for local development
  - Create Heroku Procfile and app.json
  - Create Railway deployment configuration
  - Create Render deployment configuration
  - Document environment variables in .env.example
  - Create deployment guide for at least 2 free hosting platforms
  - Configure free PostgreSQL (ElephantSQL/Supabase/Neon)
  - Configure free Redis (Redis Cloud/Upstash)
  - Configure SendGrid free tier for email
  - Set up external cron service (cron-job.org) for wake-up pings
  - _Requirements: 18.1-18.10_

- [ ]* 26.1 Write deployment verification tests
  - Test startup on free hosting constraints
  - Test memory usage under 512 MB
  - Test sleep/wake cycle handling
  - _Requirements: 18.1-18.9_

- [x] 27. Final Checkpoint - Ensure all tests pass
  - Run complete test suite
  - Verify all property tests pass (100+ iterations each)
  - Verify all unit tests pass
  - Verify all integration tests pass
  - Check memory usage stays under 512 MB
  - Verify newsletter generation completes before 9 AM ET
  - Verify trading alerts sent within 30 seconds
  - Verify all 23 correctness properties validated
  - Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at reasonable breaks
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end flows
- The system prioritizes PRIMARY function (daily newsletter) over SECONDARY function (trading alerts)
- All implementation must work within free-tier constraints: 512 MB RAM, free APIs, free hosting
- Data freshness (<30s latency) is enforced throughout the system
- Performance tracking against S&P 500 is built into the core system
