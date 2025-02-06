"""Database models package."""
from flask_sqlalchemy import SQLAlchemy

# Create SQLAlchemy instance without initializing it
db = SQLAlchemy()

# Import models after db is defined
from .base import BaseModel
from .inventory import Inventory
from .location import Location
from .audit import AuditLog

__all__ = ['db', 'BaseModel', 'Inventory', 'Location', 'AuditLog']
