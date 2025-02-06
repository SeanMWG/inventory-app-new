from flask import Blueprint, redirect, url_for, session, request, current_app, jsonify
from ..utils.auth import (
    _build_msal_app, _build_auth_url, get_token_from_cache,
    get_user_info, clear_auth_session, save_cache
)
import uuid

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login')
def login():
    """Initiate login process."""
    # Clear any existing session
    clear_auth_session()
    
    # Generate and store state for CSRF protection
    session['state'] = str(uuid.uuid4())
    
    # Get the authorization URL
    auth_url = _build_auth_url(state=session['state'])
    
    return redirect(auth_url)

@bp.route('/logout')
def logout():
    """Handle logout."""
    clear_auth_session()
    return redirect(url_for('index'))

@bp.route('/getAToken')
def authorized():
    """Handle the Azure AD OAuth callback."""
    if request.args.get('state') != session.get('state'):
        return redirect(url_for('index'))  # State mismatch, possible CSRF
    
    if 'error' in request.args:
        return jsonify({
            'error': request.args['error'],
            'error_description': request.args.get('error_description', '')
        }), 401
    
    # Get token
    cache = _build_msal_app().acquire_token_by_authorization_code(
        request.args['code'],
        scopes=current_app.config['AZURE_SCOPE'],
        redirect_uri=current_app.config.get('AZURE_REDIRECT_URI')
    )
    
    if 'error' in cache:
        return jsonify({
            'error': cache['error'],
            'error_description': cache.get('error_description', '')
        }), 401
    
    # Save token to session
    save_cache(cache)
    
    # Get user info
    user_info = get_user_info(cache)
    if user_info:
        session['user'] = {
            'name': user_info['name'],
            'email': user_info['email'],
            'id': user_info['id']
        }
    
    # Redirect to original URL or home
    next_url = session.pop('next_url', None)
    return redirect(next_url or url_for('index'))

@bp.route('/token')
def token():
    """Get a new access token."""
    token = get_token_from_cache()
    if not token:
        return jsonify({
            'error': 'No token found',
            'login_url': url_for('auth.login', _external=True)
        }), 401
    
    return jsonify(token)

@bp.route('/me')
def me():
    """Get current user information."""
    token = get_token_from_cache()
    if not token:
        return jsonify({
            'error': 'Not authenticated',
            'login_url': url_for('auth.login', _external=True)
        }), 401
    
    user_info = get_user_info(token)
    if not user_info:
        return jsonify({
            'error': 'Failed to get user info',
            'login_url': url_for('auth.login', _external=True)
        }), 401
    
    return jsonify(user_info)

@bp.route('/check')
def check_auth():
    """Check authentication status."""
    token = get_token_from_cache()
    user = session.get('user')
    
    if not token or not user:
        return jsonify({
            'authenticated': False,
            'login_url': url_for('auth.login', _external=True)
        })
    
    return jsonify({
        'authenticated': True,
        'user': user
    })

# Error handlers
@bp.errorhandler(Exception)
def handle_auth_error(e):
    """Handle authentication errors."""
    current_app.logger.error(f'Authentication error: {str(e)}')
    clear_auth_session()
    return jsonify({
        'error': 'Authentication failed',
        'message': str(e),
        'login_url': url_for('auth.login', _external=True)
    }), 401
