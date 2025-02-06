"""Inventory model."""
from datetime import datetime
from .base import BaseModel, db

class Inventory(BaseModel):
    """Inventory model."""
    __tablename__ = 'inventory'

    asset_tag = db.Column(db.String(50), unique=True, nullable=False)
    asset_type = db.Column(db.String(50), nullable=False)
    manufacturer = db.Column(db.String(100))
    model = db.Column(db.String(100))
    serial_number = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(20), default='active')
    assigned_to = db.Column(db.String(100))
    date_assigned = db.Column(db.DateTime)
    date_decommissioned = db.Column(db.DateTime)
    purchase_date = db.Column(db.DateTime)
    warranty_expiry = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    is_loaner = db.Column(db.Boolean, default=False)
    current_checkout_id = db.Column(db.Integer)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))

    # Relationships
    location = db.relationship('Location', backref=db.backref('inventory_items', lazy=True))

    def assign(self, user_email):
        """Assign the item to a user."""
        self.assigned_to = user_email
        self.date_assigned = datetime.utcnow()
        self.save()

    def decommission(self):
        """Decommission the item."""
        self.status = 'decommissioned'
        self.date_decommissioned = datetime.utcnow()
        self.save()

    def to_dict(self):
        """Convert model to dictionary."""
        data = super().to_dict()
        if self.location:
            data['location'] = self.location.to_dict()
        return data
