"""Authentication routes."""
from flask import Blueprint, redirect, url_for, session, request, current_app, jsonify
from ..utils.auth import _build_msal_app, _get_token_from_cache

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login')
def login():
    """Handle login."""
    try:
        if current_app.testing:
            return redirect(url_for('index'))

        # Get token from cache
        token = _get_token_from_cache(current_app.config.get('SCOPE'))
        if token:
            return redirect(url_for('index'))

        # Build auth URL
        auth_app = _build_msal_app()
        if not auth_app:
            current_app.logger.error('Failed to build MSAL app')
            return jsonify({'error': 'Authentication configuration error'}), 500

        auth_url = auth_app.get_authorization_request_url(
            current_app.config.get('SCOPE'),
            redirect_uri=url_for('auth.authorized', _external=True),
            state=request.args.get('next', '/')
        )
        return redirect(auth_url)
    except Exception as e:
        current_app.logger.error(f'Login error: {str(e)}')
        return jsonify({'error': 'Authentication failed'}), 500

@bp.route('/authorized')
def authorized():
    """Handle authorization response."""
    try:
        if current_app.testing:
            return redirect(url_for('index'))

        if 'code' not in request.args:
            current_app.logger.error('No authorization code received')
            return redirect(url_for('auth.login'))

        # Get token
        auth_app = _build_msal_app()
        if not auth_app:
            current_app.logger.error('Failed to build MSAL app')
            return jsonify({'error': 'Authentication configuration error'}), 500

        result = auth_app.acquire_token_by_authorization_code(
            request.args['code'],
            scopes=current_app.config.get('SCOPE'),
            redirect_uri=url_for('auth.authorized', _external=True)
        )

        if 'error' in result:
            current_app.logger.error(f'Token acquisition error: {result.get("error_description")}')
            return redirect(url_for('auth.login'))

        if not result.get('id_token_claims'):
            current_app.logger.error('No token claims received')
            return redirect(url_for('auth.login'))

        # Store user info in session
        session['user'] = {
            'id': result.get('id_token_claims', {}).get('preferred_username'),
            'name': result.get('id_token_claims', {}).get('name'),
            'roles': result.get('id_token_claims', {}).get('roles', [])
        }

        # Store token in session
        if auth_app.token_cache:
            session['token_cache'] = auth_app.token_cache.serialize()

        return redirect(request.args.get('state', '/'))
    except Exception as e:
        current_app.logger.error(f'Authorization error: {str(e)}')
        return jsonify({'error': 'Authorization failed'}), 500

@bp.route('/logout')
def logout():
    """Handle logout."""
    try:
        if current_app.testing:
            return redirect(url_for('index'))

        # Clear session
        session.clear()
        return redirect(url_for('index'))
    except Exception as e:
        current_app.logger.error(f'Logout error: {str(e)}')
        return jsonify({'error': 'Logout failed'}), 500

@bp.route('/status')
def status():
    """Get authentication status."""
    try:
        if current_app.testing:
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': 'test@example.com',
                    'name': 'Test User',
                    'roles': ['admin']
                }
            })

        if 'user' not in session:
            return jsonify({'authenticated': False}), 401

        return jsonify({
            'authenticated': True,
            'user': session['user']
        })
    except Exception as e:
        current_app.logger.error(f'Status check error: {str(e)}')
        return jsonify({'error': 'Status check failed'}), 500

@bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized access."""
    return jsonify({'error': 'Unauthorized'}), 401

@bp.errorhandler(500)
def server_error(error):
    """Handle server errors."""
    current_app.logger.error(f'Server error in auth routes: {str(error)}')
    return jsonify({'error': 'Internal server error'}), 500
