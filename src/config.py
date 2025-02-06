"""Application configuration."""
import os
from datetime import timedelta

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URI')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

class ProductionConfig(Config):
    """Production configuration."""
    ENV = 'production'
    DEBUG = False

class DevelopmentConfig(Config):
    """Development configuration."""
    ENV = 'development'
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration."""
    ENV = 'testing'
    TESTING = True
    DEBUG = True
    # Use SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

def get_config(config_name=None):
    """Get configuration class based on environment."""
    config_map = {
        'production': ProductionConfig,
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'default': DevelopmentConfig
    }
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config_map.get(config_name, config_map['default'])
