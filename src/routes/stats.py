from flask import Blueprint, jsonify, current_app
from sqlalchemy import func, desc, case
from ..models import db
from ..models.inventory import Inventory
from ..models.location import Location
from ..models.audit import AuditLog
from ..utils.auth import requires_auth
from datetime import datetime, timedelta

bp = Blueprint('stats', __name__, url_prefix='/api')

@bp.route('/stats')
@requires_auth
def get_stats():
    """Get system-wide statistics."""
    try:
        # Get inventory stats
        inventory_stats = db.session.query(
            func.count().label('total'),
            func.sum(case([(Inventory.status == 'active', 1)], else_=0)).label('active'),
            func.sum(case([(Inventory.is_loaner == True, 1)], else_=0)).label('loaners')
        ).select_from(Inventory).first()
        
        # Get location stats
        location_stats = db.session.query(
            func.count().label('total'),
            func.sum(case([(Location.status == 'active', 1)], else_=0)).label('active')
        ).select_from(Location).first()
        
        # Get pending actions (items needing attention)
        pending_actions = db.session.query(func.count()).select_from(Inventory).filter(
            (Inventory.status == 'active') &
            (
                (Inventory.warranty_expiry <= datetime.utcnow() + timedelta(days=30)) |
                ((Inventory.is_loaner == True) &
                (Inventory.current_checkout_id != None))
            )
        ).scalar()
        
        return jsonify({
            'total_items': inventory_stats.total or 0,
            'active_items': inventory_stats.active or 0,
            'total_loaners': inventory_stats.loaners or 0,
            'available_loaners': (inventory_stats.loaners or 0) - db.session.query(func.count())
                .select_from(Inventory)
                .filter(
                    Inventory.is_loaner == True,
                    Inventory.current_checkout_id != None
                ).scalar(),
            'total_locations': location_stats.total or 0,
            'active_locations': location_stats.active or 0,
            'pending_actions': pending_actions or 0
        })
        
    except Exception as e:
        current_app.logger.error(f'Error getting stats: {str(e)}')
        return jsonify({'error': 'Failed to get statistics'}), 500

@bp.route('/audit/recent')
@requires_auth
def get_recent_activity():
    """Get recent audit log entries."""
    try:
        # Get last 20 audit log entries
        entries = AuditLog.query\
            .order_by(desc(AuditLog.changed_at))\
            .limit(20)\
            .all()
            
        return jsonify([{
            'changed_at': entry.changed_at.isoformat(),
            'action_type': entry.action_type,
            'field_name': entry.field_name,
            'asset_tag': entry.asset_tag,
            'location_id': entry.location_id,
            'changed_by': entry.changed_by,
            'old_value': entry.old_value,
            'new_value': entry.new_value
        } for entry in entries])
        
    except Exception as e:
        current_app.logger.error(f'Error getting recent activity: {str(e)}')
        return jsonify({'error': 'Failed to get recent activity'}), 500

@bp.route('/stats/export')
@requires_auth
def export_stats():
    """Export system statistics."""
    try:
        # Get detailed statistics
        stats = {
            'generated_at': datetime.utcnow().isoformat(),
            'inventory': {
                'total': db.session.query(func.count()).select_from(Inventory).scalar(),
                'by_status': dict(
                    db.session.query(
                        Inventory.status,
                        func.count()
                    ).group_by(Inventory.status).all()
                ),
                'by_type': dict(
                    db.session.query(
                        Inventory.asset_type,
                        func.count()
                    ).group_by(Inventory.asset_type).all()
                ),
                'loaners': {
                    'total': db.session.query(func.count())
                        .select_from(Inventory)
                        .filter(Inventory.is_loaner == True)
                        .scalar(),
                    'checked_out': db.session.query(func.count())
                        .select_from(Inventory)
                        .filter(
                            Inventory.is_loaner == True,
                            Inventory.current_checkout_id != None
                        ).scalar()
                }
            },
            'locations': {
                'total': db.session.query(func.count()).select_from(Location).scalar(),
                'by_status': dict(
                    db.session.query(
                        Location.status,
                        func.count()
                    ).group_by(Location.status).all()
                ),
                'by_type': dict(
                    db.session.query(
                        Location.room_type,
                        func.count()
                    ).group_by(Location.room_type).all()
                ),
                'by_site': dict(
                    db.session.query(
                        Location.site_name,
                        func.count()
                    ).group_by(Location.site_name).all()
                )
            },
            'activity': {
                'last_24h': db.session.query(func.count())
                    .select_from(AuditLog)
                    .filter(AuditLog.changed_at >= datetime.utcnow() - timedelta(days=1))
                    .scalar(),
                'by_action': dict(
                    db.session.query(
                        AuditLog.action_type,
                        func.count()
                    ).group_by(AuditLog.action_type).all()
                ),
                'by_user': dict(
                    db.session.query(
                        AuditLog.changed_by,
                        func.count()
                    ).group_by(AuditLog.changed_by)
                    .order_by(desc(func.count()))
                    .limit(10)
                    .all()
                )
            }
        }
        
        return jsonify(stats)
        
    except Exception as e:
        current_app.logger.error(f'Error exporting stats: {str(e)}')
        return jsonify({'error': 'Failed to export statistics'}), 500
