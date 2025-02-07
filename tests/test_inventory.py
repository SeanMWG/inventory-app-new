"""Test inventory routes."""
import json
import pytest
from unittest.mock import patch
from src.models.inventory import Inventory
from src.models.location import Location

def test_get_inventory_error_handling(client, auth_headers):
    """Test inventory list error handling."""
    with patch('src.models.Inventory.get_all') as mock_get_all:
        mock_get_all.side_effect = Exception('Database error')
        response = client.get('/api/inventory', headers=auth_headers)
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data

def test_get_inventory_item_error_handling(client, auth_headers):
    """Test inventory item retrieval error handling."""
    # Test non-existent item
    response = client.get('/api/inventory/99999', headers=auth_headers)
    assert response.status_code == 404
    
    # Test database error
    with patch('src.models.Inventory.get_by_id') as mock_get:
        mock_get.side_effect = Exception('Database error')
        response = client.get('/api/inventory/1', headers=auth_headers)
        assert response.status_code == 500

def test_create_inventory_validation(client, auth_headers, sample_location):
    """Test inventory creation validation."""
    # Test missing required fields
    response = client.post('/api/inventory',
                         headers={**auth_headers, 'Content-Type': 'application/json'},
                         data=json.dumps({}))
    assert response.status_code == 400
    
    # Test invalid location ID
    response = client.post('/api/inventory',
                         headers={**auth_headers, 'Content-Type': 'application/json'},
                         data=json.dumps({
                             'asset_tag': 'TEST001',
                             'asset_type': 'Laptop',
                             'location_id': 99999
                         }))
    assert response.status_code == 500
    
    # Test duplicate asset tag
    data = {
        'asset_tag': 'TEST001',
        'asset_type': 'Laptop',
        'location_id': sample_location.id
    }
    response = client.post('/api/inventory',
                         headers={**auth_headers, 'Content-Type': 'application/json'},
                         data=json.dumps(data))
    assert response.status_code == 201
    
    response = client.post('/api/inventory',
                         headers={**auth_headers, 'Content-Type': 'application/json'},
                         data=json.dumps(data))
    assert response.status_code == 500

def test_update_inventory_validation(client, auth_headers, sample_inventory):
    """Test inventory update validation."""
    # Test non-existent item
    response = client.put('/api/inventory/99999',
                        headers={**auth_headers, 'Content-Type': 'application/json'},
                        data=json.dumps({'asset_type': 'Desktop'}))
    assert response.status_code == 404
    
    # Test invalid data
    response = client.put(f'/api/inventory/{sample_inventory.id}',
                        headers={**auth_headers, 'Content-Type': 'application/json'},
                        data=json.dumps({'invalid_field': 'value'}))
    assert response.status_code == 200  # Should ignore invalid fields
    
    # Test database error
    with patch('src.models.Inventory.update') as mock_update:
        mock_update.side_effect = Exception('Database error')
        response = client.put(f'/api/inventory/{sample_inventory.id}',
                           headers={**auth_headers, 'Content-Type': 'application/json'},
                           data=json.dumps({'asset_type': 'Desktop'}))
        assert response.status_code == 500

def test_delete_inventory_validation(client, auth_headers, sample_inventory):
    """Test inventory deletion validation."""
    # Test non-existent item
    response = client.delete('/api/inventory/99999', headers=auth_headers)
    assert response.status_code == 404
    
    # Test database error
    with patch('src.models.Inventory.delete') as mock_delete:
        mock_delete.side_effect = Exception('Database error')
        response = client.delete(f'/api/inventory/{sample_inventory.id}',
                              headers=auth_headers)
        assert response.status_code == 500

def test_toggle_loaner_validation(client, auth_headers, sample_inventory):
    """Test loaner toggle validation."""
    # Test non-existent item
    response = client.post('/api/inventory/99999/toggle-loaner', headers=auth_headers)
    assert response.status_code == 404
    
    # Test successful toggle
    response = client.post(f'/api/inventory/{sample_inventory.id}/toggle-loaner',
                         headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['is_loaner'] is True
    
    # Test database error
    with patch('src.models.Inventory.save') as mock_save:
        mock_save.side_effect = Exception('Database error')
        response = client.post(f'/api/inventory/{sample_inventory.id}/toggle-loaner',
                            headers=auth_headers)
        assert response.status_code == 500

def test_inventory_filters(client, auth_headers, session, sample_location):
    """Test inventory filtering."""
    # Create test data
    items = [
        Inventory(
            asset_tag=f'TEST{i}',
            asset_type='Laptop' if i % 2 == 0 else 'Desktop',
            status='active' if i % 3 == 0 else 'decommissioned',
            is_loaner=i % 2 == 0,
            location_id=sample_location.id
        )
        for i in range(5)
    ]
    for item in items:
        session.add(item)
    session.commit()
    
    # Test type filter
    response = client.get('/api/inventory?type=Laptop', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(item['asset_type'] == 'Laptop' for item in data)
    
    # Test status filter
    response = client.get('/api/inventory?status=active', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(item['status'] == 'active' for item in data)
    
    # Test loaner filter
    response = client.get('/api/inventory?is_loaner=true', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(item['is_loaner'] is True for item in data)

def test_bulk_operations(client, auth_headers, session, sample_location):
    """Test bulk operations."""
    # Create test items
    items = [
        {
            'asset_tag': f'BULK{i}',
            'asset_type': 'Laptop',
            'location_id': sample_location.id
        }
        for i in range(3)
    ]
    
    # Test bulk create
    response = client.post('/api/inventory/bulk',
                         headers={**auth_headers, 'Content-Type': 'application/json'},
                         data=json.dumps({'items': items}))
    assert response.status_code == 201
    data = json.loads(response.data)
    assert len(data['created']) == 3
    
    # Test bulk update
    updates = [
        {
            'id': data['created'][i]['id'],
            'status': 'decommissioned'
        }
        for i in range(3)
    ]
    response = client.put('/api/inventory/bulk',
                        headers={**auth_headers, 'Content-Type': 'application/json'},
                        data=json.dumps({'items': updates}))
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['updated']) == 3
    assert all(item['status'] == 'decommissioned' for item in data['updated'])
