"""Models package."""
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# Import models after db initialization to avoid circular imports
from .location import Location  # noqa: E402
from .inventory import Inventory  # noqa: E402
from .audit import AuditLog  # noqa: E402

__all__ = ['db', 'Location', 'Inventory', 'AuditLog']
