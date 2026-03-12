"""Unit tests for Scheduler"""

import pytest
import time
from datetime import datetime, time as dt_time
from unittest.mock import Mock, patch
import pytz

from src.utils.scheduler import Scheduler, ScheduledTask
from src.utils.configuration_manager import ConfigurationManager


class TestScheduledTask:
    """Tests for ScheduledTask class"""
    
    def test_interval_based_task_should_run_first_time(self):
        """Test that interval-based task should run on first check"""
        task = ScheduledTask(
            name="Test Task",
            func=lambda: None,
            interval_seconds=60
        )
        
        assert task.should_run() is True
    
    def test_interval_based_task_should_not_run_before_interval(self):
        """Test that interval-based task should not run before interval elapses"""
        task = ScheduledTask(
            name="Test Task",
            func=lambda: None,
            interval_seconds=60
        )
        
        # Simulate last run
        task.last_run = datetime.now(pytz.timezone("America/New_York"))
        
        # Should not run immediately after
        assert task.should_run() is False
    
    def test_interval_based_task_should_run_after_interval(self):
        """Test that interval-based task should run after interval elapses"""
        task = ScheduledTask(
            name="Test Task",
            func=lambda: None,
            interval_seconds=1  # 1 second for testing
        )
        
        # Simulate last run
        task.last_run = datetime.now(pytz.timezone("America/New_York"))
        
        # Wait for interval to elapse
        time.sleep(1.1)
        
        # Should run now
        assert task.should_run() is True
    
    def test_time_based_task_should_run_first_time_if_past_scheduled_time(self):
        """Test that time-based task should run first time if past scheduled time"""
        # Set scheduled time to 1 hour ago
        now = datetime.now(pytz.timezone("America/New_York"))
        scheduled_time = dt_time(hour=(now.hour - 1) % 24, minute=0)
        
        task = ScheduledTask(
            name="Test Task",
            func=lambda: None,
            scheduled_time=scheduled_time,
            timezone="America/New_York"
        )
        
        assert task.should_run() is True
    
    def test_time_based_task_should_not_run_if_before_scheduled_time(self):
        """Test that time-based task should not run if before scheduled time"""
        # Set scheduled time to 1 hour from now
        now = datetime.now(pytz.timezone("America/New_York"))
        scheduled_time = dt_time(hour=(now.hour + 1) % 24, minute=0)
        
        task = ScheduledTask(
            name="Test Task",
            func=lambda: None,
            scheduled_time=scheduled_time,
            timezone="America/New_York"
        )
        
        assert task.should_run() is False
    
    def test_task_execution_updates_last_run(self):
        """Test that task execution updates last_run timestamp"""
        executed = []
        
        def test_func():
            executed.append(True)
        
        task = ScheduledTask(
            name="Test Task",
            func=test_func,
            interval_seconds=60
        )
        
        assert task.last_run is None
        
        task.run()
        
        assert task.last_run is not None
        assert len(executed) == 1
    
    def test_task_execution_sets_is_running_flag(self):
        """Test that task execution sets is_running flag"""
        def slow_func():
            time.sleep(0.1)
        
        task = ScheduledTask(
            name="Test Task",
            func=slow_func,
            interval_seconds=60
        )
        
        assert task.is_running is False
        
        # Run in thread to check flag during execution
        import threading
        thread = threading.Thread(target=task.run)
        thread.start()
        
        # Wait a bit for task to start
        time.sleep(0.05)
        
        # Should be running now
        assert task.is_running is True
        
        # Wait for completion
        thread.join()
        
        # Should be done now
        assert task.is_running is False
    
    def test_task_skips_if_already_running(self):
        """Test that task skips execution if already running"""
        execution_count = []
        
        def slow_func():
            execution_count.append(1)
            time.sleep(0.2)
        
        task = ScheduledTask(
            name="Test Task",
            func=slow_func,
            interval_seconds=60
        )
        
        # Start first execution
        import threading
        thread1 = threading.Thread(target=task.run)
        thread1.start()
        
        # Wait a bit for first execution to start
        time.sleep(0.05)
        
        # Try to run again while first is still running
        task.run()
        
        # Wait for first execution to complete
        thread1.join()
        
        # Should have only executed once
        assert len(execution_count) == 1


