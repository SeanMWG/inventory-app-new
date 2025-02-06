"""Audit log model."""
from datetime import datetime
from .base import BaseModel, db

class AuditLog(BaseModel):
    """Audit log model."""
    __tablename__ = 'audit_log'

    action_type = db.Column(db.String(50), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    changed_by = db.Column(db.String(100), nullable=False)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    asset_tag = db.Column(db.String(50))
    location_id = db.Column(db.Integer)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(200))

    @classmethod
    def get_inventory_history(cls, asset_tag):
        """Get audit history for an inventory item."""
        return cls.query.filter_by(asset_tag=asset_tag).order_by(cls.changed_at.desc()).all()

    @classmethod
    def get_user_actions(cls, user_email):
        """Get audit history for a user."""
        return cls.query.filter_by(changed_by=user_email).order_by(cls.changed_at.desc()).all()

    def to_dict(self):
        """Convert model to dictionary."""
        data = super().to_dict()
        data['changed_at'] = self.changed_at.isoformat() if self.changed_at else None
        return data
