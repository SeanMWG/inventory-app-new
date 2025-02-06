"""Test configuration and fixtures."""
import os
import tempfile
import pytest
from src.app import create_app
from src.models import db as _db

@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    # Set up the test database
    db_fd, db_path = tempfile.mkstemp()
    
    # Create app with testing config
    test_app = create_app('testing')
    
    # Establish application context
    with test_app.app_context():
        _db.create_all()
        yield test_app
        _db.session.remove()
        _db.drop_all()
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture(scope='session')
def db(app):
    """Create database for the tests."""
    return _db

@pytest.fixture(scope='function')
def session(db):
    """Create a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)
    
    db.session = session
    
    yield session
    
    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()

@pytest.fixture
def auth_headers():
    """Create mock authentication headers."""
    return {
        'X-User-ID': 'test@example.com',
        'X-User-Name': 'Test User',
        'X-User-Roles': '["admin"]'
    }

@pytest.fixture
def sample_location(session):
    """Create a sample location."""
    from src.models.location import Location
    
    location = Location(
        site_name='Test Site',
        room_number='101',
        room_name='Test Room',
        room_type='Office'
    )
    session.add(location)
    session.commit()
    
    return location

@pytest.fixture
def sample_inventory(session, sample_location):
    """Create a sample inventory item."""
    from src.models.inventory import Inventory
    
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
    
    return item

@pytest.fixture
def sample_audit_log(session, sample_inventory):
    """Create a sample audit log entry."""
    from src.models.audit import AuditLog
    
    log = AuditLog(
        action_type='CREATE',
        field_name='item',
        changed_by='test@example.com',
        asset_tag=sample_inventory.asset_tag
    )
    session.add(log)
    session.commit()
    
    return log
