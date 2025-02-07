"""Test application."""
import json
import pytest
from unittest.mock import patch
from werkzeug.exceptions import NotFound, InternalServerError
from src.app import create_app

def test_app_creation():
    """Test app creation."""
    app = create_app('testing')
    assert app.config['TESTING'] is True
    assert app.config['SQLALCHEMY_DATABASE_URI'] is not None

def test_app_configuration():
    """Test different configurations."""
    # Test development config
    app = create_app('development')
    assert app.config['DEBUG'] is True
    assert 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']
    
    # Test production config
    with pytest.raises(ValueError):
        # Should fail without required env vars
        create_app('production')

def test_request_handlers(client, auth_headers):
    """Test request handlers."""
    response = client.get('/api/inventory', headers=auth_headers)
    assert 'X-Content-Type-Options' in response.headers
    assert 'X-Frame-Options' in response.headers
    assert 'X-XSS-Protection' in response.headers
    assert 'Strict-Transport-Security' in response.headers
    assert 'Content-Security-Policy' in response.headers

def test_error_handlers(client):
    """Test error handlers."""
    # Test 404 handler
    response = client.get('/nonexistent-endpoint')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data
    
    # Test 500 handler
    with patch('src.models.db.session.commit') as mock_commit:
        mock_commit.side_effect = Exception('Database error')
        response = client.post('/api/locations',
                            headers={'Content-Type': 'application/json'},
                            data=json.dumps({'site_name': 'Test'}))
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data

def test_health_check(client):
    """Test health check endpoint."""
    # Test successful health check
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['database'] == 'connected'
    
    # Test database failure
    with patch('src.models.db.session.execute') as mock_execute:
        mock_execute.side_effect = Exception('Database error')
        response = client.get('/health')
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['status'] == 'unhealthy'
        assert data['database'] == 'disconnected'

def test_index_route(client):
    """Test index route."""
    response = client.get('/')
    assert response.status_code == 200

def test_shell_context():
    """Test shell context."""
    app = create_app('testing')
    ctx = app.make_shell_context()
    assert 'db' in ctx
    assert 'Inventory' in ctx
    assert 'Location' in ctx
    assert 'AuditLog' in ctx

def test_logging_setup(tmp_path):
    """Test logging setup."""
    log_dir = tmp_path / 'logs'
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = False
        with patch('os.mkdir') as mock_mkdir:
            app = create_app('production')
            mock_mkdir.assert_called_once()
            assert any(handler.level == 20 for handler in app.logger.handlers)  # INFO level

def test_request_timing(client):
    """Test request timing header in debug mode."""
    app = create_app('development')
    with app.test_client() as test_client:
        response = test_client.get('/health')
        assert 'X-Request-Duration' in response.headers

def test_error_logging(client, caplog):
    """Test error logging."""
    # Test 404 logging
    client.get('/nonexistent-endpoint')
    assert any('Page not found' in record.message for record in caplog.records)
    
    # Test 500 logging
    with patch('src.models.db.session.commit') as mock_commit:
        mock_commit.side_effect = Exception('Test error')
        client.post('/api/locations',
                   headers={'Content-Type': 'application/json'},
                   data=json.dumps({'site_name': 'Test'}))
        assert any('Server Error' in record.message for record in caplog.records)
