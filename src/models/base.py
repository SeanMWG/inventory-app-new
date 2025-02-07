"""Base model for all database models."""
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
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
        try:
            return db.session.get(cls, id)
        except SQLAlchemyError as e:
            current_app.logger.error(f'Error getting {cls.__name__} by ID {id}: {str(e)}')
            db.session.rollback()
            raise

    @classmethod
    def get_all(cls):
        """Get all model instances."""
        try:
            return db.session.execute(db.select(cls)).scalars().all()
        except SQLAlchemyError as e:
            current_app.logger.error(f'Error getting all {cls.__name__}: {str(e)}')
            db.session.rollback()
            raise

    def save(self):
        """Save the model instance."""
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except SQLAlchemyError as e:
            current_app.logger.error(f'Error saving {self.__class__.__name__}: {str(e)}')
            db.session.rollback()
            raise

    def delete(self):
        """Delete the model instance."""
        try:
            db.session.delete(self)
            db.session.commit()
        except SQLAlchemyError as e:
            current_app.logger.error(f'Error deleting {self.__class__.__name__}: {str(e)}')
            db.session.rollback()
            raise

    def to_dict(self):
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def update(self, **kwargs):
        """Update model attributes."""
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            db.session.commit()
            return self
        except SQLAlchemyError as e:
            current_app.logger.error(f'Error updating {self.__class__.__name__}: {str(e)}')
            db.session.rollback()
            raise

    def refresh(self):
        """Refresh the model instance from the database."""
        try:
            db.session.refresh(self)
            return self
        except SQLAlchemyError as e:
            current_app.logger.error(f'Error refreshing {self.__class__.__name__}: {str(e)}')
            db.session.rollback()
            raise
