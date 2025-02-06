#!/usr/bin/env python3
"""Migrate data from old database to new schema."""
import os
import sys
import pyodbc
from datetime import datetime
from sqlalchemy import create_engine, text
from src.app import create_app, db
from src.models.inventory import Inventory
from src.models.location import Location
from src.models.audit import AuditLog

def get_old_db_connection():
    """Get connection to old database."""
    connection_string = os.getenv('OLD_DATABASE_URL')
    if not connection_string:
        raise ValueError("OLD_DATABASE_URL environment variable not set")
    return pyodbc.connect(connection_string)

def migrate_locations(old_conn, new_session):
    """Migrate location data."""
    print("Migrating locations...")
    
    # Get unique locations from old database
    cursor = old_conn.cursor()
    cursor.execute("""
        SELECT DISTINCT
            site_name,
            room_number,
            room_name,
            room_type,
            floor,
            building
        FROM formatted_company_inventory
        WHERE site_name IS NOT NULL
          AND room_number IS NOT NULL
    """)
    
    location_map = {}  # Map old location info to new IDs
    count = 0
    
    for row in cursor.fetchall():
        site_name = row.site_name.strip() if row.site_name else None
        room_number = row.room_number.strip() if row.room_number else None
        
        if not site_name or not room_number:
            continue
            
        # Create new location
        location = Location(
            site_name=site_name,
            room_number=room_number,
            room_name=row.room_name.strip() if row.room_name else room_number,
            room_type=row.room_type.strip() if row.room_type else 'Office',
            floor=row.floor.strip() if row.floor else None,
            building=row.building.strip() if row.building else None
        )
        new_session.add(location)
        new_session.flush()  # Get ID without committing
        
        # Store mapping
        location_map[f"{site_name}|{room_number}"] = location.id
        count += 1
        
        if count % 100 == 0:
            print(f"Processed {count} locations...")
    
    new_session.commit()
    print(f"Migrated {count} locations")
    return location_map

def migrate_inventory(old_conn, new_session, location_map):
    """Migrate inventory data."""
    print("Migrating inventory items...")
    
    cursor = old_conn.cursor()
    cursor.execute("""
        SELECT *
        FROM formatted_company_inventory
        ORDER BY asset_tag
    """)
    
    columns = [column[0] for column in cursor.description]
    count = 0
    
    for row in cursor.fetchall():
        data = dict(zip(columns, row))
        
        # Get location ID from mapping
        location_id = None
        if data.get('site_name') and data.get('room_number'):
            location_key = f"{data['site_name'].strip()}|{data['room_number'].strip()}"
            location_id = location_map.get(location_key)
        
        # Create new inventory item
        item = Inventory(
            asset_tag=data['asset_tag'].strip(),
            asset_type=data['asset_type'].strip() if data['asset_type'] else 'Unknown',
            manufacturer=data['manufacturer'].strip() if data['manufacturer'] else None,
            model=data['model'].strip() if data['model'] else None,
            serial_number=data['serial_number'].strip() if data['serial_number'] else None,
            status=data['status'].strip() if data['status'] else 'active',
            assigned_to=data['assigned_to'].strip() if data['assigned_to'] else None,
            location_id=location_id,
            is_loaner=bool(data.get('is_loaner')),
            notes=data['notes'].strip() if data.get('notes') else None
        )
        
        # Handle dates
        for date_field in ['date_assigned', 'date_decommissioned', 'purchase_date', 'warranty_expiry']:
            if data.get(date_field):
                try:
                    setattr(item, date_field, datetime.strptime(data[date_field], '%Y-%m-%d'))
                except (ValueError, TypeError):
                    pass
        
        new_session.add(item)
        count += 1
        
        if count % 100 == 0:
            print(f"Processed {count} items...")
            new_session.commit()  # Commit in batches
    
    new_session.commit()
    print(f"Migrated {count} inventory items")

def migrate_audit_log(old_conn, new_session):
    """Migrate audit log data."""
    print("Migrating audit log...")
    
    cursor = old_conn.cursor()
    cursor.execute("""
        SELECT *
        FROM audit_log
        ORDER BY changed_at
    """)
    
    columns = [column[0] for column in cursor.description]
    count = 0
    
    for row in cursor.fetchall():
        data = dict(zip(columns, row))
        
        entry = AuditLog(
            action_type=data['action_type'].strip(),
            field_name=data['field_name'].strip(),
            changed_by=data['changed_by'].strip(),
            old_value=data['old_value'].strip() if data['old_value'] else None,
            new_value=data['new_value'].strip() if data['new_value'] else None,
            asset_tag=data['asset_tag'].strip() if data.get('asset_tag') else None,
            location_id=data.get('location_id'),
            changed_at=datetime.strptime(data['changed_at'], '%Y-%m-%d %H:%M:%S')
                if data['changed_at'] else datetime.utcnow(),
            ip_address=data.get('ip_address'),
            user_agent=data.get('user_agent')
        )
        
        new_session.add(entry)
        count += 1
        
        if count % 1000 == 0:
            print(f"Processed {count} audit entries...")
            new_session.commit()  # Commit in batches
    
    new_session.commit()
    print(f"Migrated {count} audit log entries")

def main():
    """Main migration function."""
    try:
        print("Starting data migration...")
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            # Connect to old database
            old_conn = get_old_db_connection()
            
            # Start migration
            db.session.execute(text('BEGIN'))
            try:
                # Migrate in order: locations -> inventory -> audit
                location_map = migrate_locations(old_conn, db.session)
                migrate_inventory(old_conn, db.session, location_map)
                migrate_audit_log(old_conn, db.session)
                
                print("Migration completed successfully!")
                return 0
                
            except Exception as e:
                db.session.rollback()
                print(f"Error during migration: {str(e)}", file=sys.stderr)
                return 1
            
            finally:
                old_conn.close()
                
    except Exception as e:
        print(f"Error setting up migration: {str(e)}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
