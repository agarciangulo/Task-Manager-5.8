"""
Asynchronous email tasks for Task Manager.
Handles email operations without blocking the main application.
"""
import traceback
from typing import Dict, List, Any, Optional
from celery import current_task
from celery_config import celery_app
from core.logging_config import get_logger
from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, GMAIL_SERVER
import pandas as pd
from datetime import datetime, timedelta

logger = get_logger(__name__)

@celery_app.task(bind=True, name='core.tasks.email_tasks.send_confirmation_email_async')
def send_confirmation_email_async(self, recipient: str, tasks: List[Dict], 
                                coaching_insights: Optional[str] = None, 
                                user_database_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Asynchronously send confirmation email with processed tasks and coaching insights.
    
    Args:
        recipient: Email address to send to
        tasks: List of processed tasks
        coaching_insights: Optional coaching insights text
        user_database_id: Optional database ID to fetch open tasks from
        
    Returns:
        Dict with success status and result/error
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Preparing email...'}
        )
        
        # Import here to avoid circular imports
        from gmail_processor import send_confirmation_email
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 25, 'total': 100, 'status': 'Sending email...'}
        )
        
        success = send_confirmation_email(recipient, tasks, coaching_insights, user_database_id)
        
        if success:
            logger.info(f"Successfully sent confirmation email to {recipient}")
            return {
                'success': True,
                'recipient': recipient,
                'task_count': len(tasks),
                'has_insights': coaching_insights is not None
            }
        else:
            logger.error(f"Failed to send confirmation email to {recipient}")
            return {
                'success': False,
                'error': 'Email sending failed',
                'recipient': recipient,
                'task_count': len(tasks)
            }
            
    except Exception as e:
        logger.error(f"Error sending confirmation email to {recipient}: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'recipient': recipient,
            'task_count': len(tasks)
        }

