"""Web server for handling wake-up pings and health checks"""

from flask import Flask, jsonify
import logging
import os
from typing import Optional

from src.utils.scheduler import Scheduler
from src.utils.logger import get_logger


logger = get_logger(__name__)


class WebServer:
    """
    Simple web server for handling external cron pings and health checks.
    
    This server provides endpoints for:
    - /ping: Wake-up endpoint for external cron service (cron-job.org)
    - /health: Health check endpoint
    - /status: Scheduler status endpoint
    """
    
    def __init__(self, scheduler: Optional[Scheduler] = None, port: int = None):
        """
        Initialize web server.
        
        Args:
            scheduler: Scheduler instance to manage
            port: Port to run server on (default: from PORT env var or 8000)
        """
        self.app = Flask(__name__)
        self.scheduler = scheduler
        # Use PORT from environment (for Heroku/Render) or default to 8000
        self.port = port or int(os.environ.get('PORT', 8000))
        
        # Disable Flask's default logging to avoid duplicate logs
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.WARNING)
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up Flask routes"""
        
        @self.app.route('/ping', methods=['GET', 'POST'])
        def ping():
            """
            Wake-up endpoint for external cron service.
            
            This endpoint should be pinged by cron-job.org every 25 minutes
            to keep the free hosting platform awake.
            
            Returns:
                JSON response with wake-up status
            """
            if self.scheduler:
                status = self.scheduler.handle_wake_up()
                return jsonify(status), 200
            else:
                return jsonify({
                    "status": "awake",
                    "message": "No scheduler configured"
                }), 200
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """
            Health check endpoint.
            
            Returns:
                JSON response with health status
            """
            health_status = {
                "status": "healthy",
                "scheduler_running": self.scheduler.is_running if self.scheduler else False
            }
            return jsonify(health_status), 200
        
        @self.app.route('/status', methods=['GET'])
        def status():
            """
            Scheduler status endpoint.
            
            Returns:
                JSON response with detailed scheduler status
            """
            if self.scheduler:
                status_info = self.scheduler.get_status()
                return jsonify(status_info), 200
            else:
                return jsonify({
                    "error": "No scheduler configured"
                }), 503
        
        @self.app.route('/trigger/<task_name>', methods=['POST'])
        def trigger_task(task_name: str):
            """
            Manually trigger a specific task.
            
            Args:
                task_name: Name of the task to trigger
                
            Returns:
                JSON response with trigger status
            """
            if not self.scheduler:
                return jsonify({
                    "error": "No scheduler configured"
                }), 503
            
            success = self.scheduler.trigger_task(task_name)
            if success:
                return jsonify({
                    "status": "triggered",
                    "task": task_name
                }), 200
            else:
                return jsonify({
                    "error": f"Failed to trigger task: {task_name}",
                    "message": "Task not found or already running"
                }), 400
    
    def run(self, debug: bool = False):
        """
        Run the web server.
        
        Args:
            debug: Enable debug mode (default: False)
        """
        logger.info("web_server_start", f"Starting web server on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=debug)


if __name__ == "__main__":
    """
    Standalone web server entry point.
    
    This is used by the Procfile 'web' process to run just the web server
    without the full application (scheduler, market monitor, etc.).
    
    Useful for:
    - Health checks
    - Wake-up pings from external cron
    - Monitoring endpoints
    """
    import os
    from src.utils.logger import setup_logging
    
    # Set up logging
    setup_logging()
    
    # Create standalone web server (no scheduler)
    server = WebServer(scheduler=None)
    
    # Run in production mode
    debug = os.environ.get('ENVIRONMENT', 'production') == 'development'
    server.run(debug=debug)
