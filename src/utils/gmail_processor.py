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

# Import AuthService for user lookup
from src.core.services.auth_service import AuthService

# Import EmailArchiveService for email archiving
if EMAIL_ARCHIVE_ENABLED:
    from src.core.services.email_archive_service import EmailArchiveService

from src.core.ai.extractors import chunk_email_text
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
# In production, this should be replaced with a proper database
PENDING_CONTEXT_CONVERSATIONS = {}

# Configuration for reminders
CONTEXT_REMINDER_INTERVAL_HOURS = 24  # Send reminder after 24 hours
TASK_REMINDER_INTERVAL_HOURS = 72     # Send task reminder after 3 days (for future use)

# Persistence configuration
PERSISTENCE_FILE = "pending_conversations.json"
PERSISTENCE_BACKUP_FILE = "pending_conversations_backup.json"
PERSISTENCE_TEMP_FILE = "pending_conversations_temp.json"

# Outstanding tasks tracking
OUTSTANDING_TASKS = {}

def extract_reply_from_email_body(body: str) -> str:
    """
    Extract just the reply part from an email body that contains a full thread.
    
    Args:
        body: Full email body containing thread history
        
    Returns:
        str: Just the reply part, or original body if no clear reply detected
    """
    if not body:
        return body
    
    # Common patterns that indicate the start of quoted/replied content
    quote_patterns = [
        r'^>.*$',  # Lines starting with >
        r'^On .* wrote:$',  # "On [date] [person] wrote:"
        r'^From:.*$',  # "From: [email]"
        r'^Sent:.*$',  # "Sent: [date]"
        r'^To:.*$',    # "To: [email]"
        r'^Subject:.*$',  # "Subject: [subject]"
        r'^-{3,}.*$',  # Separator lines (---)
        r'^_{3,}.*$',  # Separator lines (___)
        r'^\*{3,}.*$',  # Separator lines (***)
        r'^From:.*\nSent:.*\nTo:.*\nSubject:.*',  # Outlook style headers
        r'^Le .* a écrit :$',  # French "On [date] wrote:"
        r'^El .* escribió:$',  # Spanish "On [date] wrote:"
        r'^Am .* schrieb .*:$',  # German "On [date] wrote:"
    ]
    
    lines = body.split('\n')
    reply_lines = []
    
    for i, line in enumerate(lines):
        # Check if this line matches any quote pattern
        is_quote_start = False
        for pattern in quote_patterns:
            if re.match(pattern, line.strip(), re.IGNORECASE):
                is_quote_start = True
                break
        
        if is_quote_start:
            # Found the start of quoted content, return everything before this
            reply_lines = lines[:i]
            break
        else:
            reply_lines.append(line)
    
    # Join the reply lines and clean up
    reply_text = '\n'.join(reply_lines).strip()
    
    # If we didn't find any quote patterns, try to find the last non-empty line
    # that doesn't look like a quote
    if not reply_text:
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if line and not any(re.match(pattern, line, re.IGNORECASE) for pattern in quote_patterns):
                # Found a non-quote line, take everything up to this point
                reply_lines = lines[:i+1]
                reply_text = '\n'.join(reply_lines).strip()
                break
    
    # If still no reply found, return the first few lines (likely the actual reply)
    if not reply_text:
        # Take first 10 lines or until we hit a quote pattern
        reply_lines = []
        for line in lines[:10]:
            if any(re.match(pattern, line.strip(), re.IGNORECASE) for pattern in quote_patterns):
                break
            reply_lines.append(line)
        reply_text = '\n'.join(reply_lines).strip()
    
    return reply_text if reply_text else body

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
    
    for conversation_id, conversation in PENDING_CONTEXT_CONVERSATIONS.items():
        created_time = datetime.datetime.fromisoformat(conversation['created_at'])
        if created_time < cutoff_time:
            conversations_to_remove.append(conversation_id)
    
    if conversations_to_remove:
        for conv_id in conversations_to_remove:
            del PENDING_CONTEXT_CONVERSATIONS[conv_id]
        print(f"🗑️ Cleaned up {len(conversations_to_remove)} old conversations")
        save_persistent_state()

def track_outstanding_task(task_id, user_email, task_data, user_database_id):
    """
    Track a task that needs completion reminders.
    
    Args:
        task_id: Unique task identifier
        user_email: Email of the user responsible
        task_data: Task information (title, description, due_date, etc.)
        user_database_id: User's Notion database ID
    """
    OUTSTANDING_TASKS[task_id] = {
        'user_email': user_email,
        'task_data': task_data,
        'user_database_id': user_database_id,
        'created_at': datetime.datetime.now().isoformat(),
        'last_reminder_sent': None,
        'reminder_count': 0,
        'status': 'pending'  # pending, completed, cancelled
    }
    print(f"📝 Tracking outstanding task: {task_id} for {user_email}")
    
    # Save state immediately
    save_persistent_state()

def mark_task_completed(task_id):
    """Mark a task as completed and remove from tracking."""
    if task_id in OUTSTANDING_TASKS:
        del OUTSTANDING_TASKS[task_id]
        print(f"✅ Task completed and removed from tracking: {task_id}")
        
        # Save state immediately
        save_persistent_state()

def should_track_task_for_reminders(task):
    """
    Determine if a task should be tracked for completion reminders.
    
    Args:
        task: Task dictionary from Notion
        
    Returns:
        bool: True if task should be tracked
    """
    # Track tasks that are not completed
    status = task.get('status', '').lower()
    if status in ['completed', 'cancelled', 'done']:
        return False
    
    # Track tasks with specific statuses
    if status in ['not started', 'in progress', 'pending', 'on hold']:
        return True
    
    # Track tasks with due dates (if implemented)
    if task.get('due_date'):
        return True
    
    # If we can't determine, don't track (conservative approach)
    return False

def generate_task_id(task, user_database_id):
    """
    Generate a unique task ID for tracking.
    
    Args:
        task: Task dictionary
        user_database_id: User's Notion database ID
        
    Returns:
        str: Unique task identifier
    """
    # Use a combination of database ID, task title, and employee for uniqueness
    task_title = task.get('task', '')[:50]  # Limit length
    employee = task.get('employee', '')
    date = task.get('date', '')
    
    # Create a hash-based ID
    import hashlib
    task_string = f"{user_database_id}:{task_title}:{employee}:{date}"
    task_hash = hashlib.md5(task_string.encode()).hexdigest()[:12]
    
    return f"task_{task_hash}"

def sync_outstanding_tasks_with_notion(user_database_id, user_email):
    """
    Sync outstanding tasks with current Notion state to detect completions.
    
    Args:
        user_database_id: User's Notion database ID
        user_email: User's email address
    """
    try:
        # Get current tasks from Notion
        current_tasks = fetch_notion_tasks(database_id=user_database_id)
        
        if current_tasks.empty:
            return
        
        # Check each tracked task against current Notion state
        tasks_to_remove = []
        
        for task_id, tracked_task in OUTSTANDING_TASKS.items():
            # Only check tasks for this user
            if tracked_task['user_email'] != user_email:
                continue
                
            tracked_task_data = tracked_task['task_data']
            tracked_title = tracked_task_data.get('task', '')
            tracked_employee = tracked_task_data.get('employee', '')
            tracked_date = tracked_task_data.get('date', '')
            
            # Find matching task in current Notion data
            matching_task = None
            for _, notion_task in current_tasks.iterrows():
                notion_title = notion_task.get('task', '')
                notion_employee = notion_task.get('employee', '')
                notion_date = notion_task.get('date', '')
                
                # Check if this is the same task
                if (notion_title == tracked_title and 
                    notion_employee == tracked_employee and 
                    notion_date == tracked_date):
                    matching_task = notion_task
                    break
            
            # If task not found or status changed to completed, mark for removal
            if matching_task is None:
                print(f"📋 Task not found in Notion, marking as completed: {tracked_title}")
                tasks_to_remove.append(task_id)
            elif matching_task.get('status', '').lower() in ['completed', 'done']:
                print(f"📋 Task marked as completed in Notion: {tracked_title}")
                tasks_to_remove.append(task_id)
        
        # Remove completed tasks
        for task_id in tasks_to_remove:
            mark_task_completed(task_id)
            
    except Exception as e:
        print(f"⚠️ Error syncing outstanding tasks with Notion: {e}")

