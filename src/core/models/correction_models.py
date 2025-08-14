"""
Simplified database models for the correction handler system.
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

Base = declarative_base()


class TaskCorrectionLog(Base):
    """Simplified model for tracking correlation between notification emails and tasks."""
    __tablename__ = 'task_correction_logs'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    correlation_id = Column(String(255), unique=True, nullable=False, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    task_ids = Column(JSON, nullable=False)  # List of task IDs from the original email
    email_subject = Column(String(500))
    email_sent_at = Column(DateTime, default=func.now())
    status = Column(String(50), default='pending', index=True)  # pending, processed, failed
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<TaskCorrectionLog(correlation_id='{self.correlation_id}', user_email='{self.user_email}', status='{self.status}')>"


class TaskCorrection(Base):
    """Model for tracking individual task corrections."""
    __tablename__ = 'task_corrections'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    correction_log_id = Column(String(36), nullable=False, index=True)
    task_id = Column(String(255), nullable=False, index=True)
    correction_type = Column(String(50), nullable=False)  # update, delete
    original_data = Column(JSON, nullable=False)  # Snapshot of original task
    corrected_data = Column(JSON, nullable=False)  # What was changed
    processed_at = Column(DateTime, default=func.now())
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<TaskCorrection(task_id='{self.task_id}', type='{self.correction_type}', success={self.success})>" 