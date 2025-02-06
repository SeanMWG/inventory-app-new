#!/usr/bin/env python3
"""Initialize database and apply migrations."""
import os
import sys
from flask_migrate import upgrade, init, migrate, stamp
from src.app import create_app, db
from src.models.inventory import Inventory
from src.models.location import Location
from src.models.audit import AuditLog

def init_db():
    """Initialize database and apply migrations."""
    try:
        app = create_app()
        
        with app.app_context():
            # Check if database exists
            if not os.path.exists('instance'):
                os.makedirs('instance')
            
            # Initialize migrations if they don't exist
            if not os.path.exists('migrations'):
                print("Initializing migrations directory...")
                init()
                
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            
            # Generate initial migration
            print("Generating initial migration...")
            migrate()
            
            # Apply migrations
            print("Applying migrations...")
            upgrade()
            
            # Mark migrations as stamped
            print("Stamping migrations...")
            stamp()
            
            print("Database initialization completed successfully!")
            return 0
            
    except Exception as e:
        print(f"Error initializing database: {str(e)}", file=sys.stderr)
        return 1

def verify_db():
    """Verify database tables and connections."""
    try:
        app = create_app()
        
        with app.app_context():
            # Test database connection
            db.session.execute('SELECT 1')
            print("Database connection successful!")
            
            # Verify tables
            tables = [Inventory, Location, AuditLog]
            for table in tables:
                name = table.__tablename__
                exists = db.session.execute(
                    f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{name}')"
                ).scalar()
                if exists:
                    count = db.session.query(table).count()
                    print(f"Table '{name}' exists with {count} records")
                else:
                    print(f"Table '{name}' does not exist!")
            
            return 0
            
    except Exception as e:
        print(f"Error verifying database: {str(e)}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        sys.exit(verify_db())
    else:
        sys.exit(init_db())
