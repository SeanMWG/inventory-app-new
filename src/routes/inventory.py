"""Inventory routes."""
from flask import Blueprint, request, jsonify, current_app
from ..models.inventory import Inventory
from ..utils.auth import requires_auth, requires_roles

bp = Blueprint('inventory', __name__, url_prefix='/api/inventory')

@bp.route('', methods=['GET'])
@requires_auth
def get_inventory():
    """Get all inventory items."""
    try:
        items = Inventory.get_all()
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
