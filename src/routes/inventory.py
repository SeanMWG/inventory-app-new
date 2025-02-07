"""Inventory routes."""
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from ..models import db
from ..models.inventory import Inventory
from ..models.location import Location
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
        return jsonify({'error': 'Internal Server Error'}), 500

@bp.route('/<int:id>', methods=['GET'])
@requires_auth
def get_inventory_item(id):
    """Get inventory item by ID."""
    try:
        item = Inventory.query.get(id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        return jsonify(item.to_dict())
    except Exception as e:
        current_app.logger.error(f'Error getting inventory item {id}: {str(e)}')
        return jsonify({'error': 'Internal Server Error'}), 500

@bp.route('', methods=['POST'])
@requires_auth
@requires_roles('admin')
def create_inventory_item():
    """Create new inventory item."""
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ('asset_tag', 'asset_type', 'location_id')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Verify location exists
        location = Location.query.get(data['location_id'])
        if not location:
            return jsonify({'error': 'Location not found'}), 404
        
        # Check for duplicate asset tag
        if Inventory.query.filter_by(asset_tag=data['asset_tag']).first():
            return jsonify({'error': 'Asset tag already exists'}), 400
        
        item = Inventory(**data)
        db.session.add(item)
        db.session.commit()
        
        return jsonify(item.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating inventory item: {str(e)}')
        return jsonify({'error': 'Internal Server Error'}), 500

@bp.route('/<int:id>', methods=['PUT'])
@requires_auth
@requires_roles('admin')
def update_inventory_item(id):
    """Update inventory item."""
    try:
        item = Inventory.query.get(id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        data = request.get_json()
        
        # Check location if provided
        if 'location_id' in data:
            location = Location.query.get(data['location_id'])
            if not location:
                return jsonify({'error': 'Location not found'}), 404
        
        # Update fields
        for key, value in data.items():
            if hasattr(item, key):
                setattr(item, key, value)
        
        db.session.commit()
        return jsonify(item.to_dict())
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating inventory item {id}: {str(e)}')
        return jsonify({'error': 'Internal Server Error'}), 500

@bp.route('/<int:id>', methods=['DELETE'])
@requires_auth
@requires_roles('admin')
def delete_inventory_item(id):
    """Delete inventory item."""
    try:
        item = Inventory.query.get(id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        db.session.delete(item)
        db.session.commit()
        return jsonify({'message': 'Item deleted successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting inventory item {id}: {str(e)}')
        return jsonify({'error': 'Internal Server Error'}), 500

@bp.route('/<int:id>/toggle-loaner', methods=['POST'])
@requires_auth
@requires_roles('admin')
def toggle_loaner(id):
    """Toggle loaner status of inventory item."""
    try:
        item = Inventory.query.get(id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        item.is_loaner = not item.is_loaner
        db.session.commit()
        
        return jsonify(item.to_dict())
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error toggling loaner status for item {id}: {str(e)}')
        return jsonify({'error': 'Internal Server Error'}), 500

@bp.route('/bulk', methods=['POST'])
@requires_auth
@requires_roles('admin')
def bulk_create():
    """Bulk create inventory items."""
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({'error': 'Missing items array'}), 400
        
        created = []
        for item_data in data['items']:
            # Verify location exists
            location = Location.query.get(item_data.get('location_id'))
            if not location:
                return jsonify({'error': f'Location not found: {item_data.get("location_id")}'}), 404
            
            # Check for duplicate asset tag
            if Inventory.query.filter_by(asset_tag=item_data.get('asset_tag')).first():
                return jsonify({'error': f'Asset tag already exists: {item_data.get("asset_tag")}'}), 400
            
            item = Inventory(**item_data)
            db.session.add(item)
            created.append(item)
        
        db.session.commit()
        return jsonify({'created': [item.to_dict() for item in created]}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in bulk create: {str(e)}')
        return jsonify({'error': 'Internal Server Error'}), 500

@bp.route('/bulk', methods=['PUT'])
@requires_auth
@requires_roles('admin')
def bulk_update():
    """Bulk update inventory items."""
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({'error': 'Missing items array'}), 400
        
        updated = []
        for item_data in data['items']:
            if 'id' not in item_data:
                continue
            
            item = Inventory.query.get(item_data['id'])
            if not item:
                continue
            
            # Check location if provided
            if 'location_id' in item_data:
                location = Location.query.get(item_data['location_id'])
                if not location:
                    return jsonify({'error': f'Location not found: {item_data["location_id"]}'}), 404
            
            # Update fields
            for key, value in item_data.items():
                if hasattr(item, key) and key != 'id':
                    setattr(item, key, value)
            
            updated.append(item)
        
        db.session.commit()
        return jsonify({'updated': [item.to_dict() for item in updated]})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in bulk update: {str(e)}')
        return jsonify({'error': 'Internal Server Error'}), 500
