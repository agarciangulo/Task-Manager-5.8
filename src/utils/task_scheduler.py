"""
Task scheduler for periodic asynchronous operations.
Handles scheduled tasks like Gmail checking, stale task identification, and analytics generation.
"""
import os
import time
from datetime import datetime, timedelta
from celery.schedules import crontab
from celery_config import celery_app
from src.core.logging_config import get_logger
from src.config.settings import DEBUG_MODE

logger = get_logger(__name__)

# Import task modules
from src.core.tasks.email_tasks import process_gmail_updates_async
from src.core.tasks.notion_tasks import identify_stale_tasks_async
from src.core.tasks.dashboard_tasks import generate_analytics_report_async

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks when Celery starts."""
    
    # Gmail checking - every 5 minutes
    sender.add_periodic_task(
        crontab(minute='*/5'),  # Every 5 minutes
        check_gmail_periodic.s(),
        name='check-gmail-every-5-minutes'
    )
    
    # Stale task identification - every hour
    sender.add_periodic_task(
        crontab(minute=0, hour='*'),  # Every hour at minute 0
        identify_stale_tasks_periodic.s(),
        name='identify-stale-tasks-every-hour'
    )
    
    # Daily analytics report - every day at 9 AM
    sender.add_periodic_task(
        crontab(minute=0, hour=9),  # Every day at 9 AM
        generate_daily_analytics.s(),
        name='generate-daily-analytics-at-9am'
    )
    
    # Weekly analytics report - every Monday at 8 AM
    sender.add_periodic_task(
        crontab(minute=0, hour=8, day_of_week=1),  # Every Monday at 8 AM
        generate_weekly_analytics.s(),
        name='generate-weekly-analytics-monday-8am'
    )
    
    logger.info("Periodic tasks configured successfully")

@celery_app.task(name='task_manager.check_gmail_periodic')
def check_gmail_periodic():
    """Periodic task to check Gmail for new emails."""
    try:
        logger.info("Starting periodic Gmail check")
        
        # Queue the Gmail processing task
        result = process_gmail_updates_async.delay()
        
        logger.info(f"Gmail check queued with task ID: {result.id}")
        return {
            'success': True,
            'task_id': result.id,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in periodic Gmail check: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@celery_app.task(name='task_manager.identify_stale_tasks_periodic')
def identify_stale_tasks_periodic():
    """Periodic task to identify stale tasks across all databases."""
    try:
        logger.info("Starting periodic stale task identification")
        
        # Get all user databases (you'll need to implement this based on your user management)
        from src.core.services.auth_service import AuthService
        from src.core.security.jwt_utils import JWTManager
        from src.config.settings import NOTION_TOKEN, NOTION_USERS_DB_ID
        
        jwt_manager = JWTManager(secret_key="dummy", algorithm="HS256")
        auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, None)
        
        # Get all users with task databases
        users = auth_service.get_all_users_with_task_databases()
        
        results = []
        for user in users:
            if user.task_database_id:
                # Queue stale task identification for each user
                result = identify_stale_tasks_async.delay(user.task_database_id, 7)
                results.append({
                    'user_id': user.user_id,
                    'database_id': user.task_database_id,
                    'task_id': result.id
                })
        
        logger.info(f"Stale task identification queued for {len(results)} users")
        return {
            'success': True,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in periodic stale task identification: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@celery_app.task(name='task_manager.generate_daily_analytics')
def generate_daily_analytics():
    """Periodic task to generate daily analytics reports."""
    try:
        logger.info("Starting daily analytics generation")
        
        # Get all user databases
        from src.core.services.auth_service import AuthService
        from src.core.security.jwt_utils import JWTManager
        from src.config.settings import NOTION_TOKEN, NOTION_USERS_DB_ID
        
        jwt_manager = JWTManager(secret_key="dummy", algorithm="HS256")
        auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, None)
        
        users = auth_service.get_all_users_with_task_databases()
        
        results = []
        for user in users:
            if user.task_database_id:
                # Queue daily analytics generation for each user
                result = generate_analytics_report_async.delay(user.task_database_id, 'daily')
                results.append({
                    'user_id': user.user_id,
                    'database_id': user.task_database_id,
                    'task_id': result.id
                })
        
        logger.info(f"Daily analytics generation queued for {len(results)} users")
        return {
            'success': True,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in daily analytics generation: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@celery_app.task(name='task_manager.generate_weekly_analytics')
def generate_weekly_analytics():
    """Periodic task to generate weekly analytics reports."""
    try:
        logger.info("Starting weekly analytics generation")
        
        # Get all user databases
        from src.core.services.auth_service import AuthService
        from src.core.security.jwt_utils import JWTManager
        from src.config.settings import NOTION_TOKEN, NOTION_USERS_DB_ID
        
        jwt_manager = JWTManager(secret_key="dummy", algorithm="HS256")
        auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, None)
        
        users = auth_service.get_all_users_with_task_databases()
        
        results = []
        for user in users:
            if user.task_database_id:
                # Queue weekly analytics generation for each user
                result = generate_analytics_report_async.delay(user.task_database_id, 'weekly')
                results.append({
                    'user_id': user.user_id,
                    'database_id': user.task_database_id,
                    'task_id': result.id
                })
        
        logger.info(f"Weekly analytics generation queued for {len(results)} users")
        return {
            'success': True,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in weekly analytics generation: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@celery_app.task(name='task_manager.cleanup_old_results')
def cleanup_old_results():
    """Periodic task to cleanup old task results from Redis."""
    try:
        logger.info("Starting cleanup of old task results")
        
        # This would typically be handled by Celery's result backend
        # You can implement custom cleanup logic here if needed
        
        logger.info("Cleanup of old task results completed")
        return {
            'success': True,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup of old results: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def get_task_status(task_id: str):
    """Get the status of a specific task."""
    try:
        from celery.result import AsyncResult
        result = AsyncResult(task_id, app=celery_app)
        
        return {
            'task_id': task_id,
            'status': result.status,
            'result': result.result if result.ready() else None,
            'info': result.info if hasattr(result, 'info') else None
        }
    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {str(e)}")
        return {
            'task_id': task_id,
            'status': 'ERROR',
            'error': str(e)
        }

def cancel_task(task_id: str):
    """Cancel a running task."""
    try:
        from celery.result import AsyncResult
        result = AsyncResult(task_id, app=celery_app)
        
        if result.state in ['PENDING', 'STARTED']:
            result.revoke(terminate=True)
            return {
                'success': True,
                'task_id': task_id,
                'message': 'Task cancelled successfully'
            }
        else:
            return {
                'success': False,
                'task_id': task_id,
                'message': f'Cannot cancel task in state: {result.state}'
            }
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}")
        return {
            'success': False,
            'task_id': task_id,
            'error': str(e)
        }

if __name__ == "__main__":
    # For testing the scheduler
    print("Task Scheduler Test")
    print("=" * 50)
    
    # Test periodic tasks
    print("Testing periodic tasks...")
    
    # Test Gmail check
    result = check_gmail_periodic.delay()
    print(f"Gmail check queued: {result.id}")
    
    # Test stale task identification
    result = identify_stale_tasks_periodic.delay()
    print(f"Stale task identification queued: {result.id}")
    
    print("Periodic tasks queued successfully!") 