"""
Enhanced Gmail processor with correction handler integration.
"""
import imaplib
import email
import smtplib
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback
from datetime import timedelta
import pandas as pd
import sys
import os
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
import json
import re
import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.task_extractor import extract_tasks_from_update
from src.core.task_processor import insert_or_update_task
from src.core import fetch_notion_tasks
from src.core.ai.insights import get_coaching_insight
from src.config.settings import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, GMAIL_SERVER, NOTION_TOKEN, NOTION_USERS_DB_ID, EMAIL_ARCHIVE_ENABLED

# Import services
from src.core.services.auth_service import AuthService
from src.core.services.correction_service import CorrectionService
from src.core.services.email_router import EmailRouter
from src.core.tasks.correction_tasks import process_correction

# Import EmailArchiveService for email archiving
if EMAIL_ARCHIVE_ENABLED:
    from src.core.services.email_archive_service import EmailArchiveService

# Removed OpenAI dependency - using simple text chunking instead
def chunk_email_text(text, max_chunks=20):
    """Simple text chunking without OpenAI dependency."""
    if not text:
        return []
    
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    chunks = []
    
    for paragraph in paragraphs:
        if len(paragraph.strip()) > 0:
            # If paragraph is too long, split by sentences
            if len(paragraph) > 1000:
                sentences = paragraph.split('. ')
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk + sentence) > 1000:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += sentence + ". " if not sentence.endswith('.') else sentence + " "
                if current_chunk:
                    chunks.append(current_chunk.strip())
            else:
                chunks.append(paragraph.strip())
    
    # Limit to max_chunks
    return chunks[:max_chunks]
from src.plugins.plugin_manager_instance import plugin_manager

# Import context verification utilities
from src.core.chat.verification import generate_verification_questions, parse_verification_response

# Discover and initialize plugins
PLUGIN_DIRECTORIES = [
    'src/plugins/guidelines',
    'src/plugins/feedback', 
    'src/plugins/integrations',
    'src/plugins/security'
]
plugin_manager.discover_plugins(PLUGIN_DIRECTORIES)
# Register all discovered plugins
for plugin_name in plugin_manager.plugin_classes:
    plugin_manager.register_plugin_by_name(plugin_name)

# Global storage for pending context conversations
PENDING_CONTEXT_CONVERSATIONS = {}

# Persistence configuration
PERSISTENCE_FILE = "pending_conversations.json"
PERSISTENCE_BACKUP_FILE = "pending_conversations_backup.json"
PERSISTENCE_TEMP_FILE = "pending_conversations_temp.json"

# Configuration for reminders
CONTEXT_REMINDER_INTERVAL_HOURS = 24
TASK_REMINDER_INTERVAL_HOURS = 72

