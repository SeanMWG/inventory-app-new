"""Authentication utilities."""
from functools import wraps
from flask import current_app, request, redirect, url_for, session, g
import json

def init_app(app):
    """Initialize authentication utilities."""
    pass

def requires_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Skip auth in testing
        if current_app.testing:
            # Use test headers if available
            if 'X-User-ID' in request.headers:
                g.user = {
                    'id': request.headers.get('X-User-ID'),
                    'name': request.headers.get('X-User-Name'),
                    'roles': json.loads(request.headers.get('X-User-Roles', '[]'))
                }
            return f(*args, **kwargs)

        # Check if user is authenticated
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        
        # Set user in g for request
        g.user = session['user']
        return f(*args, **kwargs)
    return decorated

def requires_roles(*roles):
    """Decorator to require specific roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip role check in testing
            if current_app.testing:
                if 'X-User-Roles' in request.headers:
                    user_roles = json.loads(request.headers.get('X-User-Roles', '[]'))
                    if not any(role in user_roles for role in roles):
                        return {'error': 'Forbidden'}, 403
                return f(*args, **kwargs)

            # Check if user has required role
            if not g.user or not any(role in g.user.get('roles', []) for role in roles):
                return {'error': 'Forbidden'}, 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def refresh_token_if_needed():
    """Refresh authentication token if needed."""
    # Skip in testing
    if current_app.testing:
        return

    # Implement token refresh logic here
    pass
