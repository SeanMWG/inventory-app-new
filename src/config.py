"""Application configuration."""
import os
from pathlib import Path

class Config:
    """Base configuration."""
    
    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')
    DEBUG = True  # Enable debug mode by default
    
    # SQLAlchemy config
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///instance/inventory.db')
    
    # Azure AD config
    CLIENT_ID = os.environ.get('CLIENT_ID')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
    AUTHORITY = os.environ.get('AUTHORITY')
    SCOPE = os.environ.get('SCOPE', []).split(',') if os.environ.get('SCOPE') else []
    
    @staticmethod
    def init_app(app):
        """Initialize application."""
        os.makedirs(app.instance_path, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///instance/dev.db')

class TestingConfig(Config):
    """Testing configuration."""
    
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    
    # Test Azure AD config
    CLIENT_ID = 'test-client-id'
    CLIENT_SECRET = 'test-client-secret'
    AUTHORITY = 'https://login.microsoftonline.com/test-tenant-id'
    SCOPE = ['test-scope']
    
    @staticmethod
    def init_app(app):
        """Initialize application for testing."""
        Config.init_app(app)
        # Ensure test database directory exists
        os.makedirs('instance', exist_ok=True)

class ProductionConfig(Config):
    """Production configuration."""
    
    DEBUG = True  # Temporarily enable debug for troubleshooting
    
    @staticmethod
    def init_app(app):
        """Initialize application for production."""
        Config.init_app(app)
        
        # Log configuration
        app.logger.info('Production config loaded')
        app.logger.info(f'Debug mode: {app.debug}')
        app.logger.info(f'Database URL: {app.config["SQLALCHEMY_DATABASE_URI"]}')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Get configuration class."""
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'default')
    return config.get(config_name, config['default'])
