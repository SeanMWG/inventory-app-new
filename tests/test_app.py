"""Test application."""
import json
import pytest
import os
from unittest.mock import patch, Mock
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
    assert response.status_code == 200
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

def test_index_route(client, tmp_path):
    """Test index route."""
    # Create temporary static folder
    static_folder = tmp_path / 'static'
    static_folder.mkdir()
    index_file = static_folder / 'index.html'
    index_file.write_text('<html><body>Test</body></html>')
    
    app = create_app('testing')
    app.static_folder = str(static_folder)
    
    with app.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 200
        assert b'Test' in response.data

def test_static_files(client, tmp_path):
    """Test static file serving."""
    # Create temporary static folder
    static_folder = tmp_path / 'static'
    static_folder.mkdir()
    test_file = static_folder / 'test.txt'
    test_file.write_text('Test content')
    
    app = create_app('testing')
    app.static_folder = str(static_folder)
    
    with app.test_client() as test_client:
        response = test_client.get('/test.txt')
        assert response.status_code == 200
        assert b'Test content' in response.data

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
        with patch('os.makedirs') as mock_mkdir:
            app = create_app('development')
            mock_mkdir.assert_called_once()
            assert app.logger.handlers

def test_request_timing(client):
    """Test request timing header in debug mode."""
    app = create_app('development')
    app.debug = True
    with app.test_client() as test_client:
        response = test_client.get('/health')
        assert response.status_code == 200
        assert 'X-Request-Duration' in response.headers

def test_error_logging(client, caplog):
    """Test error logging."""
    # Test 404 logging
    client.get('/nonexistent-endpoint')
    assert 'Page not found' in caplog.text
    
    # Test 500 logging
    with patch('src.models.db.session.commit') as mock_commit:
        mock_commit.side_effect = Exception('Test error')
        client.post('/api/locations',
                   headers={'Content-Type': 'application/json'},
                   data=json.dumps({'site_name': 'Test'}))
        assert 'Server Error' in caplog.text
