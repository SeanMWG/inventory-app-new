from flask import Blueprint, jsonify, request, current_app
from ..models import db
from ..models.location import Location
from ..models.audit import AuditLog
from ..utils.auth import requires_auth, requires_roles

bp = Blueprint('location', __name__, url_prefix='/api/locations')

@bp.route('/', methods=['GET'])
@requires_auth
def get_locations():
    """Get all locations."""
    try:
        # Get query parameters
        room_type = request.args.get('room_type')
        status = request.args.get('status', 'active')
        
        # Base query
        query = Location.query
        
        # Apply filters
        if room_type:
            query = query.filter_by(room_type=room_type)
        if status:
            query = query.filter_by(status=status)
            
        # Execute query
        locations = query.order_by(Location.site_name, Location.room_number).all()
        
        return jsonify([loc.to_dict() for loc in locations])
        
    except Exception as e:
        current_app.logger.error(f'Error getting locations: {str(e)}')
        return jsonify({'error': 'Failed to get locations'}), 500

@bp.route('/<int:location_id>', methods=['GET'])
@requires_auth
def get_location(location_id):
    """Get a specific location."""
    try:
        location = Location.get_by_id(location_id)
        if not location:
            return jsonify({'error': 'Location not found'}), 404
            
        return jsonify(location.to_dict())
        
    except Exception as e:
        current_app.logger.error(f'Error getting location {location_id}: {str(e)}')
        return jsonify({'error': 'Failed to get location'}), 500

@bp.route('/', methods=['POST'])
@requires_auth
@requires_roles(['admin', 'manager'])
def create_location():
    """Create a new location."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['site_name', 'room_number', 'room_name', 'room_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check for duplicate
        existing = Location.get_by_site_and_room(
            data['site_name'],
            data['room_number']
        )
        if existing:
            return jsonify({'error': 'Location already exists'}), 409
        
        # Create location
        location = Location(
            site_name=data['site_name'],
            room_number=data['room_number'],
            room_name=data['room_name'],
            room_type=data['room_type'],
            floor=data.get('floor'),
            building=data.get('building'),
            description=data.get('description')
        )
        location.save()
        
        # Log the creation
        AuditLog.log_location_change(
            location_id=location.id,
            action_type='CREATE',
            field_name='location',
            old_value=None,
            new_value=location.full_name,
            changed_by=request.headers.get('X-User-ID', 'system'),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        return jsonify(location.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating location: {str(e)}')
        return jsonify({'error': 'Failed to create location'}), 500

@bp.route('/<int:location_id>', methods=['PUT'])
@requires_auth
@requires_roles(['admin', 'manager'])
def update_location(location_id):
    """Update a location."""
    try:
        location = Location.get_by_id(location_id)
        if not location:
            return jsonify({'error': 'Location not found'}), 404
            
        data = request.get_json()
        old_values = location.to_dict()
        
        # Update fields
        for field in ['site_name', 'room_number', 'room_name', 'room_type',
                     'floor', 'building', 'description', 'status']:
            if field in data:
                old_value = getattr(location, field)
                new_value = data[field]
                if old_value != new_value:
                    setattr(location, field, new_value)
                    # Log the change
                    AuditLog.log_location_change(
                        location_id=location.id,
                        action_type='UPDATE',
                        field_name=field,
                        old_value=old_value,
                        new_value=new_value,
                        changed_by=request.headers.get('X-User-ID', 'system'),
                        ip_address=request.remote_addr,
                        user_agent=request.user_agent.string
                    )
        
        location.save()
        return jsonify(location.to_dict())
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating location {location_id}: {str(e)}')
        return jsonify({'error': 'Failed to update location'}), 500

@bp.route('/<int:location_id>', methods=['DELETE'])
@requires_auth
@requires_roles(['admin'])
def delete_location(location_id):
    """Delete a location."""
    try:
        location = Location.get_by_id(location_id)
        if not location:
            return jsonify({'error': 'Location not found'}), 404
            
        # Check if location has inventory items
        if location.inventory_items:
            return jsonify({
                'error': 'Cannot delete location with assigned inventory items'
            }), 400
            
        # Log the deletion
        AuditLog.log_location_change(
            location_id=location.id,
            action_type='DELETE',
            field_name='location',
            old_value=location.full_name,
            new_value=None,
            changed_by=request.headers.get('X-User-ID', 'system'),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        location.delete()
        return jsonify({'message': 'Location deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting location {location_id}: {str(e)}')
        return jsonify({'error': 'Failed to delete location'}), 500

@bp.route('/types', methods=['GET'])
@requires_auth
def get_room_types():
    """Get all room types."""
    try:
        types = db.session.query(Location.room_type)\
            .distinct()\
            .order_by(Location.room_type)\
            .all()
        return jsonify([t[0] for t in types])
        
    except Exception as e:
        current_app.logger.error(f'Error getting room types: {str(e)}')
        return jsonify({'error': 'Failed to get room types'}), 500

@bp.route('/<int:location_id>/history', methods=['GET'])
@requires_auth
def get_location_history(location_id):
    """Get audit history for a location."""
    try:
        location = Location.get_by_id(location_id)
        if not location:
            return jsonify({'error': 'Location not found'}), 404
            
        history = AuditLog.get_location_history(location_id)
        return jsonify([h.to_dict() for h in history])
        
    except Exception as e:
        current_app.logger.error(
            f'Error getting history for location {location_id}: {str(e)}'
        )
        return jsonify({'error': 'Failed to get location history'}), 500
