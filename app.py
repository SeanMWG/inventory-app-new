from flask import Flask, render_template, request, jsonify, g, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')

# Load configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///instance/inventory.db')

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Import routes after app initialization to avoid circular imports
from src.routes import auth, inventory, location, stats

# Register blueprints
app.register_blueprint(auth.bp)
app.register_blueprint(inventory.bp)
app.register_blueprint(location.bp)
app.register_blueprint(stats.bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db.session.commit()
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        app.logger.error(f'Health check failed: {str(e)}')
        return jsonify({'status': 'unhealthy', 'database': 'disconnected'}), 500

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

if __name__ == '__main__':
    app.run(debug=True)
