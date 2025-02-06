"""Database utilities."""
from flask import current_app
from sqlalchemy import text
from ..models import db

def init_db(app):
    """Initialize database."""
    # Don't initialize SQLAlchemy again if it's already initialized
    if not hasattr(app, 'extensions') or 'sqlalchemy' not in app.extensions:
        db.init_app(app)

def init_app(app):
    """Initialize database utilities."""
    init_db(app)

def health_check():
    """Check database connection."""
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        return {'status': 'healthy', 'database': 'connected'}
    except Exception as e:
        current_app.logger.error(f'Database health check failed: {str(e)}')
        return {'status': 'unhealthy', 'database': 'disconnected'}, 500
