"""Scheduler and orchestration for Investment Scout system"""

import asyncio
import logging
import threading
import time
from datetime import datetime, time as dt_time, timedelta
from typing import Callable, Dict, List, Optional
import pytz

from src.utils.logger import get_logger
from src.utils.configuration_manager import ConfigurationManager


logger = get_logger(__name__)


class ScheduledTask:
    """Represents a scheduled task with timing and execution details"""
    
    def __init__(
        self,
        name: str,
        func: Callable,
        interval_seconds: Optional[int] = None,
        scheduled_time: Optional[dt_time] = None,
        timezone: str = "America/New_York"
    ):
        """
        Initialize a scheduled task.
        
        Args:
            name: Task name for logging
            func: Function to execute
            interval_seconds: Interval in seconds for periodic tasks (None for time-based)
            scheduled_time: Specific time of day for daily tasks (None for interval-based)
            timezone: Timezone for scheduled_time (default: America/New_York)
        """
        self.name = name
        self.func = func
        self.interval_seconds = interval_seconds
        self.scheduled_time = scheduled_time
        self.timezone = pytz.timezone(timezone)
        self.last_run: Optional[datetime] = None
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
    
    def should_run(self) -> bool:
        """
        Check if task should run now.
        
        Returns:
            bool: True if task should run
        """
        now = datetime.now(self.timezone)
        
        # For interval-based tasks
        if self.interval_seconds is not None:
            if self.last_run is None:
                return True
            elapsed = (now - self.last_run).total_seconds()
            return elapsed >= self.interval_seconds
        
        # For time-based tasks (daily)
        if self.scheduled_time is not None:
            if self.last_run is None:
                # Check if we're past the scheduled time today
                scheduled_datetime = now.replace(
                    hour=self.scheduled_time.hour,
                    minute=self.scheduled_time.minute,
                    second=0,
                    microsecond=0
                )
                return now >= scheduled_datetime
            
            # Check if it's a new day and past the scheduled time
            last_run_date = self.last_run.date()
            current_date = now.date()
            
            if current_date > last_run_date:
                scheduled_datetime = now.replace(
                    hour=self.scheduled_time.hour,
                    minute=self.scheduled_time.minute,
                    second=0,
                    microsecond=0
                )
                return now >= scheduled_datetime
        
        return False
    
    def run(self):
        """Execute the task"""
        if self.is_running:
            logger.warning("task_already_running", f"Task {self.name} is already running, skipping", 
                          task_name=self.name)
            return
        
        try:
            self.is_running = True
            logger.info("task_started", f"Starting task: {self.name}", task_name=self.name)
            start_time = time.time()
            
            self.func()
            
            elapsed = time.time() - start_time
            self.last_run = datetime.now(self.timezone)
            logger.info("task_completed", f"Completed task: {self.name} in {elapsed:.2f}s", 
                       task_name=self.name, elapsed_seconds=elapsed)
            
        except Exception as e:
            logger.error("task_error", f"Error executing task {self.name}: {e}", 
                        error=e, task_name=self.name)
        finally:
            self.is_running = False


