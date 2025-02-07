"""Models package."""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection

# Initialize SQLAlchemy with session options
db = SQLAlchemy(session_options={
    'expire_on_commit': False,
    'autoflush': True
})

# Enable SQLite foreign key support
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

# Import models after db initialization to avoid circular imports
from .location import Location  # noqa: E402
from .inventory import Inventory  # noqa: E402
from .audit import AuditLog  # noqa: E402

__all__ = ['db', 'Location', 'Inventory', 'AuditLog']
