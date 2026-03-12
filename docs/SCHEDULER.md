# Scheduler and Orchestration

## Overview

The Scheduler is the central orchestration component of the Investment Scout system. It coordinates all system components with proper timing to ensure:

1. **PRIMARY**: Daily investment newsletters at 9 AM ET with 1-5 long-term opportunities
2. **SECONDARY**: Real-time trading alerts (max 3 per day)
3. Continuous 24/7 market monitoring
4. Regular updates for all analysis components

## Architecture

### Components

The Scheduler manages the following components:

| Component | Schedule | Purpose |
|-----------|----------|---------|
| **Investment Analyzer** | 8:30 AM ET daily | Generate 1-5 long-term investment opportunities (PRIMARY) |
| **Newsletter Generator** | After Investment Analyzer | Create and send daily newsletter before 9 AM ET |
| **Market Monitor** | 24/7 continuous | Monitor global markets with 15s polling for active stocks |
| **Trading Analyzer** | Every 15 seconds | Detect real-time trading opportunities (SECONDARY) |
| **Performance Tracker** | 10:00 PM ET daily | Update portfolio performance metrics |
| **Geopolitical Monitor** | Every 6 hours | Collect and analyze geopolitical events |
| **Industry Analyzer** | 7:00 AM ET daily | Analyze sector trends and competitive dynamics |
| **Projection Engine** | Every hour | Generate forward-looking projections |

### Task Types

The Scheduler supports two types of tasks:

1. **Interval-based tasks**: Run at fixed intervals (e.g., every 15 seconds, every hour)
2. **Time-based tasks**: Run at specific times of day (e.g., 8:30 AM ET)

## Free Hosting Sleep Cycle Handling

Free hosting platforms (Heroku, Railway, Render) sleep after 30 minutes of inactivity. The Scheduler handles this with:

### External Cron Service

Configure an external cron service (e.g., cron-job.org) to ping the `/ping` endpoint every 25 minutes:

```
URL: https://your-app-url/ping
Method: GET or POST
Interval: Every 25 minutes
```

### Wake-up Behavior

When the `/ping` endpoint is called:

1. The system records the wake-up time and calculates sleep duration
2. Checks if the scheduler is running; restarts if needed
3. Identifies any overdue tasks that should run immediately
4. Returns status information including overdue tasks

## Web Server Endpoints

The system provides a Flask web server with the following endpoints:

### `/ping` (GET/POST)

Wake-up endpoint for external cron service. Keeps the system awake and restarts scheduler if needed.

**Response:**
```json
{
  "status": "awake",
  "timestamp": "2024-01-15T08:30:00.000Z",
  "sleep_duration_seconds": 1500,
  "scheduler_running": true,
  "overdue_tasks": ["Investment Analyzer"],
  "active_tasks": []
}
```

### `/health` (GET)

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "scheduler_running": true
}
```

### `/status` (GET)

Detailed scheduler status.

**Response:**
```json
{
  "scheduler_running": true,
  "last_wake_time": "2024-01-15T08:30:00.000Z",
  "tasks": [
    {
      "name": "Investment Analyzer",
      "is_running": false,
      "last_run": "2024-01-15T08:30:00.000Z",
      "type": "daily",
      "scheduled_time": "08:30",
      "timezone": "America/New_York"
    },
    {
      "name": "Trading Analyzer",
      "is_running": false,
      "last_run": "2024-01-15T08:30:15.000Z",
      "type": "interval",
      "interval_seconds": 15,
      "next_run": "2024-01-15T08:30:30.000Z"
    }
  ]
}
```

### `/trigger/<task_name>` (POST)

Manually trigger a specific task.

**Example:**
```bash
curl -X POST https://your-app-url/trigger/Investment%20Analyzer
```

**Response:**
```json
{
  "status": "triggered",
  "task": "Investment Analyzer"
}
```

## Usage

### Starting the Application

```python
from src.main import main

if __name__ == "__main__":
    main()
