"""Location model."""
from .base import BaseModel, db

class Location(BaseModel):
    """Location model."""
    __tablename__ = 'location'

    site_name = db.Column(db.String(100), nullable=False)
    room_number = db.Column(db.String(50), nullable=False)
    room_name = db.Column(db.String(100))
    room_type = db.Column(db.String(50))
    floor = db.Column(db.String(50))
    building = db.Column(db.String(100))
    status = db.Column(db.String(20), default='active')
    description = db.Column(db.Text)

    # Relationships
    inventory_items = db.relationship(
        'Inventory',
        backref='location',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    __table_args__ = (
        db.UniqueConstraint('site_name', 'room_number', name='uix_site_room'),
    )

    @property
    def full_name(self):
        """Get full location name."""
        return f"{self.site_name} - {self.room_number} ({self.room_name})"

    def to_dict(self):
        """Convert model to dictionary."""
        data = super().to_dict()
        data['full_name'] = self.full_name
        data['inventory_count'] = self.inventory_items.count()
        return data
