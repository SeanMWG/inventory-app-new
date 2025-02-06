"""Location routes."""
from flask import Blueprint, request, jsonify, current_app
from ..models.location import Location
from ..utils.auth import requires_auth, requires_roles

bp = Blueprint('location', __name__, url_prefix='/api/locations')

@bp.route('', methods=['GET'])
@requires_auth
def get_locations():
    """Get all locations."""
    try:
        locations = Location.get_all()
        return jsonify([loc.to_dict() for loc in locations])
    except Exception as e:
        current_app.logger.error(f'Error getting locations: {str(e)}')
        return {'error': 'Internal Server Error'}, 500

@bp.route('/<int:id>', methods=['GET'])
@requires_auth
def get_location(id):
    """Get location by ID."""
    try:
        location = Location.get_by_id(id)
        if not location:
            return {'error': 'Location not found'}, 404
        return jsonify(location.to_dict())
    except Exception as e:
        current_app.logger.error(f'Error getting location {id}: {str(e)}')
        return {'error': 'Internal Server Error'}, 500

@bp.route('', methods=['POST'])
@requires_auth
@requires_roles('admin')
def create_location():
    """Create new location."""
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ('site_name', 'room_number')):
            return {'error': 'Missing required fields'}, 400
        
        location = Location(**data)
        location.save()
        
        return jsonify(location.to_dict()), 201
    except Exception as e:
        current_app.logger.error(f'Error creating location: {str(e)}')
        return {'error': 'Internal Server Error'}, 500

@bp.route('/<int:id>', methods=['PUT'])
@requires_auth
@requires_roles('admin')
def update_location(id):
    """Update location."""
    try:
        location = Location.get_by_id(id)
        if not location:
            return {'error': 'Location not found'}, 404
        
        data = request.get_json()
        location.update(**data)
        
        return jsonify(location.to_dict())
    except Exception as e:
        current_app.logger.error(f'Error updating location {id}: {str(e)}')
        return {'error': 'Internal Server Error'}, 500

@bp.route('/<int:id>', methods=['DELETE'])
@requires_auth
@requires_roles('admin')
def delete_location(id):
    """Delete location."""
    try:
        location = Location.get_by_id(id)
        if not location:
            return {'error': 'Location not found'}, 404
        
        location.delete()
        return {'message': 'Location deleted successfully'}
    except Exception as e:
        current_app.logger.error(f'Error deleting location {id}: {str(e)}')
        return {'error': 'Internal Server Error'}, 500
