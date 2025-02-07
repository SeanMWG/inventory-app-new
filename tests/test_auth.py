"""Test authentication."""
import json
import pytest
from unittest.mock import patch, Mock
from flask import session, url_for

def test_login_success(client):
    """Test successful login."""
    response = client.get('/auth/login')
    assert response.status_code == 302
    assert response.location == '/'
    with client.session_transaction() as sess:
        assert sess['user']['id'] == 'test@example.com'

def test_login_error(client):
    """Test login error handling."""
    with patch('src.utils.auth._build_msal_app', return_value=None) as mock_build:
        with patch('flask.current_app.testing', False):
            response = client.get('/auth/login')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data

def test_authorized_no_code(client):
    """Test authorized endpoint without code."""
    with patch('flask.current_app.testing', False):
        response = client.get('/auth/authorized')
        assert response.status_code == 302
        assert response.location == '/auth/login'

def test_authorized_success(client):
    """Test successful authorization."""
    response = client.get('/auth/authorized')
    assert response.status_code == 302
    assert response.location == '/'
    with client.session_transaction() as sess:
        assert sess['user']['id'] == 'test@example.com'

def test_authorized_error(client):
    """Test authorization error handling."""
    with patch('flask.current_app.testing', False):
        with patch('src.utils.auth._build_msal_app') as mock_build:
            mock_app = Mock()
            mock_app.acquire_token_by_authorization_code.return_value = {
                'error': 'test_error',
                'error_description': 'Test error'
            }
            mock_build.return_value = mock_app
            
            response = client.get('/auth/authorized?code=test-code')
            assert response.status_code == 302
            assert response.location == '/auth/login'

def test_authorized_no_claims(client):
    """Test authorization with no token claims."""
    with patch('flask.current_app.testing', False):
        with patch('src.utils.auth._build_msal_app') as mock_build:
            mock_app = Mock()
            mock_app.acquire_token_by_authorization_code.return_value = {}
            mock_build.return_value = mock_app
            
            response = client.get('/auth/authorized?code=test-code')
            assert response.status_code == 302
            assert response.location == '/auth/login'

def test_authorized_msal_error(client):
    """Test MSAL error handling."""
    with patch('flask.current_app.testing', False):
        with patch('src.utils.auth._build_msal_app', return_value=None) as mock_build:
            response = client.get('/auth/authorized?code=test-code')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data

def test_logout_success(client):
    """Test successful logout."""
    with client.session_transaction() as sess:
        sess['user'] = {'id': 'test@example.com'}
    
    response = client.get('/auth/logout')
    assert response.status_code == 302
    assert response.location == '/'
    with client.session_transaction() as sess:
        assert 'user' not in sess

def test_logout_error(client):
    """Test logout error handling."""
    with patch('flask.session.clear') as mock_clear:
        mock_clear.side_effect = Exception('Test error')
        with patch('flask.current_app.testing', False):
            response = client.get('/auth/logout')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data

def test_status_authenticated(client):
    """Test status endpoint when authenticated."""
    response = client.get('/auth/status')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['authenticated'] is True
    assert data['user']['id'] == 'test@example.com'

def test_status_unauthenticated(client):
    """Test status endpoint when not authenticated."""
    with patch('flask.current_app.testing', False):
        response = client.get('/auth/status')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['authenticated'] is False

def test_status_error(client):
    """Test status endpoint error handling."""
    with patch('flask.current_app.testing', False):
        with patch('flask.session.__contains__') as mock_contains:
            mock_contains.side_effect = Exception('Test error')
            response = client.get('/auth/status')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data

def test_error_handlers(client):
    """Test error handlers."""
    # Test 401 handler
    with patch('flask.current_app.testing', False):
        response = client.get('/auth/status')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    # Test 500 handler
    with patch('flask.current_app.testing', False):
        with patch('src.routes.auth.bp.dispatch_request') as mock_dispatch:
            mock_dispatch.side_effect = Exception('Server error')
            response = client.get('/auth/status')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data

def test_testing_mode(client):
    """Test endpoints in testing mode."""
    # Test login in testing mode
    response = client.get('/auth/login')
    assert response.status_code == 302
    assert response.location == '/'
    
    # Test authorized in testing mode
    response = client.get('/auth/authorized')
    assert response.status_code == 302
    assert response.location == '/'
    
    # Test logout in testing mode
    response = client.get('/auth/logout')
    assert response.status_code == 302
    assert response.location == '/'
    
    # Test status in testing mode
    response = client.get('/auth/status')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['authenticated'] is True
    assert data['user']['roles'] == ['admin']

def test_auth_headers(client):
    """Test authentication headers."""
    # Test valid headers
    headers = {
        'X-User-ID': 'test@example.com',
        'X-User-Name': 'Test User',
        'X-User-Roles': '["admin"]'
    }
    response = client.get('/api/inventory', headers=headers)
    assert response.status_code == 200

    # Test invalid JSON in roles
    headers['X-User-Roles'] = 'invalid-json'
    response = client.get('/api/inventory', headers=headers)
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data

    # Test missing headers
    response = client.get('/api/inventory')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data
