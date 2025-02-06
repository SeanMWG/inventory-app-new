"""Database models package."""
from flask_sqlalchemy import SQLAlchemy

# Create SQLAlchemy instance without initializing it
db = SQLAlchemy()

# Import models after db is defined to avoid circular imports
from .inventory import Inventory
from .location import Location
from .audit import AuditLog

__all__ = ['db', 'Inventory', 'Location', 'AuditLog']
