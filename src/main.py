"""Main application entry point for Investment Scout"""

import sys
import signal
import threading
from typing import Optional
from datetime import datetime, timedelta

from src.utils.configuration_manager import initialize_config, ConfigurationError
from src.utils.logger import get_logger, setup_logging
from src.utils.scheduler import Scheduler
from src.web_server import WebServer

# Import all components
from src.utils.data_manager_scout import DataManager
from src.utils.credential_manager import CredentialManager
from src.clients.yfinance_client_scout import YFinanceClient
from src.clients.finnhub_client_scout import FinnhubClient
from src.clients.twelve_data_client_scout import TwelveDataClient
from src.clients.robinhood_client_scout import RobinhoodClient
from src.utils.market_monitor import MarketMonitor
from src.utils.research_engine import ResearchEngine
from src.utils.geopolitical_monitor import GeopoliticalMonitor
from src.utils.industry_analyzer import IndustryAnalyzer
from src.utils.projection_engine import ProjectionEngine
from src.utils.investment_analyzer import InvestmentAnalyzer
from src.utils.trading_analyzer import TradingAnalyzer
from src.utils.performance_tracker import PerformanceTracker
from src.utils.newsletter_generator import NewsletterGenerator
from src.utils.alert_generator import AlertGenerator
from src.utils.email_service import EmailService


logger = get_logger(__name__)


