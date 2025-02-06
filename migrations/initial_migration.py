"""Initial database migration

Revision ID: 001
Revises: 
Create Date: 2025-02-06 10:09:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create locations table
    op.create_table('locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_name', sa.String(length=100), nullable=False),
        sa.Column('room_number', sa.String(length=50), nullable=False),
        sa.Column('room_name', sa.String(length=100), nullable=False),
        sa.Column('room_type', sa.String(length=50), nullable=False),
        sa.Column('floor', sa.String(length=10)),
        sa.Column('building', sa.String(length=100)),
        sa.Column('description', sa.Text()),
        sa.Column('status', sa.String(length=20), server_default='active'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('site_name', 'room_number', name='uq_location_site_room')
    )
    
    # Create loaner_checkouts table
    op.create_table('loaner_checkouts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('checkout_date', sa.DateTime(), nullable=False),
        sa.Column('expected_return_date', sa.DateTime(), nullable=False),
        sa.Column('actual_return_date', sa.DateTime()),
        sa.Column('checked_out_to', sa.String(length=100), nullable=False),
        sa.Column('checked_out_by', sa.String(length=100), nullable=False),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create inventory table
    op.create_table('formatted_company_inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_tag', sa.String(length=50), nullable=False),
        sa.Column('asset_type', sa.String(length=50), nullable=False),
        sa.Column('manufacturer', sa.String(length=100)),
        sa.Column('model', sa.String(length=100)),
        sa.Column('serial_number', sa.String(length=100)),
        sa.Column('status', sa.String(length=20), server_default='active'),
        sa.Column('assigned_to', sa.String(length=100)),
        sa.Column('date_assigned', sa.DateTime()),
        sa.Column('date_decommissioned', sa.DateTime()),
        sa.Column('location_id', sa.Integer()),
        sa.Column('is_loaner', sa.Boolean(), server_default='false'),
        sa.Column('current_checkout_id', sa.Integer()),
        sa.Column('purchase_date', sa.DateTime()),
        sa.Column('warranty_expiry', sa.DateTime()),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['current_checkout_id'], ['loaner_checkouts.id']),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asset_tag'),
        sa.UniqueConstraint('serial_number')
    )
    
    # Create audit_log table
    op.create_table('audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_tag', sa.String(length=50)),
        sa.Column('location_id', sa.Integer()),
        sa.Column('action_type', sa.String(length=20), nullable=False),
        sa.Column('field_name', sa.String(length=50), nullable=False),
        sa.Column('old_value', sa.Text()),
        sa.Column('new_value', sa.Text()),
        sa.Column('changed_by', sa.String(length=100), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ip_address', sa.String(length=45)),
        sa.Column('user_agent', sa.String(length=200)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_inventory_asset_tag', 'formatted_company_inventory', ['asset_tag'])
    op.create_index('ix_inventory_serial_number', 'formatted_company_inventory', ['serial_number'])
    op.create_index('ix_inventory_status', 'formatted_company_inventory', ['status'])
    op.create_index('ix_inventory_assigned_to', 'formatted_company_inventory', ['assigned_to'])
    op.create_index('ix_locations_site_name', 'locations', ['site_name'])
    op.create_index('ix_locations_room_type', 'locations', ['room_type'])
    op.create_index('ix_locations_status', 'locations', ['status'])
    op.create_index('ix_audit_log_asset_tag', 'audit_log', ['asset_tag'])
    op.create_index('ix_audit_log_location_id', 'audit_log', ['location_id'])
    op.create_index('ix_audit_log_changed_at', 'audit_log', ['changed_at'])

def downgrade():
    op.drop_table('audit_log')
    op.drop_table('formatted_company_inventory')
    op.drop_table('loaner_checkouts')
    op.drop_table('locations')
