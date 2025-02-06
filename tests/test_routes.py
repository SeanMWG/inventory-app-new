"""Test routes."""
import json
import pytest
from src.models.location import Location
from src.models.inventory import Inventory

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_get_locations(client, auth_headers):
    """Test get locations endpoint."""
    response = client.get('/api/locations', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_get_location(client, auth_headers, sample_location):
    """Test get location endpoint."""
    response = client.get(f'/api/locations/{sample_location.id}', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['site_name'] == 'Test Site'

def test_create_location(client, auth_headers):
    """Test create location endpoint."""
    data = {
        'site_name': 'New Site',
        'room_number': '201',
        'room_name': 'New Room',
        'room_type': 'Lab'
    }
    response = client.post('/api/locations', 
                         headers={**auth_headers, 'Content-Type': 'application/json'},
                         data=json.dumps(data))
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['site_name'] == 'New Site'

def test_update_location(client, auth_headers, sample_location):
    """Test update location endpoint."""
    data = {'room_name': 'Updated Room'}
    response = client.put(f'/api/locations/{sample_location.id}',
                        headers={**auth_headers, 'Content-Type': 'application/json'},
                        data=json.dumps(data))
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['room_name'] == 'Updated Room'

def test_delete_location(client, auth_headers, sample_location):
    """Test delete location endpoint."""
    response = client.delete(f'/api/locations/{sample_location.id}', headers=auth_headers)
    assert response.status_code == 200
    assert Location.query.get(sample_location.id) is None

def test_get_inventory(client, auth_headers):
    """Test get inventory endpoint."""
    response = client.get('/api/inventory', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_get_inventory_item(client, auth_headers, sample_inventory):
    """Test get inventory item endpoint."""
    response = client.get(f'/api/inventory/{sample_inventory.id}', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['asset_tag'] == sample_inventory.asset_tag

def test_create_inventory_item(client, auth_headers, sample_location):
    """Test create inventory item endpoint."""
    data = {
        'asset_tag': 'NEW001',
        'asset_type': 'Desktop',
        'manufacturer': 'Test Manufacturer',
        'model': 'Test Model',
        'serial_number': 'SN999999',
        'location_id': sample_location.id
    }
    response = client.post('/api/inventory',
                         headers={**auth_headers, 'Content-Type': 'application/json'},
                         data=json.dumps(data))
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['asset_tag'] == 'NEW001'

def test_update_inventory_item(client, auth_headers, sample_inventory):
    """Test update inventory item endpoint."""
    data = {'asset_type': 'Updated Type'}
    response = client.put(f'/api/inventory/{sample_inventory.id}',
                        headers={**auth_headers, 'Content-Type': 'application/json'},
                        data=json.dumps(data))
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['asset_type'] == 'Updated Type'

def test_delete_inventory_item(client, auth_headers, sample_inventory):
    """Test delete inventory item endpoint."""
    response = client.delete(f'/api/inventory/{sample_inventory.id}', headers=auth_headers)
    assert response.status_code == 200
    assert Inventory.query.get(sample_inventory.id) is None

def test_toggle_loaner(client, auth_headers, sample_inventory):
    """Test toggle loaner endpoint."""
    response = client.post(f'/api/inventory/{sample_inventory.id}/toggle-loaner',
                         headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['is_loaner'] is True

def test_get_stats(client, auth_headers):
    """Test get stats endpoint."""
    response = client.get('/api/stats', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'total_items' in data

def test_get_recent_activity(client, auth_headers):
    """Test get recent activity endpoint."""
    response = client.get('/api/stats/recent-activity', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_unauthorized_access(client):
    """Test unauthorized access."""
    response = client.get('/api/inventory')
    assert response.status_code == 401

def test_forbidden_access(client):
    """Test forbidden access."""
    headers = {
        'X-User-ID': 'test@example.com',
        'X-User-Name': 'Test User',
        'X-User-Roles': '["user"]'  # Non-admin role
    }
    response = client.post('/api/locations',
                         headers={**headers, 'Content-Type': 'application/json'},
                         data=json.dumps({'site_name': 'Test'}))
    assert response.status_code == 403

def test_invalid_input(client, auth_headers):
    """Test invalid input handling."""
    response = client.post('/api/locations',
                         headers={**auth_headers, 'Content-Type': 'application/json'},
                         data=json.dumps({}))
    assert response.status_code == 400

def test_not_found(client, auth_headers):
    """Test not found handling."""
    response = client.get('/api/locations/99999', headers=auth_headers)
    assert response.status_code == 404
