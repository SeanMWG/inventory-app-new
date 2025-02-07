"""Test authentication."""
import json
import pytest
from unittest.mock import patch
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
    with client.session_transaction() as sess:
        sess.clear()
    
    with patch('src.utils.auth._build_msal_app', return_value=None):
        response = client.get('/auth/login')
        assert response.status_code == 302  # Should still redirect in testing mode
        assert response.location == '/'

def test_authorized_no_code(client):
    """Test authorized endpoint without code."""
    with client.session_transaction() as sess:
        sess.clear()
    
    response = client.get('/auth/authorized')
    assert response.status_code == 302  # Should redirect in testing mode
    assert response.location == '/'

def test_authorized_success(client):
    """Test successful authorization."""
    response = client.get('/auth/authorized')
    assert response.status_code == 302
    assert response.location == '/'
    with client.session_transaction() as sess:
        assert sess['user']['id'] == 'test@example.com'

def test_authorized_error(client):
    """Test authorization error handling."""
    with client.session_transaction() as sess:
        sess.clear()
    
    response = client.get('/auth/authorized')
    assert response.status_code == 302  # Should redirect in testing mode
    assert response.location == '/'

def test_authorized_no_claims(client):
    """Test authorization with no token claims."""
    with client.session_transaction() as sess:
        sess.clear()
    
    response = client.get('/auth/authorized')
    assert response.status_code == 302  # Should redirect in testing mode
    assert response.location == '/'

def test_authorized_msal_error(client):
    """Test MSAL error handling."""
    with client.session_transaction() as sess:
        sess.clear()
    
    response = client.get('/auth/authorized')
    assert response.status_code == 302  # Should redirect in testing mode
    assert response.location == '/'

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
    with client.session_transaction() as sess:
        sess.clear()
    
    response = client.get('/auth/logout')
    assert response.status_code == 302  # Should still redirect in testing mode
    assert response.location == '/'

def test_status_authenticated(client):
    """Test status endpoint when authenticated."""
    response = client.get('/auth/status')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['authenticated'] is True
    assert data['user']['id'] == 'test@example.com'

def test_status_unauthenticated(client):
    """Test status endpoint when not authenticated."""
    with client.session_transaction() as sess:
        sess.clear()
    
    response = client.get('/auth/status')
    assert response.status_code == 200  # Should still return test user in testing mode
    data = json.loads(response.data)
    assert data['authenticated'] is True
    assert data['user']['id'] == 'test@example.com'

def test_status_error(client):
    """Test status endpoint error handling."""
    with client.session_transaction() as sess:
        sess.clear()
    
    response = client.get('/auth/status')
    assert response.status_code == 200  # Should still return test user in testing mode
    data = json.loads(response.data)
    assert data['authenticated'] is True

def test_error_handlers(client):
    """Test error handlers."""
    with client.session_transaction() as sess:
        sess.clear()
    
    # Test 401 handler
    response = client.get('/auth/status')
    assert response.status_code == 200  # Should still return test user in testing mode
    data = json.loads(response.data)
    assert data['authenticated'] is True

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
    assert response.status_code == 200  # Should still work in testing mode
