from . import db, BaseModel
from sqlalchemy.orm import relationship
from datetime import datetime

class Inventory(db.Model, BaseModel):
    """Model for managing hardware inventory items."""
    __tablename__ = 'formatted_company_inventory'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic information
    asset_tag = db.Column(db.String(50), unique=True, nullable=False)
    asset_type = db.Column(db.String(50), nullable=False)
    manufacturer = db.Column(db.String(100))
    model = db.Column(db.String(100))
    serial_number = db.Column(db.String(100), unique=True)
    
    # Status and assignment
    status = db.Column(db.String(20), default='active')
    assigned_to = db.Column(db.String(100))
    date_assigned = db.Column(db.DateTime)
    date_decommissioned = db.Column(db.DateTime)
    
    # Location relationship
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    location = relationship('Location', back_populates='inventory_items')
    
    # Loaner tracking
    is_loaner = db.Column(db.Boolean, default=False)
    current_checkout_id = db.Column(db.Integer, db.ForeignKey('loaner_checkouts.id'), nullable=True)
    
    # Additional details
    purchase_date = db.Column(db.DateTime)
    warranty_expiry = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    def __init__(self, asset_tag, asset_type, **kwargs):
        self.asset_tag = asset_tag
        self.asset_type = asset_type
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def assign(self, assigned_to):
        """Assign the item to someone."""
        self.assigned_to = assigned_to
        self.date_assigned = datetime.utcnow()
        self.save()
    
    def decommission(self):
        """Decommission the item."""
        self.status = 'decommissioned'
        self.date_decommissioned = datetime.utcnow()
        self.save()
    
    def toggle_loaner(self):
        """Toggle loaner status."""
        self.is_loaner = not self.is_loaner
        self.save()
    
    def to_dict(self):
        """Convert inventory item to dictionary."""
        return {
            'id': self.id,
            'asset_tag': self.asset_tag,
            'asset_type': self.asset_type,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'serial_number': self.serial_number,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'date_assigned': self.date_assigned.isoformat() if self.date_assigned else None,
            'date_decommissioned': self.date_decommissioned.isoformat() if self.date_decommissioned else None,
            'location': self.location.to_dict() if self.location else None,
            'is_loaner': self.is_loaner,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'warranty_expiry': self.warranty_expiry.isoformat() if self.warranty_expiry else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_by_asset_tag(cls, asset_tag):
        """Get inventory item by asset tag."""
        return cls.query.filter_by(asset_tag=asset_tag).first()
    
    @classmethod
    def get_by_serial(cls, serial_number):
        """Get inventory item by serial number."""
        return cls.query.filter_by(serial_number=serial_number).first()
    
    @classmethod
    def get_by_type(cls, asset_type):
        """Get all inventory items of a specific type."""
        return cls.query.filter_by(asset_type=asset_type).all()
    
    @classmethod
    def get_active(cls):
        """Get all active inventory items."""
        return cls.query.filter_by(status='active').all()
    
    @classmethod
    def get_loaners(cls):
        """Get all loaner items."""
        return cls.query.filter_by(is_loaner=True).all()
    
    def __repr__(self):
        return f"<Inventory {self.asset_tag}>"