class Scheduler:
    """
    Orchestrates all Investment Scout components with proper timing.
    
    Schedules:
    - Investment Analyzer: 8:30 AM ET daily
    - Newsletter Generator: Before 9:00 AM ET (triggered after Investment Analyzer)
    - Market Monitor: Continuous 24/7 operation
    - Trading Analyzer: Real-time monitoring (15s intervals)
    - Performance Tracker: Daily updates
    - Geopolitical Monitor: Every 6 hours
    - Industry Analyzer: Daily updates
    - Projection Engine: Hourly updates
    
    Handles free hosting sleep cycles with external cron pings every 25 minutes.
    """
    
    def __init__(
        self,
        config: ConfigurationManager,
        investment_analyzer: Optional[Callable] = None,
        newsletter_generator: Optional[Callable] = None,
        market_monitor: Optional[Callable] = None,
        trading_analyzer: Optional[Callable] = None,
        performance_tracker: Optional[Callable] = None,
        geopolitical_monitor: Optional[Callable] = None,
        industry_analyzer: Optional[Callable] = None,
        projection_engine: Optional[Callable] = None
    ):
        """
        Initialize scheduler with component callbacks.
        
        Args:
            config: Configuration manager
            investment_analyzer: Investment analyzer callback
            newsletter_generator: Newsletter generator callback
            market_monitor: Market monitor callback
            trading_analyzer: Trading analyzer callback
            performance_tracker: Performance tracker callback
            geopolitical_monitor: Geopolitical monitor callback
            industry_analyzer: Industry analyzer callback
            projection_engine: Projection engine callback
        """
        self.config = config
        self.tasks: List[ScheduledTask] = []
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.last_wake_time = datetime.now()
        
        # Store component callbacks
        self.investment_analyzer = investment_analyzer
        self.newsletter_generator = newsletter_generator
        self.market_monitor = market_monitor
        self.trading_analyzer = trading_analyzer
        self.performance_tracker = performance_tracker
        self.geopolitical_monitor = geopolitical_monitor
        self.industry_analyzer = industry_analyzer
        self.projection_engine = projection_engine
        
        self._setup_tasks()
    
    def _setup_tasks(self):
        """Set up all scheduled tasks"""
        
        # Investment Analyzer - 8:30 AM ET daily (PRIMARY function)
        if self.investment_analyzer:
            self.tasks.append(ScheduledTask(
                name="Investment Analyzer",
                func=self.investment_analyzer,
                scheduled_time=dt_time(hour=8, minute=30),
                timezone="America/New_York"
            ))
        
        # Newsletter Generator - triggered after Investment Analyzer completes
        # This is handled in the Investment Analyzer callback, not as a separate task
        
        # Market Monitor - continuous 24/7 operation (runs in its own thread)
        # This is started separately and runs continuously
        
        # Trading Analyzer - real-time monitoring every 15 seconds
        if self.trading_analyzer:
            self.tasks.append(ScheduledTask(
                name="Trading Analyzer",
                func=self.trading_analyzer,
                interval_seconds=15
            ))
        
        # Performance Tracker - daily updates at 10:00 PM ET
        if self.performance_tracker:
            self.tasks.append(ScheduledTask(
                name="Performance Tracker",
                func=self.performance_tracker,
                scheduled_time=dt_time(hour=22, minute=0),
                timezone="America/New_York"
            ))
        
        # Geopolitical Monitor - every 6 hours
        if self.geopolitical_monitor:
            self.tasks.append(ScheduledTask(
                name="Geopolitical Monitor",
                func=self.geopolitical_monitor,
                interval_seconds=6 * 3600  # 6 hours
            ))
        
        # Industry Analyzer - daily at 7:00 AM ET (before Investment Analyzer)
        if self.industry_analyzer:
            self.tasks.append(ScheduledTask(
                name="Industry Analyzer",
                func=self.industry_analyzer,
                scheduled_time=dt_time(hour=7, minute=0),
                timezone="America/New_York"
            ))
        
        # Projection Engine - hourly updates
        if self.projection_engine:
            self.tasks.append(ScheduledTask(
                name="Projection Engine",
                func=self.projection_engine,
                interval_seconds=3600  # 1 hour
            ))
        
        logger.info("scheduler_initialized", f"Scheduler initialized with {len(self.tasks)} tasks", 
                   task_count=len(self.tasks))
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("scheduler_already_running", "Scheduler is already running")
            return
        
        self.is_running = True
        logger.info("scheduler_started", "Starting Investment Scout Scheduler")
        
        # Start Market Monitor in its own thread (24/7 continuous operation)
        if self.market_monitor:
            market_monitor_thread = threading.Thread(
                target=self.market_monitor,
                name="MarketMonitor",
                daemon=True
            )
            market_monitor_thread.start()
            logger.info("market_monitor_started", "Market Monitor started (24/7 continuous operation)")
        
        # Start scheduler loop in a separate thread
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="Scheduler",
            daemon=True
        )
        self.scheduler_thread.start()
        logger.info("scheduler_loop_started", "Scheduler loop started")
    
    def stop(self):
        """Stop the scheduler"""
        logger.info("scheduler_stopping", "Stopping Investment Scout Scheduler")
        self.is_running = False
        
        # Wait for scheduler thread to finish
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info("scheduler_stopped", "Scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop that checks and runs tasks"""
        logger.info("scheduler_loop_running", "Scheduler loop running")
        
        while self.is_running:
            try:
                # Check each task to see if it should run
                for task in self.tasks:
                    if task.should_run() and not task.is_running:
                        # Run task in a separate thread to avoid blocking
                        task_thread = threading.Thread(
                            target=task.run,
                            name=f"Task-{task.name}",
                            daemon=True
                        )
                        task_thread.start()
                
                # Sleep for 1 second before next check
                time.sleep(1)
                
            except Exception as e:
                logger.error("scheduler_loop_error", f"Error in scheduler loop: {e}", error=e)
                time.sleep(5)  # Wait a bit longer on error
    
    def handle_wake_up(self):
        """
        Handle wake-up from free hosting sleep cycle.
        
        This method should be called by an external cron service (cron-job.org)
        that pings every 25 minutes to keep the system awake.
        
        Returns:
            dict: Status information
        """
        now = datetime.now()
        sleep_duration = (now - self.last_wake_time).total_seconds()
        self.last_wake_time = now
        
        logger.info("wake_up_ping", f"Wake-up ping received (slept for {sleep_duration:.0f}s)", 
                   sleep_duration_seconds=sleep_duration)
        
        # Check if any tasks are overdue BEFORE restarting scheduler
        overdue_tasks = []
        for task in self.tasks:
            if task.should_run() and not task.is_running:
                overdue_tasks.append(task.name)
        
        if overdue_tasks:
            logger.info("overdue_tasks_detected", f"Overdue tasks detected: {', '.join(overdue_tasks)}", 
                       overdue_tasks=overdue_tasks)
        
        # Check if scheduler is running, restart if needed
        if not self.is_running:
            logger.warning("scheduler_not_running", "Scheduler was not running, restarting")
            self.start()
        
        return {
            "status": "awake",
            "timestamp": now.isoformat(),
            "sleep_duration_seconds": sleep_duration,
            "scheduler_running": self.is_running,
            "overdue_tasks": overdue_tasks,
            "active_tasks": [task.name for task in self.tasks if task.is_running]
        }
    
    def get_status(self) -> Dict:
        """
        Get current scheduler status.
        
        Returns:
            dict: Status information including task states
        """
        task_status = []
        for task in self.tasks:
            task_info = {
                "name": task.name,
                "is_running": task.is_running,
                "last_run": task.last_run.isoformat() if task.last_run else None,
            }
            
            if task.interval_seconds:
                task_info["type"] = "interval"
                task_info["interval_seconds"] = task.interval_seconds
                if task.last_run:
                    next_run = task.last_run + timedelta(seconds=task.interval_seconds)
                    task_info["next_run"] = next_run.isoformat()
            elif task.scheduled_time:
                task_info["type"] = "daily"
                task_info["scheduled_time"] = task.scheduled_time.strftime("%H:%M")
                task_info["timezone"] = str(task.timezone)
            
            task_status.append(task_info)
        
        return {
            "scheduler_running": self.is_running,
            "last_wake_time": self.last_wake_time.isoformat(),
            "tasks": task_status
        }
    
    def trigger_task(self, task_name: str) -> bool:
        """
        Manually trigger a specific task.
        
        Args:
            task_name: Name of the task to trigger
            
        Returns:
            bool: True if task was triggered, False if not found or already running
        """
        for task in self.tasks:
            if task.name == task_name:
                if task.is_running:
                    logger.warning("task_already_running", f"Task {task_name} is already running", 
                                 task_name=task_name)
                    return False
                
                # Run task in a separate thread
                task_thread = threading.Thread(
                    target=task.run,
                    name=f"Manual-{task.name}",
                    daemon=True
                )
                task_thread.start()
                logger.info("task_triggered", f"Manually triggered task: {task_name}", 
                           task_name=task_name)
                return True
        
        logger.warning("task_not_found", f"Task not found: {task_name}", task_name=task_name)
        return False
