"""Base model for all database models."""
from datetime import datetime
from . import db

class BaseModel(db.Model):
    """Abstract base model class."""
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_by_id(cls, id):
        """Get model instance by ID."""
        return db.session.get(cls, id)

    @classmethod
    def get_all(cls):
        """Get all model instances."""
        return db.session.execute(db.select(cls)).scalars().all()

    def save(self):
        """Save the model instance."""
        db.session.add(self)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def delete(self):
        """Delete the model instance."""
        db.session.delete(self)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def to_dict(self):
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def update(self, **kwargs):
        """Update model attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()

    def refresh(self):
        """Refresh the model instance from the database."""
        db.session.refresh(self)