class TestScheduler:
    """Tests for Scheduler class"""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration"""
        config = Mock(spec=ConfigurationManager)
        config.newsletter_time = dt_time(hour=9, minute=0)
        config.max_trading_alerts_per_day = 3
        return config
    
    def test_scheduler_initialization(self, mock_config):
        """Test scheduler initialization"""
        scheduler = Scheduler(config=mock_config)
        
        assert scheduler.config == mock_config
        assert scheduler.is_running is False
        assert len(scheduler.tasks) == 0  # No callbacks provided
    
    def test_scheduler_initialization_with_callbacks(self, mock_config):
        """Test scheduler initialization with component callbacks"""
        investment_analyzer = Mock()
        newsletter_generator = Mock()
        trading_analyzer = Mock()
        
        scheduler = Scheduler(
            config=mock_config,
            investment_analyzer=investment_analyzer,
            newsletter_generator=newsletter_generator,
            trading_analyzer=trading_analyzer
        )
        
        # Should have created tasks for provided callbacks
        assert len(scheduler.tasks) > 0
        
        # Check that tasks were created
        task_names = [task.name for task in scheduler.tasks]
        assert "Investment Analyzer" in task_names
        assert "Trading Analyzer" in task_names
    
    def test_scheduler_start_sets_running_flag(self, mock_config):
        """Test that scheduler start sets is_running flag"""
        scheduler = Scheduler(config=mock_config)
        
        assert scheduler.is_running is False
        
        scheduler.start()
        
        assert scheduler.is_running is True
        
        # Clean up
        scheduler.stop()
    
    def test_scheduler_stop_clears_running_flag(self, mock_config):
        """Test that scheduler stop clears is_running flag"""
        scheduler = Scheduler(config=mock_config)
        
        scheduler.start()
        assert scheduler.is_running is True
        
        scheduler.stop()
        assert scheduler.is_running is False
    
    def test_scheduler_handle_wake_up(self, mock_config):
        """Test wake-up handling"""
        scheduler = Scheduler(config=mock_config)
        
        # Record initial wake time
        initial_wake_time = scheduler.last_wake_time
        
        # Wait a bit
        time.sleep(0.1)
        
        # Handle wake-up
        status = scheduler.handle_wake_up()
        
        # Check status
        assert status["status"] == "awake"
        assert "timestamp" in status
        assert "sleep_duration_seconds" in status
        assert status["sleep_duration_seconds"] > 0
        assert scheduler.last_wake_time > initial_wake_time
    
    def test_scheduler_get_status(self, mock_config):
        """Test get_status method"""
        investment_analyzer = Mock()
        
        scheduler = Scheduler(
            config=mock_config,
            investment_analyzer=investment_analyzer
        )
        
        status = scheduler.get_status()
        
        assert "scheduler_running" in status
        assert "last_wake_time" in status
        assert "tasks" in status
        assert isinstance(status["tasks"], list)
    
    def test_scheduler_trigger_task(self, mock_config):
        """Test manual task triggering"""
        executed = []
        
        def test_func():
            executed.append(True)
        
        scheduler = Scheduler(config=mock_config)
        
        # Add a test task
        scheduler.tasks.append(ScheduledTask(
            name="Test Task",
            func=test_func,
            interval_seconds=60
        ))
        
        # Trigger the task
        success = scheduler.trigger_task("Test Task")
        
        assert success is True
        
        # Wait for execution
        time.sleep(0.1)
        
        assert len(executed) == 1
    
    def test_scheduler_trigger_nonexistent_task(self, mock_config):
        """Test triggering a nonexistent task"""
        scheduler = Scheduler(config=mock_config)
        
        success = scheduler.trigger_task("Nonexistent Task")
        
        assert success is False
    
    def test_scheduler_creates_investment_analyzer_task_at_8_30_am(self, mock_config):
        """Test that Investment Analyzer is scheduled at 8:30 AM ET"""
        investment_analyzer = Mock()
        
        scheduler = Scheduler(
            config=mock_config,
            investment_analyzer=investment_analyzer
        )
        
        # Find Investment Analyzer task
        ia_task = None
        for task in scheduler.tasks:
            if task.name == "Investment Analyzer":
                ia_task = task
                break
        
        assert ia_task is not None
        assert ia_task.scheduled_time == dt_time(hour=8, minute=30)
        assert str(ia_task.timezone) == "America/New_York"
    
    def test_scheduler_creates_trading_analyzer_task_with_15s_interval(self, mock_config):
        """Test that Trading Analyzer is scheduled with 15s interval"""
        trading_analyzer = Mock()
        
        scheduler = Scheduler(
            config=mock_config,
            trading_analyzer=trading_analyzer
        )
        
        # Find Trading Analyzer task
        ta_task = None
        for task in scheduler.tasks:
            if task.name == "Trading Analyzer":
                ta_task = task
                break
        
        assert ta_task is not None
        assert ta_task.interval_seconds == 15
    
    def test_scheduler_creates_geopolitical_monitor_task_with_6h_interval(self, mock_config):
        """Test that Geopolitical Monitor is scheduled with 6 hour interval"""
        geopolitical_monitor = Mock()
        
        scheduler = Scheduler(
            config=mock_config,
            geopolitical_monitor=geopolitical_monitor
        )
        
        # Find Geopolitical Monitor task
        gm_task = None
        for task in scheduler.tasks:
            if task.name == "Geopolitical Monitor":
                gm_task = task
                break
        
        assert gm_task is not None
        assert gm_task.interval_seconds == 6 * 3600  # 6 hours
    
    def test_scheduler_creates_projection_engine_task_with_hourly_interval(self, mock_config):
        """Test that Projection Engine is scheduled with hourly interval"""
        projection_engine = Mock()
        
        scheduler = Scheduler(
            config=mock_config,
            projection_engine=projection_engine
        )
        
        # Find Projection Engine task
        pe_task = None
        for task in scheduler.tasks:
            if task.name == "Projection Engine":
                pe_task = task
                break
        
        assert pe_task is not None
        assert pe_task.interval_seconds == 3600  # 1 hour
    
    def test_scheduler_wake_up_restarts_if_not_running(self, mock_config):
        """Test that wake-up restarts scheduler if not running"""
        scheduler = Scheduler(config=mock_config)
        
        # Ensure scheduler is not running
        scheduler.is_running = False
        
        # Handle wake-up
        status = scheduler.handle_wake_up()
        
        # Should have restarted
        assert scheduler.is_running is True
        
        # Clean up
        scheduler.stop()
    
    def test_scheduler_detects_overdue_tasks_on_wake_up(self, mock_config):
        """Test that wake-up detects overdue tasks"""
        executed = []
        
        def test_func():
            executed.append(True)
        
        scheduler = Scheduler(config=mock_config)
        
        # Add a task that should run immediately
        task = ScheduledTask(
            name="Overdue Task",
            func=test_func,
            interval_seconds=1
        )
        # Set last run to past so it's overdue
        task.last_run = datetime.now(pytz.timezone("America/New_York"))
        time.sleep(1.1)
        
        scheduler.tasks.append(task)
        
        # Handle wake-up (scheduler is not running, so it will detect overdue before starting)
        status = scheduler.handle_wake_up()
        
        # Should detect overdue task
        assert "Overdue Task" in status["overdue_tasks"]
        
        # Stop scheduler to clean up
        scheduler.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