def check_and_send_task_reminders():
    """
    Check for outstanding tasks that need reminders and send them.
    This follows the same pattern as context verification reminders.
    """
    print(f"\n🔍 Checking for outstanding tasks that need reminders...")
    
    current_time = datetime.datetime.now()
    tasks_to_remind = []
    
    for task_id, task_info in OUTSTANDING_TASKS.items():
        # Skip if already completed
        if task_info.get('status') == 'completed':
            continue
            
        # Check if reminder is due
        last_reminder = task_info.get('last_reminder_sent')
        reminder_count = task_info.get('reminder_count', 0)
        
        if last_reminder:
            last_reminder_time = datetime.datetime.fromisoformat(last_reminder)
            hours_since_last = (current_time - last_reminder_time).total_seconds() / 3600
        else:
            # No reminder sent yet, check if task was created more than 3 days ago
            created_time = datetime.datetime.fromisoformat(task_info['created_at'])
            hours_since_last = (current_time - created_time).total_seconds() / 3600
        
        # Determine reminder interval based on urgency
        if reminder_count >= 2:  # After 2 reminders, send urgent reminders
            reminder_interval = 168  # 7 days
        else:
            reminder_interval = TASK_REMINDER_INTERVAL_HOURS  # 3 days
        
        if hours_since_last >= reminder_interval:
            tasks_to_remind.append((task_id, task_info))
    
    if not tasks_to_remind:
        print(f"✅ No outstanding tasks need reminders")
        return
    
    print(f"📧 Sending reminders for {len(tasks_to_remind)} outstanding tasks...")
    
    for task_id, task_info in tasks_to_remind:
        try:
            # Send reminder email
            success = send_task_reminder_email(
                recipient=task_info['user_email'],
                task_data=task_info['task_data'],
                task_id=task_id,
                reminder_count=task_info.get('reminder_count', 0) + 1
            )
            
            if success:
                # Update task with reminder info
                task_info['last_reminder_sent'] = current_time.isoformat()
                task_info['reminder_count'] = task_info.get('reminder_count', 0) + 1
                print(f"✅ Sent reminder for task: {task_id}")
                
                # Save state after updating reminder info
                save_persistent_state()
            else:
                print(f"❌ Failed to send reminder for task: {task_id}")
                
        except Exception as e:
            print(f"❌ Error sending reminder for task {task_id}: {e}")

