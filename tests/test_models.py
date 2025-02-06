"""Test cases for database models."""
import pytest
from datetime import datetime
from src.models.inventory import Inventory
from src.models.location import Location
from src.models.audit import AuditLog

def test_location_creation(session, sample_location):
    """Test location model creation."""
    assert sample_location.id is not None
    assert sample_location.site_name == 'Test Site'
    assert sample_location.room_number == '101'
    assert sample_location.room_name == 'Test Room'
    assert sample_location.room_type == 'Office'
    assert sample_location.status == 'active'
    assert isinstance(sample_location.created_at, datetime)
    assert isinstance(sample_location.updated_at, datetime)

def test_location_full_name(sample_location):
    """Test location full name property."""
    assert sample_location.full_name == 'Test Site - 101 (Test Room)'

def test_location_unique_constraint(session):
    """Test location unique constraint."""
    # Create duplicate location
    duplicate = Location(
        site_name='Test Site',
        room_number='101',
        room_name='Duplicate Room',
        room_type='Office'
    )
    session.add(duplicate)
    
    with pytest.raises(Exception):  # SQLAlchemy will raise an integrity error
        session.commit()

def test_inventory_creation(session, sample_inventory, sample_location):
    """Test inventory model creation."""
    assert sample_inventory.id is not None
    assert sample_inventory.asset_tag == 'TEST001'
    assert sample_inventory.asset_type == 'Laptop'
    assert sample_inventory.manufacturer == 'Test Manufacturer'
    assert sample_inventory.model == 'Test Model'
    assert sample_inventory.serial_number == 'SN123456'
    assert sample_inventory.status == 'active'
    assert sample_inventory.location_id == sample_location.id
    assert isinstance(sample_inventory.created_at, datetime)
    assert isinstance(sample_inventory.updated_at, datetime)

def test_inventory_unique_constraints(session, sample_inventory):
    """Test inventory unique constraints."""
    # Test duplicate asset tag
    duplicate_tag = Inventory(
        asset_tag='TEST001',
        asset_type='Desktop',
        serial_number='DIFFERENT123'
    )
    session.add(duplicate_tag)
    with pytest.raises(Exception):
        session.commit()
    session.rollback()
    
    # Test duplicate serial number
    duplicate_serial = Inventory(
        asset_tag='TEST002',
        asset_type='Desktop',
        serial_number='SN123456'
    )
    session.add(duplicate_serial)
    with pytest.raises(Exception):
        session.commit()

def test_inventory_location_relationship(session, sample_inventory, sample_location):
    """Test inventory-location relationship."""
    assert sample_inventory.location == sample_location
    assert sample_inventory in sample_location.inventory_items

def test_inventory_assignment(session, sample_inventory):
    """Test inventory assignment functionality."""
    sample_inventory.assign('test.user@example.com')
    assert sample_inventory.assigned_to == 'test.user@example.com'
    assert sample_inventory.date_assigned is not None

def test_inventory_decommission(session, sample_inventory):
    """Test inventory decommission functionality."""
    sample_inventory.decommission()
    assert sample_inventory.status == 'decommissioned'
    assert sample_inventory.date_decommissioned is not None

def test_audit_log_creation(session, sample_audit_log, sample_inventory):
    """Test audit log model creation."""
    assert sample_audit_log.id is not None
    assert sample_audit_log.action_type == 'CREATE'
    assert sample_audit_log.field_name == 'item'
    assert sample_audit_log.changed_by == 'test@example.com'
    assert sample_audit_log.asset_tag == sample_inventory.asset_tag
    assert isinstance(sample_audit_log.changed_at, datetime)

def test_audit_log_queries(session, sample_audit_log, sample_inventory):
    """Test audit log query methods."""
    # Test get by asset tag
    logs = AuditLog.get_inventory_history(sample_inventory.asset_tag)
    assert len(logs) == 1
    assert logs[0] == sample_audit_log
    
    # Test get by user
    user_logs = AuditLog.get_user_actions('test@example.com')
    assert len(user_logs) == 1
    assert user_logs[0] == sample_audit_log

def test_model_to_dict_methods(sample_location, sample_inventory, sample_audit_log):
    """Test model to_dict methods."""
    # Test location to_dict
    location_dict = sample_location.to_dict()
    assert location_dict['site_name'] == 'Test Site'
    assert location_dict['room_number'] == '101'
    
    # Test inventory to_dict
    inventory_dict = sample_inventory.to_dict()
    assert inventory_dict['asset_tag'] == 'TEST001'
    assert inventory_dict['asset_type'] == 'Laptop'
    assert 'location' in inventory_dict
    
    # Test audit log to_dict
    audit_dict = sample_audit_log.to_dict()
    assert audit_dict['action_type'] == 'CREATE'
    assert audit_dict['changed_by'] == 'test@example.com'

def test_cascade_delete(session, sample_location, sample_inventory):
    """Test cascade delete behavior."""
    # Delete location should not delete inventory items
    location_id = sample_location.id
    session.delete(sample_location)
    session.commit()
    
    # Inventory item should still exist but with no location
    updated_item = session.get(Inventory, sample_inventory.id)
    assert updated_item is not None
    assert updated_item.location_id is None
