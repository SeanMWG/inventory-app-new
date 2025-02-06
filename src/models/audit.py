from . import db, BaseModel
from datetime import datetime

class AuditLog(db.Model, BaseModel):
    """Model for tracking changes to inventory items and locations."""
    __tablename__ = 'audit_log'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Reference information
    asset_tag = db.Column(db.String(50))  # For inventory items
    location_id = db.Column(db.Integer)    # For locations
    
    # Change details
    action_type = db.Column(db.String(20), nullable=False)  # CREATE, UPDATE, DELETE
    field_name = db.Column(db.String(50), nullable=False)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    
    # Who made the change
    changed_by = db.Column(db.String(100), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Additional context
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(200))
    
    def __init__(self, action_type, field_name, changed_by, **kwargs):
        self.action_type = action_type
        self.field_name = field_name
        self.changed_by = changed_by
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self):
        """Convert audit log entry to dictionary."""
        return {
            'id': self.id,
            'asset_tag': self.asset_tag,
            'location_id': self.location_id,
            'action_type': self.action_type,
            'field_name': self.field_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'changed_by': self.changed_by,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }
    
    @classmethod
    def log_inventory_change(cls, asset_tag, action_type, field_name, old_value, new_value, changed_by, **kwargs):
        """Log a change to an inventory item."""
        log = cls(
            asset_tag=asset_tag,
            action_type=action_type,
            field_name=field_name,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            changed_by=changed_by,
            **kwargs
        )
        log.save()
        return log
    
    @classmethod
    def log_location_change(cls, location_id, action_type, field_name, old_value, new_value, changed_by, **kwargs):
        """Log a change to a location."""
        log = cls(
            location_id=location_id,
            action_type=action_type,
            field_name=field_name,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            changed_by=changed_by,
            **kwargs
        )
        log.save()
        return log
    
    @classmethod
    def get_inventory_history(cls, asset_tag):
        """Get audit history for an inventory item."""
        return cls.query.filter_by(asset_tag=asset_tag).order_by(cls.changed_at.desc()).all()
    
    @classmethod
    def get_location_history(cls, location_id):
        """Get audit history for a location."""
        return cls.query.filter_by(location_id=location_id).order_by(cls.changed_at.desc()).all()
    
    @classmethod
    def get_user_actions(cls, changed_by):
        """Get all actions performed by a specific user."""
        return cls.query.filter_by(changed_by=changed_by).order_by(cls.changed_at.desc()).all()
    
    def __repr__(self):
        return f"<AuditLog {self.action_type} {self.field_name} by {self.changed_by}>"
