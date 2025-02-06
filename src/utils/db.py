from flask import current_app, g
from flask_migrate import Migrate
from sqlalchemy import text
from datetime import datetime
import pyodbc
from ..models import db

migrate = Migrate()

def init_db(app):
    """Initialize database and migrations."""
    db.init_app(app)
    migrate.init_app(app, db)

def get_db():
    """Get database connection."""
    if 'db' not in g:
        g.db = db

    return g.db

def close_db(e=None):
    """Close database connection."""
    db = g.pop('db', None)
    if db is not None:
        db.session.remove()

def test_connection():
    """Test database connection."""
    try:
        # Test SQLAlchemy connection
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        return True, "Database connection successful"
    except Exception as e:
        db.session.rollback()
        return False, f"Database connection failed: {str(e)}"

def init_app(app):
    """Initialize database functions with app."""
    app.teardown_appcontext(close_db)
    init_db(app)

def get_db_info():
    """Get database information."""
    try:
        result = db.session.execute(text("""
            SELECT 
                DB_NAME() as database_name,
                SERVERPROPERTY('ServerName') as server_name,
                SERVERPROPERTY('Edition') as edition,
                SERVERPROPERTY('ProductVersion') as version
        """))
        row = result.fetchone()
        return {
            'database_name': row.database_name,
            'server_name': row.server_name,
            'edition': row.edition,
            'version': row.version,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        current_app.logger.error(f"Error getting database info: {str(e)}")
        return None

def check_migrations():
    """Check if all migrations are applied."""
    try:
        # This assumes you're using Alembic through Flask-Migrate
        from flask_migrate import current
        from alembic.migration import MigrationContext
        from alembic.script import ScriptDirectory

        # Get current revision
        context = MigrationContext.configure(db.engine.connect())
        current_rev = context.get_current_revision()

        # Get latest available revision
        config = current.get_config()
        script = ScriptDirectory.from_config(config)
        head_rev = script.get_current_head()

        return {
            'current_revision': current_rev,
            'latest_revision': head_rev,
            'is_current': current_rev == head_rev
        }
    except Exception as e:
        current_app.logger.error(f"Error checking migrations: {str(e)}")
        return None

def get_table_sizes():
    """Get size information for all tables."""
    try:
        result = db.session.execute(text("""
            SELECT 
                t.name AS table_name,
                p.rows AS row_count,
                SUM(a.total_pages) * 8 AS total_space_kb
            FROM sys.tables t
            INNER JOIN sys.indexes i ON t.object_id = i.object_id
            INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
            INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
            GROUP BY t.name, p.rows
            ORDER BY total_space_kb DESC
        """))
        return [dict(row) for row in result]
    except Exception as e:
        current_app.logger.error(f"Error getting table sizes: {str(e)}")
        return None

def backup_database(backup_path):
    """Create a database backup."""
    try:
        result = db.session.execute(text(f"""
            BACKUP DATABASE {current_app.config['DB_NAME']}
            TO DISK = :backup_path
            WITH FORMAT, COMPRESSION
        """), {'backup_path': backup_path})
        db.session.commit()
        return True, "Backup created successfully"
    except Exception as e:
        db.session.rollback()
        return False, f"Backup failed: {str(e)}"

def health_check():
    """Perform a database health check."""
    try:
        # Basic connectivity test
        connection_ok, message = test_connection()
        if not connection_ok:
            return {'status': 'error', 'message': message}

        # Get database info
        db_info = get_db_info()
        
        # Check migrations
        migration_status = check_migrations()
        
        # Get table sizes
        table_sizes = get_table_sizes()
        
        return {
            'status': 'healthy',
            'database_info': db_info,
            'migration_status': migration_status,
            'table_sizes': table_sizes,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        current_app.logger.error(f"Health check failed: {str(e)}")
        return {'status': 'error', 'message': str(e)}