@celery_app.task(bind=True, name='core.tasks.email_tasks.process_gmail_updates_async')
def process_gmail_updates_async(self) -> Dict[str, Any]:
    """
    Asynchronously check Gmail for new emails and process them.
    
    Returns:
        Dict with success status and processing results
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Connecting to Gmail...'}
        )
        
        # Import here to avoid circular imports
        from gmail_processor import check_gmail_for_updates
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 25, 'total': 100, 'status': 'Checking for new emails...'}
        )
        
        # This will process all emails and return results
        # We need to modify the original function to return results instead of just printing
        results = check_gmail_for_updates()
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Email processing completed'}
        )
        
        logger.info("Successfully processed Gmail updates")
        
        return {
            'success': True,
            'results': results,
            'processed_at': 'now'  # You might want to add actual timestamp
        }
        
    except Exception as e:
        logger.error(f"Error processing Gmail updates: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e)
        }

@celery_app.task(bind=True, name='core.tasks.email_tasks.process_single_email_async')
def process_single_email_async(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Asynchronously process a single email.
    
    Args:
        email_data: Dictionary containing email information
            - sender_email: Email address of sender
            - subject: Email subject
            - body: Email body
            - date: Email date
            
    Returns:
        Dict with success status and processing results
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Analyzing email...'}
        )
        
        sender_email = email_data.get('sender_email')
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        date = email_data.get('date', '')
        
        # Format the update text
        update_text = f"From: {sender_email}\nDate: {date}\n\nSubject: {subject}\n\n{body}"
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 25, 'total': 100, 'status': 'Extracting tasks...'}
        )
        
        # Extract tasks
        from core.task_extractor import extract_tasks_from_update
        tasks = extract_tasks_from_update(update_text)
        
        if not tasks:
            logger.info(f"No tasks extracted from email from {sender_email}")
            return {
                'success': True,
                'tasks_extracted': 0,
                'sender_email': sender_email,
                'message': 'No tasks found in email'
            }
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'Looking up user...'}
        )
        
        # Look up user by email address
        from core.services.auth_service import AuthService
        from core.security.jwt_utils import JWTManager
        from config import NOTION_TOKEN, NOTION_USERS_DB_ID
        
        jwt_manager = JWTManager(secret_key="dummy", algorithm="HS256")
        auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, None)
        
        user = auth_service.get_user_by_email(sender_email)
        if not user:
            logger.warning(f"No user found for email: {sender_email}")
            return {
                'success': False,
                'error': 'User not found',
                'sender_email': sender_email
            }
        
        if not user.task_database_id:
            logger.warning(f"User {sender_email} does not have a task database configured")
            return {
                'success': False,
                'error': 'User has no task database',
                'sender_email': sender_email
            }
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 75, 'total': 100, 'status': 'Processing tasks...'}
        )
        
        # Process tasks
        from core.task_processor import insert_or_update_task
        from core import fetch_notion_tasks
        
        existing_tasks = fetch_notion_tasks(database_id=user.task_database_id)
        
        processed_tasks = []
        failed_tasks = []
        
        for task in tasks:
            try:
                log_output = []
                success, message = insert_or_update_task(
                    database_id=user.task_database_id,
                    task=task,
                    existing_tasks=existing_tasks,
                    log_output=log_output
                )
                
                if success:
                    processed_tasks.append(task)
                else:
                    failed_tasks.append({
                        'task': task,
                        'error': message
                    })
                    
            except Exception as e:
                failed_tasks.append({
                    'task': task,
                    'error': str(e)
                })
        
        # Generate coaching insights if we have processed tasks
        coaching_insights = None
        if processed_tasks:
            try:
                from core.ai.insights import get_coaching_insight
                
                # Get person name from the first task
                person_name = ""
                if processed_tasks and "employee" in processed_tasks[0]:
                    person_name = processed_tasks[0].get("employee", "")
                
                if person_name:
                    # Get recent tasks for this person
                    recent_tasks = existing_tasks[existing_tasks['employee'] == person_name]
                    if len(recent_tasks) > 0:
                        # Fix: Convert date column to datetime if it's not already
                        try:
                            if recent_tasks['date'].dtype == 'object':
                                recent_tasks = recent_tasks.copy()
                                recent_tasks['date'] = pd.to_datetime(recent_tasks['date'], errors='coerce')
                            recent_tasks = recent_tasks[recent_tasks['date'] >= datetime.now() - timedelta(days=14)]
                        except Exception as date_error:
                            logger.warning(f"Error processing dates for coaching insights: {date_error}")
                            # If date processing fails, use all recent tasks
                            recent_tasks = recent_tasks
                    
                    # Get peer feedback
                    peer_feedback = []
                    try:
                        from core import fetch_peer_feedback
                        peer_feedback = fetch_peer_feedback(person_name)
                    except Exception as e:
                        logger.warning(f"Error fetching peer feedback: {str(e)}")
                    
                    # Generate coaching insights
                    coaching_insights = get_coaching_insight(person_name, processed_tasks, recent_tasks, peer_feedback)
                    
            except Exception as e:
                logger.warning(f"Error generating coaching insights: {str(e)}")
        
        # Send confirmation email
        if processed_tasks:
            # Queue the email sending task
            send_confirmation_email_async.delay(sender_email, processed_tasks, coaching_insights, user.task_database_id)
        
        logger.info(f"Successfully processed email from {sender_email}: {len(processed_tasks)} tasks processed, {len(failed_tasks)} failed")
        
        return {
            'success': True,
            'sender_email': sender_email,
            'tasks_extracted': len(tasks),
            'tasks_processed': len(processed_tasks),
            'tasks_failed': len(failed_tasks),
            'failed_tasks': failed_tasks,
            'coaching_insights_generated': coaching_insights is not None,
            'confirmation_email_queued': len(processed_tasks) > 0
        }
        
    except Exception as e:
        logger.error(f"Error processing email from {email_data.get('sender_email', 'unknown')}: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'sender_email': email_data.get('sender_email', 'unknown')
        }

@celery_app.task(bind=True, name='core.tasks.email_tasks.send_notification_email_async')
def send_notification_email_async(self, recipient: str, subject: str, 
                                message: str, email_type: str = 'notification') -> Dict[str, Any]:
    """
    Asynchronously send a generic notification email.
    
    Args:
        recipient: Email address to send to
        subject: Email subject
        message: Email message content
        email_type: Type of email (notification, alert, etc.)
        
    Returns:
        Dict with success status and result/error
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Preparing notification email...'}
        )
        
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Create plain text email
        text_content = message
        
        # Create HTML version
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #4361ee; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Task Manager Notification</h2>
            </div>
            <div class="content">
                <p>{message.replace(chr(10), '<br>')}</p>
            </div>
            <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        # Attach parts
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'Sending email...'}
        )
        
        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Successfully sent {email_type} email to {recipient}")
        
        return {
            'success': True,
            'recipient': recipient,
            'subject': subject,
            'email_type': email_type
        }
        
    except Exception as e:
        logger.error(f"Error sending {email_type} email to {recipient}: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'recipient': recipient,
            'subject': subject,
            'email_type': email_type
        } 