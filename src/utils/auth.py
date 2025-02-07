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
    if not app.testing and not app.debug and msal is None:
        raise ImportError('msal package is required for production')

def requires_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_app.testing or current_app.debug:
            # In testing/debug mode, always set test user unless headers are provided
            if 'X-User-ID' in request.headers:
                try:
                    g.user = {
                        'id': request.headers.get('X-User-ID'),
                        'name': request.headers.get('X-User-Name'),
                        'roles': json.loads(request.headers.get('X-User-Roles', '[]'))
                    }
                except json.JSONDecodeError:
                    return jsonify({'error': 'Invalid role format'}), 401
            else:
                g.user = {
                    'id': 'test@example.com',
                    'name': 'Test User',
                    'roles': ['admin']
                }
                session['user'] = g.user
            return f(*args, **kwargs)

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
            if current_app.testing or current_app.debug:
                # In testing/debug mode, check headers if present
                if 'X-User-Roles' in request.headers:
                    try:
                        user_roles = json.loads(request.headers.get('X-User-Roles', '[]'))
                    except json.JSONDecodeError:
                        return jsonify({'error': 'Invalid role format'}), 401
                else:
                    # Default test user has admin role
                    user_roles = ['admin']
                
                if not any(role in user_roles for role in roles):
                    return jsonify({'error': 'Forbidden'}), 403
                return f(*args, **kwargs)

            # Check if user has required role
            if not g.user or not any(role in g.user.get('roles', []) for role in roles):
                return jsonify({'error': 'Forbidden'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def refresh_token_if_needed():
    """Refresh authentication token if needed."""
    # Skip in testing or debug mode
    if current_app.testing or current_app.debug:
        if 'user' not in session:
            session['user'] = {
                'id': 'test@example.com',
                'name': 'Test User',
                'roles': ['admin']
            }
        return

    # Get token from cache
    token = _get_token_from_cache(current_app.config.get('SCOPE'))
    if not token:
        session['user'] = {
            'id': 'anonymous@example.com',
            'name': 'Anonymous User',
            'roles': ['viewer']
        }

def _build_msal_app(cache=None):
    """Build the MSAL app."""
    if current_app.testing or current_app.debug:
        return None
        
    if msal is None:
        current_app.logger.error('MSAL package not available')
        return None

    try:
        return msal.ConfidentialClientApplication(
            current_app.config.get('CLIENT_ID'),
            authority=current_app.config.get('AUTHORITY'),
            client_credential=current_app.config.get('CLIENT_SECRET'),
            token_cache=cache
        )
    except Exception as e:
        current_app.logger.error(f'Failed to build MSAL app: {str(e)}')
        return None

def _get_token_from_cache(scope=None):
    """Get token from cache."""
    if current_app.testing or current_app.debug:
        return {'access_token': 'test-token'}

    if msal is None:
        return None
        
    try:
        cache = msal.SerializableTokenCache()
        if session.get('token_cache'):
            cache.deserialize(session['token_cache'])
            
        auth_app = _build_msal_app(cache)
        if auth_app and auth_app.get_accounts():
            result = auth_app.acquire_token_silent(scope, account=auth_app.get_accounts()[0])
            session['token_cache'] = cache.serialize()
            return result
    except Exception as e:
        current_app.logger.error(f'Failed to get token from cache: {str(e)}')
    return None
