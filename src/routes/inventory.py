from flask import Blueprint, jsonify, request, current_app
from ..models import db
from ..models.inventory import Inventory
from ..models.location import Location
from ..models.audit import AuditLog
from ..utils.auth import requires_auth, requires_roles
from sqlalchemy import or_

bp = Blueprint('inventory', __name__, url_prefix='/api/inventory')

@bp.route('/', methods=['GET'])
@requires_auth
def get_inventory():
    """Get inventory items with filtering and pagination."""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25))
        asset_type = request.args.get('asset_type')
        room_type = request.args.get('room_type')
        status = request.args.get('status', 'active')
        search = request.args.get('search')
        is_loaner = request.args.get('is_loaner', type=bool)
        
        # Base query
        query = Inventory.query
        
        # Apply filters
        if asset_type:
            query = query.filter_by(asset_type=asset_type)
        if status:
            query = query.filter_by(status=status)
        if is_loaner is not None:
            query = query.filter_by(is_loaner=is_loaner)
        if room_type:
            query = query.join(Location).filter(Location.room_type == room_type)
        if search:
            search_term = f"%{search}%"
            query = query.filter(or_(
                Inventory.asset_tag.ilike(search_term),
                Inventory.serial_number.ilike(search_term),
                Inventory.model.ilike(search_term),
                Inventory.assigned_to.ilike(search_term)
            ))
            
        # Execute query with pagination
        pagination = query.order_by(Inventory.asset_tag)\
            .paginate(page=page, per_page=per_page)
        
        return jsonify({
            'items': [item.to_dict() for item in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        current_app.logger.error(f'Error getting inventory: {str(e)}')
        return jsonify({'error': 'Failed to get inventory'}), 500

@bp.route('/<asset_tag>', methods=['GET'])
@requires_auth
def get_item(asset_tag):
    """Get a specific inventory item."""
    try:
        item = Inventory.get_by_asset_tag(asset_tag)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
            
        return jsonify(item.to_dict())
        
    except Exception as e:
        current_app.logger.error(f'Error getting item {asset_tag}: {str(e)}')
        return jsonify({'error': 'Failed to get item'}), 500

@bp.route('/', methods=['POST'])
@requires_auth
@requires_roles(['admin', 'manager'])
def create_item():
    """Create a new inventory item."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['asset_tag', 'asset_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check for duplicate asset tag
        if Inventory.get_by_asset_tag(data['asset_tag']):
            return jsonify({'error': 'Asset tag already exists'}), 409
            
        # Check for duplicate serial number
        if data.get('serial_number') and Inventory.get_by_serial(data['serial_number']):
            return jsonify({'error': 'Serial number already exists'}), 409
        
        # Create item
        item = Inventory(
            asset_tag=data['asset_tag'],
            asset_type=data['asset_type'],
            manufacturer=data.get('manufacturer'),
            model=data.get('model'),
            serial_number=data.get('serial_number'),
            assigned_to=data.get('assigned_to'),
            notes=data.get('notes'),
            is_loaner=data.get('is_loaner', False)
        )
        
        # Set location if provided
        if data.get('location_id'):
            location = Location.get_by_id(data['location_id'])
            if not location:
                return jsonify({'error': 'Invalid location ID'}), 400
            item.location = location
        
        item.save()
        
        # Log the creation
        AuditLog.log_inventory_change(
            asset_tag=item.asset_tag,
            action_type='CREATE',
            field_name='item',
            old_value=None,
            new_value=f"{item.asset_tag} ({item.asset_type})",
            changed_by=request.headers.get('X-User-ID', 'system'),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        return jsonify(item.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating inventory item: {str(e)}')
        return jsonify({'error': 'Failed to create item'}), 500

@bp.route('/<asset_tag>', methods=['PUT'])
@requires_auth
@requires_roles(['admin', 'manager'])
def update_item(asset_tag):
    """Update an inventory item."""
    try:
        item = Inventory.get_by_asset_tag(asset_tag)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
            
        data = request.get_json()
        old_values = item.to_dict()
        
        # Update fields
        updatable_fields = [
            'asset_type', 'manufacturer', 'model', 'serial_number',
            'assigned_to', 'notes', 'is_loaner', 'status'
        ]
        
        for field in updatable_fields:
            if field in data:
                old_value = getattr(item, field)
                new_value = data[field]
                if old_value != new_value:
                    setattr(item, field, new_value)
                    # Log the change
                    AuditLog.log_inventory_change(
                        asset_tag=item.asset_tag,
                        action_type='UPDATE',
                        field_name=field,
                        old_value=old_value,
                        new_value=new_value,
                        changed_by=request.headers.get('X-User-ID', 'system'),
                        ip_address=request.remote_addr,
                        user_agent=request.user_agent.string
                    )
        
        # Update location if provided
        if 'location_id' in data:
            old_location = item.location
            new_location = Location.get_by_id(data['location_id']) if data['location_id'] else None
            
            if data['location_id'] and not new_location:
                return jsonify({'error': 'Invalid location ID'}), 400
                
            item.location = new_location
            # Log location change
            AuditLog.log_inventory_change(
                asset_tag=item.asset_tag,
                action_type='UPDATE',
                field_name='location',
                old_value=old_location.full_name if old_location else None,
                new_value=new_location.full_name if new_location else None,
                changed_by=request.headers.get('X-User-ID', 'system'),
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
        
        item.save()
        return jsonify(item.to_dict())
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating item {asset_tag}: {str(e)}')
        return jsonify({'error': 'Failed to update item'}), 500

@bp.route('/<asset_tag>', methods=['DELETE'])
@requires_auth
@requires_roles(['admin'])
def delete_item(asset_tag):
    """Delete an inventory item."""
    try:
        item = Inventory.get_by_asset_tag(asset_tag)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
            
        # Log the deletion
        AuditLog.log_inventory_change(
            asset_tag=item.asset_tag,
            action_type='DELETE',
            field_name='item',
            old_value=f"{item.asset_tag} ({item.asset_type})",
            new_value=None,
            changed_by=request.headers.get('X-User-ID', 'system'),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        item.delete()
        return jsonify({'message': 'Item deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting item {asset_tag}: {str(e)}')
        return jsonify({'error': 'Failed to delete item'}), 500

@bp.route('/<asset_tag>/toggle-loaner', methods=['POST'])
@requires_auth
@requires_roles(['admin', 'manager'])
def toggle_loaner(asset_tag):
    """Toggle loaner status of an item."""
    try:
        item = Inventory.get_by_asset_tag(asset_tag)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
            
        old_value = item.is_loaner
        item.toggle_loaner()
        
        # Log the change
        AuditLog.log_inventory_change(
            asset_tag=item.asset_tag,
            action_type='UPDATE',
            field_name='is_loaner',
            old_value=str(old_value),
            new_value=str(item.is_loaner),
            changed_by=request.headers.get('X-User-ID', 'system'),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        return jsonify({
            'asset_tag': asset_tag,
            'is_loaner': item.is_loaner
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error toggling loaner status for {asset_tag}: {str(e)}')
        return jsonify({'error': 'Failed to toggle loaner status'}), 500

@bp.route('/<asset_tag>/history', methods=['GET'])
@requires_auth
def get_item_history(asset_tag):
    """Get audit history for an item."""
    try:
        item = Inventory.get_by_asset_tag(asset_tag)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
            
        history = AuditLog.get_inventory_history(asset_tag)
        return jsonify([h.to_dict() for h in history])
        
    except Exception as e:
        current_app.logger.error(
            f'Error getting history for item {asset_tag}: {str(e)}'
        )
        return jsonify({'error': 'Failed to get item history'}), 500

@bp.route('/types', methods=['GET'])
@requires_auth
def get_asset_types():
    """Get all asset types."""
    try:
        types = db.session.query(Inventory.asset_type)\
            .distinct()\
            .order_by(Inventory.asset_type)\
            .all()
        return jsonify([t[0] for t in types])
        
    except Exception as e:
        current_app.logger.error(f'Error getting asset types: {str(e)}')
        return jsonify({'error': 'Failed to get asset types'}), 500
