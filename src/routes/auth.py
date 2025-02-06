"""Authentication routes."""
from flask import Blueprint, redirect, url_for, session, request, current_app
from ..utils.auth import _build_msal_app, _get_token_from_cache

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login')
def login():
    """Handle login."""
    if current_app.testing:
        return redirect(url_for('index'))

    # Get token from cache
    token = _get_token_from_cache(current_app.config.get('SCOPE'))
    if token:
        return redirect(url_for('index'))

    # Build auth URL
    auth_app = _build_msal_app()
    auth_url = auth_app.get_authorization_request_url(
        current_app.config.get('SCOPE'),
        redirect_uri=url_for('auth.authorized', _external=True),
        state=request.args.get('next', '/')
    )
    return redirect(auth_url)

@bp.route('/authorized')
def authorized():
    """Handle authorization response."""
    if current_app.testing:
        return redirect(url_for('index'))

    # Get token
    auth_app = _build_msal_app()
    result = auth_app.acquire_token_by_authorization_code(
        request.args['code'],
        scopes=current_app.config.get('SCOPE'),
        redirect_uri=url_for('auth.authorized', _external=True)
    )

    if 'error' in result:
        return redirect(url_for('auth.login'))

    # Store user info in session
    session['user'] = {
        'id': result.get('id_token_claims', {}).get('preferred_username'),
        'name': result.get('id_token_claims', {}).get('name'),
        'roles': result.get('id_token_claims', {}).get('roles', [])
    }

    # Store token in session
    if 'token_cache' not in session:
        session['token_cache'] = auth_app.token_cache.serialize()

    return redirect(request.args.get('state', '/'))

@bp.route('/logout')
def logout():
    """Handle logout."""
    if current_app.testing:
        return redirect(url_for('index'))

    # Clear session
    session.clear()
    return redirect(url_for('index'))