class InvestmentScoutApp:
    """Main Investment Scout application"""
    
    def __init__(self):
        """Initialize the application"""
        self.config = None
        self.scheduler: Optional[Scheduler] = None
        self.web_server: Optional[WebServer] = None
        self.shutdown_event = threading.Event()
        
        # Component instances
        self.credential_manager: Optional[CredentialManager] = None
        self.data_manager: Optional[DataManager] = None
        self.yfinance_client: Optional[YFinanceClient] = None
        self.finnhub_client: Optional[FinnhubClient] = None
        self.twelve_data_client: Optional[TwelveDataClient] = None
        self.robinhood_client: Optional[RobinhoodClient] = None
        self.market_monitor: Optional[MarketMonitor] = None
        self.research_engine: Optional[ResearchEngine] = None
        self.geopolitical_monitor: Optional[GeopoliticalMonitor] = None
        self.industry_analyzer: Optional[IndustryAnalyzer] = None
        self.projection_engine: Optional[ProjectionEngine] = None
        self.investment_analyzer: Optional[InvestmentAnalyzer] = None
        self.trading_analyzer: Optional[TradingAnalyzer] = None
        self.performance_tracker: Optional[PerformanceTracker] = None
        self.newsletter_generator: Optional[NewsletterGenerator] = None
        self.alert_generator: Optional[AlertGenerator] = None
        self.email_service: Optional[EmailService] = None
    
    def initialize(self):
        """Initialize all components with proper wiring"""
        try:
            # Set up logging
            setup_logging()
            logger.info("app_startup", "=" * 80)
            logger.info("app_startup", "Investment Scout - Automated Market Intelligence System")
            logger.info("app_startup", "=" * 80)
            
            # Load and validate configuration
            logger.info("config_loading", "Loading configuration...")
            self.config = initialize_config()
            logger.info("config_loaded", f"Configuration loaded successfully (Environment: {self.config.environment})")
            
            # Initialize credential manager
            logger.info("component_init", "Initializing credential manager...")
            self.credential_manager = CredentialManager()
            
            # Initialize Data Manager
            logger.info("component_init", "Initializing Data Manager...")
            self.data_manager = DataManager(
                redis_url=self.config.redis_url,
                postgres_url=self.config.postgres_url
            )
            logger.info("component_ready", "Data Manager initialized")
            
            # Initialize API Clients
            logger.info("component_init", "Initializing API clients...")
            self.yfinance_client = YFinanceClient()
            
            # Finnhub client (optional - only if API key available)
            try:
                finnhub_key = self.credential_manager.get_credential('finnhub_api_key')
                if finnhub_key:
                    self.finnhub_client = FinnhubClient(api_key=finnhub_key)
                    logger.info("component_ready", "Finnhub client initialized")
            except Exception as e:
                logger.warning("component_init_warning", f"Finnhub client not initialized: {e}")
            
            # Twelve Data client (optional - only if API key available)
            try:
                twelve_data_key = self.credential_manager.get_credential('twelve_data_api_key')
                if twelve_data_key:
                    self.twelve_data_client = TwelveDataClient(api_key=twelve_data_key)
                    logger.info("component_ready", "Twelve Data client initialized")
            except Exception as e:
                logger.warning("component_init_warning", f"Twelve Data client not initialized: {e}")
            
            # Robinhood client
            self.robinhood_client = RobinhoodClient()
            logger.info("component_ready", "API clients initialized")
            
            # Initialize Market Monitor (wired to API clients and Data Manager)
            logger.info("component_init", "Initializing Market Monitor...")
            self.market_monitor = MarketMonitor(
                data_manager=self.data_manager,
                yfinance_client=self.yfinance_client,
                finnhub_client=self.finnhub_client,
                twelve_data_client=self.twelve_data_client
            )
            logger.info("component_ready", "Market Monitor initialized")
            
            # Initialize Research Engine (wired to Data Manager)
            logger.info("component_init", "Initializing Research Engine...")
            self.research_engine = ResearchEngine(
                data_manager=self.data_manager
            )
            logger.info("component_ready", "Research Engine initialized")
            
            # Initialize Geopolitical Monitor (wired to Research Engine)
            logger.info("component_init", "Initializing Geopolitical Monitor...")
            self.geopolitical_monitor = GeopoliticalMonitor(
                research_engine=self.research_engine
            )
            logger.info("component_ready", "Geopolitical Monitor initialized")
            
            # Initialize Industry Analyzer (wired to Research Engine)
            logger.info("component_init", "Initializing Industry Analyzer...")
            self.industry_analyzer = IndustryAnalyzer(
                research_engine=self.research_engine
            )
            logger.info("component_ready", "Industry Analyzer initialized")
            
            # Initialize Projection Engine (wired to Research Engine)
            logger.info("component_init", "Initializing Projection Engine...")
            self.projection_engine = ProjectionEngine(
                research_engine=self.research_engine
            )
            logger.info("component_ready", "Projection Engine initialized")
            
            # Initialize Investment Analyzer (wired to Research Engine, Projection Engine, Market Monitor)
            logger.info("component_init", "Initializing Investment Analyzer...")
            self.investment_analyzer = InvestmentAnalyzer(
                research_engine=self.research_engine,
                projection_engine=self.projection_engine,
                market_monitor=self.market_monitor
            )
            logger.info("component_ready", "Investment Analyzer initialized")
            
            # Initialize Trading Analyzer (wired to Data Manager, Research Engine)
            logger.info("component_init", "Initializing Trading Analyzer...")
            self.trading_analyzer = TradingAnalyzer(
                data_manager=self.data_manager,
                research_engine=self.research_engine,
                max_alerts_per_day=self.config.max_trading_alerts_per_day
            )
            logger.info("component_ready", "Trading Analyzer initialized")
            
            # Initialize Performance Tracker
            logger.info("component_init", "Initializing Performance Tracker...")
            self.performance_tracker = PerformanceTracker(
                postgres_url=self.config.postgres_url
            )
            logger.info("component_ready", "Performance Tracker initialized")
            
            # Initialize Newsletter Generator (wired to Performance Tracker, Market Monitor, etc.)
            logger.info("component_init", "Initializing Newsletter Generator...")
            self.newsletter_generator = NewsletterGenerator(
                performance_tracker=self.performance_tracker,
                market_monitor=self.market_monitor,
                geopolitical_monitor=self.geopolitical_monitor,
                industry_analyzer=self.industry_analyzer
            )
            logger.info("component_ready", "Newsletter Generator initialized")
            
            # Initialize Alert Generator
            logger.info("component_init", "Initializing Alert Generator...")
            self.alert_generator = AlertGenerator()
            logger.info("component_ready", "Alert Generator initialized")
            
            # Initialize Email Service (wired to Credential Manager)
            logger.info("component_init", "Initializing Email Service...")
            self.email_service = EmailService(
                credential_manager=self.credential_manager
            )
            logger.info("component_ready", "Email Service initialized")
            
            # Create component callbacks for scheduler
            def investment_analyzer_callback():
                """Run investment analysis and generate opportunities"""
                logger.info("task_execution", "Running Investment Analyzer (8:30 AM ET)")
                try:
                    # Get candidate symbols (would come from watchlist in production)
                    candidate_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
                    
                    # Analyze opportunities
                    opportunities = self.investment_analyzer.analyze_opportunities(candidate_symbols)
                    
                    if opportunities:
                        logger.info("task_complete", f"Generated {len(opportunities)} investment opportunities")
                        
                        # Track recommendations
                        for opp in opportunities:
                            self.performance_tracker.track_recommendation(opp)
                        
                        # Trigger newsletter generation
                        newsletter_generator_callback(opportunities)
                    else:
                        logger.warning("task_warning", "No investment opportunities generated")
                        
                except Exception as e:
                    logger.error("task_error", f"Error in investment analyzer: {e}", error=e)
            
            def newsletter_generator_callback(opportunities=None):
                """Generate and send daily newsletter"""
                logger.info("task_execution", "Running Newsletter Generator (before 9:00 AM ET)")
                try:
                    if not opportunities:
                        logger.warning("task_warning", "No opportunities provided for newsletter")
                        return
                    
                    # Generate newsletter
                    newsletter = self.newsletter_generator.generate_newsletter(opportunities)
                    
                    # Format HTML and plain text
                    html_content = self.newsletter_generator.format_html(newsletter)
                    plain_text_content = self.newsletter_generator.format_plain_text(newsletter)
                    
                    # Get recipient emails
                    recipient_emails = self.config.recipient_emails
                    
                    # Send newsletter
                    subject = f"Investment Scout Daily - {newsletter.date.strftime('%B %d, %Y')}"
                    success = self.email_service.send_newsletter(
                        html_content=html_content,
                        plain_text_content=plain_text_content,
                        recipients=recipient_emails,
                        subject=subject
                    )
                    
                    if success:
                        logger.info("task_complete", "Newsletter sent successfully")
                    else:
                        logger.error("task_error", "Newsletter delivery failed")
                        
                except Exception as e:
                    logger.error("task_error", f"Error in newsletter generator: {e}", error=e)
            
            def market_monitor_callback():
                """Start continuous market monitoring"""
                logger.info("task_execution", "Starting Market Monitor (24/7 continuous)")
                try:
                    # Define active and watchlist symbols
                    active_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
                    watchlist_symbols = ['NVDA', 'META', 'NFLX', 'AMD', 'INTC']
                    
                    # Start monitoring
                    self.market_monitor.start_monitoring(
                        active_symbols=active_symbols,
                        watchlist_symbols=watchlist_symbols
                    )
                    
                except Exception as e:
                    logger.error("task_error", f"Error in market monitor: {e}", error=e)
            
            def trading_analyzer_callback():
                """Analyze real-time data for trading alerts"""
                logger.info("task_execution", "Running Trading Analyzer (15s intervals)")
                try:
                    # Get active symbols
                    active_symbols = list(self.market_monitor.active_symbols)
                    
                    for symbol in active_symbols:
                        # Get fresh quote
                        quote = self.market_monitor.get_current_price(symbol)
                        
                        if quote and quote.is_fresh:
                            # Analyze for trading opportunity
                            alert = self.trading_analyzer.analyze_real_time(quote)
                            
                            if alert:
                                logger.info("alert_generated", f"Trading alert generated for {symbol}")
                                
                                # Generate alert email
                                html_content = self.alert_generator.format_alert_html(alert)
                                plain_text_content = self.alert_generator.format_alert_plain_text(alert)
                                
                                # Send alert
                                subject = f"🚨 Trading Alert: {alert.signal_type.value.upper()} {alert.symbol}"
                                success = self.email_service.send_alert(
                                    html_content=html_content,
                                    plain_text_content=plain_text_content,
                                    recipients=self.config.recipient_emails,
                                    subject=subject
                                )
                                
                                if success:
                                    # Increment alert count
                                    self.trading_analyzer.increment_alert_count()
                                    logger.info("alert_sent", f"Trading alert sent for {symbol}")
                                
                except Exception as e:
                    logger.error("task_error", f"Error in trading analyzer: {e}", error=e)
            
            def performance_tracker_callback():
                """Update performance metrics"""
                logger.info("task_execution", "Running Performance Tracker (daily)")
                try:
                    # Get current prices for all tracked positions
                    # This is simplified - would get actual positions from database
                    current_prices = {}
                    
                    # Update positions
                    self.performance_tracker.update_positions(current_prices)
                    
                    # Calculate returns
                    metrics = self.performance_tracker.calculate_returns()
                    logger.info("task_complete", f"Portfolio return: {metrics['total_return_percent']:.2f}%")
                    
                except Exception as e:
                    logger.error("task_error", f"Error in performance tracker: {e}", error=e)
            
            def geopolitical_monitor_callback():
                """Monitor geopolitical events"""
                logger.info("task_execution", "Running Geopolitical Monitor (every 6 hours)")
                try:
                    # Collect news articles (would use actual news sources)
                    # This is a placeholder
                    news_articles = []
                    
                    # Collect and store events
                    events = self.geopolitical_monitor.collect_events(news_articles)
                    
                    for event in events:
                        self.geopolitical_monitor.store_event(event)
                    
                    logger.info("task_complete", f"Processed {len(events)} geopolitical events")
                    
                except Exception as e:
                    logger.error("task_error", f"Error in geopolitical monitor: {e}", error=e)
            
            def industry_analyzer_callback():
                """Analyze industry trends"""
                logger.info("task_execution", "Running Industry Analyzer (daily)")
                try:
                    # Analyze major sectors
                    sectors = ['Technology', 'Healthcare', 'Financial', 'Energy']
                    
                    for sector in sectors:
                        analysis = self.industry_analyzer.analyze_sector(sector)
                        logger.info("task_complete", f"Sector {sector}: {analysis.trend_direction}")
                    
                except Exception as e:
                    logger.error("task_error", f"Error in industry analyzer: {e}", error=e)
            
            def projection_engine_callback():
                """Update projections"""
                logger.info("task_execution", "Running Projection Engine (hourly)")
                try:
                    # Update projections for tracked symbols
                    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
                    self.projection_engine.update_projections(symbols)
                    
                except Exception as e:
                    logger.error("task_error", f"Error in projection engine: {e}", error=e)
            
            # Initialize scheduler with component callbacks
            logger.info("component_init", "Initializing scheduler...")
            self.scheduler = Scheduler(
                config=self.config,
                investment_analyzer=investment_analyzer_callback,
                newsletter_generator=lambda: None,  # Called by investment_analyzer
                market_monitor=market_monitor_callback,
                trading_analyzer=trading_analyzer_callback,
                performance_tracker=performance_tracker_callback,
                geopolitical_monitor=geopolitical_monitor_callback,
                industry_analyzer=industry_analyzer_callback,
                projection_engine=projection_engine_callback
            )
            logger.info("component_ready", "Scheduler initialized successfully")
            
            # Initialize web server for wake-up pings
            logger.info("component_init", "Initializing web server...")
            self.web_server = WebServer(scheduler=self.scheduler)
            logger.info("component_ready", "Web server initialized successfully")
            
            logger.info("app_ready", "=" * 80)
            logger.info("app_ready", "All components initialized and wired successfully")
            logger.info("app_ready", "=" * 80)
            return True
            
        except ConfigurationError as e:
            logger.error("config_error", f"Configuration error: {e}", error=e)
            return False
        except Exception as e:
            logger.error("init_error", f"Initialization error: {e}", error=e)
            return False
    
    def start(self):
        """Start the application"""
        try:
            logger.info("app_start", "=" * 80)
            logger.info("app_start", "Starting Investment Scout...")
            logger.info("app_start", "=" * 80)
            
            # Start scheduler
            if self.scheduler:
                self.scheduler.start()
                logger.info("scheduler_started", "✓ Scheduler started")
            
            # Start web server in main thread (blocking)
            if self.web_server:
                logger.info("web_server_info", "")
                logger.info("web_server_info", "Starting web server...")
                logger.info("web_server_info", "")
                logger.info("web_server_info", "Web server endpoints:")
                logger.info("web_server_info", "  - GET/POST /ping: Wake-up endpoint for external cron")
                logger.info("web_server_info", "  - GET /health: Health check")
                logger.info("web_server_info", "  - GET /status: Scheduler status")
                logger.info("web_server_info", "  - POST /trigger/<task_name>: Manually trigger a task")
                logger.info("web_server_info", "")
                logger.info("web_server_info", "IMPORTANT: Configure cron-job.org to ping http://your-app-url/ping every 25 minutes")
                logger.info("web_server_info", "           This prevents free hosting platforms from sleeping")
                logger.info("web_server_info", "")
                logger.info("app_running", "=" * 80)
                logger.info("app_running", "Investment Scout is now running!")
                logger.info("app_running", "=" * 80)
                
                # Run web server (blocking)
                self.web_server.run(debug=self.config.is_development)
            
        except KeyboardInterrupt:
            logger.info("shutdown_signal", "Received keyboard interrupt")
            self.shutdown()
        except Exception as e:
            logger.error("app_start_error", f"Error starting application: {e}", error=e)
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the application gracefully"""
        logger.info("app_shutdown", "=" * 80)
        logger.info("app_shutdown", "Shutting down Investment Scout...")
        logger.info("app_shutdown", "=" * 80)
        
        # Stop market monitor
        if self.market_monitor:
            logger.info("component_shutdown", "Stopping Market Monitor...")
            self.market_monitor.stop_monitoring()
        
        # Stop scheduler
        if self.scheduler:
            logger.info("component_shutdown", "Stopping Scheduler...")
            self.scheduler.stop()
        
        # Close data manager connections
        if self.data_manager:
            logger.info("component_shutdown", "Closing Data Manager connections...")
            self.data_manager.close()
        
        # Close performance tracker connections
        if self.performance_tracker:
            logger.info("component_shutdown", "Closing Performance Tracker connections...")
            self.performance_tracker.close()
        
        logger.info("app_shutdown_complete", "=" * 80)
        logger.info("app_shutdown_complete", "Investment Scout shutdown complete")
        logger.info("app_shutdown_complete", "=" * 80)
        self.shutdown_event.set()
    
    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info("shutdown_signal", f"Received signal {signum}")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Main entry point"""
    app = InvestmentScoutApp()
    
    # Set up signal handlers
    app.setup_signal_handlers()
    
    # Initialize application
    if not app.initialize():
        logger.error("init_failed", "Failed to initialize application")
        sys.exit(1)
    
    # Start application
    app.start()


if __name__ == "__main__":
    main()
