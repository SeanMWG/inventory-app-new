#!/usr/bin/env python3
"""Run the application in production mode with gunicorn."""
import os
import sys
import multiprocessing
import gunicorn.app.base
from src.app import create_app

class StandaloneApplication(gunicorn.app.base.BaseApplication):
    """Gunicorn application for production deployment."""
    
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()
    
    def load_config(self):
        """Load gunicorn configuration."""
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)
    
    def load(self):
        """Load WSGI application."""
        return self.application

def get_workers():
    """Calculate number of workers based on CPU cores."""
    cores = multiprocessing.cpu_count()
    # Use workers = 2-4 x $(NUM_CORES)
    # We'll use 3x as a middle ground
    return cores * 3

def main():
    """Main production server function."""
    try:
        # Create app with production config
        app = create_app('production')
        
        # Ensure required environment variables are set
        required_vars = [
            'SECRET_KEY',
            'DATABASE_URL',
            'CLIENT_ID',
            'CLIENT_SECRET',
            'TENANT_ID'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print(f"Missing required environment variables: {', '.join(missing_vars)}", 
                  file=sys.stderr)
            return 1
        
        # Gunicorn configuration
        options = {
            'bind': '0.0.0.0:8000',
            'workers': get_workers(),
            'worker_class': 'sync',
            'threads': 4,
            'timeout': 120,
            'keepalive': 5,
            'max_requests': 1000,
            'max_requests_jitter': 50,
            'accesslog': 'logs/access.log',
            'errorlog': 'logs/error.log',
            'loglevel': 'info',
            'capture_output': True,
            'enable_stdio_inheritance': True,
            'preload_app': True,
            'worker_tmp_dir': '/dev/shm'  # Use RAM for temp files
        }
        
        # Ensure log directory exists
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Start gunicorn
        StandaloneApplication(app, options).run()
        
        return 0
        
    except Exception as e:
        print(f"Error starting production server: {str(e)}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
