"""
Celery tasks for email archiving operations.
"""
import traceback
from typing import Dict, List, Any, Optional
from celery import current_task
from celery_config import celery_app
from datetime import datetime, timedelta
import os

from core.services.email_archive_service import EmailArchiveService
from core.logging_config import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, name='core.tasks.email_archive_tasks.archive_email_async')
def archive_email_async(self, email_data: Dict[str, Any], storage_type: str = 'hot') -> Dict[str, Any]:
    """
    Asynchronously archive an email.
    
    Args:
        email_data: Email data to archive
        storage_type: 'hot' or 'cold'
        
    Returns:
        Dict with success status and email ID
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Initializing archive service...'}
        )
        
        # Initialize archive service
        archive_service = EmailArchiveService()
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 25, 'total': 100, 'status': 'Storing email...'}
        )
        
        # Store email
        email_id = archive_service.store_email(email_data, storage_type)
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Email archived successfully'}
        )
        
        logger.info(f"Successfully archived email {email_id}")
        
        return {
            'success': True,
            'email_id': email_id,
            'storage_type': storage_type,
            'message': 'Email archived successfully'
        }
        
    except Exception as e:
        logger.error(f"Error archiving email: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'storage_type': storage_type,
            'message': 'Failed to archive email'
        }


@celery_app.task(bind=True, name='core.tasks.email_archive_tasks.move_to_cold_storage_async')
def move_to_cold_storage_async(self, days_threshold: int = 30) -> Dict[str, Any]:
    """
    Asynchronously move emails from hot to cold storage.
    
    Args:
        days_threshold: Number of days after which emails are moved
        
    Returns:
        Dict with success status and count of moved emails
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Initializing archive service...'}
        )
        
        # Initialize archive service
        archive_service = EmailArchiveService()
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 25, 'total': 100, 'status': 'Moving emails to cold storage...'}
        )
        
        # Move emails to cold storage
        moved_count = archive_service.move_to_cold_storage(days_threshold)
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 75, 'total': 100, 'status': 'Updating statistics...'}
        )
        
        # Get updated storage statistics
        stats = archive_service.get_storage_stats()
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Cold storage migration completed'}
        )
        
        logger.info(f"Successfully moved {moved_count} emails to cold storage")
        
        return {
            'success': True,
            'moved_count': moved_count,
            'days_threshold': days_threshold,
            'storage_stats': stats,
            'message': f'Moved {moved_count} emails to cold storage'
        }
        
    except Exception as e:
        logger.error(f"Error moving emails to cold storage: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'days_threshold': days_threshold,
            'message': 'Failed to move emails to cold storage'
        }


@celery_app.task(bind=True, name='core.tasks.email_archive_tasks.cleanup_old_emails_async')
def cleanup_old_emails_async(self, days_threshold: int = 365) -> Dict[str, Any]:
    """
    Asynchronously cleanup old emails from cold storage.
    
    Args:
        days_threshold: Number of days after which emails are deleted
        
    Returns:
        Dict with success status and count of deleted emails
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Initializing archive service...'}
        )
        
        # Initialize archive service
        archive_service = EmailArchiveService()
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 25, 'total': 100, 'status': 'Cleaning up old emails...'}
        )
        
        # Cleanup old emails
        deleted_count = archive_service.cleanup_old_emails(days_threshold)
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 75, 'total': 100, 'status': 'Updating statistics...'}
        )
        
        # Get updated storage statistics
        stats = archive_service.get_storage_stats()
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Cleanup completed'}
        )
        
        logger.warning(f"Successfully deleted {deleted_count} old emails from cold storage")
        
        return {
            'success': True,
            'deleted_count': deleted_count,
            'days_threshold': days_threshold,
            'storage_stats': stats,
            'message': f'Deleted {deleted_count} old emails from cold storage'
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old emails: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'days_threshold': days_threshold,
            'message': 'Failed to cleanup old emails'
        }


@celery_app.task(bind=True, name='core.tasks.email_archive_tasks.get_storage_stats_async')
def get_storage_stats_async(self) -> Dict[str, Any]:
    """
    Asynchronously get storage statistics.
    
    Returns:
        Dict with storage statistics
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Initializing archive service...'}
        )
        
        # Initialize archive service
        archive_service = EmailArchiveService()
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'Fetching storage statistics...'}
        )
        
        # Get storage statistics
        stats = archive_service.get_storage_stats()
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Statistics retrieved'}
        )
        
        return {
            'success': True,
            'storage_stats': stats,
            'message': 'Storage statistics retrieved successfully'
        }
        
    except Exception as e:
        logger.error(f"Error getting storage stats: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to get storage statistics'
        }


@celery_app.task(bind=True, name='core.tasks.email_archive_tasks.search_emails_async')
def search_emails_async(self, 
                       query: str = None,
                       user_id: str = None,
                       sender_email: str = None,
                       date_from: str = None,
                       date_to: str = None,
                       storage_type: str = 'hot',
                       limit: int = 100,
                       offset: int = 0) -> Dict[str, Any]:
    """
    Asynchronously search emails in the archive.
    
    Args:
        query: Text search query
        user_id: Filter by user ID
        sender_email: Filter by sender email
        date_from: Start date filter (ISO format string)
        date_to: End date filter (ISO format string)
        storage_type: 'hot' or 'cold'
        limit: Maximum number of results
        offset: Number of results to skip
        
    Returns:
        Dict with search results
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Initializing archive service...'}
        )
        
        # Initialize archive service
        archive_service = EmailArchiveService()
        
        # Parse dates
        parsed_date_from = datetime.fromisoformat(date_from) if date_from else None
        parsed_date_to = datetime.fromisoformat(date_to) if date_to else None
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 25, 'total': 100, 'status': 'Searching emails...'}
        )
        
        # Search emails
        emails = archive_service.search_emails(
            query=query,
            user_id=user_id,
            sender_email=sender_email,
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            storage_type=storage_type,
            limit=limit,
            offset=offset
        )
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Search completed'}
        )
        
        return {
            'success': True,
            'emails': emails,
            'count': len(emails),
            'storage_type': storage_type,
            'query': query,
            'message': f'Found {len(emails)} emails'
        }
        
    except Exception as e:
        logger.error(f"Error searching emails: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'storage_type': storage_type,
            'query': query,
            'message': 'Failed to search emails'
        } 