# Initialize services with enhanced error handling
def initialize_correction_service(max_retries=3):
    """Initialize correction service with retry logic."""
    for attempt in range(max_retries):
        try:
            service = CorrectionService()
            print(f"✅ Correction service initialized successfully (attempt {attempt + 1})")
            return service
        except ValueError as e:
            if "DATABASE_URL" in str(e):
                print(f"⚠️ DATABASE_URL not configured: {e}")
                print("📧 Correction features will be disabled until DATABASE_URL is set")
                return None
            else:
                print(f"⚠️ Configuration error: {e}")
                return None
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize correction service (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                print(f"🔄 Retrying in {2 ** attempt} seconds...")
                import time
                time.sleep(2 ** attempt)
            else:
                print("❌ Failed to initialize correction service after all attempts")
                print("📧 Correction features will be disabled")
                return None

correction_service = initialize_correction_service()

# Initialize email router
try:
    email_router = EmailRouter()
    print("✅ Email router initialized successfully")
except Exception as e:
    print(f"⚠️ Warning: Could not initialize email router: {e}")
    email_router = None


def send_confirmation_email_with_correction_support(recipient, tasks, coaching_insights=None, user_database_id=None):
    """
    Send confirmation email with correction support.
    
    Args:
        recipient: Email address to send to
        tasks: List of processed tasks
        coaching_insights: Optional coaching insights
        user_database_id: Optional database ID
    """
    try:
        # Create correlation ID and log if correction service is available
        correlation_id = None
        if correction_service:
            correlation_id = correction_service.create_correction_log(
                user_email=recipient,
                task_ids=[task.get('id', str(i)) for i, task in enumerate(tasks)],
                email_subject=f"Task Manager: {len(tasks)} Tasks Processed"
            )
        else:
            # Generate a simple correlation ID for email subject
            import uuid
            correlation_id = f"corr-{uuid.uuid4()}"
        
        # Get open tasks from user's database if database_id provided
        open_tasks = []
        if user_database_id:
            try:
                from src.core.notion_service import NotionService
                notion_service = NotionService()
                all_tasks = notion_service.fetch_tasks(user_database_id)
                
                # Convert to list if it's a DataFrame
                if hasattr(all_tasks, 'to_dict'):
                    tasks_list = all_tasks.to_dict('records')
                else:
                    tasks_list = all_tasks if isinstance(all_tasks, list) else list(all_tasks)
                
                # Filter for open tasks (not completed)
                open_tasks = [task for task in tasks_list if task.get('status', '').lower() != 'completed']
                
                # Limit to most recent 10 open tasks to avoid overwhelming the email
                open_tasks = open_tasks[:10]
                
            except Exception as e:
                print(f"Warning: Could not fetch open tasks: {e}")
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = recipient
        msg['Subject'] = f"Your Daily Summary [Ref: {correlation_id}]"
        
        # Create plain text email
        text_content = f"Hello,\n\n"
        text_content += f"I've successfully processed {len(tasks)} tasks from your email.\n\n"
        
        # List processed tasks
        text_content += "Processed Tasks:\n"
        for i, task in enumerate(tasks, 1):
            task_title = task.get('task', task.get('title', 'Untitled Task'))
            task_status = task.get('status', 'Not Started')
            task_category = task.get('category', 'General')
            
            text_content += f"{i}. {task_title}\n"
            text_content += f"   Status: {task_status}\n"
            text_content += f"   Category: {task_category}\n\n"
        
        # Add coaching insights if available
        if coaching_insights:
            text_content += f"Coaching Insights:\n{coaching_insights}\n\n"
        
        # Add correction instructions
        text_content += "--- Correction Instructions ---\n"
        text_content += "If you need to make changes to any of these tasks, simply reply to this email with your corrections.\n\n"
        text_content += "Examples:\n"
        text_content += "- \"Change task 1 status to completed\"\n"
        text_content += "- \"Delete task 2, it's no longer needed\"\n"
        text_content += "- \"Update task 3 priority to high and due date to 2024-01-15\"\n\n"
        text_content += "I'll process your corrections and send you a confirmation.\n\n"
        
        # Add open tasks summary if available
        if open_tasks and len(open_tasks) > 0:
            text_content += f"\n--- Your Open Tasks ({len(open_tasks)} tasks) ---\n\n"
            text_content += "Here are your current open tasks:\n\n"
            
            for i, task in enumerate(open_tasks, 1):
                task_title = task.get('task', task.get('title', 'Untitled Task'))
                task_status = task.get('status', 'Unknown')
                task_category = task.get('category', 'General')
                task_date = task.get('date', 'No date')
                
                text_content += f"{i}. {task_title}\n"
                text_content += f"   Status: {task_status} | Category: {task_category} | Date: {task_date}\n\n"
        
        text_content += "Thank you for using the Task Manager!\n"
        
        # Create HTML version
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #4361ee; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .task {{ margin-bottom: 10px; padding: 10px; background-color: #f8f9fa; border-left: 4px solid #4361ee; }}
                .section-header {{ margin-top: 30px; margin-bottom: 15px; padding: 10px; background-color: #e9ecef; border-radius: 5px; font-weight: bold; }}
                .status {{ display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
                .status-completed {{ background-color: #10b981; color: white; }}
                .status-in-progress {{ background-color: #3b82f6; color: white; }}
                .status-not-started {{ background-color: #6c757d; color: white; }}
                .status-on-hold {{ background-color: #f59e0b; color: white; }}
                .correction-section {{ margin-top: 30px; padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107; }}
                .correlation-id {{ background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace; margin: 20px 0; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Task Manager Update</h2>
            </div>
            <div class="content">
                <p>I've successfully processed {len(tasks)} tasks from your email:</p>
                
                <div class="tasks">
        """
        
        for i, task in enumerate(tasks, 1):
            title = task.get('title', '')
            task_desc = task.get('task', '')
            status = task.get('status', 'Unknown')
            category = task.get('category', 'Uncategorized')
            status_class = f"status-{status.lower().replace(' ', '-')}"
            
            html_content += f"""
                    <div class="task">
            """
            
            if title:
                html_content += f"""
                        <strong>{i}. {title}</strong><br>
                    """
                if task_desc and task_desc != title:
                    html_content += f"""
                        <em style="color: #666; font-size: 14px;">{task_desc}</em><br>
                        """
            else:
                html_content += f"""
                        <strong>{i}. {task_desc}</strong><br>
                    """
            
            html_content += f"""
                        <span class="status {status_class}">{status}</span>
                        <span style="margin-left: 10px; color: #666;">Category: {category}</span>
                    </div>
                """
        
        # Add coaching insights if available
        if coaching_insights:
            html_content += f"""
                <div class="correction-section">
                    <h3>AI Coaching Insights</h3>
                    <p>{coaching_insights.replace(chr(10), '<br>')}</p>
                </div>
            """
        
        # Add correction instructions
        html_content += f"""
                <div class="correction-section">
                    <h3>📝 Correction Instructions</h3>
                    <p>If you need to make changes to any of these tasks, simply reply to this email with your corrections.</p>                                 
                    
                    <h4>Examples:</h4>
                    <ul>
                        <li>Change task 1 status to completed</li>
                        <li>Delete task 2, it is no longer needed</li>
                        <li>Update task 3 priority to high and due date to 2024-01-15</li>                                                                    
                    </ul>
                    
                    <p>I will process your corrections and send you a confirmation.</p>                                                                           
                </div>
                
                <div class="correlation-id">
                    <strong>Reference ID:</strong> {correlation_id}
                </div>
            """
        
        # Add open tasks summary if available
        if open_tasks and len(open_tasks) > 0:
            html_content += f"""
                <div class="section-header">
                    📋 Your Open Tasks ({len(open_tasks)} tasks)
                </div>
                <p>Here are your current open tasks:</p>
                
                <div class="open-tasks">
            """
            
            for i, task in enumerate(open_tasks, 1):
                task_title = task.get('task', task.get('title', 'Untitled Task'))
                task_status = task.get('status', 'Unknown')
                task_category = task.get('category', 'General')
                task_date = task.get('date', 'No date')
                status_class = f"status-{task_status.lower().replace(' ', '-')}"
                
                html_content += f"""
                    <div class="open-task">
                        <strong>{i}. {task_title}</strong><br>
                        <span class="status {status_class}">{task_status}</span>
                        <span style="margin-left: 10px; color: #666;">Category: {task_category}</span>
                        <span style="margin-left: 10px; color: #666;">Date: {task_date}</span>
                    </div>
                """
            
            html_content += """
                </div>
            """
        
        html_content += """
                </div>
                
                <p>Thank you for using the Task Manager!</p>
            </div>
            <div class="footer">
                <p>This is an automated message. Please reply to this email with corrections if needed.</p>
            </div>
        </body>
        </html>
        """
        
        # Attach parts
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Confirmation email with correction support sent to {recipient}")
        print(f"🔗 Correlation ID: {correlation_id}")
        
    except Exception as e:
        print(f"❌ Error sending confirmation email: {str(e)}")
        print(traceback.format_exc())


def process_correction_email(msg, body, sender_email, correlation_id):
    """
    Process a correction email with enhanced error handling.
    
    Args:
        msg: Email message object
        body: Email body
        sender_email: Sender email address
        correlation_id: Correlation ID
        
    Returns:
        bool: True if successfully processed
    """
    try:
        print(f"📧 Processing correction email from {sender_email}")
        print(f"🔗 Correlation ID: {correlation_id}")
        
        # Check if correction service is available
        if not correction_service:
            print(f"❌ Correction service not available, skipping correction processing")
            # Send a helpful email to the user explaining the issue
            try:
                send_correction_service_unavailable_email(sender_email, correlation_id)
            except Exception as email_error:
                print(f"⚠️ Could not send service unavailable email: {email_error}")
            return False
        
        # Check if email router is available
        if not email_router:
            print(f"❌ Email router not available, skipping correction processing")
            return False
        
        # Extract just the reply part from the email body
        try:
            from src.utils.gmail_processor import extract_reply_from_email_body
            reply_body = extract_reply_from_email_body(body)
            
            print(f"📝 Original email body length: {len(body)} characters")
            print(f"📝 Reply body length: {len(reply_body)} characters")
            
            if len(reply_body) < len(body):
                print(f"✅ Successfully extracted reply (reduced from {len(body)} to {len(reply_body)} chars)")
            else:
                print(f"⚠️ No clear reply detected, using full email body")
        except Exception as extract_error:
            print(f"⚠️ Error extracting reply, using full body: {extract_error}")
            reply_body = body
        
        # Queue correction processing task with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = process_correction.delay(correlation_id, reply_body, sender_email)
                print(f"✅ Correction task queued with ID: {result.id}")
                return True
            except Exception as queue_error:
                print(f"⚠️ Failed to queue correction task (attempt {attempt + 1}): {queue_error}")
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying in {2 ** attempt} seconds...")
                    import time
                    time.sleep(2 ** attempt)
                else:
                    print(f"❌ Failed to queue correction task after {max_retries} attempts")
                    # Send error notification to user
                    try:
                        send_correction_queue_error_email(sender_email, correlation_id, str(queue_error))
                    except Exception as email_error:
                        print(f"⚠️ Could not send queue error email: {email_error}")
                    return False
        
    except Exception as e:
        print(f"❌ Error processing correction email: {str(e)}")
        print(traceback.format_exc())
        
        # Send error notification to user
        try:
            send_correction_processing_error_email(sender_email, correlation_id, str(e))
        except Exception as email_error:
            print(f"⚠️ Could not send processing error email: {email_error}")
        
        return False


def send_correction_service_unavailable_email(recipient_email, correlation_id):
    """Send email notifying user that correction service is unavailable."""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = recipient_email
        msg['Subject'] = f"Correction Service Temporarily Unavailable [Ref: {correlation_id}]"
        
        text_content = f"""Hello,

We received your correction request, but our correction service is currently unavailable.

Your request has been logged and will be processed as soon as the service is restored.

Reference ID: {correlation_id}

We apologize for the inconvenience. Please try again later.

Best regards,
Your Task Manager
"""
        
        msg.attach(MIMEText(text_content, 'plain'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"📧 Sent service unavailable notification to {recipient_email}")
        
    except Exception as e:
        print(f"❌ Error sending service unavailable email: {e}")


def send_correction_queue_error_email(recipient_email, correlation_id, error_details):
    """Send email notifying user of task queue error."""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = recipient_email
        msg['Subject'] = f"Correction Processing Delayed [Ref: {correlation_id}]"
        
        text_content = f"""Hello,

We received your correction request but encountered a temporary issue processing it.

Your request has been logged and will be retried automatically.

Reference ID: {correlation_id}
Error: {error_details}

Please try again in a few minutes, or contact support if the issue persists.

Best regards,
Your Task Manager
"""
        
        msg.attach(MIMEText(text_content, 'plain'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"📧 Sent queue error notification to {recipient_email}")
        
    except Exception as e:
        print(f"❌ Error sending queue error email: {e}")


def send_correction_processing_error_email(recipient_email, correlation_id, error_details):
    """Send email notifying user of processing error."""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = recipient_email
        msg['Subject'] = f"Correction Processing Error [Ref: {correlation_id}]"
        
        text_content = f"""Hello,

We encountered an error processing your correction request.

Reference ID: {correlation_id}
Error: {error_details}

Please try again with a simpler request, or contact support for assistance.

Best regards,
Your Task Manager
"""
        
        msg.attach(MIMEText(text_content, 'plain'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"📧 Sent processing error notification to {recipient_email}")
        
    except Exception as e:
        print(f"❌ Error sending processing error email: {e}")


def check_gmail_for_updates_enhanced():
    """Enhanced Gmail checking with correction support."""
    try:
        # Load persistent state at startup
        print("📂 Loading persistent state...")
        load_persistent_state()
        
        # Initialize AuthService for user lookup
        from src.core.security.jwt_utils import JWTManager
        jwt_manager = JWTManager(secret_key="dummy", algorithm="HS256")
        auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, None)
        
        # Check for pending context conversations that need reminders
        check_and_send_context_reminders()
        
        # Clean up old conversations
        cleanup_old_conversations()

        # Check for outstanding tasks that need reminders
        check_and_send_task_reminders()

        # Sync outstanding tasks with Notion
        unique_users = set()
        for task_info in OUTSTANDING_TASKS.values():
            unique_users.add((task_info['user_email'], task_info['user_database_id']))
        
        for user_email, user_database_id in unique_users:
            sync_outstanding_tasks_with_notion(user_database_id, user_email)
        
        # Connect to Gmail
        print(f"Connecting to {GMAIL_SERVER}...")
        mail = imaplib.IMAP4_SSL(GMAIL_SERVER)
        
        # Login
        print(f"Logging in as {GMAIL_ADDRESS}...")
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        
        # Select inbox
        mail.select("INBOX")
        
        # Search for unread messages
        status, message_ids = mail.search(None, "UNSEEN")
        
        if status != "OK":
            print(f"Error searching for messages: {status}")
            return
        
        if not message_ids[0]:
            print("No unread messages found")
            return
        
        message_id_list = message_ids[0].split()
        print(f"Found {len(message_id_list)} unread messages")
        
        # Process each unread message
        for msg_id in message_id_list:
            print(f"Processing email ID: {msg_id.decode()}")
            
            # Fetch the email
            status, msg_data = mail.fetch(msg_id, "(RFC822)")
            if status != "OK":
                print(f"Error fetching message {msg_id}: {status}")
                continue
                
            # Parse the email
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Get email details
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")
                
            # Get sender info
            from_header = msg["From"]
            sender_name = from_header.split('<')[0].strip() if '<' in from_header else from_header.split('@')[0]
            sender_email = from_header.split('<')[1].split('>')[0] if '<' in from_header else from_header
            
            # Get email body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    if "attachment" in content_disposition:
                        continue
                    
                    if content_type == "text/plain":
                        try:
                            payload = part.get_payload(decode=True)
                            charset = part.get_content_charset() or "utf-8"
                            body = payload.decode(charset)
                            break
                        except:
                            pass
            else:
                content_type = msg.get_content_type()
                if content_type == "text/plain":
                    try:
                        payload = msg.get_payload(decode=True)
                        charset = msg.get_content_charset() or "utf-8"
                        body = payload.decode(charset)
                    except:
                        pass
            
            if not body:
                print("Could not extract email body")
                continue
            
            # Classify email using router
            email_type, correlation_id = email_router.classify_email(msg, subject, body, sender_email)
            
            if email_type == 'correction':
                # Process as correction
                if process_correction_email(msg, body, sender_email, correlation_id):
                    print(f"✅ Correction email processed successfully")
                else:
                    print(f"❌ Failed to process correction email")
                mail.store(msg_id, "+FLAGS", "\\Seen")
                continue
                
            elif email_type == 'context_response':
                # Process as context response (existing logic)
                if process_context_response_email(msg, body, sender_email, sender_name):
                    print(f"✅ Context response processed successfully")
                else:
                    print(f"❌ Failed to process context response")
                mail.store(msg_id, "+FLAGS", "\\Seen")
                continue
                
            else:
                # Process as new task email (existing logic)
                success = process_new_task_email(msg, body, sender_email, sender_name)
                
                # Only mark as read if processing succeeded (or returned None for context verification)
                # If user not found, function returns early and email stays unread for reprocessing
                if success is not False:  # None or True means we can mark as read
                    mail.store(msg_id, "+FLAGS", "\\Seen")
                else:
                    print(f"⚠️ Email NOT marked as read - will retry on next check")
        
        # Close the connection
        mail.close()
        mail.logout()
        print("Enhanced email processing completed")
        
        # Save final state
        print("💾 Saving final persistent state...")
        save_persistent_state()
        
    except Exception as e:
        print(f"Error in enhanced Gmail processing: {str(e)}")
        print(traceback.format_exc())


# Import existing functions from gmail_processor.py
# (These would be imported from the existing gmail_processor.py file)
def load_persistent_state():
    """
    Load persistent state from file with fallback to backup.
    
    Returns:
        dict: Loaded state or empty dict if no file exists
    """
    global PENDING_CONTEXT_CONVERSATIONS, OUTSTANDING_TASKS
    print(f"[DEBUG] Loading persistent state from: {PERSISTENCE_FILE}")
    
    # Try to load from primary file first
    if os.path.exists(PERSISTENCE_FILE):
        try:
            with open(PERSISTENCE_FILE, 'r') as f:
                state = json.load(f)
                print(f"[DEBUG] Raw loaded state: {state}")
                PENDING_CONTEXT_CONVERSATIONS = state.get('pending_context_conversations', {})
                OUTSTANDING_TASKS = state.get('outstanding_tasks', {})
                print(f"✅ Loaded {len(PENDING_CONTEXT_CONVERSATIONS)} pending conversations and {len(OUTSTANDING_TASKS)} outstanding tasks from {PERSISTENCE_FILE}")
                return state
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Error loading primary persistence file: {e}")
    
    # Try backup file if primary failed
    if os.path.exists(PERSISTENCE_BACKUP_FILE):
        try:
            with open(PERSISTENCE_BACKUP_FILE, 'r') as f:
                state = json.load(f)
                print(f"[DEBUG] Raw loaded backup state: {state}")
                PENDING_CONTEXT_CONVERSATIONS = state.get('pending_context_conversations', {})
                OUTSTANDING_TASKS = state.get('outstanding_tasks', {})
                print(f"✅ Loaded {len(PENDING_CONTEXT_CONVERSATIONS)} pending conversations and {len(OUTSTANDING_TASKS)} outstanding tasks from backup file")
                return state
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Error loading backup persistence file: {e}")
    
    # Initialize empty state if no files exist
    print("📝 No persistence files found, starting with empty state")
    PENDING_CONTEXT_CONVERSATIONS = {}
    OUTSTANDING_TASKS = {}
    return {
        'pending_context_conversations': {},
        'outstanding_tasks': {},
        'metadata': {
            'last_save': datetime.datetime.now().isoformat(),
            'version': '1.0'
        }
    }

def save_persistent_state():
    """
    Save current state to file with atomic writes and backup.
    
    Returns:
        bool: True if save was successful
    """
    try:
        # Prepare state data
        state = {
            'pending_context_conversations': PENDING_CONTEXT_CONVERSATIONS,
            'outstanding_tasks': OUTSTANDING_TASKS,
            'metadata': {
                'last_save': datetime.datetime.now().isoformat(),
                'version': '1.0'
            }
        }
        print(f"[DEBUG] Saving persistent state to: {PERSISTENCE_FILE}")
        print(f"[DEBUG] State to save: {json.dumps(state, indent=2, default=str)}")
        
        # Write to temporary file first
        with open(PERSISTENCE_TEMP_FILE, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        # Create backup of current primary file if it exists
        if os.path.exists(PERSISTENCE_FILE):
            import shutil
            shutil.copy2(PERSISTENCE_FILE, PERSISTENCE_BACKUP_FILE)
        
        # Atomic move from temp to primary
        os.rename(PERSISTENCE_TEMP_FILE, PERSISTENCE_FILE)
        
        print(f"✅ Saved {len(PENDING_CONTEXT_CONVERSATIONS)} pending conversations and {len(OUTSTANDING_TASKS)} outstanding tasks to {PERSISTENCE_FILE}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving persistent state: {e}")
        # Clean up temp file if it exists
        if os.path.exists(PERSISTENCE_TEMP_FILE):
            try:
                os.remove(PERSISTENCE_TEMP_FILE)
            except:
                pass
        return False

def cleanup_old_conversations():
    """
    Clean up conversations that are older than 30 days to prevent bloat.
    """
    current_time = datetime.datetime.now()
    cutoff_time = current_time - timedelta(days=30)
    
    conversations_to_remove = []
    for conversation_id, conversation_data in PENDING_CONTEXT_CONVERSATIONS.items():
        if 'created_at' in conversation_data:
            created_time = datetime.datetime.fromisoformat(conversation_data['created_at'])
            if created_time < cutoff_time:
                conversations_to_remove.append(conversation_id)
    
    for conversation_id in conversations_to_remove:
        del PENDING_CONTEXT_CONVERSATIONS[conversation_id]
        print(f"🗑️ Cleaned up old conversation: {conversation_id}")
    
    if conversations_to_remove:
        print(f"✅ Cleaned up {len(conversations_to_remove)} old conversations")

def check_and_send_context_reminders():
    """Check and send context reminders for pending conversations."""
    current_time = datetime.datetime.now()
    cutoff_time = current_time - timedelta(hours=CONTEXT_REMINDER_INTERVAL_HOURS)
    
    for conversation_id, conversation_data in PENDING_CONTEXT_CONVERSATIONS.items():
        if 'last_reminder_sent' not in conversation_data or conversation_data['last_reminder_sent'] is None:
            # Send first reminder
            send_context_reminder_email(
                conversation_data['user_email'],
                conversation_data['context_needed_tasks'],
                conversation_id,
                reminder_count=1
            )
            conversation_data['last_reminder_sent'] = current_time.isoformat()
            print(f"📧 Sent first context reminder for conversation: {conversation_id}")
        else:
            # Check if enough time has passed for another reminder
            try:
                last_reminder = datetime.datetime.fromisoformat(str(conversation_data['last_reminder_sent']))
                if last_reminder < cutoff_time:
                    reminder_count = conversation_data.get('reminder_count', 0) + 1
                    send_context_reminder_email(
                        conversation_data['user_email'],
                        conversation_data['context_needed_tasks'],
                        conversation_id,
                        reminder_count=reminder_count
                    )
                    conversation_data['last_reminder_sent'] = current_time.isoformat()
                    conversation_data['reminder_count'] = reminder_count
                    print(f"📧 Sent reminder #{reminder_count} for conversation: {conversation_id}")
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error parsing reminder date for conversation {conversation_id}: {e}")
                # Reset the reminder timestamp
                conversation_data['last_reminder_sent'] = current_time.isoformat()

def check_and_send_task_reminders():
    """Check and send consolidated task reminders for outstanding tasks."""
    current_time = datetime.datetime.now()
    cutoff_time = current_time - timedelta(hours=TASK_REMINDER_INTERVAL_HOURS)
    
    # Group tasks by user and escalation level
    user_tasks = {}
    
    for task_id, task_data in list(OUTSTANDING_TASKS.items()):
        user_email = task_data['user_email']
        
        # Check if reminder is due
        last_reminder = task_data.get('last_reminder_sent')
        reminder_count = task_data.get('reminder_count', 0)
        
        if last_reminder:
            last_reminder_time = datetime.datetime.fromisoformat(str(last_reminder))
            hours_since_last = (current_time - last_reminder_time).total_seconds() / 3600
        else:
            # No reminder sent yet, check if task was created more than 3 days ago
            created_time = datetime.datetime.fromisoformat(task_data['created_at'])
            hours_since_last = (current_time - created_time).total_seconds() / 3600
        
        # Determine reminder interval based on urgency
        if reminder_count >= 2:  # After 2 reminders, send urgent reminders
            reminder_interval = 168  # 7 days
        else:
            reminder_interval = TASK_REMINDER_INTERVAL_HOURS  # 3 days
        
        if hours_since_last >= reminder_interval:
            # Determine escalation level
            if reminder_count >= 3:
                escalation_level = "URGENT"
            elif reminder_count >= 2:
                escalation_level = "IMPORTANT"
            else:
                escalation_level = "GENTLE"
            
            # Group by user and escalation level
            if user_email not in user_tasks:
                user_tasks[user_email] = {}
            
            if escalation_level not in user_tasks[user_email]:
                user_tasks[user_email][escalation_level] = []
            
            user_tasks[user_email][escalation_level].append({
                'task_id': task_id,
                'task_data': task_data,
                'reminder_count': reminder_count
            })
    
    # Send consolidated reminders for each user
    for user_email, escalation_groups in user_tasks.items():
        if escalation_groups:
            print(f"📧 Sending consolidated task reminders to {user_email}")
            
            # Send consolidated reminder email
            success = send_consolidated_task_reminder_email(user_email, escalation_groups)
            
            if success:
                # Update all tasks for this user with reminder info
                for escalation_level, tasks in escalation_groups.items():
                    for task_info in tasks:
                        task_id = task_info['task_id']
                        reminder_count = task_info['reminder_count']
                        
                        OUTSTANDING_TASKS[task_id]['last_reminder_sent'] = current_time.isoformat()
                        OUTSTANDING_TASKS[task_id]['reminder_count'] = reminder_count + 1
                
                print(f"✅ Sent consolidated reminder to {user_email} with {sum(len(tasks) for tasks in escalation_groups.values())} tasks")
                
                # Save state after updating reminder info
                save_persistent_state()
            else:
                print(f"❌ Failed to send consolidated reminder to {user_email}")
    
    if not user_tasks:
        print(f"✅ No outstanding tasks need reminders")

def sync_outstanding_tasks_with_notion(user_database_id, user_email):
    """Sync outstanding tasks with Notion database."""
    try:
        # Get existing tasks from Notion
        existing_tasks = fetch_notion_tasks(user_database_id)
        
        # Update outstanding tasks with current status
        for task_id, task_data in OUTSTANDING_TASKS.items():
            if task_data['user_email'] == user_email:
                # Check if task still exists in Notion
                task_exists = any(task.get('id') == task_id for task in existing_tasks)
                if not task_exists:
                    # Task was completed or deleted, remove from outstanding
                    del OUTSTANDING_TASKS[task_id]
                    print(f"🗑️ Removed completed task from outstanding: {task_id}")
        
        print(f"✅ Synced outstanding tasks with Notion for user: {user_email}")
        
    except Exception as e:
        print(f"❌ Error syncing outstanding tasks with Notion: {e}")

def process_context_response_email(msg, body, sender_email, sender_name):
    """
    Process context response email and complete the workflow.
    
    Args:
        msg: Email message object
        body: Email body
        sender_email: Sender email address
        sender_name: Sender name
        
    Returns:
        bool: True if successfully processed
    """
    try:
        print(f"📧 Processing context response from {sender_email}")
        
        # Extract conversation ID
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else "utf-8")
        
        conversation_id = email_router.extract_conversation_id(subject, body)
        if not conversation_id:
            print("Could not extract conversation ID from email")
            return False
        
        # Get pending conversation
        conversation = get_pending_context_conversation(conversation_id)
        if not conversation:
            print(f"No pending conversation found for ID: {conversation_id}")
            return False
        
        print(f"📧 Processing context response for conversation: {conversation_id}")
        
        # Parse the user's response using existing logic
        context_needed_tasks = conversation['context_needed_tasks']
        
        # Create a mock chat context for the parsing function
        chat_context = {
            'pending_tasks': context_needed_tasks
        }
        
        # Parse the response using existing verification logic
        result = parse_verification_response(body, chat_context)
        
        if result['status'] == 'complete':
            # All tasks verified, process them
            verified_tasks = result['updated_tasks']
            ready_tasks = conversation['ready_tasks']
            all_tasks = ready_tasks + verified_tasks
            
            print(f"✅ All tasks verified, processing {len(all_tasks)} tasks")
            
            # Get existing tasks from user's database
            existing_tasks = fetch_notion_tasks(conversation['user_database_id'])
            
            # Process all tasks
            successful_tasks = 0
            for task in all_tasks:
                try:
                    success, message = insert_or_update_task(
                        database_id=conversation['user_database_id'],
                        task=task,
                        existing_tasks=existing_tasks
                    )
                    if success:
                        successful_tasks += 1
                        print(f"✅ Processed task: {task.get('task', '')[:50]}...")
                    else:
                        print(f"❌ Failed to process task: {message}")
                except Exception as e:
                    print(f"❌ Error processing task: {e}")
            
            # Generate coaching insights
            coaching_insights = None
            if successful_tasks > 0:
                try:
                    coaching_insights = get_coaching_insight(
                        sender_name,
                        all_tasks,
                        existing_tasks,
                        []
                    )
                    print("✅ Generated coaching insights")
                except Exception as e:
                    print(f"⚠️ Failed to generate coaching insights: {e}")
            
            # NOW send confirmation email WITH correlation ID (after context verification is complete)
            send_confirmation_email_with_correction_support(
                recipient=sender_email,
                tasks=all_tasks,
                coaching_insights=coaching_insights,
                user_database_id=conversation['user_database_id']
            )
            
            # Clean up conversation
            remove_pending_context_conversation(conversation_id)
            
            print(f"✅ Context response processed successfully. {successful_tasks} tasks processed.")
            return True
            
        elif result['status'] == 'partial':
            # Some tasks verified, but others still need context
            verified_tasks = result['updated_tasks']
            still_pending_tasks = result['pending_tasks']
            ready_tasks = conversation['ready_tasks']
            
            # Get existing tasks from user's database
            existing_tasks = fetch_notion_tasks(conversation['user_database_id'])
            
            # Process verified tasks
            successful_tasks = 0
            for task in verified_tasks + ready_tasks:
                try:
                    success, message = insert_or_update_task(
                        database_id=conversation['user_database_id'],
                        task=task,
                        existing_tasks=existing_tasks
                    )
                    if success:
                        successful_tasks += 1
                except Exception as e:
                    print(f"❌ Error processing task: {e}")
            
            # Update conversation with remaining pending tasks
            update_pending_context_conversation(
                conversation_id=conversation_id,
                context_needed_tasks=still_pending_tasks
            )
            
            # Send follow-up context request
            send_context_request_email(
                recipient=sender_email,
                context_needed_tasks=still_pending_tasks,
                conversation_id=conversation_id,
                ready_tasks_count=successful_tasks
            )
            
            print(f"✅ Partial context response processed. {successful_tasks} tasks processed, {len(still_pending_tasks)} still need context.")
            return True
            
        else:
            # Error or no tasks updated
            print(f"❌ Failed to process context response: {result.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing context response: {str(e)}")
        print(traceback.format_exc())
        return False


def process_new_task_email(msg, body, sender_email, sender_name):
    """
    Process new task email with context verification support.
    
    Args:
        msg: Email message object
        body: Email body
        sender_email: Sender email address
        sender_name: Sender name
        
    Returns:
        bool: True if processing succeeded, False if failed (user not found), None if context verification needed
    """
    try:
        print(f"📧 Processing new task email from {sender_email}")
        
        # Get user information
        from src.core.security.jwt_utils import JWTManager
        jwt_manager = JWTManager(secret_key="dummy", algorithm="HS256")
        auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, None)
        user = auth_service.get_user_by_email(sender_email)
        
        if not user:
            print(f"❌ User not found for email: {sender_email}")
            print(f"   ACTION REQUIRED: Register this email in the Notion users database")
            print(f"   The email will NOT be marked as read so it can be reprocessed after registration")
            # Don't mark as read - allow reprocessing after user is registered
            return False  # Return False to indicate failure
        
        # Get existing tasks from user's database
        existing_tasks = fetch_notion_tasks(user.task_database_id)
        
        # Extract tasks from email
        chunks = chunk_email_text(body, 20)
        tasks = []
        
        for chunk in chunks:
            chunk_tasks = extract_tasks_from_update(chunk)
            tasks.extend(chunk_tasks)
        
        if not tasks:
            print("No tasks found in email")
            return True  # Mark as read - no tasks to process
        
        print(f"📋 Extracted {len(tasks)} tasks")
        
        # Classify tasks by context needs
        ready_tasks, context_needed_tasks = classify_tasks_by_context_needs(tasks)
        
        print(f"📊 Task classification:")
        print(f"   Ready tasks: {len(ready_tasks)}")
        print(f"   Context needed tasks: {len(context_needed_tasks)}")
        
        # Handle context verification if needed
        if context_needed_tasks:
            print(f"📧 Context verification needed for {len(context_needed_tasks)} tasks")
            
            # Process ready tasks immediately (even when context verification is needed)
            if ready_tasks:
                print(f"✅ Processing {len(ready_tasks)} ready tasks immediately (before context verification)")
                ready_successful = 0
                for task in ready_tasks:
                    try:
                        success, message = insert_or_update_task(
                            database_id=user.task_database_id,
                            task=task,
                            existing_tasks=existing_tasks
                        )
                        if success:
                            ready_successful += 1
                            print(f"✅ Processed ready task: {task.get('task', '')[:50]}...")
                        else:
                            print(f"❌ Failed to process ready task: {message}")
                    except Exception as e:
                        print(f"❌ Error processing ready task: {e}")
                
                # Send confirmation for ready tasks if any were processed
                if ready_successful > 0:
                    try:
                        coaching_insights = get_coaching_insight(
                            sender_name,
                            ready_tasks,
                            existing_tasks,
                            []
                        )
                    except Exception as e:
                        print(f"⚠️ Failed to generate coaching insights: {e}")
                        coaching_insights = None
                    
                    send_confirmation_email_with_correction_support(
                        recipient=sender_email,
                        tasks=[t for i, t in enumerate(ready_tasks) if i < ready_successful],
                        coaching_insights=coaching_insights,
                        user_database_id=user.task_database_id
                    )
                    print(f"✅ Sent confirmation email for {ready_successful} processed tasks")
            
            # Generate conversation ID for tracking
            conversation_id = generate_conversation_id()
            
            # Store pending conversation (only for context_needed_tasks, ready_tasks already processed)
            store_pending_context_conversation(
                conversation_id=conversation_id,
                user_email=sender_email,
                ready_tasks=[],  # Empty - already processed above
                context_needed_tasks=context_needed_tasks,
                original_email_id=msg.get('Message-ID', ''),
                user_database_id=user.task_database_id
            )
            
            # Send context request email (NO correlation ID yet)
            send_context_request_email(
                recipient=sender_email,
                context_needed_tasks=context_needed_tasks,
                conversation_id=conversation_id,
                ready_tasks_count=len(ready_tasks)  # Report count of already-processed tasks
            )
            
            print(f"✅ Context request email sent with conversation_id: {conversation_id}")
            return None  # Return None for context verification (email will be marked as read)
        
        # If no context needed, process tasks immediately
        print(f"✅ No context verification needed, processing {len(ready_tasks)} tasks immediately")
        
        # Process ready tasks
        successful_tasks = 0
        for task in ready_tasks:
            try:
                success, message = insert_or_update_task(
                    database_id=user.task_database_id,
                    task=task,
                    existing_tasks=existing_tasks
                )
                if success:
                    successful_tasks += 1
                    print(f"✅ Processed task: {task.get('task', '')[:50]}...")
                else:
                    print(f"❌ Failed to process task: {message}")
            except Exception as e:
                print(f"❌ Error processing task: {e}")
        
        # Generate coaching insights
        coaching_insights = None
        if successful_tasks > 0:
            try:
                coaching_insights = get_coaching_insight(
                    sender_name,
                    ready_tasks,
                    existing_tasks,
                    []
                )
                print("✅ Generated coaching insights")
            except Exception as e:
                print(f"⚠️ Failed to generate coaching insights: {e}")
        
        # NOW send confirmation email WITH correlation ID (after context verification is complete)
        send_confirmation_email_with_correction_support(
            recipient=sender_email,
            tasks=ready_tasks,
            coaching_insights=coaching_insights,
            user_database_id=user.task_database_id
        )
        
        print(f"✅ Confirmation email with correction support sent to {sender_email}")
        
        return True  # Success
        
    except Exception as e:
        print(f"❌ Error processing new task email: {str(e)}")
        print(traceback.format_exc())
        return False  # Failure


# Global variables (would be imported from existing gmail_processor.py)
OUTSTANDING_TASKS = {} 

# Persistence configuration
PERSISTENCE_FILE = "pending_conversations.json"
PERSISTENCE_BACKUP_FILE = "pending_conversations_backup.json"
PERSISTENCE_TEMP_FILE = "pending_conversations_temp.json"

# Helper functions (would be imported from existing gmail_processor.py)
def generate_conversation_id():
    """Generate a unique conversation ID."""
    return str(uuid.uuid4())

def store_pending_context_conversation(conversation_id, user_email, ready_tasks, context_needed_tasks, original_email_id, user_database_id):
    """Store pending context conversation."""
    try:
        PENDING_CONTEXT_CONVERSATIONS[conversation_id] = {
            'user_email': user_email,
            'ready_tasks': ready_tasks,
            'context_needed_tasks': context_needed_tasks,
            'original_email_id': original_email_id,
            'user_database_id': user_database_id,
            'created_at': datetime.datetime.now().isoformat(),
            'last_reminder_sent': None,
            'reminder_count': 0,
            'ready_tasks_processed': False,
            'context_tasks_processed': False
        }
        print(f"✅ Stored pending context conversation: {conversation_id}")
        return True
    except Exception as e:
        print(f"❌ Error storing pending context conversation: {e}")
        return False

def get_pending_context_conversation(conversation_id):
    """Get pending context conversation."""
    return PENDING_CONTEXT_CONVERSATIONS.get(conversation_id)

def update_pending_context_conversation(conversation_id, context_needed_tasks):
    """Update pending context conversation."""
    if conversation_id in PENDING_CONTEXT_CONVERSATIONS:
        PENDING_CONTEXT_CONVERSATIONS[conversation_id]['context_needed_tasks'] = context_needed_tasks
        return True
    return False

def remove_pending_context_conversation(conversation_id):
    """Remove pending context conversation."""
    if conversation_id in PENDING_CONTEXT_CONVERSATIONS:
        del PENDING_CONTEXT_CONVERSATIONS[conversation_id]
        print(f"🗑️ Removed pending context conversation: {conversation_id}")
        return True
    return False

def send_context_request_email(recipient, context_needed_tasks, conversation_id, ready_tasks_count=0):
    """Send context request email."""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = recipient
        msg['Subject'] = f"Context Needed for {len(context_needed_tasks)} Tasks"
        
        # Create plain text version
        text_content = f"""Hi there,

We need additional context for some of your tasks.

Tasks requiring context:
"""
        for i, task in enumerate(context_needed_tasks, 1):
            text_content += f"{i}. {task.get('task', 'Unknown task')}\n"
        
        if ready_tasks_count > 0:
            text_content += f"\nNote: {ready_tasks_count} other tasks were processed successfully.\n"
        
        text_content += f"""

Please reply to this email with the additional context needed for the tasks above.

Conversation ID: {conversation_id}

Best regards,
Your Task Manager
"""
        
        # Create HTML version
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #4361ee; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .task {{ margin-bottom: 10px; padding: 10px; background-color: #fff3cd; border-left: 4px solid #ffc107; }}
                .section-header {{ margin-top: 30px; margin-bottom: 15px; padding: 10px; background-color: #e9ecef; border-radius: 5px; font-weight: bold; }}
                .conversation-id {{ background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace; margin: 20px 0; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Context Required</h2>
            </div>
            <div class="content">
                <p>We need additional context for some of your tasks before we can process them.</p>
                
                <div class="section-header">
                    📋 Tasks Requiring Context ({len(context_needed_tasks)} tasks)
                </div>
                
                <div class="tasks">
        """
        
        for i, task in enumerate(context_needed_tasks, 1):
            title = task.get('title', '')
            task_desc = task.get('task', '')
            status = task.get('status', 'Unknown')
            category = task.get('category', 'Uncategorized')
            
            html_content += f"""
                    <div class="task">
            """
            
            if title:
                html_content += f"""
                        <strong>{i}. {title}</strong><br>
                    """
                if task_desc and task_desc != title:
                    html_content += f"""
                        <em style="color: #666; font-size: 14px;">{task_desc}</em><br>
                        """
            else:
                html_content += f"""
                        <strong>{i}. {task_desc}</strong><br>
                    """
            
            html_content += f"""
                        <span style="margin-left: 10px; color: #666;">Category: {category}</span>
                    </div>
                """
        
        if ready_tasks_count > 0:
            html_content += f"""
                <div style="margin-top: 20px; padding: 10px; background-color: #d4edda; border-left: 4px solid #28a745; border-radius: 5px;">
                    <strong>✅ {ready_tasks_count} other tasks were processed successfully.</strong>
                </div>
            """
        
        html_content += f"""
                </div>
                
                <p>Please reply to this email with the additional context needed for the tasks above.</p>
                
                <div class="conversation-id">
                    <strong>Conversation ID:</strong> {conversation_id}
                </div>
                
                <p>Best regards,<br>Your Task Manager</p>
            </div>
            <div class="footer">
                <p>This is an automated message. Please reply to this email with additional context.</p>
            </div>
        </body>
        </html>
        """
        
        # Attach parts
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"📧 Sent context request email to {recipient}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending context request email: {e}")
        return False

def classify_tasks_by_context_needs(tasks):
    """Classify tasks by context needs."""
    try:
        ready_tasks = []
        context_needed_tasks = []
        
        for task in tasks:
            # Check if task needs context verification
            task_text = task.get('task', '')
            task_title = task.get('title', '')
            
            # Simple heuristic: if task contains vague terms, it needs context
            vague_terms = [
                'check', 'review', 'follow up', 'update', 'progress',
                'status', 'next steps', 'continue', 'ongoing', 'work on',
                'develop', 'plan', 'organize', 'coordinate', 'meet',
                'discuss', 'talk', 'contact', 'reach out', 'schedule'
            ]
            
            needs_context = any(term in task_text.lower() or term in task_title.lower() 
                              for term in vague_terms)
            
            if needs_context:
                context_needed_tasks.append(task)
            else:
                ready_tasks.append(task)
        
        print(f"📋 Classified {len(ready_tasks)} ready tasks and {len(context_needed_tasks)} tasks needing context")
        return ready_tasks, context_needed_tasks
        
    except Exception as e:
        print(f"❌ Error classifying tasks: {e}")
        # Return all tasks as ready if classification fails
        return tasks, []

def parse_verification_response(user_response, chat_context):
    """Parse verification response."""
    # Implementation from existing gmail_processor.py
    pass 

# Add missing helper functions
def send_context_reminder_email(recipient, context_needed_tasks, conversation_id, reminder_count=1):
    """Send context reminder email."""
    try:
        # Create email content
        subject = f"Reminder: Context Needed for Tasks (Reminder #{reminder_count})"
        
        # Build email body
        body = f"""Hi there,

This is a reminder that we need additional context for some of your tasks.

Tasks requiring context:
"""
        for i, task in enumerate(context_needed_tasks, 1):
            body += f"{i}. {task.get('task', 'Unknown task')}\n"
        
        body += f"""

Please reply to this email with the additional context needed.

Conversation ID: {conversation_id}

Best regards,
Your Task Manager
"""
        
        # Send email
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = recipient
        
        with smtplib.SMTP_SSL(GMAIL_SERVER, 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"📧 Sent context reminder email to {recipient}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending context reminder email: {e}")
        return False

def send_consolidated_task_reminder_email(recipient, escalation_groups):
    """
    Send a consolidated task reminder email with tasks grouped by escalation level.
    
    Args:
        recipient: Email address to send to
        escalation_groups: Dict with escalation levels as keys and lists of task info as values
        
    Returns:
        bool: True if email sent successfully
    """
    try:
        # Calculate total tasks and determine overall urgency
        total_tasks = sum(len(tasks) for tasks in escalation_groups.values())
        
        # Determine overall urgency level
        if "URGENT" in escalation_groups:
            overall_urgency = "URGENT"
            subject_prefix = "URGENT: "
            header_color = "#dc3545"
        elif "IMPORTANT" in escalation_groups:
            overall_urgency = "Important"
            subject_prefix = "Reminder: "
            header_color = "#ffc107"
        else:
            overall_urgency = "Gentle"
            subject_prefix = "Friendly Reminder: "
            header_color = "#17a2b8"
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = recipient
        msg['Subject'] = f"{subject_prefix}Task Reminders - {total_tasks} Tasks Need Attention"
        
        # Create plain text email
        text_content = f"Hello,\n\n"
        
        if overall_urgency == "URGENT":
            text_content += f"This is an URGENT reminder about {total_tasks} outstanding tasks that require your immediate attention:\n\n"
        elif overall_urgency == "Important":
            text_content += f"This is an important reminder about {total_tasks} outstanding tasks:\n\n"
        else:
            text_content += f"This is a friendly reminder about {total_tasks} outstanding tasks:\n\n"
        
        # Add tasks by escalation level
        for escalation_level in ["URGENT", "IMPORTANT", "GENTLE"]:
            if escalation_level in escalation_groups:
                tasks = escalation_groups[escalation_level]
                text_content += f"--- {escalation_level} PRIORITY ({len(tasks)} tasks) ---\n\n"
                
                for i, task_info in enumerate(tasks, 1):
                    task_data = task_info['task_data']['task_data']
                    task_id = task_info['task_id']
                    reminder_count = task_info['reminder_count']
                    
                    task_title = task_data.get('task', 'Untitled Task')
                    task_description = task_data.get('description', 'No description')
                    due_date = task_data.get('due_date', 'No due date')
                    priority = task_data.get('priority', 'Unknown')
                    
                    text_content += f"{i}. {task_title}\n"
                    if task_description and task_description != task_title:
                        text_content += f"   Description: {task_description}\n"
                    text_content += f"   Priority: {priority} | Due Date: {due_date}\n"
                    text_content += f"   Reminder #{reminder_count + 1}\n\n"
        
        text_content += "Please update the status of these tasks in your task management system.\n\n"
        text_content += "Thank you for your attention to these matters.\n"
        
        # Create HTML version
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: {header_color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .escalation-section {{ margin-bottom: 30px; }}
                .escalation-header {{ padding: 10px; border-radius: 5px; font-weight: bold; margin-bottom: 15px; }}
                .urgent {{ background-color: #dc3545; color: white; }}
                .important {{ background-color: #ffc107; color: #333; }}
                .gentle {{ background-color: #17a2b8; color: white; }}
                .task {{ margin-bottom: 10px; padding: 15px; background-color: #f8f9fa; border-left: 4px solid {header_color}; }}
                .task-title {{ font-weight: bold; margin-bottom: 5px; }}
                .task-details {{ color: #666; font-size: 14px; }}
                .reminder-count {{ display: inline-block; padding: 2px 6px; border-radius: 10px; font-size: 12px; font-weight: bold; margin-left: 10px; }}
                .reminder-urgent {{ background-color: #dc3545; color: white; }}
                .reminder-important {{ background-color: #ffc107; color: #333; }}
                .reminder-gentle {{ background-color: #17a2b8; color: white; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Task Manager: {overall_urgency} Reminder</h2>
                <p>{total_tasks} Tasks Need Your Attention</p>
            </div>
            <div class="content">
        """
        
        if overall_urgency == "URGENT":
            html_content += f"""
                <p>This is an <strong>URGENT</strong> reminder about {total_tasks} outstanding tasks that require your immediate attention:</p>
            """
        elif overall_urgency == "Important":
            html_content += f"""
                <p>This is an <strong>important</strong> reminder about {total_tasks} outstanding tasks:</p>
            """
        else:
            html_content += f"""
                <p>This is a <strong>friendly</strong> reminder about {total_tasks} outstanding tasks:</p>
            """
        
        # Add tasks by escalation level
        for escalation_level in ["URGENT", "IMPORTANT", "GENTLE"]:
            if escalation_level in escalation_groups:
                tasks = escalation_groups[escalation_level]
                level_class = escalation_level.lower()
                
                html_content += f"""
                    <div class="escalation-section">
                        <div class="escalation-header {level_class}">
                            🚨 {escalation_level} PRIORITY ({len(tasks)} tasks)
                        </div>
                """
                
                for i, task_info in enumerate(tasks, 1):
                    task_data = task_info['task_data']['task_data']
                    task_id = task_info['task_id']
                    reminder_count = task_info['reminder_count']
                    
                    task_title = task_data.get('task', 'Untitled Task')
                    task_description = task_data.get('description', 'No description')
                    due_date = task_data.get('due_date', 'No due date')
                    priority = task_data.get('priority', 'Unknown')
                    
                    # Determine reminder count styling
                    if reminder_count >= 3:
                        reminder_class = "reminder-urgent"
                    elif reminder_count >= 2:
                        reminder_class = "reminder-important"
                    else:
                        reminder_class = "reminder-gentle"
                    
                    html_content += f"""
                        <div class="task">
                            <div class="task-title">
                                {i}. {task_title}
                                <span class="reminder-count {reminder_class}">Reminder #{reminder_count + 1}</span>
                            </div>
                    """
                    
                    if task_description and task_description != task_title:
                        html_content += f"""
                            <div class="task-details">Description: {task_description}</div>
                        """
                    
                    html_content += f"""
                            <div class="task-details">
                                Priority: {priority} | Due Date: {due_date}
                            </div>
                        </div>
                    """
                
                html_content += """
                    </div>
                """
        
        html_content += f"""
                <p>Please update the status of these tasks in your task management system.</p>
                
                <p>Thank you for your attention to these matters.</p>
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
        
        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"📧 Sent consolidated task reminder email to {recipient}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending consolidated task reminder email: {e}")
        import traceback
        traceback.print_exc()
        return False

def send_task_reminder_email(recipient, task_data, task_id, reminder_count=1):
    """Send individual task reminder email (legacy function - kept for compatibility)."""
    # This function is now deprecated in favor of consolidated reminders
    # But kept for backward compatibility
    return send_consolidated_task_reminder_email(recipient, {
        "GENTLE": [{
            'task_id': task_id,
            'task_data': {'task_data': task_data},
            'reminder_count': reminder_count - 1
        }]
    })

# Main execution block
if __name__ == "__main__":
    print("🚀 Starting Enhanced Gmail Processor...")
    print("=" * 50)
    
    try:
        check_gmail_for_updates_enhanced()
        print("✅ Enhanced Gmail processor completed successfully")
    except Exception as e:
        print(f"❌ Enhanced Gmail processor failed: {e}")
        print(traceback.format_exc())