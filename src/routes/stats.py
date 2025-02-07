"""Statistics routes."""
from flask import Blueprint, jsonify, current_app
from sqlalchemy import func, text
from ..models.inventory import Inventory
from ..models.location import Location
from ..models.audit import AuditLog
from ..utils.auth import requires_auth

bp = Blueprint('stats', __name__, url_prefix='/api/stats')

@bp.route('', methods=['GET'])
@requires_auth
def get_stats():
    """Get inventory statistics."""
    try:
        # Get total counts
        total_items = Inventory.query.count()
        active_items = Inventory.query.filter_by(status='active').count()
        decommissioned_items = Inventory.query.filter_by(status='decommissioned').count()
        loaner_items = Inventory.query.filter_by(is_loaner=True).count()
        
        # Get counts by type using SQLAlchemy 2.0 style
        type_counts = (
            Inventory.query
            .with_entities(Inventory.asset_type, func.count(Inventory.id))
            .group_by(Inventory.asset_type)
            .all()
        )
        
        # Get counts by location using SQLAlchemy 2.0 style
        location_counts = (
            Inventory.query
            .join(Location)
            .with_entities(Location.site_name, func.count(Inventory.id))
            .group_by(Location.site_name)
            .all()
        )
        
        return jsonify({
            'total_items': total_items,
            'active_items': active_items,
            'decommissioned_items': decommissioned_items,
            'loaner_items': loaner_items,
            'by_type': dict(type_counts),
            'by_location': dict(location_counts)
        })
    except Exception as e:
        current_app.logger.error(f'Error getting stats: {str(e)}')
        return {'error': 'Internal Server Error'}, 500

@bp.route('/recent-activity', methods=['GET'])
@requires_auth
def get_recent_activity():
    """Get recent audit log entries."""
    try:
        # Get last 50 audit log entries using SQLAlchemy 2.0 style
        logs = (
            AuditLog.query
            .order_by(AuditLog.changed_at.desc())
            .limit(50)
            .all()
        )
        
        return jsonify([log.to_dict() for log in logs])
    except Exception as e:
        current_app.logger.error(f'Error getting recent activity: {str(e)}')
        return {'error': 'Internal Server Error'}, 500
