"""Test configuration and fixtures."""
import os
import tempfile
import uuid
import pytest
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import appcontext_pushed, g
from src.app import create_app
from src.models import db as _db

@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    # Create app with testing config
    test_app = create_app('testing')
    
    # Update config with test-specific settings
    test_app.config.update({
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db',
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-key',
        'SERVER_NAME': 'localhost'
    })
    
    # Establish application context
    with test_app.app_context():
        # Set up test user in g
        def handler(sender, **kwargs):
            g.user = {
                'id': 'test@example.com',
                'name': 'Test User',
                'roles': ['admin']
            }
        appcontext_pushed.connect(handler, test_app)
        
        # Create database tables
        _db.create_all()
        
        yield test_app
        
        # Clean up
        _db.session.remove()
        _db.drop_all()

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
        # Create a new connection and transaction
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Create session factory bound to this connection
        session_factory = sessionmaker(bind=connection)
        session = scoped_session(session_factory)
        
        # Begin a nested transaction (using SAVEPOINT)
        nested = connection.begin_nested()
        
        # If the application code calls session.commit, it will end the nested
        # transaction. Need to start a new one when that happens.
        @db.event.listens_for(session, 'after_transaction_end')
        def end_savepoint(session, transaction):
            nonlocal nested
            if not nested.is_active:
                nested = connection.begin_nested()
        
        # Set the session for the app
        db.session = session
        
        yield session
        
        # Clean up
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture
def client(app, session):
    """Create test client."""
    with app.test_client() as test_client:
        with app.app_context():
            # Set up test user in session
            with test_client.session_transaction() as sess:
                sess['user'] = {
                    'id': 'test@example.com',
                    'name': 'Test User',
                    'roles': ['admin']
                }
            yield test_client

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

@pytest.fixture(autouse=True)
def _push_request_context(app):
    """Automatically push request context for all tests."""
    with app.test_request_context():
        yield
