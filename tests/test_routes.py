"""Test cases for API routes."""
import json
import pytest
from datetime import datetime

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_get_locations(client, auth_headers, sample_location):
    """Test get locations endpoint."""
    response = client.get('/api/locations/', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) >= 1
    assert any(loc['site_name'] == 'Test Site' for loc in data)

def test_get_location(client, auth_headers, sample_location):
    """Test get specific location endpoint."""
    response = client.get(f'/api/locations/{sample_location.id}', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['site_name'] == 'Test Site'
    assert data['room_number'] == '101'

def test_create_location(client, auth_headers, session):
    """Test create location endpoint."""
    location_data = {
        'site_name': 'New Site',
        'room_number': '201',
        'room_name': 'New Room',
        'room_type': 'Conference'
    }
    
    response = client.post(
        '/api/locations/',
        headers={**auth_headers, 'Content-Type': 'application/json'},
        data=json.dumps(location_data)
    )
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['site_name'] == 'New Site'
    assert data['room_number'] == '201'

def test_update_location(client, auth_headers, sample_location):
    """Test update location endpoint."""
    update_data = {
        'room_name': 'Updated Room',
        'description': 'Updated description'
    }
    
    response = client.put(
        f'/api/locations/{sample_location.id}',
        headers={**auth_headers, 'Content-Type': 'application/json'},
        data=json.dumps(update_data)
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['room_name'] == 'Updated Room'
    assert data['description'] == 'Updated description'

def test_delete_location(client, auth_headers, sample_location):
    """Test delete location endpoint."""
    response = client.delete(
        f'/api/locations/{sample_location.id}',
        headers=auth_headers
    )
    assert response.status_code == 200

def test_get_inventory(client, auth_headers, sample_inventory):
    """Test get inventory endpoint."""
    response = client.get('/api/inventory/', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] >= 1
    assert any(item['asset_tag'] == 'TEST001' for item in data['items'])

def test_get_inventory_item(client, auth_headers, sample_inventory):
    """Test get specific inventory item endpoint."""
    response = client.get(
        f'/api/inventory/{sample_inventory.asset_tag}',
        headers=auth_headers
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['asset_tag'] == 'TEST001'
    assert data['asset_type'] == 'Laptop'

def test_create_inventory_item(client, auth_headers, sample_location):
    """Test create inventory item endpoint."""
    item_data = {
        'asset_tag': 'NEW001',
        'asset_type': 'Desktop',
        'manufacturer': 'Test Manufacturer',
        'model': 'Test Model',
        'serial_number': 'SN789012',
        'location_id': sample_location.id
    }
    
    response = client.post(
        '/api/inventory/',
        headers={**auth_headers, 'Content-Type': 'application/json'},
        data=json.dumps(item_data)
    )
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['asset_tag'] == 'NEW001'
    assert data['asset_type'] == 'Desktop'

def test_update_inventory_item(client, auth_headers, sample_inventory):
    """Test update inventory item endpoint."""
    update_data = {
        'model': 'Updated Model',
        'notes': 'Updated notes'
    }
    
    response = client.put(
        f'/api/inventory/{sample_inventory.asset_tag}',
        headers={**auth_headers, 'Content-Type': 'application/json'},
        data=json.dumps(update_data)
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['model'] == 'Updated Model'
    assert data['notes'] == 'Updated notes'

def test_delete_inventory_item(client, auth_headers, sample_inventory):
    """Test delete inventory item endpoint."""
    response = client.delete(
        f'/api/inventory/{sample_inventory.asset_tag}',
        headers=auth_headers
    )
    assert response.status_code == 200

def test_toggle_loaner(client, auth_headers, sample_inventory):
    """Test toggle loaner status endpoint."""
    response = client.post(
        f'/api/inventory/{sample_inventory.asset_tag}/toggle-loaner',
        headers=auth_headers
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['is_loaner'] == True

def test_get_stats(client, auth_headers, sample_inventory, sample_location):
    """Test get statistics endpoint."""
    response = client.get('/api/stats', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'total_items' in data
    assert 'active_locations' in data
    assert data['total_items'] >= 1
    assert data['active_locations'] >= 1

def test_get_recent_activity(client, auth_headers, sample_audit_log):
    """Test get recent activity endpoint."""
    response = client.get('/api/audit/recent', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) >= 1
    assert data[0]['action_type'] == 'CREATE'

def test_unauthorized_access(client):
    """Test unauthorized access to protected endpoints."""
    # Try accessing protected endpoint without auth headers
    response = client.get('/api/inventory/')
    assert response.status_code == 401

def test_forbidden_access(client, auth_headers):
    """Test forbidden access to admin-only endpoints."""
    # Modify headers to remove admin role
    non_admin_headers = {
        **auth_headers,
        'X-User-Roles': '["user"]'
    }
    
    # Try deleting a location without admin role
    response = client.delete('/api/locations/1', headers=non_admin_headers)
    assert response.status_code == 403

def test_invalid_input(client, auth_headers):
    """Test input validation."""
    # Try creating location with missing required fields
    response = client.post(
        '/api/locations/',
        headers={**auth_headers, 'Content-Type': 'application/json'},
        data=json.dumps({'site_name': 'Test Site'})  # Missing required fields
    )
    assert response.status_code == 400

def test_not_found(client, auth_headers):
    """Test not found responses."""
    # Try getting non-existent location
    response = client.get('/api/locations/99999', headers=auth_headers)
    assert response.status_code == 404
