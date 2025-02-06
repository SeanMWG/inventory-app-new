"""Base model for all database models."""
from datetime import datetime
from . import db

class BaseModel(db.Model):
    """Abstract base model class."""
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def save(self):
        """Save the model instance."""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Delete the model instance."""
        db.session.delete(self)
        db.session.commit()

    def to_dict(self):
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
