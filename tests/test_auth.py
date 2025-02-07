"""Test authentication."""
import json
import pytest
from unittest.mock import patch
from src.utils.auth import requires_auth, requires_roles

def test_login(client):
    """Test login endpoint."""
    response = client.get('/api/auth/login')
    assert response.status_code == 302  # Redirect to Azure login

def test_logout(client):
    """Test logout endpoint."""
    response = client.get('/api/auth/logout')
    assert response.status_code == 302  # Redirect to home

def test_callback(client):
    """Test callback endpoint."""
    with patch('msal.ConfidentialClientApplication') as mock_msal:
        mock_msal.return_value.acquire_token_by_authorization_code.return_value = {
            'access_token': 'test-token',
            'id_token_claims': {
                'preferred_username': 'test@example.com',
                'name': 'Test User',
                'roles': ['admin']
            }
        }
        response = client.get('/api/auth/callback?code=test-code')
        assert response.status_code == 302  # Redirect after successful login

def test_requires_auth_decorator(client):
    """Test requires_auth decorator."""
    # Test without auth headers
    response = client.get('/api/inventory')
    assert response.status_code == 401
    
    # Test with auth headers
    headers = {
        'X-User-ID': 'test@example.com',
        'X-User-Name': 'Test User',
        'X-User-Roles': '["admin"]'
    }
    response = client.get('/api/inventory', headers=headers)
    assert response.status_code == 200

def test_requires_roles_decorator(client):
    """Test requires_roles decorator."""
    # Test with non-admin role
    headers = {
        'X-User-ID': 'test@example.com',
        'X-User-Name': 'Test User',
        'X-User-Roles': '["user"]'
    }
    response = client.post('/api/inventory',
                         headers={**headers, 'Content-Type': 'application/json'},
                         data=json.dumps({'asset_tag': 'TEST001'}))
    assert response.status_code == 403
    
    # Test with admin role
    headers['X-User-Roles'] = '["admin"]'
    response = client.post('/api/inventory',
                         headers={**headers, 'Content-Type': 'application/json'},
                         data=json.dumps({
                             'asset_tag': 'TEST001',
                             'asset_type': 'Laptop',
                             'location_id': 1
                         }))
    assert response.status_code == 201

def test_token_refresh(client, auth_headers):
    """Test token refresh."""
    with patch('src.utils.auth._get_token_from_cache') as mock_get_token:
        # Test when token is valid
        mock_get_token.return_value = {'access_token': 'valid-token'}
        response = client.get('/api/inventory', headers=auth_headers)
        assert response.status_code == 200
        
        # Test when token needs refresh
        mock_get_token.return_value = None
        response = client.get('/api/inventory', headers=auth_headers)
        assert response.status_code == 200  # Should still work in test mode

def test_msal_integration(app):
    """Test MSAL integration."""
    with patch('msal.ConfidentialClientApplication') as mock_msal:
        # Test token cache
        mock_msal.return_value.get_accounts.return_value = [{'username': 'test@example.com'}]
        mock_msal.return_value.acquire_token_silent.return_value = {'access_token': 'new-token'}
        
        with app.test_client() as client:
            with client.session_transaction() as session:
                session['token_cache'] = 'test-cache'
            
            response = client.get('/api/inventory', headers={'X-User-ID': 'test@example.com'})
            assert response.status_code == 200

def test_error_handling(client):
    """Test authentication error handling."""
    # Test invalid token
    headers = {
        'X-User-ID': 'test@example.com',
        'X-User-Name': 'Test User',
        'X-User-Roles': 'invalid-json'  # Invalid JSON
    }
    response = client.get('/api/inventory', headers=headers)
    assert response.status_code == 401
    
    # Test missing required headers
    headers = {
        'X-User-Name': 'Test User',
        'X-User-Roles': '["admin"]'
    }
    response = client.get('/api/inventory', headers=headers)
    assert response.status_code == 401
