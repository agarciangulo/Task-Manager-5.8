"""
Email Archive Service for managing hot and cold storage of emails.
"""
import os
import hashlib
import gzip
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from sqlalchemy import create_engine, text, and_, or_, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import uuid

from core.models.email_archive import (
    Base, HotEmail, ColdEmail, ProcessingLog, StorageStats
)
from core.logging_config import get_logger

logger = get_logger(__name__)


class EmailArchiveService:
    """Service for managing email archiving with hot and cold storage."""
    
    def __init__(self, database_url: Optional[str] = None, storage_path: Optional[str] = None):
        """
        Initialize the email archive service.
        
        Args:
            database_url: PostgreSQL database URL. If None, uses environment variable.
            storage_path: Path for storing full email bodies. If None, uses default.
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("Database URL is required. Set DATABASE_URL environment variable.")
        
        # Initialize file storage
        self.storage_path = storage_path or os.getenv('EMAIL_STORAGE_PATH', './email_storage')
        self._ensure_storage_directory()
        
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
        
        # Initialize storage statistics
        self._initialize_storage_stats()
    
    def _ensure_storage_directory(self):
        """Ensure the email storage directory exists."""
        try:
            os.makedirs(self.storage_path, exist_ok=True)
            logger.info(f"Email storage directory ready: {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to create storage directory: {str(e)}")
            raise
    
    def _store_full_email_body(self, email_id: str, body_text: str) -> Optional[str]:
        """
        Store full email body in compressed file.
        
        Args:
            email_id: Email ID
            body_text: Full email body text
            
        Returns:
            Optional[str]: Storage key if successful, None otherwise
        """
        try:
            # Create storage key
            storage_key = f"emails/{email_id}.txt.gz"
            file_path = os.path.join(self.storage_path, storage_key)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Compress and store
            compressed_data = gzip.compress(body_text.encode('utf-8'))
            
            with open(file_path, 'wb') as f:
                f.write(compressed_data)
            
            logger.info(f"Stored full email body: {file_path}")
            return storage_key
            
        except Exception as e:
            logger.error(f"Failed to store full email body: {str(e)}")
            return None
    
    def _get_full_email_body(self, storage_key: str) -> Optional[str]:
        """
        Retrieve full email body from compressed file.
        
        Args:
            storage_key: Storage key for the email body
            
        Returns:
            Optional[str]: Email body text if successful, None otherwise
        """
        try:
            file_path = os.path.join(self.storage_path, storage_key)
            
            if not os.path.exists(file_path):
                logger.warning(f"Email body file not found: {file_path}")
                return None
            
            with open(file_path, 'rb') as f:
                compressed_data = f.read()
            
            body_text = gzip.decompress(compressed_data).decode('utf-8')
            return body_text
            
        except Exception as e:
            logger.error(f"Failed to retrieve full email body: {str(e)}")
            return None
    
    def _get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def _initialize_storage_stats(self):
        """Initialize storage statistics if they don't exist."""
        try:
            with self._get_session() as session:
                # Check if stats exist
                hot_stats = session.query(StorageStats).filter_by(storage_type='hot').first()
                cold_stats = session.query(StorageStats).filter_by(storage_type='cold').first()
                
                if not hot_stats:
                    hot_stats = StorageStats(storage_type='hot')
                    session.add(hot_stats)
                
                if not cold_stats:
                    cold_stats = StorageStats(storage_type='cold')
                    session.add(cold_stats)
                
                session.commit()
                logger.info("Storage statistics initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize storage stats: {str(e)}")
    
    def store_email(self, email_data: Dict[str, Any], storage_type: str = 'hot') -> str:
        """
        Store an email in the archive using hybrid storage.
        
        Args:
            email_data: Dictionary containing email data
            storage_type: 'hot' or 'cold'
            
        Returns:
            str: Email ID
        """
        start_time = datetime.now()
        PREVIEW_LENGTH = 250  # Small preview for database
        
        try:
            with self._get_session() as session:
                # Extract full body text
                full_body = email_data.get('body_text', '')
                
                # Create preview for database
                if len(full_body) > PREVIEW_LENGTH:
                    body_preview = full_body[:PREVIEW_LENGTH] + "..."
                    has_full_body = True
                else:
                    body_preview = full_body
                    has_full_body = False
                
                # Create email record
                if storage_type == 'hot':
                    email = HotEmail(**email_data)
                else:
                    email = ColdEmail(**email_data)
                
                # Set preview and storage flags
                email.body_preview = body_preview
                email.has_full_body = has_full_body
                
                session.add(email)
                session.flush()  # Get the ID
                email_id = str(email.id)
                
                # Store full body in file if needed
                storage_key = None
                if has_full_body and full_body:
                    storage_key = self._store_full_email_body(email_id, full_body)
                    if storage_key:
                        email.body_storage_key = storage_key
                        session.commit()
                
                # Log processing
                processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
                log = ProcessingLog(
                    email_id=email.id,
                    storage_type=storage_type,
                    processing_step='store_email',
                    status='success',
                    processing_time_ms=processing_time,
                    metadata={
                        'email_size': email_data.get('email_size_bytes', 0),
                        'body_length': len(full_body),
                        'preview_length': len(body_preview),
                        'has_full_body': has_full_body,
                        'storage_key': storage_key
                    }
                )
                session.add(log)
                
                session.commit()
                
                # Update storage statistics
                self._update_storage_stats(session, storage_type)
                
                logger.info(f"Stored email {email_id} in {storage_type} storage (preview: {len(body_preview)} chars, full body: {has_full_body})")
                return email_id
                
        except Exception as e:
            logger.error(f"Failed to store email: {str(e)}")
            raise
    
    def get_email(self, email_id: str, storage_type: str = 'hot') -> Optional[Dict[str, Any]]:
        """
        Retrieve an email from the archive.
        
        Args:
            email_id: Email ID
            storage_type: 'hot' or 'cold'
            
        Returns:
            Optional[Dict]: Email data or None if not found
        """
        try:
            with self._get_session() as session:
                if storage_type == 'hot':
                    email = session.query(HotEmail).filter(HotEmail.id == email_id).first()
                else:
                    email = session.query(ColdEmail).filter(ColdEmail.id == email_id).first()
                
                if email:
                    email_dict = email.to_dict()
                    
                    # Get full body if available
                    if email.has_full_body and email.body_storage_key:
                        full_body = self._get_full_email_body(email.body_storage_key)
                        if full_body:
                            email_dict['body_text'] = full_body
                        else:
                            # Fallback to preview if file not found
                            email_dict['body_text'] = email.body_preview
                    else:
                        # Use preview for short emails
                        email_dict['body_text'] = email.body_preview
                    
                    return email_dict
                return None
                
        except Exception as e:
            logger.error(f"Failed to get email {email_id}: {str(e)}")
            return None
    
    def search_emails(self, 
                     query: str = None,
                     user_id: str = None,
                     sender_email: str = None,
                     date_from: datetime = None,
                     date_to: datetime = None,
                     storage_type: str = 'hot',
                     limit: int = 100,
                     offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search emails in the archive.
        
        Args:
            query: Text search query
            user_id: Filter by user ID
            sender_email: Filter by sender email
            date_from: Start date filter
            date_to: End date filter
            storage_type: 'hot' or 'cold'
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Dict]: List of email data
        """
        try:
            with self._get_session() as session:
                if storage_type == 'hot':
                    query_obj = session.query(HotEmail)
                else:
                    query_obj = session.query(ColdEmail)
                
                # Apply filters
                if user_id:
                    query_obj = query_obj.filter(HotEmail.user_id == user_id)
                
                if sender_email:
                    query_obj = query_obj.filter(HotEmail.sender_email == sender_email)
                
                if date_from:
                    query_obj = query_obj.filter(HotEmail.received_date >= date_from)
                
                if date_to:
                    query_obj = query_obj.filter(HotEmail.received_date <= date_to)
                
                if query:
                    # Full-text search on subject and body preview
                    search_filter = or_(
                        text("to_tsvector('english', subject) @@ plainto_tsquery('english', :query)"),
                        text("to_tsvector('english', body_preview) @@ plainto_tsquery('english', :query)")
                    )
                    query_obj = query_obj.filter(search_filter).params(query=query)
                
                # Order by received date (newest first)
                query_obj = query_obj.order_by(HotEmail.received_date.desc())
                
                # Apply pagination
                emails = query_obj.offset(offset).limit(limit).all()
                
                return [email.to_dict() for email in emails]
                
        except Exception as e:
            logger.error(f"Failed to search emails: {str(e)}")
            return []
    
    def move_to_cold_storage(self, days_threshold: int = 30) -> int:
        """
        Move emails from hot to cold storage based on age.
        
        Args:
            days_threshold: Number of days after which emails are moved to cold storage
            
        Returns:
            int: Number of emails moved
        """
        try:
            with self._get_session() as session:
                # Use the PostgreSQL function to move emails
                result = session.execute(
                    text("SELECT email_archive.move_to_cold_storage(:days_threshold)"),
                    {"days_threshold": days_threshold}
                )
                moved_count = result.scalar()
                
                # Update storage statistics
                self._update_storage_stats(session, 'hot')
                self._update_storage_stats(session, 'cold')
                
                session.commit()
                
                logger.info(f"Moved {moved_count} emails to cold storage")
                return moved_count
                
        except Exception as e:
            logger.error(f"Failed to move emails to cold storage: {str(e)}")
            return 0
    
    def _update_storage_stats(self, session: Session, storage_type: str):
        """Update storage statistics."""
        try:
            if storage_type == 'hot':
                table = HotEmail
            else:
                table = ColdEmail
            
            # Get counts and sizes
            total_emails = session.query(table).count()
            total_size = session.query(func.sum(table.email_size_bytes)).filter(
                table.email_size_bytes.isnot(None)
            ).scalar() or 0
            
            # Get date range
            oldest = session.query(table.received_date).order_by(table.received_date.asc()).first()
            newest = session.query(table.received_date).order_by(table.received_date.desc()).first()
            
            # Update stats
            stats = session.query(StorageStats).filter_by(storage_type=storage_type).first()
            if stats:
                stats.total_emails = total_emails
                stats.total_size_bytes = total_size
                stats.oldest_email_date = oldest[0] if oldest else None
                stats.newest_email_date = newest[0] if newest else None
                stats.last_updated = datetime.now()
                
        except Exception as e:
            logger.error(f"Failed to update storage stats: {str(e)}")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            with self._get_session() as session:
                stats = session.query(StorageStats).all()
                return {
                    stat.storage_type: stat.to_dict() for stat in stats
                }
                
        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return {}
    
    def cleanup_old_emails(self, days_threshold: int = 365) -> int:
        """
        Permanently delete emails older than the threshold from cold storage.
        Use with caution!
        
        Args:
            days_threshold: Number of days after which emails are deleted
            
        Returns:
            int: Number of emails deleted
        """
        try:
            with self._get_session() as session:
                cutoff_date = datetime.now() - timedelta(days=days_threshold)
                
                # Count emails to be deleted
                count = session.query(ColdEmail).filter(
                    ColdEmail.received_date < cutoff_date
                ).count()
                
                # Delete emails
                session.query(ColdEmail).filter(
                    ColdEmail.received_date < cutoff_date
                ).delete()
                
                session.commit()
                
                logger.warning(f"Deleted {count} emails older than {days_threshold} days from cold storage")
                return count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old emails: {str(e)}")
            return 0

    def update_email(self, email_id: str, update_data: Dict[str, Any], storage_type: str = 'hot') -> bool:
        """
        Update an email record in the archive.
        
        Args:
            email_id: Email ID to update
            update_data: Dictionary containing fields to update
            storage_type: 'hot' or 'cold'
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_session() as session:
                if storage_type == 'hot':
                    email = session.query(HotEmail).filter(HotEmail.id == email_id).first()
                else:
                    email = session.query(ColdEmail).filter(ColdEmail.id == email_id).first()
                
                if not email:
                    logger.warning(f"Email {email_id} not found for update")
                    return False
                
                # Update fields
                for key, value in update_data.items():
                    if hasattr(email, key):
                        setattr(email, key, value)
                
                session.commit()
                logger.info(f"Updated email {email_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update email {email_id}: {str(e)}")
            return False

    def update_email_status(self, email_id: str, status: str, metadata: Dict[str, Any] = None, storage_type: str = 'hot') -> bool:
        """
        Update the processing status of an email.
        
        Args:
            email_id: Email ID to update
            status: New processing status
            metadata: Optional metadata to update
            storage_type: 'hot' or 'cold'
            
        Returns:
            bool: True if successful, False otherwise
        """
        update_data = {'processing_status': status}
        if metadata:
            # Merge with existing metadata if it exists
            try:
                with self._get_session() as session:
                    if storage_type == 'hot':
                        email = session.query(HotEmail).filter(HotEmail.id == email_id).first()
                    else:
                        email = session.query(ColdEmail).filter(ColdEmail.id == email_id).first()
                    
                    if email and email.processing_metadata:
                        existing_metadata = email.processing_metadata
                        existing_metadata.update(metadata)
                        update_data['processing_metadata'] = existing_metadata
                    else:
                        update_data['processing_metadata'] = metadata
            except Exception as e:
                logger.warning(f"Could not merge metadata for email {email_id}: {e}")
                update_data['processing_metadata'] = metadata
        
        return self.update_email(email_id, update_data, storage_type) 