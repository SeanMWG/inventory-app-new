"""Test models."""
import pytest
from sqlalchemy.exc import IntegrityError
from src.models.location import Location
from src.models.inventory import Inventory
from src.models.audit import AuditLog

def test_location_creation(session):
    """Test location creation."""
    location = Location(
        site_name='Test Site',
        room_number='101',
        room_name='Test Room',
        room_type='Office'
    )
    session.add(location)
    session.commit()
    
    assert location.id is not None
    assert location.site_name == 'Test Site'

def test_location_full_name(session):
    """Test location full name property."""
    location = Location(
        site_name='Test Site',
        room_number='101',
        room_name='Test Room',
        room_type='Office'
    )
    session.add(location)
    session.commit()
    
    assert location.full_name == 'Test Site - 101 (Test Room)'

def test_location_unique_constraint(session):
    """Test location unique constraint."""
    location1 = Location(
        site_name='Test Site',
        room_number='101',
        room_name='Test Room',
        room_type='Office'
    )
    session.add(location1)
    session.commit()
    
    location2 = Location(
        site_name='Test Site',
        room_number='101',  # Same site and room number
        room_name='Another Room',
        room_type='Office'
    )
    session.add(location2)
    
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

def test_inventory_creation(session, sample_location):
    """Test inventory creation."""
    item = Inventory(
        asset_tag='TEST001',
        asset_type='Laptop',
        manufacturer='Test Manufacturer',
        model='Test Model',
        serial_number='SN123456',
        location_id=sample_location.id
    )
    session.add(item)
    session.commit()
    
    assert item.id is not None
    assert item.asset_tag == 'TEST001'

def test_inventory_unique_constraints(session, sample_location):
    """Test inventory unique constraints."""
    item1 = Inventory(
        asset_tag='TEST001',
        asset_type='Laptop',
        manufacturer='Test Manufacturer',
        model='Test Model',
        serial_number='SN123456',
        location_id=sample_location.id
    )
    session.add(item1)
    session.commit()
    
    # Test duplicate asset tag
    item2 = Inventory(
        asset_tag='TEST001',  # Same asset tag
        asset_type='Desktop',
        manufacturer='Test Manufacturer',
        model='Test Model',
        serial_number='SN789012',
        location_id=sample_location.id
    )
    session.add(item2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
    
    # Test duplicate serial number
    item3 = Inventory(
        asset_tag='TEST002',
        asset_type='Laptop',
        manufacturer='Test Manufacturer',
        model='Test Model',
        serial_number='SN123456',  # Same serial number
        location_id=sample_location.id
    )
    session.add(item3)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

def test_inventory_location_relationship(session, sample_location):
    """Test inventory-location relationship."""
    item = Inventory(
        asset_tag='TEST001',
        asset_type='Laptop',
        manufacturer='Test Manufacturer',
        model='Test Model',
        serial_number='SN123456',
        location_id=sample_location.id
    )
    session.add(item)
    session.commit()
    
    assert item.location == sample_location
    assert item in sample_location.inventory_items

def test_inventory_assignment(session, sample_inventory):
    """Test inventory assignment."""
    sample_inventory.assign('user@example.com')
    assert sample_inventory.assigned_to == 'user@example.com'
    assert sample_inventory.date_assigned is not None

def test_inventory_decommission(session, sample_inventory):
    """Test inventory decommission."""
    sample_inventory.decommission()
    assert sample_inventory.status == 'decommissioned'
    assert sample_inventory.date_decommissioned is not None

def test_audit_log_creation(session, sample_inventory):
    """Test audit log creation."""
    log = AuditLog(
        action_type='UPDATE',
        field_name='status',
        old_value='active',
        new_value='decommissioned',
        changed_by='admin@example.com',
        asset_tag=sample_inventory.asset_tag
    )
    session.add(log)
    session.commit()
    
    assert log.id is not None
    assert log.action_type == 'UPDATE'

def test_audit_log_queries(session, sample_inventory):
    """Test audit log queries."""
    # Create multiple logs
    for i in range(3):
        log = AuditLog(
            action_type='UPDATE',
            field_name=f'field{i}',
            changed_by='admin@example.com',
            asset_tag=sample_inventory.asset_tag
        )
        session.add(log)
    session.commit()
    
    # Test get_inventory_history
    history = AuditLog.get_inventory_history(sample_inventory.asset_tag)
    assert len(history) == 3
    
    # Test get_user_actions
    actions = AuditLog.get_user_actions('admin@example.com')
    assert len(actions) == 3

def test_model_to_dict_methods(session, sample_location, sample_inventory):
    """Test model to_dict methods."""
    location_dict = sample_location.to_dict()
    assert location_dict['site_name'] == 'Test Site'
    assert location_dict['room_number'] == '101'
    
    inventory_dict = sample_inventory.to_dict()
    assert inventory_dict['asset_type'] == 'Laptop'
    assert inventory_dict['location'] is not None

def test_cascade_delete(session, sample_location, sample_inventory):
    """Test cascade delete behavior."""
    # Delete location should cascade to inventory
    session.delete(sample_location)
    session.commit()
    
    # Verify inventory is deleted
    assert Inventory.query.get(sample_inventory.id) is None