def send_task_reminder_email(recipient, task_data, task_id, reminder_count=1):
    """
    Send a reminder email for outstanding tasks.
    
    Args:
        recipient: Email address to send to
        task_data: Task information
        task_id: Unique task identifier
        reminder_count: Number of reminders sent so far
        
    Returns:
        bool: True if email sent successfully
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = recipient
        
        task_title = task_data.get('task', 'Untitled Task')
        task_description = task_data.get('description', 'No description')
        due_date = task_data.get('due_date', 'No due date')
        
        # Determine urgency level
        if reminder_count >= 3:
            urgency_level = "URGENT"
            subject_prefix = "URGENT: "
            header_color = "#dc3545"
        elif reminder_count >= 2:
            urgency_level = "Important"
            subject_prefix = "Reminder: "
            header_color = "#ffc107"
        else:
            urgency_level = "Gentle"
            subject_prefix = "Friendly Reminder: "
            header_color = "#17a2b8"
        
        msg['Subject'] = f"{subject_prefix}Task Reminder - {task_title}"
        
        # Create plain text email
        text_content = f"Hello,\n\n"
        
        if reminder_count == 1:
            text_content += f"This is a friendly reminder about your pending task:\n\n"
        elif reminder_count == 2:
            text_content += f"This is an important reminder about your pending task:\n\n"
        else:
            text_content += f"This is an URGENT reminder about your pending task:\n\n"
        
        text_content += f"Task: {task_title}\n"
        if task_description and task_description != task_title:
            text_content += f"Description: {task_description}\n"
        text_content += f"Due Date: {due_date}\n\n"
        
        text_content += "Please update the status of this task in your task management system.\n\n"
        
        text_content += "Thank you for your attention to this matter.\n"
        
        # Create HTML version
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: {header_color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .task {{ margin-bottom: 15px; padding: 15px; background-color: #f8f9fa; border-left: 4px solid {header_color}; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Task Manager: {urgency_level} Reminder</h2>
            </div>
            <div class="content">
        """
        
        if reminder_count == 1:
            html_content += f"""
                <p>This is a friendly reminder about your pending task:</p>
            """
        elif reminder_count == 2:
            html_content += f"""
                <p>This is an important reminder about your pending task:</p>
            """
        else:
            html_content += f"""
                <p>This is an URGENT reminder about your pending task:</p>
            """
        
        html_content += f"""
                <div class="task">
                    <strong>Task:</strong> {task_title}<br>
        """
        
        if task_description and task_description != task_title:
            html_content += f"""
                    <strong>Description:</strong> {task_description}<br>
            """
        
        html_content += f"""
                    <strong>Due Date:</strong> {due_date}
                </div>
                
                <p>Please update the status of this task in your task management system.</p>
                
                <p>Thank you for your attention to this matter.</p>
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
            
        print(f"Task reminder email sent to {recipient}")
        return True
        
    except Exception as e:
        print(f"Error sending task reminder email: {str(e)}")
        print(traceback.format_exc())
        return False

def generate_conversation_id():
    """Generate a unique conversation ID for context verification."""
    return str(uuid.uuid4())

def store_pending_context_conversation(conversation_id, user_email, ready_tasks, context_needed_tasks, original_email_id, user_database_id):
    """
    Store a pending context conversation for later processing.
    
    Args:
        conversation_id: Unique conversation identifier
        user_email: Email address of the user
        ready_tasks: Tasks that can be processed immediately
        context_needed_tasks: Tasks that need more context
        original_email_id: ID of the original email
        user_database_id: User's task database ID
    """
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
    print(f"📝 Stored pending context conversation: {conversation_id}")
    print(f"   Ready tasks: {len(ready_tasks)}")
    print(f"   Context needed tasks: {len(context_needed_tasks)}")
    
    # Save state immediately
    save_persistent_state()

def get_pending_context_conversation(conversation_id):
    """Retrieve a pending context conversation."""
    return PENDING_CONTEXT_CONVERSATIONS.get(conversation_id)

def remove_pending_context_conversation(conversation_id):
    """Remove a completed pending context conversation."""
    if conversation_id in PENDING_CONTEXT_CONVERSATIONS:
        del PENDING_CONTEXT_CONVERSATIONS[conversation_id]
        print(f"🗑️ Removed completed conversation: {conversation_id}")
        
        # Save state immediately
        save_persistent_state()

def check_and_send_context_reminders():
    """
    Check for pending context conversations that need reminders and send them.
    This should be called at the beginning of each Gmail processor run.
    """
    print(f"\n🔍 Checking for pending context conversations that need reminders...")
    
    current_time = datetime.datetime.now()
    conversations_to_remind = []
    
    for conversation_id, conversation in PENDING_CONTEXT_CONVERSATIONS.items():
        # Skip if already processed
        if conversation.get('context_tasks_processed', False):
            continue
            
        # Check if reminder is due
        last_reminder = conversation.get('last_reminder_sent')
        reminder_count = conversation.get('reminder_count', 0)
        
        if last_reminder:
            last_reminder_time = datetime.datetime.fromisoformat(last_reminder)
            hours_since_last = (current_time - last_reminder_time).total_seconds() / 3600
        else:
            # No reminder sent yet, check if initial request was sent more than 24 hours ago
            created_time = datetime.datetime.fromisoformat(conversation['created_at'])
            hours_since_last = (current_time - created_time).total_seconds() / 3600
        
        if hours_since_last >= CONTEXT_REMINDER_INTERVAL_HOURS:
            conversations_to_remind.append((conversation_id, conversation))
    
    if not conversations_to_remind:
        print(f"✅ No pending conversations need reminders")
        return
    
    print(f"📧 Sending reminders for {len(conversations_to_remind)} pending conversations...")
    
    for conversation_id, conversation in conversations_to_remind:
        try:
            # Send reminder email
            success = send_context_reminder_email(
                recipient=conversation['user_email'],
                context_needed_tasks=conversation['context_needed_tasks'],
                conversation_id=conversation_id,
                reminder_count=conversation.get('reminder_count', 0) + 1
            )
            
            if success:
                # Update conversation with reminder info
                conversation['last_reminder_sent'] = current_time.isoformat()
                conversation['reminder_count'] = conversation.get('reminder_count', 0) + 1
                print(f"✅ Sent reminder for conversation: {conversation_id}")
                
                # Save state after updating reminder info
                save_persistent_state()
            else:
                print(f"❌ Failed to send reminder for conversation: {conversation_id}")
                
        except Exception as e:
            print(f"❌ Error sending reminder for conversation {conversation_id}: {e}")

def send_context_reminder_email(recipient, context_needed_tasks, conversation_id, reminder_count=1):
    """
    Send a reminder email for pending context verification.
    
    Args:
        recipient: Email address to send to
        context_needed_tasks: List of tasks that still need context
        conversation_id: Unique conversation identifier
        reminder_count: Number of reminders sent so far
        
    Returns:
        bool: True if email sent successfully
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = recipient
        
        # Adjust subject based on reminder count
        if reminder_count == 1:
            msg['Subject'] = f"Reminder: Task Manager Needs More Details [Context Request: {conversation_id}]"
        else:
            msg['Subject'] = f"Reminder #{reminder_count}: Task Manager Needs More Details [Context Request: {conversation_id}]"
        
        # Generate verification questions using existing logic
        verification_message = generate_verification_questions(context_needed_tasks)
        
        # Create plain text email
        text_content = f"Hello,\n\n"
        
        if reminder_count == 1:
            text_content += f"I sent you a request for more details about {len(context_needed_tasks)} tasks, but I haven't received your response yet.\n\n"
        else:
            text_content += f"This is reminder #{reminder_count} - I'm still waiting for more details about {len(context_needed_tasks)} tasks.\n\n"
        
        text_content += f"Here are the tasks that need clarification:\n\n"
        text_content += verification_message
        
        text_content += "\n\n--- How to Reply ---\n"
        text_content += "You can reply to this email with the additional details. "
        text_content += "Just provide the information naturally - I'll understand your response.\n\n"
        
        text_content += "Once you provide the details, I'll process all your tasks and send you a complete summary.\n\n"
        
        text_content += "Thank you for using the Task Manager!\n"
        
        # Create HTML version
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #ff6b35; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .task {{ margin-bottom: 15px; padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107; }}
                .reminder-notice {{ margin-bottom: 20px; padding: 15px; background-color: #f8d7da; border-left: 4px solid #dc3545; }}
                .instructions {{ margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #6c757d; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Task Manager: Reminder - Need More Details</h2>
            </div>
            <div class="content">
        """
        
        if reminder_count == 1:
            html_content += f"""
                <div class="reminder-notice">
                    <strong>📧 Reminder</strong><br>
                    I sent you a request for more details about {len(context_needed_tasks)} tasks, but I haven't received your response yet.
                </div>
            """
        else:
            html_content += f"""
                <div class="reminder-notice">
                    <strong>📧 Reminder #{reminder_count}</strong><br>
                    I'm still waiting for more details about {len(context_needed_tasks)} tasks.
                </div>
            """
        
        html_content += f"""
                <p>Here are the tasks that need clarification:</p>
                
                <div class="tasks">
        """
        
        # Add each task that needs context
        for i, task in enumerate(context_needed_tasks, 1):
            task_desc = task.get('task', '')
            notes = task.get('notes', '')
            
            html_content += f"""
                <div class="task">
                    <strong>{i}. {task_desc}</strong><br>
            """
            
            if notes:
                html_content += f"""
                    <em style="color: #666; font-size: 14px;">{notes}</em>
                """
            
            html_content += """
                </div>
            """
        
        html_content += """
                </div>
                
                <div class="instructions">
                    <h3>How to Reply</h3>
                    <p>You can reply to this email with the additional details. Just provide the information naturally - I'll understand your response.</p>
                    <p>Once you provide the details, I'll process all your tasks and send you a complete summary.</p>
                </div>
                
                <p>Thank you for using the Task Manager!</p>
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
            
        print(f"Context reminder email sent to {recipient}")
        return True
        
    except Exception as e:
        print(f"Error sending context reminder email: {str(e)}")
        print(traceback.format_exc())
        return False

def classify_tasks_by_context_needs(tasks):
    """
    Classify tasks into ready and context-needed categories.
    
    Args:
        tasks: List of extracted tasks
        
    Returns:
        tuple: (ready_tasks, context_needed_tasks)
    """
    ready_tasks = []
    context_needed_tasks = []
    
    for task in tasks:
        # Check if task needs context verification
        needs_context = (
            task.get("needs_description", False) or 
            task.get("notes", "") or  # Contains suggested questions
            len(task.get("task", "").strip()) < 15 or  # Short tasks
            task.get("category") == "General" or  # Generic category
            task.get("status") == "Not Started"  # Default status
        )
        
        if needs_context:
            context_needed_tasks.append(task)
            print(f"   ⚠️ Task needs context: '{task.get('task', '')[:50]}...'")
        else:
            ready_tasks.append(task)
            print(f"   ✅ Task ready for processing: '{task.get('task', '')[:50]}...'")
    
    return ready_tasks, context_needed_tasks

def find_most_recent_pending_conversation(user_email):
    """
    Find the most recent pending conversation for a user.
    
    Args:
        user_email: Email address of the user
        
    Returns:
        tuple: (conversation_id, conversation_data) or (None, None)
    """
    most_recent = None
    most_recent_time = None
    
    for conversation_id, conversation in PENDING_CONTEXT_CONVERSATIONS.items():
        if conversation['user_email'] == user_email and not conversation.get('context_tasks_processed', False):
            created_time = datetime.datetime.fromisoformat(conversation['created_at'])
            if most_recent_time is None or created_time > most_recent_time:
                most_recent = conversation_id
                most_recent_time = created_time
    
    if most_recent:
        print(f"🔍 Found most recent pending conversation for {user_email}: {most_recent}")
        return most_recent, PENDING_CONTEXT_CONVERSATIONS[most_recent]
    
    return None, None

def is_context_response_email(msg, conversation_id):
    """
    Check if an email is a response to a context request.
    
    Args:
        msg: Email message object
        conversation_id: Conversation ID to check for
        
    Returns:
        bool: True if this is a context response
    """
    # Check subject line for conversation ID
    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding if encoding else "utf-8")
    
    # Check if subject contains the conversation ID
    if conversation_id in subject:
        return True
    
    # Check if this is a reply to our context request email
    in_reply_to = msg.get("In-Reply-To")
    references = msg.get("References")
    
    # For now, we'll use a simple heuristic - check if it's from the same user
    # and has a recent timestamp (within last 24 hours)
    if in_reply_to or references:
        return True
    
    return False

def find_existing_conversation_for_email(sender_email, subject, body):
    """
    Check if an email is already part of an existing conversation.
    
    Args:
        sender_email: Email address of the sender
        subject: Email subject
        body: Email body
        
    Returns:
        str or None: Existing conversation ID if found
    """
    # First, try to extract conversation ID from the email itself
    conversation_id = extract_conversation_id_from_email(subject, body)
    if conversation_id and conversation_id in PENDING_CONTEXT_CONVERSATIONS:
        print(f"✅ Found existing conversation ID in email: {conversation_id}")
        return conversation_id
    
    # If no conversation ID in email, check if this looks like a reply
    # and find the most recent pending conversation for this user
    if re.search(r'^re:', subject, re.IGNORECASE):
        print(f"🔍 This appears to be a reply email, checking for existing conversations...")
        fallback_conversation_id, fallback_conversation = find_most_recent_pending_conversation(sender_email)
        if fallback_conversation_id:
            print(f"✅ Using existing conversation for reply: {fallback_conversation_id}")
            return fallback_conversation_id
    
    # Check if we have any pending conversations for this user that haven't been processed
    for conv_id, conversation in PENDING_CONTEXT_CONVERSATIONS.items():
        if (conversation['user_email'] == sender_email and 
            not conversation.get('context_tasks_processed', False)):
            print(f"⚠️ Found existing unprocessed conversation for {sender_email}: {conv_id}")
            return conv_id
    
    return None

def extract_conversation_id_from_email(subject, body):
    """
    Extract conversation ID from email subject or body.
    
    Args:
        subject: Email subject
        body: Email body
        
    Returns:
        str or None: Conversation ID if found
    """
    print(f"🔍 DEBUG: Checking email subject: '{subject}'")
    
    # Look for conversation ID pattern in subject
    import re
    
    # Pattern 1: Exact pattern [Context Request: uuid]
    conversation_pattern = r'\[Context Request: ([a-f0-9-]{36})\]'
    match = re.search(conversation_pattern, subject)
    if match:
        conversation_id = match.group(1)
        print(f"✅ Found conversation ID in subject: {conversation_id}")
        return conversation_id
    
    # Pattern 2: Look for just the UUID in the subject (in case brackets were removed)
    uuid_pattern = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
    match = re.search(uuid_pattern, subject)
    if match:
        conversation_id = match.group(1)
        print(f"✅ Found UUID in subject: {conversation_id}")
        return conversation_id
    
    # Pattern 3: Check if this is a reply to our context request
    # Look for "Re:" or "RE:" in subject and check if we have any pending conversations
    if re.search(r'^re:', subject, re.IGNORECASE):
        print(f"🔍 This appears to be a reply email")
        
        # Search for conversation ID in body
        if body:
            match = re.search(conversation_pattern, body)
            if match:
                conversation_id = match.group(1)
                print(f"✅ Found conversation ID in email body: {conversation_id}")
                return conversation_id
            
            # Also check for just UUID in body
            match = re.search(uuid_pattern, body)
            if match:
                conversation_id = match.group(1)
                print(f"✅ Found UUID in email body: {conversation_id}")
                return conversation_id
    
    print(f"❌ No conversation ID found in email")
    return None

def send_confirmation_email(recipient, tasks, coaching_insights=None, user_database_id=None):
    """
    Send a confirmation email with processed tasks and coaching insights.
    
    Args:
        recipient: Email address to send to
        tasks: List of processed tasks (should be unprotected for user display)
        coaching_insights: Optional coaching insights text
        user_database_id: Optional database ID to fetch open tasks from
    """
    try:
        # Get open tasks from user's database if database_id provided
        open_tasks = []
        if user_database_id:
            try:
                existing_tasks = fetch_notion_tasks(database_id=user_database_id)
                if not existing_tasks.empty:
                    # Filter for non-completed tasks
                    open_tasks = existing_tasks[existing_tasks['status'] != 'Completed'].to_dict('records')
                    # Limit to most recent 10 open tasks to avoid overwhelming the email
                    open_tasks = open_tasks[:10]
                    
                    # Unprotect open tasks as well
                    protection_plugin = plugin_manager.get_plugin('ProjectProtectionPlugin')
                    if protection_plugin and protection_plugin.enabled:
                        # Temporarily set preserve_tokens_in_ui to False for email display
                        original_preserve_setting = protection_plugin.security_manager.preserve_tokens_in_ui
                        protection_plugin.security_manager.preserve_tokens_in_ui = False
                        
                        for task in open_tasks:
                            unprotected_task = protection_plugin.unprotect_task(task)
                            task.update(unprotected_task)
                        
                        # Restore original setting
                        protection_plugin.security_manager.preserve_tokens_in_ui = original_preserve_setting
            except Exception as e:
                print(f"Error fetching open tasks: {str(e)}")
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = recipient
        msg['Subject'] = f"Task Manager: {len(tasks)} Tasks Processed"
        
        # Create plain text email
        text_content = f"Hello,\n\nWe've processed your email and extracted {len(tasks)} tasks:\n\n"
        
        for i, task in enumerate(tasks, 1):
            title = task.get('title', '')
            task_desc = task.get('task', '')
            status = task.get('status', 'Unknown')
            category = task.get('category', 'Uncategorized')
            
            if title:
                text_content += f"{i}. {title}\n"
                if task_desc and task_desc != title:
                    text_content += f"   Description: {task_desc}\n"
            else:
                text_content += f"{i}. {task_desc}\n"
            
            text_content += f"   Status: {status} - Category: {category}\n\n"
        
        # Add open tasks section
        if open_tasks:
            text_content += "\n\n--- Your Open Tasks ---\n\n"
            text_content += "Here are your current open tasks:\n\n"
            
            for i, task in enumerate(open_tasks, 1):
                title = task.get('title', '')
                task_desc = task.get('task', '')
                status = task.get('status', 'Unknown')
                category = task.get('category', 'Uncategorized')
                date = task.get('date', '')
                
                # Format the date
                formatted_date = "No date"
                if date:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                        formatted_date = dt.strftime('%Y-%m-%d')
                    except:
                        formatted_date = "Invalid date"
                
                if title:
                    text_content += f"{i}. {title}\n"
                    if task_desc and task_desc != title:
                        text_content += f"   Description: {task_desc}\n"
                else:
                    text_content += f"{i}. {task_desc}\n"
                
                text_content += f"   Status: {status} - Category: {category} - Date: {formatted_date}\n\n"
        
        # Add coaching insights if available
        if coaching_insights:
            text_content += "\n\n--- AI Coaching Insights ---\n\n"
            text_content += coaching_insights
            text_content += "\n\n" + "-"*40
            
        text_content += "\n\nThank you for using the Task Manager!\n"
        
        # Create HTML version
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #4361ee; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .task {{ margin-bottom: 10px; padding: 10px; background-color: #f8f9fa; border-left: 4px solid #4361ee; }}
                .open-task {{ margin-bottom: 10px; padding: 10px; background-color: #fff3cd; border-left: 4px solid #ffc107; }}
                .section-header {{ margin-top: 30px; margin-bottom: 15px; padding: 10px; background-color: #e9ecef; border-radius: 5px; font-weight: bold; }}
                .status {{ display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
                .status-completed {{ background-color: #10b981; color: white; }}
                .status-in-progress {{ background-color: #3b82f6; color: white; }}
                .status-not-started {{ background-color: #6c757d; color: white; }}
                .status-on-hold {{ background-color: #f59e0b; color: white; }}
                .insights {{ margin-top: 30px; padding: 15px; background-color: #edf2fb; border-left: 4px solid #4361ee; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Task Manager Update</h2>
            </div>
            <div class="content">
                <p>We've processed your email and extracted {len(tasks)} tasks:</p>
                
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
        
        # Add open tasks section
        if open_tasks:
            html_content += f"""
                <div class="section-header">
                    📋 Your Open Tasks ({len(open_tasks)} tasks)
                </div>
                <p>Here are your current open tasks:</p>
                
                <div class="open-tasks">
            """
            
            for i, task in enumerate(open_tasks, 1):
                title = task.get('title', '')
                task_desc = task.get('task', '')
                status = task.get('status', 'Unknown')
                category = task.get('category', 'Uncategorized')
                date = task.get('date', '')
                status_class = f"status-{status.lower().replace(' ', '-')}"
                
                # Format the date
                formatted_date = "No date"
                if date:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                        formatted_date = dt.strftime('%Y-%m-%d')
                    except:
                        formatted_date = "Invalid date"
                
                html_content += f"""
                    <div class="open-task">
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
                        <span style="margin-left: 10px; color: #666;">Date: {formatted_date}</span>
                    </div>
                """
            
            html_content += """
                </div>
            """
        
        # Add coaching insights if available
        if coaching_insights:
            html_content += f"""
                <div class="insights">
                    <h3>AI Coaching Insights</h3>
                    <p>{coaching_insights.replace('\n', '<br>')}</p>
                </div>
            """
        
        html_content += """
                </div>
                
                <p>Thank you for using the Task Manager!</p>
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
            
        print(f"Confirmation email sent to {recipient}")
        return True
        
    except Exception as e:
        print(f"Error sending confirmation email: {str(e)}")
        print(traceback.format_exc())
        return False

def send_context_request_email(recipient, context_needed_tasks, conversation_id, ready_tasks_count=0):
    """
    Send a context request email asking for clarification on vague tasks.
    
    Args:
        recipient: Email address to send to
        context_needed_tasks: List of tasks that need more context
        conversation_id: Unique conversation identifier
        ready_tasks_count: Number of tasks that were processed immediately
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = recipient
        msg['Subject'] = f"Task Manager: Need More Details [Context Request: {conversation_id}]"
        
        # Generate verification questions using existing logic
        verification_message = generate_verification_questions(context_needed_tasks)
        
        # Create plain text email
        text_content = f"Hello,\n\n"
        
        if ready_tasks_count > 0:
            text_content += f"I've successfully processed {ready_tasks_count} tasks from your email that had all the needed information.\n\n"
        
        text_content += f"I found {len(context_needed_tasks)} tasks that could use a bit more detail to make them clearer. "
        text_content += "Could you please provide more information for the following tasks?\n\n"
        
        text_content += verification_message
        
        text_content += "\n\n--- How to Reply ---\n"
        text_content += "You can reply to this email with the additional details. "
        text_content += "Just provide the information naturally - I'll understand your response.\n\n"
        
        text_content += "Once you provide the details, I'll process all your tasks and send you a complete summary.\n\n"
        
        text_content += "Thank you for using the Task Manager!\n"
        
        # Create HTML version
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #ffc107; color: #333; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .task {{ margin-bottom: 15px; padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107; }}
                .section-header {{ margin-top: 30px; margin-bottom: 15px; padding: 10px; background-color: #e9ecef; border-radius: 5px; font-weight: bold; }}
                .success-message {{ margin-bottom: 20px; padding: 15px; background-color: #d4edda; border-left: 4px solid #28a745; }}
                .instructions {{ margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #6c757d; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Task Manager: Need More Details</h2>
            </div>
            <div class="content">
        """
        
        if ready_tasks_count > 0:
            html_content += f"""
                <div class="success-message">
                    <strong>✅ Successfully Processed {ready_tasks_count} Tasks</strong><br>
                    I've processed the tasks from your email that had all the needed information.
                </div>
            """
        
        html_content += f"""
                <p>I found <strong>{len(context_needed_tasks)} tasks</strong> that could use a bit more detail to make them clearer. 
                Could you please provide more information for the following tasks?</p>
                
                <div class="tasks">
        """
        
        # Add each task that needs context
        for i, task in enumerate(context_needed_tasks, 1):
            task_desc = task.get('task', '')
            notes = task.get('notes', '')
            
            html_content += f"""
                <div class="task">
                    <strong>{i}. {task_desc}</strong><br>
            """
            
            if notes:
                html_content += f"""
                    <em style="color: #666; font-size: 14px;">{notes}</em>
                """
            
            html_content += """
                </div>
            """
        
        html_content += """
                </div>
                
                <div class="instructions">
                    <h3>How to Reply</h3>
                    <p>You can reply to this email with the additional details. Just provide the information naturally - I'll understand your response.</p>
                    <p>Once you provide the details, I'll process all your tasks and send you a complete summary.</p>
                </div>
                
                <p>Thank you for using the Task Manager!</p>
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
            
        print(f"Context request email sent to {recipient}")
        return True
        
    except Exception as e:
        print(f"Error sending context request email: {str(e)}")
        print(traceback.format_exc())
        return False

def process_context_response_email(msg, body, sender_email, sender_name):
    """
    Process a context response email and enhance the pending tasks.
    
    Args:
        msg: Email message object
        body: Email body text
        sender_email: Sender's email address
        sender_name: Sender's name
        
    Returns:
        bool: True if successfully processed
    """
    try:
        # Extract conversation ID from email
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else "utf-8")
        
        conversation_id = extract_conversation_id_from_email(subject, body)
        if not conversation_id:
            print(f"Could not extract conversation ID from email")
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
        
        if result["status"] == "complete":
            # All tasks verified, process them
            enhanced_tasks = result["updated_tasks"]
            ready_tasks = conversation['ready_tasks']
            all_tasks = ready_tasks + enhanced_tasks
            
            print(f"✅ All tasks enhanced successfully. Processing {len(all_tasks)} total tasks.")
            
            # Process all tasks
            user_database_id = conversation['user_database_id']
            existing_tasks = fetch_notion_tasks(database_id=user_database_id)
            
            # Apply protection if needed
            protection_plugin = plugin_manager.get_plugin('ProjectProtectionPlugin')
            if protection_plugin and protection_plugin.enabled:
                for i, task in enumerate(all_tasks):
                    protected_task = protection_plugin.protect_task(task)
                    all_tasks[i] = protected_task
            
            # Process tasks
            log_output = []
            successful_tasks = 0
            for task in all_tasks:
                success, message = insert_or_update_task(
                    database_id=user_database_id,
                    task=task,
                    existing_tasks=existing_tasks,
                    log_output=log_output
                )
                if success:
                    successful_tasks += 1
                    
                    # NEW: Track task for completion reminders if needed
                    if should_track_task_for_reminders(task):
                        task_id = generate_task_id(task, user_database_id)
                        track_outstanding_task(
                            task_id=task_id,
                            user_email=sender_email,
                            task_data=task,
                            user_database_id=user_database_id
                        )
                        print(f"   📝 Enhanced task tracked for completion reminders: {task_id}")
            
            # Create unprotected versions for email display
            unprotected_tasks = []
            if protection_plugin and protection_plugin.enabled:
                original_preserve_setting = protection_plugin.security_manager.preserve_tokens_in_ui
                protection_plugin.security_manager.preserve_tokens_in_ui = False
                
                for task in all_tasks:
                    unprotected_task = protection_plugin.unprotect_task(task)
                    unprotected_tasks.append(unprotected_task)
                
                protection_plugin.security_manager.preserve_tokens_in_ui = original_preserve_setting
            else:
                unprotected_tasks = all_tasks
            
            # Generate coaching insights
            coaching_insights = None
            try:
                person_name = sender_name
                if person_name and not existing_tasks.empty and "employee" in existing_tasks.columns:
                    recent_tasks = existing_tasks[existing_tasks['employee'] == person_name]
                    if len(recent_tasks) > 0:
                        if 'date' in recent_tasks.columns:
                            try:
                                if recent_tasks['date'].dtype == 'object':
                                    recent_tasks = recent_tasks.copy()
                                    recent_tasks['date'] = pd.to_datetime(recent_tasks['date'], errors='coerce')
                                recent_tasks = recent_tasks[recent_tasks['date'] >= datetime.datetime.now() - timedelta(days=14)]
                            except Exception as date_error:
                                print(f"Error processing dates for coaching insights: {date_error}")
                        
                    peer_feedback = []
                    try:
                        from core import fetch_peer_feedback
                        peer_feedback = fetch_peer_feedback(person_name)
                    except Exception as e:
                        print(f"Error fetching peer feedback: {str(e)}")
                        
                    coaching_insights = get_coaching_insight(person_name, unprotected_tasks, recent_tasks, peer_feedback)
            except Exception as e:
                print(f"Error generating coaching insights: {str(e)}")
            
            # Send final summary email
            send_confirmation_email(sender_email, unprotected_tasks, coaching_insights, user_database_id)
            
            # Clean up conversation
            remove_pending_context_conversation(conversation_id)
            
            print(f"✅ Context response processed successfully. {successful_tasks} tasks processed.")
            return True
            
        else:
            print(f"⚠️ Context response parsing incomplete: {result.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"Error processing context response: {str(e)}")
        print(traceback.format_exc())
        return False

def check_gmail_for_updates():
    """Check Gmail for new emails and process them."""
    try:
        # Load persistent state at startup
        print("📂 Loading persistent state...")
        load_persistent_state()
        
        # Initialize AuthService for user lookup
        from src.core.security.jwt_utils import JWTManager
        jwt_manager = JWTManager(secret_key="dummy", algorithm="HS256")  # We don't need real JWT for this
        auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, None)
        
        # NEW: Check for pending context conversations that need reminders
        check_and_send_context_reminders()
        
        # Clean up old conversations
        cleanup_old_conversations()

        # NEW: Check for outstanding tasks that need reminders
        check_and_send_task_reminders()

        # NEW: Sync outstanding tasks with Notion to detect completions
        # Get unique users from outstanding tasks and sync for each
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
        
        # Search for unread messages first
        status, message_ids = mail.search(None, "UNSEEN")
        
        if status != "OK" or not message_ids[0]:
            print("No unread emails found")
            
            # If no unread emails, also check for recent emails (last 24 hours) that might be replies
            # This helps catch reply emails that were marked as read
            print("Checking for recent emails that might be context responses...")
            
            # Search for emails from the last 24 hours
            yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%d-%b-%Y")
            status, message_ids = mail.search(None, f'SINCE {yesterday}')
            
            if status != "OK" or not message_ids[0]:
                print("No recent emails found")
                mail.close()
                mail.logout()
                return
            else:
                print(f"Found {len(message_ids[0].split())} recent emails to check")
        else:
            print(f"Found {len(message_ids[0].split())} unread email(s)")
            
        message_id_list = message_ids[0].split()
        print(f"Found {len(message_id_list)} new email(s)")
            
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
            
            # Get date
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            if msg["Date"]:
                try:
                    from email.utils import parsedate_to_datetime
                    email_date = parsedate_to_datetime(msg["Date"])
                    date_str = email_date.strftime("%Y-%m-%d")
                except:
                    pass  # Use today's date as fallback
            
            # Get email body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    # Skip attachments
                    if "attachment" in content_disposition:
                        continue
                    
                    # Get text content
                    if content_type == "text/plain":
                        try:
                            payload = part.get_payload(decode=True)
                            charset = part.get_content_charset() or "utf-8"
                            body = payload.decode(charset)
                            break  # Use the first text/plain part
                        except:
                            pass
            else:
                # Not multipart - get payload directly
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
                
            # Format the update text
            update_text = f"From: {sender_name}\nDate: {date_str}\n\nSubject: {subject}\n\n{body}"
            
            print(f"Processing email from {sender_name} ({sender_email}) with subject: {subject}")
            
            # Archive email immediately (async) - before user lookup and task processing
            email_id = None
            if EMAIL_ARCHIVE_ENABLED:
                try:
                    # Check if email already exists in archive
                    archive_service = EmailArchiveService()
                    existing_email = archive_service.get_email_by_message_id(msg_id.decode())
                    
                    if existing_email:
                        print(f"📧 Email with message_id {msg_id.decode()} already archived, skipping...")
                        email_id = existing_email.get('id')
                    else:
                        # Prepare email data for archiving
                        email_data = {
                            'message_id': msg_id.decode(),
                            'thread_id': msg.get('In-Reply-To') or msg.get('References'),
                            'sender_email': sender_email,
                            'sender_name': sender_name,
                            'recipient_email': GMAIL_ADDRESS,
                            'subject': subject,
                            'body_text': body,
                            'body_html': body,  # Could extract HTML if needed
                            'received_date': email_date if 'email_date' in locals() else datetime.datetime.now(),
                            'user_id': None,  # Will be updated after user lookup
                            'task_database_id': None,  # Will be updated after user lookup
                            'email_size_bytes': len(raw_email),
                            'has_attachments': bool(msg.get_payload()),
                            'attachment_count': 0,  # Could count attachments if needed
                            'priority': 'normal',
                            'labels': [],
                            'is_read': False,
                            'is_archived': False,
                            'processing_status': 'processing',
                            'processing_metadata': {
                                'source': 'gmail_processor',
                                'parsed_at': datetime.datetime.now().isoformat(),
                                'original_message_id': msg_id.decode()
                            }
                        }
                        
                        # Store email in hot storage
                        email_id = archive_service.store_email(email_data, 'hot')
                        print(f"✅ Email archived with ID: {email_id}")
                    
                except Exception as e:
                    print(f"⚠️ Email archiving failed: {e}")
                    print(traceback.format_exc())
                    # Continue with task processing anyway
                    email_id = None
            
            # Look up user by email address
            user = auth_service.get_user_by_email(sender_email)
            if not user:
                print(f"No user found for email: {sender_email}. Skipping email.")
                # Update email record with failure status if archived
                if email_id and EMAIL_ARCHIVE_ENABLED:
                    try:
                        archive_service = EmailArchiveService()
                        archive_service.update_email_status(email_id, 'failed', {'error': 'User not found'})
                    except Exception as e:
                        print(f"⚠️ Failed to update email status: {e}")
                # Mark as read anyway to avoid reprocessing
                mail.store(msg_id, "+FLAGS", "\\Seen")
                continue
                
            if not user.task_database_id:
                print(f"User {sender_email} does not have a task database configured. Skipping email.")
                # Update email record with failure status if archived
                if email_id and EMAIL_ARCHIVE_ENABLED:
                    try:
                        archive_service = EmailArchiveService()
                        archive_service.update_email_status(email_id, 'failed', {'error': 'No task database configured'})
                    except Exception as e:
                        print(f"⚠️ Failed to update email status: {e}")
                # Mark as read anyway to avoid reprocessing
                mail.store(msg_id, "+FLAGS", "\\Seen")
                continue
            
            try:
                # Extract tasks
                print(f"\n🔍 DEBUG: Starting task extraction for email from {sender_name}")
                print(f"📧 Email body length: {len(body)} characters")
                
                chunks = chunk_email_text(body, 20)
                print(f"📦 DEBUG: Email split into {len(chunks)} chunks")
                
                tasks = []  # Initialize the tasks list
                
                for i, chunk in enumerate(chunks):
                    print(f"\n📋 DEBUG: Processing chunk {i+1}/{len(chunks)}")
                    print(f"   Chunk length: {len(chunk)} characters")
                    print(f"   Chunk preview: {chunk[:200]}...")
                    
                    # Create context-enriched chunk with email metadata
                    enriched_chunk = f"""From: {sender_name}
Date: {date_str}
Subject: {subject}

{chunk}"""
                    
                    print(f"   📧 DEBUG: Enriched chunk with context:")
                    print(f"     Sender: {sender_name}")
                    print(f"     Date: {date_str}")
                    print(f"     Subject: {subject}")
                    
                    # Extract tasks from this enriched chunk
                    chunk_tasks = extract_tasks_from_update(enriched_chunk)
                    print(f"   ✅ Extracted {len(chunk_tasks)} tasks from chunk {i+1}")
                    
                    # Apply fallback values for missing fields
                    for task in chunk_tasks:
                        if not task.get('employee') or task.get('employee') == 'Unknown':
                            task['employee'] = sender_name
                            print(f"     🔧 Applied fallback employee: {sender_name}")
                        if not task.get('date') or task.get('date') == 'Unknown':
                            task['date'] = date_str
                            print(f"     🔧 Applied fallback date: {date_str}")
                    
                    if chunk_tasks:
                        for j, task in enumerate(chunk_tasks):
                            print(f"     Task {j+1}: {task.get('task', 'No task field')[:100]}...")
                            print(f"       Employee: {task.get('employee', 'Missing')}")
                            print(f"       Date: {task.get('date', 'Missing')}")
                    else:
                        print(f"     ⚠️ No tasks extracted from chunk {i+1}")
                    
                    tasks.extend(chunk_tasks)
                
                print(f"\n📊 DEBUG: Total tasks extracted across all chunks: {len(tasks)}")
                
                # Apply protection to tasks if ProjectProtectionPlugin is enabled
                protection_plugin = plugin_manager.get_plugin('ProjectProtectionPlugin')
                print(f"🔍 DEBUG: Protection plugin check:")
                print(f"   Plugin found: {protection_plugin is not None}")
                if protection_plugin:
                    print(f"   Plugin enabled: {protection_plugin.enabled}")
                    print(f"   Plugin config: {protection_plugin.config}")
                else:
                    print(f"   ❌ ProjectProtectionPlugin not found!")
                    print(f"   Available plugins: {list(plugin_manager.plugins.keys())}")
                
                if protection_plugin and protection_plugin.enabled:
                    print(f"🛡️ DEBUG: Applying task protection...")
                    try:
                        # Force token creation for any new category before protection
                        for i, task in enumerate(tasks):
                            if 'category' in task and task['category'] and task['category'] != 'Uncategorized':
                                token = protection_plugin.security_manager.tokenize_project(task['category'])
                                print(f"   🏷️ Token for category '{task['category']}': {token}")
                        # Protect each task to tokenize categories
                        for i, task in enumerate(tasks):
                            protected_task = protection_plugin.protect_task(task)
                            tasks[i] = protected_task
                            print(f"   🔒 Protected task {i+1}: category '{task.get('category')}' -> '{protected_task.get('category')}'")
                        print(f"   🗺️ Token map after protection: {protection_plugin.security_manager.token_map}")
                    except Exception as e:
                        print(f"⚠️ Error protecting tasks: {e}")
                        # Continue with unprotected tasks if protection fails
                
                print(f"Extracted {len(tasks)} tasks for user {sender_name}")
                
                # Get existing tasks from user's database (needed for both paths)
                existing_tasks = fetch_notion_tasks(database_id=user.task_database_id)
                print(f"📋 DEBUG: Found {len(existing_tasks)} existing tasks in database")
                
                # NEW: Check if this is a context response email first
                conversation_id = find_existing_conversation_for_email(sender_email, subject, body)
                
                if conversation_id:
                    print(f"🔍 Found existing conversation ID: {conversation_id}")
                    # Try to process as context response
                    if process_context_response_email(msg, body, sender_email, sender_name):
                        print(f"✅ Successfully processed context response email")
                        # Mark as read and continue to next email
                        mail.store(msg_id, "+FLAGS", "\\Seen")
                        continue
                    else:
                        print(f"⚠️ Failed to process as context response, treating as new email")
                        # Don't create a new conversation if we already have one
                        print(f"⚠️ Skipping new conversation creation - already have conversation {conversation_id}")
                        mail.store(msg_id, "+FLAGS", "\\Seen")
                        continue
                
                # If no conversation ID found in email, try fallback for reply emails
                if not conversation_id:
                    # Check if this looks like a reply email
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    
                    if re.search(r'^re:', subject, re.IGNORECASE):
                        print(f"🔍 This is a reply email but no conversation ID found, trying fallback...")
                        # Try to find the most recent pending conversation for this user
                        fallback_conversation_id, fallback_conversation = find_most_recent_pending_conversation(sender_email)
                        if fallback_conversation_id:
                            conversation_id = fallback_conversation_id
                            print(f"✅ Using fallback conversation ID: {conversation_id}")
                
                if conversation_id:
                    print(f"🔍 Found conversation ID in email: {conversation_id}")
                    # Try to process as context response
                    if process_context_response_email(msg, body, sender_email, sender_name):
                        print(f"✅ Successfully processed context response email")
                        # Mark as read and continue to next email
                        mail.store(msg_id, "+FLAGS", "\\Seen")
                        continue
                    else:
                        print(f"⚠️ Failed to process as context response, treating as new email")
                
                # NEW: Classify tasks by context needs
                print(f"\n🔍 DEBUG: Classifying tasks by context needs...")
                ready_tasks, context_needed_tasks = classify_tasks_by_context_needs(tasks)
                
                print(f"📊 Task classification results:")
                print(f"   Ready tasks: {len(ready_tasks)}")
                print(f"   Context needed tasks: {len(context_needed_tasks)}")
                
                # NEW: Handle context verification if needed
                if context_needed_tasks:
                    print(f"\n📧 Context verification needed for {len(context_needed_tasks)} tasks")
                    
                    # Generate conversation ID for tracking
                    conversation_id = generate_conversation_id()
                    
                    # Store pending conversation
                    store_pending_context_conversation(
                        conversation_id=conversation_id,
                        user_email=sender_email,
                        ready_tasks=ready_tasks,
                        context_needed_tasks=context_needed_tasks,
                        original_email_id=msg_id.decode(),
                        user_database_id=user.task_database_id
                    )
                    
                    # Process ready tasks immediately if any
                    if ready_tasks:
                        print(f"🔄 Processing {len(ready_tasks)} ready tasks immediately...")
                        
                        # Apply protection to ready tasks if needed
                        if protection_plugin and protection_plugin.enabled:
                            for i, task in enumerate(ready_tasks):
                                protected_task = protection_plugin.protect_task(task)
                                ready_tasks[i] = protected_task
                        
                        # Process ready tasks
                        ready_log_output = []
                        ready_successful = 0
                        for task in ready_tasks:
                            success, message = insert_or_update_task(
                                database_id=user.task_database_id,
                                task=task,
                                existing_tasks=existing_tasks,
                                log_output=ready_log_output
                            )
                            if success:
                                ready_successful += 1
                                
                                # NEW: Track task for completion reminders if needed
                                if should_track_task_for_reminders(task):
                                    task_id = generate_task_id(task, user.task_database_id)
                                    track_outstanding_task(
                                        task_id=task_id,
                                        user_email=sender_email,
                                        task_data=task,
                                        user_database_id=user.task_database_id
                                    )
                                    print(f"   📝 Ready task tracked for completion reminders: {task_id}")
                        
                        print(f"✅ Processed {ready_successful}/{len(ready_tasks)} ready tasks")
                    
                    # Send context request email
                    print(f"📧 Sending context request email...")
                    send_context_request_email(
                        recipient=sender_email,
                        context_needed_tasks=context_needed_tasks,
                        conversation_id=conversation_id,
                        ready_tasks_count=len(ready_tasks)
                    )
                    
                    # Update email record with context verification status
                    if email_id and EMAIL_ARCHIVE_ENABLED:
                        try:
                            archive_service = EmailArchiveService()
                            update_data = {
                                'user_id': user.user_id if hasattr(user, 'user_id') else sender_email,
                                'task_database_id': user.task_database_id,
                                'processing_status': 'context_verification_pending',
                                'processing_metadata': {
                                    'source': 'gmail_processor',
                                    'tasks_extracted': len(tasks),
                                    'ready_tasks_processed': len(ready_tasks),
                                    'context_tasks_pending': len(context_needed_tasks),
                                    'conversation_id': conversation_id,
                                    'context_verification_sent_at': datetime.datetime.now().isoformat(),
                                    'user_email': sender_email
                                }
                            }
                            archive_service.update_email(email_id, update_data)
                            print(f"✅ Email record updated with context verification status")
                        except Exception as e:
                            print(f"⚠️ Failed to update email context verification status: {e}")
                    
                    # Mark as read and continue to next email
                    mail.store(msg_id, "+FLAGS", "\\Seen")
                    continue
                
                # ORIGINAL: Process all tasks normally if no context verification needed
                print(f"\n🔄 Processing all {len(tasks)} tasks normally (no context verification needed)")
                
                # Process each task
                log_output = []
                successful_tasks = 0
                failed_tasks = 0
                
                print(f"\n🔄 DEBUG: Starting task insertion process...")
                for i, task in enumerate(tasks):
                    print(f"\n📝 DEBUG: Processing task {i+1}/{len(tasks)}")
                    print(f"   Task data: {task}")
                    
                    # Validate task data before insertion
                    print(f"   🔍 DEBUG: Task validation:")
                    print(f"     - task: '{task.get('task', 'MISSING')}'")
                    print(f"     - employee: '{task.get('employee', 'MISSING')}'")
                    print(f"     - date: '{task.get('date', 'MISSING')}'")
                    print(f"     - status: '{task.get('status', 'MISSING')}'")
                    print(f"     - category: '{task.get('category', 'MISSING')}'")
                    
                    # Check for null/empty values that might cause Notion API errors
                    validation_errors = []
                    if not task.get('task') or not task['task'].strip():
                        validation_errors.append("Empty task description")
                    if not task.get('employee') or not task['employee'].strip():
                        validation_errors.append("Empty employee field")
                    if not task.get('date'):
                        validation_errors.append("Missing date")
                    if not task.get('status'):
                        validation_errors.append("Missing status")
                    
                    if validation_errors:
                        print(f"   ⚠️ Validation errors: {validation_errors}")
                    
                    # Use the protected task as the base for task_fixed
                    task_fixed = task.copy()
                    if not task_fixed.get('task') or not task_fixed['task'].strip():
                        task_fixed['task'] = "Untitled Task"
                        print(f"   🔧 Applied fallback task: 'Untitled Task'")
                    if not task_fixed.get('employee') or not task_fixed['employee'].strip():
                        task_fixed['employee'] = sender_name
                        print(f"   🔧 Applied fallback employee: {sender_name}")
                    if not task_fixed.get('date'):
                        task_fixed['date'] = date_str
                        print(f"   🔧 Applied fallback date: {date_str}")
                    if not task_fixed.get('status'):
                        task_fixed['status'] = "Not Started"
                        print(f"   🔧 Applied fallback status: 'Not Started'")
                    if not task_fixed.get('category'):
                        task_fixed['category'] = "Uncategorized"
                        print(f"   🔧 Applied fallback category: 'Uncategorized'")
                    print(f"   🛡️ DEBUG: Category before Notion insert: '{task_fixed.get('category')}'")
                    
                    success, message = insert_or_update_task(
                        database_id=user.task_database_id,
                        task=task_fixed, 
                        existing_tasks=existing_tasks, 
                        log_output=log_output
                    )
                    
                    if success:
                        print(f"   ✅ Successfully processed task: {task.get('task')}")
                        successful_tasks += 1
                        
                        # NEW: Track task for completion reminders if needed
                        if should_track_task_for_reminders(task_fixed):
                            task_id = generate_task_id(task_fixed, user.task_database_id)
                            track_outstanding_task(
                                task_id=task_id,
                                user_email=sender_email,
                                task_data=task_fixed,
                                user_database_id=user.task_database_id
                            )
                            print(f"   📝 Task tracked for completion reminders: {task_id}")
                    else:
                        print(f"   ❌ Failed to process task: {task.get('task')}")
                        print(f"   Error message: {message}")
                        print(f"   🔍 DEBUG: Full error details:")
                        print(f"     Task data that failed: {task}")
                        print(f"     Error message: {message}")
                        failed_tasks += 1
                
                print(f"\n📈 DEBUG: Task processing summary:")
                print(f"   Total tasks: {len(tasks)}")
                print(f"   Successful: {successful_tasks}")
                print(f"   Failed: {failed_tasks}")
                
                print(f"Successfully processed {successful_tasks} tasks for user {sender_name}")
                
                # Create unprotected versions of tasks for user-facing content
                unprotected_tasks = []
                if protection_plugin and protection_plugin.enabled:
                    print(f"📧 DEBUG: Creating unprotected tasks for user display...")
                    # Temporarily set preserve_tokens_in_ui to False for email display
                    original_preserve_setting = protection_plugin.security_manager.preserve_tokens_in_ui
                    protection_plugin.security_manager.preserve_tokens_in_ui = False
                    
                    for task in tasks:
                        unprotected_task = protection_plugin.unprotect_task(task)
                        unprotected_tasks.append(unprotected_task)
                        print(f"   🔓 Unprotected task: category '{task.get('category')}' -> '{unprotected_task.get('category')}'")
                    
                    # Restore original setting
                    protection_plugin.security_manager.preserve_tokens_in_ui = original_preserve_setting
                else:
                    unprotected_tasks = tasks
                
                # Generate coaching insights
                coaching_insights = None
                try:
                    # Get person name from the first task
                    person_name = ""
                    if unprotected_tasks and "employee" in unprotected_tasks[0]:
                        person_name = unprotected_tasks[0].get("employee", "")
                        
                    if person_name and not existing_tasks.empty and "employee" in existing_tasks.columns:
                        # Get recent tasks for this person from user's database
                        recent_tasks = existing_tasks[existing_tasks['employee'] == person_name]
                        if len(recent_tasks) > 0:
                            # Filter to recent tasks (last 14 days)
                            if 'date' in recent_tasks.columns:
                                # Fix: Convert date column to datetime if it's not already
                                try:
                                    if recent_tasks['date'].dtype == 'object':
                                        recent_tasks = recent_tasks.copy()
                                        recent_tasks['date'] = pd.to_datetime(recent_tasks['date'], errors='coerce')
                                    recent_tasks = recent_tasks[recent_tasks['date'] >= datetime.datetime.now() - timedelta(days=14)]
                                except Exception as date_error:
                                    print(f"Error processing dates for coaching insights: {date_error}")
                                    # If date processing fails, use all recent tasks
                                    recent_tasks = recent_tasks
                            
                        # Get peer feedback
                        peer_feedback = []
                        try:
                            from core import fetch_peer_feedback
                            peer_feedback = fetch_peer_feedback(person_name)
                        except Exception as e:
                            print(f"Error fetching peer feedback: {str(e)}")
                            
                        # Generate coaching insights using unprotected tasks
                        coaching_insights = get_coaching_insight(person_name, unprotected_tasks, recent_tasks, peer_feedback)
                        print("Generated coaching insights successfully")
                    else:
                        print(f"Skipping coaching insights - person_name: {person_name}, DataFrame empty: {existing_tasks.empty}, has employee column: {'employee' in existing_tasks.columns if not existing_tasks.empty else 'N/A'}")
                except Exception as e:
                    print(f"Error generating coaching insights: {str(e)}")
                    print(traceback.format_exc())
                    
                # Send confirmation with coaching insights using unprotected tasks
                send_confirmation_email(sender_email, unprotected_tasks, coaching_insights, user.task_database_id)
                
                # Update email record with completion status and task metadata
                if email_id and EMAIL_ARCHIVE_ENABLED:
                    try:
                        archive_service = EmailArchiveService()
                        # Update with user info and task results
                        update_data = {
                            'user_id': user.user_id if hasattr(user, 'user_id') else sender_email,
                            'task_database_id': user.task_database_id,
                            'processing_status': 'completed',
                            'processing_metadata': {
                                'source': 'gmail_processor',
                                'tasks_extracted': len(tasks),
                                'tasks_processed': successful_tasks,
                                'tasks_failed': failed_tasks,
                                'chunks_processed': len(chunks),
                                'coaching_insights_generated': coaching_insights is not None,
                                'completed_at': datetime.datetime.now().isoformat(),
                                'user_email': sender_email
                            }
                        }
                        archive_service.update_email(email_id, update_data)
                        print(f"✅ Email record updated with completion status")
                    except Exception as e:
                        print(f"⚠️ Failed to update email completion status: {e}")
            except Exception as e:
                print(f"Error processing email: {str(e)}")
                print(traceback.format_exc())
                
            # Mark the email as read
            mail.store(msg_id, "+FLAGS", "\\Seen")
            
        # Close the connection
        mail.close()
        mail.logout()
        print("Email processing completed")
        
        # Save final state
        print("💾 Saving final persistent state...")
        save_persistent_state()
        
    except Exception as e:
        print(f"Error checking Gmail: {str(e)}")
        print(traceback.format_exc())
        
        # Save state even on error to preserve any changes
        try:
            print("💾 Saving persistent state after error...")
            save_persistent_state()
        except Exception as save_error:
            print(f"⚠️ Failed to save state after error: {save_error}")
        
if __name__ == "__main__":
    # Run once when executed directly
    check_gmail_for_updates()