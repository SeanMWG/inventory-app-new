from . import db, BaseModel
from sqlalchemy.orm import relationship
from sqlalchemy import UniqueConstraint

class Location(db.Model, BaseModel):
    """Model for managing locations/spaces."""
    __tablename__ = 'locations'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Location details
    site_name = db.Column(db.String(100), nullable=False)
    room_number = db.Column(db.String(50), nullable=False)
    room_name = db.Column(db.String(100), nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    
    # Optional fields
    floor = db.Column(db.String(10))
    building = db.Column(db.String(100))
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')
    
    # Relationships
    inventory_items = relationship('Inventory', back_populates='location')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('site_name', 'room_number', name='uq_location_site_room'),
    )
    
    def __init__(self, site_name, room_number, room_name, room_type, **kwargs):
        self.site_name = site_name
        self.room_number = room_number
        self.room_name = room_name
        self.room_type = room_type
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @property
    def full_name(self):
        """Get the full location name."""
        return f"{self.site_name} - {self.room_number} ({self.room_name})"
    
    def to_dict(self):
        """Convert location to dictionary."""
        return {
            'id': self.id,
            'site_name': self.site_name,
            'room_number': self.room_number,
            'room_name': self.room_name,
            'room_type': self.room_type,
            'floor': self.floor,
            'building': self.building,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_by_site_and_room(cls, site_name, room_number):
        """Get location by site name and room number."""
        return cls.query.filter_by(
            site_name=site_name,
            room_number=room_number
        ).first()
    
    @classmethod
    def get_by_type(cls, room_type):
        """Get all locations of a specific type."""
        return cls.query.filter_by(room_type=room_type).all()
    
    @classmethod
    def get_active(cls):
        """Get all active locations."""
        return cls.query.filter_by(status='active').all()
    
    def __repr__(self):
        return f"<Location {self.site_name} - {self.room_number}>"
