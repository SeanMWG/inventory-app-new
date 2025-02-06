from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class BaseModel:
    """Base model class with common fields and methods."""
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def save(self):
        """Save the model instance to the database."""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Delete the model instance from the database."""
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, id):
        """Get a model instance by ID."""
        return cls.query.get(id)

    @classmethod
    def get_all(cls):
        """Get all instances of the model."""
        return cls.query.all()