```

This will:
1. Load and validate configuration
2. Initialize all components
3. Start the scheduler
4. Start the web server (blocking)

### Manual Task Triggering

You can manually trigger any task via the API:

```bash
# Trigger Investment Analyzer
curl -X POST http://localhost:5000/trigger/Investment%20Analyzer

# Trigger Trading Analyzer
curl -X POST http://localhost:5000/trigger/Trading%20Analyzer
```

### Monitoring

Check scheduler status:

```bash
curl http://localhost:5000/status
```

Check health:

```bash
curl http://localhost:5000/health
```

## Configuration

The Scheduler uses the ConfigurationManager for all settings:

- `NEWSLETTER_HOUR`: Hour for newsletter delivery (default: 9)
- `NEWSLETTER_MINUTE`: Minute for newsletter delivery (default: 0)
- `MAX_TRADING_ALERTS_PER_DAY`: Maximum trading alerts per day (default: 3)
- `ENVIRONMENT`: Application environment (development/production)
- `LOG_LEVEL`: Logging level (default: INFO)

## Deployment

### Setting Up External Cron

1. Go to [cron-job.org](https://cron-job.org) (free tier)
2. Create a new cron job:
   - Title: "Investment Scout Wake-up"
   - URL: `https://your-app-url/ping`
   - Schedule: Every 25 minutes
   - Method: GET
3. Save and enable the job

### Heroku Deployment

```bash
# Deploy to Heroku
git push heroku main

# Set up external cron at cron-job.org
# URL: https://your-app.herokuapp.com/ping
```

### Railway Deployment

```bash
# Deploy to Railway
railway up

# Set up external cron at cron-job.org
# URL: https://your-app.railway.app/ping
```

### Render Deployment

```bash
# Deploy to Render via GitHub integration

# Set up external cron at cron-job.org
# URL: https://your-app.onrender.com/ping
```

## Testing

Run scheduler tests:

```bash
python3 -m pytest tests/test_scheduler.py -v
```

## Logging

The Scheduler uses structured logging with JSON format. All events are logged with:

- `timestamp`: ISO 8601 timestamp
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `component`: "src.utils.scheduler"
- `event`: Event type (e.g., "task_started", "scheduler_started", "wake_up_ping")
- `message`: Human-readable message
- Additional context fields

### Key Events

- `scheduler_initialized`: Scheduler created with task count
- `scheduler_started`: Scheduler started
- `scheduler_stopped`: Scheduler stopped
- `task_started`: Task execution started
- `task_completed`: Task execution completed with timing
- `task_error`: Task execution failed
- `wake_up_ping`: Wake-up ping received
- `overdue_tasks_detected`: Overdue tasks found after wake-up
- `task_triggered`: Manual task trigger

## Error Handling

The Scheduler implements robust error handling:

1. **Task Execution Errors**: Logged but don't crash the scheduler
2. **Scheduler Loop Errors**: Logged with 5-second backoff before retry
3. **Wake-up Failures**: Scheduler restarts automatically
4. **Concurrent Execution**: Tasks skip if already running

## Performance Considerations

### Memory Usage

The Scheduler is designed for free hosting (512 MB RAM):

- Minimal memory footprint
- Tasks run in separate threads
- No task queuing (tasks run immediately when due)

### Thread Safety

- Each task runs in its own thread
- Tasks check `is_running` flag to prevent concurrent execution
- Scheduler loop runs in a separate daemon thread

### Timing Accuracy

- Scheduler checks tasks every 1 second
- Time-based tasks use timezone-aware datetime (America/New_York)
- Interval-based tasks track last run time precisely

## Future Enhancements

Potential improvements for future versions:

1. **Task Dependencies**: Define task execution order
2. **Task Priorities**: Prioritize critical tasks
3. **Task Retry Logic**: Automatic retry for failed tasks
4. **Task History**: Store task execution history
5. **Dynamic Scheduling**: Adjust schedules based on market conditions
6. **Task Metrics**: Track task execution time and success rate
