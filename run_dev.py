#!/usr/bin/env python3
"""Run the application in development mode."""
import os
import sys
import logging
from src.app import create_app

def setup_logging():
    """Setup development logging configuration."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/development.log')
        ]
    )

def main():
    """Main development server function."""
    try:
        # Ensure logs directory exists
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Setup logging
        setup_logging()
        
        # Create app with development config
        app = create_app('development')
        
        # Development-specific configuration
        app.config.update(
            DEBUG=True,
            TEMPLATES_AUTO_RELOAD=True,
            SEND_FILE_MAX_AGE_DEFAULT=0,  # Disable caching for static files
            SQLALCHEMY_ECHO=True  # Log SQL queries
        )
        
        # Run development server
        app.run(
            host='0.0.0.0',  # Allow external access
            port=5000,
            use_reloader=True,  # Auto-reload on file changes
            use_debugger=True,  # Enable debugger
            threaded=True
        )
        
        return 0
        
    except Exception as e:
        print(f"Error starting development server: {str(e)}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
