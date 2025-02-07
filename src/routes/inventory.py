"""Inventory routes."""
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from ..models.inventory import Inventory
from ..utils.auth import requires_auth, requires_roles

bp = Blueprint('inventory', __name__, url_prefix='/api/inventory')

@bp.route('', methods=['GET'])
@requires_auth
def get_inventory():
    """Get all inventory items."""
    try:
        query = Inventory.query
        
        # Apply filters
        if 'type' in request.args:
            query = query.filter(Inventory.asset_type == request.args['type'])
        if 'status' in request.args:
            query = query.filter(Inventory.status == request.args['status'])
        if 'is_loaner' in request.args:
            is_loaner = request.args['is_loaner'].lower() == 'true'
            query = query.filter(Inventory.is_loaner == is_loaner)
        
        items = query.all()
        return jsonify([item.to_dict() for item in items])
    except Exception as e:
        current_app.logger.error(f'Error getting inventory: {str(e)}')
        return {'error': 'Internal Server Error'}, 500

@bp.route('/<int:id>', methods=['GET'])
@requires_auth
def get_inventory_item(id):
    """Get inventory item by ID."""
    try:
        item = Inventory.get_by_id(id)
        if not item:
            return {'error': 'Item not found'}, 404
        return jsonify(item.to_dict())
    except Exception as e:
        current_app.logger.error(f'Error getting inventory item {id}: {str(e)}')
        return {'error': 'Internal Server Error'}, 500

@bp.route('', methods=['POST'])
@requires_auth
@requires_roles('admin')
def create_inventory_item():
    """Create new inventory item."""
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ('asset_tag', 'asset_type', 'location_id')):
            return {'error': 'Missing required fields'}, 400
        
        item = Inventory(**data)
        item.save()
        
        return jsonify(item.to_dict()), 201
    except IntegrityError:
        current_app.logger.error('Duplicate asset tag or serial number')
        return {'error': 'Duplicate asset tag or serial number'}, 500
    except Exception as e:
        current_app.logger.error(f'Error creating inventory item: {str(e)}')
        return {'error': 'Internal Server Error'}, 500

@bp.route('/<int:id>', methods=['PUT'])
@requires_auth
@requires_roles('admin')
def update_inventory_item(id):
    """Update inventory item."""
    try:
        item = Inventory.get_by_id(id)
        if not item:
            return {'error': 'Item not found'}, 404
        
        data = request.get_json()
        item.update(**data)
        
        return jsonify(item.to_dict())
    except Exception as e:
        current_app.logger.error(f'Error updating inventory item {id}: {str(e)}')
        return {'error': 'Internal Server Error'}, 500

@bp.route('/<int:id>', methods=['DELETE'])
@requires_auth
@requires_roles('admin')
def delete_inventory_item(id):
    """Delete inventory item."""
    try:
        item = Inventory.get_by_id(id)
        if not item:
            return {'error': 'Item not found'}, 404
        
        item.delete()
        return {'message': 'Item deleted successfully'}
    except Exception as e:
        current_app.logger.error(f'Error deleting inventory item {id}: {str(e)}')
        return {'error': 'Internal Server Error'}, 500

@bp.route('/<int:id>/toggle-loaner', methods=['POST'])
@requires_auth
@requires_roles('admin')
def toggle_loaner(id):
    """Toggle loaner status of inventory item."""
    try:
        item = Inventory.get_by_id(id)
        if not item:
            return {'error': 'Item not found'}, 404
        
        item.is_loaner = not item.is_loaner
        item.save()
        
        return jsonify(item.to_dict())
    except Exception as e:
        current_app.logger.error(f'Error toggling loaner status for item {id}: {str(e)}')
        return {'error': 'Internal Server Error'}, 500

@bp.route('/bulk', methods=['POST'])
@requires_auth
@requires_roles('admin')
def bulk_create():
    """Bulk create inventory items."""
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return {'error': 'Missing items array'}, 400
        
        created = []
        for item_data in data['items']:
            item = Inventory(**item_data)
            item.save()
            created.append(item.to_dict())
        
        return jsonify({'created': created}), 201
    except Exception as e:
        current_app.logger.error(f'Error in bulk create: {str(e)}')
        return {'error': 'Internal Server Error'}, 500

@bp.route('/bulk', methods=['PUT'])
@requires_auth
@requires_roles('admin')
def bulk_update():
    """Bulk update inventory items."""
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return {'error': 'Missing items array'}, 400
        
        updated = []
        for item_data in data['items']:
            if 'id' not in item_data:
                continue
            item = Inventory.get_by_id(item_data['id'])
            if item:
                item.update(**item_data)
                updated.append(item.to_dict())
        
        return jsonify({'updated': updated})
    except Exception as e:
        current_app.logger.error(f'Error in bulk update: {str(e)}')
        return {'error': 'Internal Server Error'}, 500

@bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized access."""
    return {'error': 'Unauthorized'}, 401

@bp.errorhandler(403)
def forbidden(error):
    """Handle forbidden access."""
    return {'error': 'Forbidden'}, 403
