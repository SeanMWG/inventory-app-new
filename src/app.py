"""Flask application factory."""
from flask import Flask, g, request, current_app, jsonify, send_from_directory
from flask_migrate import Migrate
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import os
from sqlalchemy import text

from src.models import db
from src.utils import auth as auth_utils
from src.routes import auth, inventory, location, stats

def create_app(config_name=None):
    """Application factory function."""
    app = Flask(__name__, static_folder='../static')
    
    # Load configuration
    from src.config import get_config
    config_obj = get_config(config_name)
    app.config.from_object(config_obj)
    
    # Initialize configuration
    config_obj.init_app(app)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)
    
    # Initialize auth utilities
    auth_utils.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(inventory.bp)
    app.register_blueprint(location.bp)
    app.register_blueprint(stats.bp)
    
    # Setup logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.makedirs('logs')
        file_handler = RotatingFileHandler(
            'logs/inventory.log',
            maxBytes=10240,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Inventory App startup')
    
    # Request handlers
    @app.before_request
    def before_request():
        g.request_start_time = datetime.utcnow()
        
        # Skip auth for static files, health check, and auth endpoints
        if request.path.startswith('/static/') or request.endpoint in ['static_files', 'health', 'index', 'auth.login', 'auth.authorized', 'auth.status']:
            return
            
        # Skip token refresh for testing
        if not app.testing:
            auth_utils.refresh_token_if_needed()
    
    @app.after_request
    def after_request(response):
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self' https:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: https:; font-src 'self' data: https:;"
        
        # Add timing header in development
        if app.debug:
            duration = datetime.utcnow() - g.request_start_time
            response.headers['X-Request-Duration'] = str(duration.total_seconds())
        
        return response
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f'Page not found: {request.url}')
        return jsonify({'error': 'Not Found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Server Error: {error}')
        return jsonify({'error': 'Internal Server Error'}), 500
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        return jsonify({'error': 'Unauthorized'}), 401
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return jsonify({'error': 'Forbidden'}), 403
    
    # Health check endpoint
    @app.route('/health')
    def health():
        try:
            # Test database connection
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            return jsonify({'status': 'healthy', 'database': 'connected'})
        except Exception as e:
            app.logger.error(f'Health check failed: {str(e)}')
            return jsonify({'status': 'unhealthy', 'database': 'disconnected'}), 500
    
    # Index route
    @app.route('/')
    def index():
        try:
            return send_from_directory(app.static_folder, 'index.html')
        except Exception:
            return jsonify({'error': 'Not Found'}), 404
    
    # Static files
    @app.route('/<path:filename>')
    def static_files(filename):
        try:
            return send_from_directory(app.static_folder, filename)
        except Exception:
            return jsonify({'error': 'Not Found'}), 404
    
    # Shell context
    @app.shell_context_processor
    def make_shell_context():
        from src.models.inventory import Inventory
        from src.models.location import Location
        from src.models.audit import AuditLog
        return {
            'db': db,
            'Inventory': Inventory,
            'Location': Location,
            'AuditLog': AuditLog
        }
    
    return app

# Only create app instance if running directly
if __name__ == '__main__':
    app = create_app()
    app.run()
