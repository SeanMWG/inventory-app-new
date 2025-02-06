"""Authentication utilities."""
from functools import wraps
from flask import current_app, request, redirect, url_for, session, g, jsonify
import json

# Only import msal if not in testing mode
try:
    import msal
except ImportError:
    msal = None

def init_app(app):
    """Initialize authentication utilities."""
    if not app.testing and msal is None:
        raise ImportError('msal package is required for production')

def requires_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Handle testing mode
        if current_app.testing:
            # Use test headers if available
            if 'X-User-ID' in request.headers:
                g.user = {
                    'id': request.headers.get('X-User-ID'),
                    'name': request.headers.get('X-User-Name'),
                    'roles': json.loads(request.headers.get('X-User-Roles', '[]'))
                }
                return f(*args, **kwargs)
            # Return 401 if no test headers
            return jsonify({'error': 'Unauthorized'}), 401

        # Check if user is authenticated
        if 'user' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Set user in g for request
        g.user = session['user']
        return f(*args, **kwargs)
    return decorated

def requires_roles(*roles):
    """Decorator to require specific roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Handle testing mode
            if current_app.testing:
                if 'X-User-Roles' in request.headers:
                    user_roles = json.loads(request.headers.get('X-User-Roles', '[]'))
                    if not any(role in user_roles for role in roles):
                        return jsonify({'error': 'Forbidden'}), 403
                    return f(*args, **kwargs)
                # Return 401 if no test headers
                return jsonify({'error': 'Unauthorized'}), 401

            # Check if user has required role
            if not g.user or not any(role in g.user.get('roles', []) for role in roles):
                return jsonify({'error': 'Forbidden'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def refresh_token_if_needed():
    """Refresh authentication token if needed."""
    # Skip in testing
    if current_app.testing:
        return

    # Get token from cache
    token = _get_token_from_cache(current_app.config.get('SCOPE'))
    if not token:
        return jsonify({'error': 'Unauthorized'}), 401

def _build_msal_app(cache=None):
    """Build the MSAL app."""
    if current_app.testing or msal is None:
        return None
        
    return msal.ConfidentialClientApplication(
        current_app.config.get('CLIENT_ID'),
        authority=current_app.config.get('AUTHORITY'),
        client_credential=current_app.config.get('CLIENT_SECRET'),
        token_cache=cache
    )

def _get_token_from_cache(scope=None):
    """Get token from cache."""
    if current_app.testing or msal is None:
        return None
        
    cache = msal.SerializableTokenCache()
    if session.get('token_cache'):
        cache.deserialize(session['token_cache'])
        
    auth_app = _build_msal_app(cache)
    if auth_app and auth_app.get_accounts():
        result = auth_app.acquire_token_silent(scope, account=auth_app.get_accounts()[0])
        session['token_cache'] = cache.serialize()
        return result
    return None
