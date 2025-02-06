from functools import wraps
from flask import current_app, session, redirect, url_for, request
from msal import ConfidentialClientApplication
import requests
from datetime import datetime, timedelta

def load_cache():
    """Load token cache from session."""
    cache = session.get('token_cache')
    if cache:
        return cache
    return None

def save_cache(cache):
    """Save token cache to session."""
    session['token_cache'] = cache

def _build_msal_app(cache=None):
    """Build the MSAL confidential client application."""
    return ConfidentialClientApplication(
        current_app.config['AZURE_CLIENT_ID'],
        authority=current_app.config['AZURE_AUTHORITY'],
        client_credential=current_app.config['AZURE_CLIENT_SECRET'],
        token_cache=cache
    )

def _build_auth_url(authority=None, scopes=None, state=None):
    """Build the authorization URL."""
    return _build_msal_app().get_authorization_request_url(
        scopes or current_app.config['AZURE_SCOPE'],
        state=state or str(datetime.utcnow().timestamp()),
        redirect_uri=current_app.config.get('AZURE_REDIRECT_URI')
    )

def get_token_from_cache(scope=None):
    """Get token from cache."""
    cache = load_cache()
    if cache:
        cca = _build_msal_app(cache=cache)
        accounts = cca.get_accounts()
        if accounts:
            result = cca.acquire_token_silent(
                scope or current_app.config['AZURE_SCOPE'],
                account=accounts[0]
            )
            save_cache(cache)
            return result
    return None

def get_user_info(token):
    """Get user information from Microsoft Graph."""
    if not token:
        return None
    
    graph_data = requests.get(
        'https://graph.microsoft.com/v1.0/me',
        headers={'Authorization': f'Bearer {token["access_token"]}'},
    ).json()
    
    return {
        'name': graph_data.get('displayName'),
        'email': graph_data.get('userPrincipalName'),
        'id': graph_data.get('id')
    }

def requires_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user'):
            # Save the requested URL for redirecting after auth
            session['next_url'] = request.url
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def requires_roles(roles):
    """Decorator to require specific roles."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get('user'):
                session['next_url'] = request.url
                return redirect(url_for('auth.login'))
            
            user_roles = session.get('user', {}).get('roles', [])
            if not any(role in roles for role in user_roles):
                return {
                    'error': 'Unauthorized',
                    'message': 'You do not have the required roles to access this resource'
                }, 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

def validate_token(token):
    """Validate the token is not expired and has required claims."""
    if not token:
        return False
    
    try:
        # Check expiration
        expires_in = token.get('expires_in', 0)
        expires_on = token.get('expires_on', 0)
        now = datetime.utcnow().timestamp()
        
        if now >= expires_on or expires_in <= 0:
            return False
        
        # Check required claims
        required_claims = ['aud', 'iss', 'iat', 'nbf', 'exp']
        if not all(claim in token for claim in required_claims):
            return False
        
        return True
    except Exception:
        return False

def refresh_token_if_needed():
    """Refresh the token if it's about to expire."""
    token = get_token_from_cache()
    if not token:
        return None
    
    # Check if token expires in less than 5 minutes
    expires_on = token.get('expires_on', 0)
    now = datetime.utcnow()
    expiration = datetime.fromtimestamp(expires_on)
    
    if expiration - now < timedelta(minutes=5):
        cache = load_cache()
        if cache:
            cca = _build_msal_app(cache=cache)
            accounts = cca.get_accounts()
            if accounts:
                token = cca.acquire_token_silent(
                    current_app.config['AZURE_SCOPE'],
                    account=accounts[0]
                )
                save_cache(cache)
    
    return token

def clear_auth_session():
    """Clear authentication-related session data."""
    session.pop('user', None)
    session.pop('token_cache', None)
    session.pop('next_url', None)

def init_app(app):
    """Initialize authentication functions with app."""
    # Add authentication-related template context
    @app.context_processor
    def inject_user():
        return dict(user=session.get('user', None))
    
    # Add authentication error handlers
    @app.errorhandler(401)
    def unauthorized(e):
        clear_auth_session()
        return redirect(url_for('auth.login'))
