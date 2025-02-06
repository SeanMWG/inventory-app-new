"""Test configuration and fixtures."""
import os
import tempfile
import uuid
import pytest
from sqlalchemy.orm import scoped_session, sessionmaker
from src.app import create_app
from src.models import db as _db

@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    # Set up the test database
    db_fd, db_path = tempfile.mkstemp()
    
    # Create app with testing config
    test_app = create_app('testing')
    test_app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    # Establish application context
    with test_app.app_context():
        _db.create_all()
        yield test_app
        _db.session.remove()
        _db.drop_all()
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture(scope='function')
def db(app):
    """Create database for the tests."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()

@pytest.fixture(scope='function')
def session(app, db):
    """Create a new database session for a test."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Create session factory
        session_factory = sessionmaker(bind=connection)
        session = scoped_session(session_factory)
        
        # Set session
        db.session = session
        
        yield session
        
        # Clean up
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture
def client(app, session):
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
    session.refresh(location)
    
    return location

@pytest.fixture
def sample_inventory(session, sample_location):
    """Create a sample inventory item."""
    from src.models.inventory import Inventory
    
    item = Inventory(
        asset_tag=f'TEST{uuid.uuid4().hex[:6].upper()}',
        asset_type='Laptop',
        manufacturer='Test Manufacturer',
        model='Test Model',
        serial_number=f'SN{uuid.uuid4().hex[:8].upper()}',
        location_id=sample_location.id
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    
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
    session.refresh(log)
    
    return log
