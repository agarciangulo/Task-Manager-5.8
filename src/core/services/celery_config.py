"""
Celery configuration for asynchronous task processing.
"""
import os
from celery import Celery
from src.config.settings import DEBUG_MODE

# Celery configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery instance
celery_app = Celery(
    'task_manager',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        'core.tasks.notion_tasks',
        'core.tasks.ai_tasks', 
        'core.tasks.email_tasks',
        'core.tasks.dashboard_tasks',
        'core.tasks.correction_tasks'  # Add correction tasks
    ]
)

# Auto-discover tasks to ensure all tasks are registered
celery_app.autodiscover_tasks(['src.core.tasks'], force=True)

# Explicitly import correction tasks to ensure they're registered
try:
    import src.core.tasks.correction_tasks
    print("✅ Correction tasks imported successfully")
except Exception as e:
    print(f"⚠️ Warning: Could not import correction tasks: {e}")

# Celery settings
celery_app.conf.update(
    # Task routing
    task_routes={
        'core.tasks.notion_tasks.*': {'queue': 'notion'},
        'core.tasks.ai_tasks.*': {'queue': 'ai'},
        'core.tasks.email_tasks.*': {'queue': 'email'},
        'core.tasks.dashboard_tasks.*': {'queue': 'dashboard'},
        'core.tasks.correction_tasks.*': {'queue': 'corrections'},  # Add correction queue
    },
    
    # Task execution settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Rate limiting
    task_annotations={
        'core.tasks.notion_tasks.*': {'rate_limit': '10/m'},  # 10 tasks per minute
        'core.tasks.ai_tasks.*': {'rate_limit': '30/m'},      # 30 tasks per minute
        'core.tasks.email_tasks.*': {'rate_limit': '5/m'},    # 5 tasks per minute
        'core.tasks.correction_tasks.*': {'rate_limit': '10/m'},  # 10 correction tasks per minute
    },
    
    # Result expiration
    result_expires=3600,  # 1 hour
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

if DEBUG_MODE:
    celery_app.conf.update(
        task_always_eager=False,  # Allow async execution even in debug
        task_eager_propagates=True,
    ) 