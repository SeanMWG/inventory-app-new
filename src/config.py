"""Application configuration."""
import os
from datetime import timedelta

class Config:
    """Base configuration."""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    
    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Azure AD
    CLIENT_ID = os.environ.get('CLIENT_ID')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
    AUTHORITY = os.environ.get('AUTHORITY')
    SCOPE = os.environ.get('SCOPE', 'User.Read')
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    @classmethod
    def init_app(cls, app):
        """Initialize application."""
        pass

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance', 'dev.db')
    SESSION_COOKIE_SECURE = False

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    # Use in-memory SQLite by default, but allow override from environment
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:')
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    SERVER_NAME = 'localhost'
    
    # Test Azure AD settings
    CLIENT_ID = 'test-client-id'
    CLIENT_SECRET = 'test-client-secret'
    AUTHORITY = 'https://login.microsoftonline.com/test-tenant-id'
    SCOPE = 'test-scope'

    @classmethod
    def init_app(cls, app):
        """Initialize test application."""
        Config.init_app(app)
        # Disable MSAL validation in testing
        app.config['TESTING'] = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    @classmethod
    def init_app(cls, app):
        """Initialize production application."""
        Config.init_app(app)
        
        # Ensure required settings are present
        required_settings = [
            ('SECRET_KEY', 'Production SECRET_KEY must be set'),
            ('SQLALCHEMY_DATABASE_URI', 'Production DATABASE_URL must be set'),
            ('CLIENT_ID', 'Azure AD CLIENT_ID must be set'),
            ('CLIENT_SECRET', 'Azure AD CLIENT_SECRET must be set'),
            ('AUTHORITY', 'Azure AD AUTHORITY must be set')
        ]
        
        for setting, message in required_settings:
            if not app.config.get(setting):
                raise ValueError(message)

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
    return config[config_name]
