"""
SQLAlchemy models for email archive database with hot and cold storage.
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, BigInteger, JSON, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

Base = declarative_base()


class HotEmail(Base):
    """Model for hot storage emails (recent, frequently accessed)."""
    __tablename__ = 'hot_emails'
    __table_args__ = {'schema': 'email_archive'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(String(255), unique=True, nullable=False, index=True)
    thread_id = Column(String(255), index=True)
    sender_email = Column(String(255), nullable=False, index=True)
    sender_name = Column(String(255))
    recipient_email = Column(String(255), nullable=False)
    subject = Column(Text, index=True)
    body_text = Column(Text, index=True)
    body_preview = Column(Text, index=True)
    body_storage_key = Column(String(255))
    has_full_body = Column(Boolean, default=False)
    body_html = Column(Text)
    received_date = Column(DateTime(timezone=True), nullable=False, index=True)
    processed_date = Column(DateTime(timezone=True), default=func.now())
    user_id = Column(String(255), index=True)
    task_database_id = Column(String(255))
    email_size_bytes = Column(Integer)
    has_attachments = Column(Boolean, default=False)
    attachment_count = Column(Integer, default=0)
    priority = Column(String(20), default='normal')
    labels = Column(ARRAY(String))
    is_read = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    processing_status = Column(String(50), default='pending', index=True)
    processing_metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'id': str(self.id),
            'message_id': self.message_id,
            'thread_id': self.thread_id,
            'sender_email': self.sender_email,
            'sender_name': self.sender_name,
            'recipient_email': self.recipient_email,
            'subject': self.subject,
            'body_text': self.body_text,
            'body_preview': self.body_preview,
            'body_storage_key': self.body_storage_key,
            'has_full_body': self.has_full_body,
            'body_html': self.body_html,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'processed_date': self.processed_date.isoformat() if self.processed_date else None,
            'user_id': self.user_id,
            'task_database_id': self.task_database_id,
            'email_size_bytes': self.email_size_bytes,
            'has_attachments': self.has_attachments,
            'attachment_count': self.attachment_count,
            'priority': self.priority,
            'labels': self.labels,
            'is_read': self.is_read,
            'is_archived': self.is_archived,
            'processing_status': self.processing_status,
            'processing_metadata': self.processing_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ColdEmail(Base):
    """Model for cold storage emails (older, less frequently accessed)."""
    __tablename__ = 'cold_emails'
    __table_args__ = {'schema': 'email_archive'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(String(255), unique=True, nullable=False, index=True)
    thread_id = Column(String(255), index=True)
    sender_email = Column(String(255), nullable=False, index=True)
    sender_name = Column(String(255))
    recipient_email = Column(String(255), nullable=False)
    subject = Column(Text, index=True)
    body_text = Column(Text, index=True)
    body_preview = Column(Text, index=True)
    body_storage_key = Column(String(255))
    has_full_body = Column(Boolean, default=False)
    body_html = Column(Text)
    received_date = Column(DateTime(timezone=True), nullable=False, index=True)
    processed_date = Column(DateTime(timezone=True), default=func.now())
    user_id = Column(String(255), index=True)
    task_database_id = Column(String(255))
    email_size_bytes = Column(Integer)
    has_attachments = Column(Boolean, default=False)
    attachment_count = Column(Integer, default=0)
    priority = Column(String(20), default='normal')
    labels = Column(ARRAY(String))
    is_read = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    processing_status = Column(String(50), default='pending', index=True)
    processing_metadata = Column(JSONB)
    archived_date = Column(DateTime(timezone=True), default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'id': str(self.id),
            'message_id': self.message_id,
            'thread_id': self.thread_id,
            'sender_email': self.sender_email,
            'sender_name': self.sender_name,
            'recipient_email': self.recipient_email,
            'subject': self.subject,
            'body_text': self.body_text,
            'body_preview': self.body_preview,
            'body_storage_key': self.body_storage_key,
            'has_full_body': self.has_full_body,
            'body_html': self.body_html,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'processed_date': self.processed_date.isoformat() if self.processed_date else None,
            'user_id': self.user_id,
            'task_database_id': self.task_database_id,
            'email_size_bytes': self.email_size_bytes,
            'has_attachments': self.has_attachments,
            'attachment_count': self.attachment_count,
            'priority': self.priority,
            'labels': self.labels,
            'is_read': self.is_read,
            'is_archived': self.is_archived,
            'processing_status': self.processing_status,
            'processing_metadata': self.processing_metadata,
            'archived_date': self.archived_date.isoformat() if self.archived_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ProcessingLog(Base):
    """Model for email processing logs."""
    __tablename__ = 'processing_logs'
    __table_args__ = (
        CheckConstraint("storage_type IN ('hot', 'cold')", name='valid_log_storage_type'),
        {'schema': 'email_archive'}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    storage_type = Column(String(20), nullable=False, index=True)
    processing_step = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    error_message = Column(Text)
    processing_time_ms = Column(Integer)
    processing_metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=func.now(), index=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'id': str(self.id),
            'email_id': str(self.email_id),
            'storage_type': self.storage_type,
            'processing_step': self.processing_step,
            'status': self.status,
            'error_message': self.error_message,
            'processing_time_ms': self.processing_time_ms,
            'processing_metadata': self.processing_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class StorageStats(Base):
    """Model for storage statistics."""
    __tablename__ = 'storage_stats'
    __table_args__ = (
        CheckConstraint("storage_type IN ('hot', 'cold')", name='valid_stats_storage_type'),
        {'schema': 'email_archive'}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    storage_type = Column(String(20), nullable=False, unique=True, index=True)
    total_emails = Column(Integer, default=0)
    total_size_bytes = Column(BigInteger, default=0)
    total_attachments = Column(Integer, default=0)
    oldest_email_date = Column(DateTime(timezone=True))
    newest_email_date = Column(DateTime(timezone=True))
    last_updated = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'id': str(self.id),
            'storage_type': self.storage_type,
            'total_emails': self.total_emails,
            'total_size_bytes': self.total_size_bytes,
            'total_attachments': self.total_attachments,
            'oldest_email_date': self.oldest_email_date.isoformat() if self.oldest_email_date else None,
            'newest_email_date': self.newest_email_date.isoformat() if self.newest_email_date else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        } 