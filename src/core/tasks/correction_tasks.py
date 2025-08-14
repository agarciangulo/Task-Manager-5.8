"""
Simplified Celery tasks for processing correction requests.
"""
import os
import time
import random
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from celery import current_task
from celery.exceptions import MaxRetriesExceededError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.core.services.correction_service import CorrectionService
from src.core.services.correction_email_service import CorrectionEmailService
from src.core.agents.correction_agent import CorrectionAgent
from src.core.notion_service import NotionService
from src.core.logging_config import get_logger
from src.core.services.celery_config import celery_app  # Import main Celery app

logger = get_logger(__name__)

class CorrectionTaskRetry(Exception):
    """Custom exception for retryable correction task errors."""
    pass

class CorrectionTaskFatal(Exception):
    """Custom exception for fatal correction task errors."""
    pass

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_correction(self, correlation_id: str, email_body: str, sender_email: str) -> Dict[str, Any]:
    """
    Process a correction request with enhanced error handling and retry logic.
    
    Args:
        correlation_id: Unique identifier for the correction
        email_body: Email body containing correction instructions
        sender_email: Email address of the sender
        
    Returns:
        Dict containing processing results
    """
    start_time = time.time()
    logger.info(f"Starting correction processing for correlation_id: {correlation_id}")
    
    try:
        # Initialize services with retry logic
        correction_service = _initialize_service_with_retry(CorrectionService)
        email_service = _initialize_service_with_retry(CorrectionEmailService)
        agent = _initialize_service_with_retry(CorrectionAgent)
        notion_service = _initialize_service_with_retry(NotionService)
        
        # Step 1: Get correction log with validation
        correction_log = _get_correction_log_with_retry(correction_service, correlation_id)
        if not correction_log:
            raise CorrectionTaskFatal(f"Correction log not found for correlation_id: {correlation_id}")
        
        # Step 2: Validate sender email
        if not correction_service._validate_sender(sender_email, correction_log['user_email']):
            logger.warning(f"Security violation: sender {sender_email} != expected {correction_log['user_email']}")
            email_service.send_security_violation_email(sender_email, correlation_id)
            raise CorrectionTaskFatal("Sender email validation failed")
        
        # Step 3: Interpret corrections with enhanced error handling
        interpretation_result = _interpret_corrections_with_retry(
            agent, email_body, correction_log['task_ids']
        )
        
        if interpretation_result['requires_clarification']:
            logger.info(f"Correction requires clarification for correlation_id: {correlation_id}")
            email_service.send_clarification_email(
                sender_email, 
                correlation_id, 
                interpretation_result.get('raw_response', '')
            )
            return {
                'status': 'clarification_sent',
                'correlation_id': correlation_id,
                'message': 'Clarification email sent'
            }
        
        # Step 4: Apply corrections with transaction safety
        applied_corrections = []
        failed_corrections = []
        
        for correction in interpretation_result['corrections']:
            try:
                success = _apply_single_correction_with_retry(
                    correction, correction_log, correction_service, notion_service
                )
                if success:
                    applied_corrections.append(correction)
                else:
                    failed_corrections.append(correction)
            except Exception as e:
                logger.error(f"Failed to apply correction {correction}: {e}")
                failed_corrections.append(correction)
        
        # Step 5: Update correction log status
        if failed_corrections:
            status = 'partial_success' if applied_corrections else 'failed'
            error_message = f"Failed corrections: {len(failed_corrections)}"
        else:
            status = 'completed'
            error_message = None
        
        correction_service.update_correction_log_status(correlation_id, status, error_message)
        
        # Step 6: Send confirmation email
        email_service.send_correction_confirmation(
            sender_email,
            applied_corrections,
            failed_corrections,
            correlation_id
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Correction processing completed for {correlation_id} in {processing_time:.2f}s")
        
        return {
            'status': 'success',
            'correlation_id': correlation_id,
            'applied_corrections': len(applied_corrections),
            'failed_corrections': len(failed_corrections),
            'processing_time': processing_time
        }
        
    except CorrectionTaskFatal as e:
        logger.error(f"Fatal error in correction processing: {e}")
        _handle_fatal_error(correlation_id, sender_email, str(e), email_service)
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error in correction processing: {e}")
        return _handle_retryable_error(self, correlation_id, sender_email, str(e), email_service)

def _initialize_service_with_retry(service_class, max_retries=3):
    """Initialize service with retry logic."""
    for attempt in range(max_retries):
        try:
            return service_class()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to initialize {service_class.__name__} after {max_retries} attempts: {e}")
                raise CorrectionTaskFatal(f"Service initialization failed: {e}")
            logger.warning(f"Service initialization attempt {attempt + 1} failed, retrying...")
            time.sleep(2 ** attempt + random.uniform(0, 1))  # Exponential backoff with jitter

def _get_correction_log_with_retry(correction_service, correlation_id, max_retries=3):
    """Get correction log with retry logic."""
    for attempt in range(max_retries):
        try:
            return correction_service.get_correction_log(correlation_id)
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to get correction log after {max_retries} attempts: {e}")
                raise CorrectionTaskRetry(f"Failed to get correction log: {e}")
            logger.warning(f"Get correction log attempt {attempt + 1} failed, retrying...")
            time.sleep(2 ** attempt + random.uniform(0, 1))

def _interpret_corrections_with_retry(agent, email_body, task_ids, max_retries=3):
    """Interpret corrections with retry logic."""
    for attempt in range(max_retries):
        try:
            return agent.interpret_corrections(email_body, task_ids)
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to interpret corrections after {max_retries} attempts: {e}")
                raise CorrectionTaskRetry(f"Failed to interpret corrections: {e}")
            logger.warning(f"Interpret corrections attempt {attempt + 1} failed, retrying...")
            time.sleep(2 ** attempt + random.uniform(0, 1))

def _apply_single_correction_with_retry(correction, correction_log, correction_service, notion_service, max_retries=3):
    """Apply single correction with retry logic."""
    for attempt in range(max_retries):
        try:
            return _apply_single_correction(correction, correction_log, correction_service, notion_service)
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to apply correction after {max_retries} attempts: {e}")
                return False
            logger.warning(f"Apply correction attempt {attempt + 1} failed, retrying...")
            time.sleep(2 ** attempt + random.uniform(0, 1))

def _apply_single_correction(correction: Dict[str, Any], correction_log: Dict[str, Any], 
                           correction_service: CorrectionService, notion_service: NotionService) -> bool:
    """
    Apply a single correction with enhanced error handling.
    
    Args:
        correction: Correction data
        correction_log: Correction log data
        correction_service: Correction service instance
        notion_service: Notion service instance
        
    Returns:
        bool: True if successful
    """
    try:
        task_id = correction['task_id']
        correction_type = correction['correction_type']
        updates = correction.get('updates', {})
        
        # Get original task data for logging
        original_task = notion_service.get_task(task_id)
        if not original_task:
            logger.error(f"Task {task_id} not found in Notion")
            return False
        
        # Apply correction based on type
        if correction_type == 'update':
            success, error = notion_service.update_task(task_id, updates)
        elif correction_type == 'delete':
            success, error = notion_service.delete_task(task_id)  # Archive task
        else:
            logger.error(f"Unknown correction type: {correction_type}")
            return False
        
        # Log the correction application
        correction_service.log_correction_application(
            correction_log['id'],
            task_id,
            correction_type,
            original_task,
            updates if correction_type == 'update' else {'archived': True},
            success,
            error
        )
        
        if success:
            logger.info(f"Successfully applied {correction_type} correction to task {task_id}")
        else:
            logger.error(f"Failed to apply {correction_type} correction to task {task_id}: {error}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error applying correction: {e}")
        return False

def _handle_fatal_error(correlation_id: str, sender_email: str, error_message: str, email_service: CorrectionEmailService):
    """Handle fatal errors that should not be retried."""
    try:
        email_service.send_error_email(sender_email, correlation_id, error_message)
        logger.error(f"Fatal error handled for correlation_id: {correlation_id}")
    except Exception as e:
        logger.error(f"Failed to send error email: {e}")

def _handle_retryable_error(task_instance, correlation_id: str, sender_email: str, error_message: str, email_service: CorrectionEmailService):
    """Handle retryable errors with exponential backoff."""
    try:
        # Check if we've exceeded max retries
        if task_instance.request.retries >= task_instance.max_retries:
            logger.error(f"Max retries exceeded for correlation_id: {correlation_id}")
            email_service.send_error_email(sender_email, correlation_id, f"Processing failed after {task_instance.max_retries} attempts: {error_message}")
            return {
                'status': 'failed',
                'correlation_id': correlation_id,
                'error': 'Max retries exceeded'
            }
        
        # Calculate retry delay with exponential backoff and jitter
        retry_delay = task_instance.default_retry_delay * (2 ** task_instance.request.retries) + random.uniform(0, 1)
        
        logger.warning(f"Retrying correction processing for {correlation_id}. Attempt {task_instance.request.retries + 1}")
        
        # Retry the task
        raise task_instance.retry(countdown=int(retry_delay))
        
    except MaxRetriesExceededError:
        logger.error(f"Max retries exceeded for correlation_id: {correlation_id}")
        email_service.send_error_email(sender_email, correlation_id, f"Processing failed after maximum retries: {error_message}")
        return {
            'status': 'failed',
            'correlation_id': correlation_id,
            'error': 'Max retries exceeded'
        }

@celery_app.task
def cleanup_old_correction_logs(days_old: int = 30) -> Dict[str, Any]:
    """
    Clean up old correction logs with enhanced error handling.
    
    Args:
        days_old: Number of days old to consider for cleanup
        
    Returns:
        Dict containing cleanup results
    """
    try:
        correction_service = CorrectionService()
        deleted_count = correction_service.cleanup_old_logs(days_old)
        
        logger.info(f"Cleanup completed: {deleted_count} old correction logs deleted")
        
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'days_old': days_old
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'days_old': days_old
        }

@celery_app.task
def get_correction_stats() -> Dict[str, Any]:
    """
    Get correction statistics with enhanced error handling.
    
    Returns:
        Dict containing correction statistics
    """
    try:
        correction_service = CorrectionService()
        stats = correction_service.get_correction_stats()
        
        logger.info(f"Retrieved correction stats: {stats}")
        
        return {
            'status': 'success',
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get correction stats: {e}")
        return {
            'status': 'failed',
            'error': str(e)
        } 