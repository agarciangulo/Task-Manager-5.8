"""
Centralized SQLAlchemy models for the application.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

class TrackedActivity(Base):
    """
    Model for tracking recurring activities identified by the system.
    """
    __tablename__ = 'tracked_activities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    normalized_name = Column(String(255), nullable=False)
    instance_count = Column(Integer, nullable=False, default=1)
    last_instance_date = Column(DateTime(timezone=True), nullable=False)
    representative_tasks = Column(JSONB, default=list)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Ensure unique combination of user and activity name
    __table_args__ = (
        UniqueConstraint('user_id', 'normalized_name', name='uq_user_activity'),
    )
    
    def __repr__(self):
        return f"<TrackedActivity(id={self.id}, user_id='{self.user_id}', name='{self.normalized_name}', count={self.instance_count})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'normalized_name': self.normalized_name,
            'instance_count': self.instance_count,
            'last_instance_date': self.last_instance_date.isoformat() if self.last_instance_date else None,
            'representative_tasks': self.representative_tasks or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 