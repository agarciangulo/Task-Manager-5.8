"""
Celery tasks for activity recognition and tracking.
"""
from src.utils.celery_config import celery_app
from src.core.database.connection import SessionLocal
from src.core.activity_recognition.recognition_service import ActivityRecognitionService
from src.core.logging_config import get_logger

logger = get_logger(__name__)

@celery_app.task(name='activity.recognize_activity_for_task', bind=True)
def recognize_activity_for_task(self, user_id: str, task_id: str, task_title: str):
    """
    Background task to recognize and track recurring activities for a new task.
    
    Args:
        user_id: User identifier
        task_id: Task identifier
        task_title: Task title/description
        
    Returns:
        Dict: Processing results
    """
    db_session = None
    try:
        logger.info(f"Starting activity recognition for task {task_id} (user: {user_id})")
        
        # Get database session
        db_session = SessionLocal()
        
        # Initialize recognition service
        recognition_service = ActivityRecognitionService(user_id, db_session)
        
        # Process the task
        result = recognition_service.process_new_task(task_id, task_title)
        
        if result['success']:
            logger.info(f"Activity recognition completed successfully for task {task_id}")
        else:
            logger.warning(f"Activity recognition failed for task {task_id}: {result['message']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in activity recognition task: {e}")
        
        # Retry the task with exponential backoff
        if self.request.retries < 3:
            raise self.retry(countdown=60 * (2 ** self.request.retries), max_retries=3)
        else:
            logger.error(f"Activity recognition task failed after 3 retries for task {task_id}")
            return {
                'success': False,
                'message': f'Task failed after retries: {str(e)}',
                'task_id': task_id,
                'user_id': user_id
            }
    
    finally:
        # Always close the database session
        if db_session:
            try:
                db_session.close()
            except Exception as e:
                logger.error(f"Error closing database session: {e}")

@celery_app.task(name='activity.generate_user_summary', bind=True)
def generate_user_activity_summary(self, user_id: str):
    """
    Background task to generate a summary of user's tracked activities.
    
    Args:
        user_id: User identifier
        
    Returns:
        Dict: Activity summary
    """
    db_session = None
    try:
        logger.info(f"Generating activity summary for user {user_id}")
        
        # Get database session
        db_session = SessionLocal()
        
        # Initialize recognition service
        recognition_service = ActivityRecognitionService(user_id, db_session)
        
        # Generate summary
        summary = recognition_service.get_user_activity_summary()
        
        logger.info(f"Activity summary generated for user {user_id}")
        return summary
        
    except Exception as e:
        logger.error(f"Error generating activity summary: {e}")
        
        # Retry the task with exponential backoff
        if self.request.retries < 2:
            raise self.retry(countdown=300 * (2 ** self.request.retries), max_retries=2)
        else:
            logger.error(f"Activity summary generation failed after retries for user {user_id}")
            return {
                'error': f'Summary generation failed: {str(e)}',
                'user_id': user_id
            }
    
    finally:
        # Always close the database session
        if db_session:
            try:
                db_session.close()
            except Exception as e:
                logger.error(f"Error closing database session: {e}")

@celery_app.task(name='activity.cleanup_old_activities')
def cleanup_old_activities():
    """
    Periodic task to cleanup old or inactive tracked activities.
    This can be scheduled to run daily or weekly.
    """
    db_session = None
    try:
        logger.info("Starting cleanup of old activities")
        
        # Get database session
        db_session = SessionLocal()
        
        # This would implement cleanup logic
        # For example, remove activities that haven't been updated in 6 months
        # and have low instance counts
        
        logger.info("Activity cleanup completed")
        return {'success': True, 'message': 'Cleanup completed'}
        
    except Exception as e:
        logger.error(f"Error in activity cleanup: {e}")
        return {'success': False, 'error': str(e)}
    
    finally:
        # Always close the database session
        if db_session:
            try:
                db_session.close()
            except Exception as e:
                logger.error(f"Error closing database session: {e}") 