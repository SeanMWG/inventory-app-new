import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class Config:
    """Base configuration."""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Azure AD
    AZURE_CLIENT_ID = os.getenv('CLIENT_ID')
    AZURE_CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    AZURE_TENANT_ID = os.getenv('TENANT_ID')
    AZURE_AUTHORITY = f'https://login.microsoftonline.com/{AZURE_TENANT_ID}'
    AZURE_REDIRECT_PATH = '/getAToken'
    AZURE_SCOPE = ['User.Read']
    
    # Application Insights
    APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
    
    # Session
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    DEVELOPMENT = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    DEVELOPMENT = False
    
    # Override these in production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    def __init__(self):
        super().__init__()
        if not self.SECRET_KEY or self.SECRET_KEY == 'dev':
            raise ValueError("Production SECRET_KEY must be set")
        if not self.SQLALCHEMY_DATABASE_URI:
            raise ValueError("Production DATABASE_URL must be set")

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    
    # Set default configuration
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Helper function to get configuration class."""
    if not config_name:
        config_name = os.getenv('FLASK_CONFIG', 'default')
    return config[config_name]
