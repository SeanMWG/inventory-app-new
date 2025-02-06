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
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    
    # Test Azure AD settings
    CLIENT_ID = os.environ.get('CLIENT_ID', 'test-client-id')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET', 'test-client-secret')
    AUTHORITY = os.environ.get('AUTHORITY', 'https://login.microsoftonline.com/test-tenant-id')
    SCOPE = os.environ.get('SCOPE', 'test-scope')

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Ensure these are set
    @classmethod
    def init_app(cls, app):
        """Initialize production application."""
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'dev-key-please-change':
            raise ValueError('Production SECRET_KEY must be set')
        if not cls.SQLALCHEMY_DATABASE_URI:
            raise ValueError('Production DATABASE_URL must be set')
        if not all([cls.CLIENT_ID, cls.CLIENT_SECRET, cls.AUTHORITY]):
            raise ValueError('Azure AD credentials must be set')

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
