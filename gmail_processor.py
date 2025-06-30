import imaplib
import email
import smtplib
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback
from datetime import datetime, timedelta
import pandas as pd

from core.task_extractor import extract_tasks_from_update
from core.task_processor import insert_or_update_task
from core import fetch_notion_tasks
from core.ai.insights import get_coaching_insight
from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, GMAIL_SERVER, NOTION_TOKEN, NOTION_USERS_DB_ID, EMAIL_ARCHIVE_ENABLED

# Import AuthService for user lookup
from core.services.auth_service import AuthService

# Import EmailArchiveService for email archiving
if EMAIL_ARCHIVE_ENABLED:
    from core.services.email_archive_service import EmailArchiveService

from core.ai.extractors import chunk_email_text
from plugin_manager_instance import plugin_manager

# Discover and initialize plugins
PLUGIN_DIRECTORIES = [
    'plugins/guidelines',
    'plugins/feedback', 
    'plugins/integrations',
    'plugins/security'
]
plugin_manager.discover_plugins(PLUGIN_DIRECTORIES)
# Register all discovered plugins
for plugin_name in plugin_manager.plugin_classes:
    plugin_manager.register_plugin_by_name(plugin_name)

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

def check_gmail_for_updates():
    """Check Gmail for new emails and process them."""
    try:
        # Initialize AuthService for user lookup
        from core.security.jwt_utils import JWTManager
        jwt_manager = JWTManager(secret_key="dummy", algorithm="HS256")  # We don't need real JWT for this
        auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, None)
        
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
        
        if status != "OK" or not message_ids[0]:
            print("No new emails found")
            mail.close()
            mail.logout()
            return
            
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
            date_str = datetime.now().strftime("%Y-%m-%d")
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
                            'received_date': email_date if 'email_date' in locals() else datetime.now(),
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
                                'parsed_at': datetime.now().isoformat(),
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
                
                # Get existing tasks from user's database
                existing_tasks = fetch_notion_tasks(database_id=user.task_database_id)
                print(f"📋 DEBUG: Found {len(existing_tasks)} existing tasks in database")
                
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
                                    recent_tasks = recent_tasks[recent_tasks['date'] >= datetime.now() - timedelta(days=14)]
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
                                'completed_at': datetime.now().isoformat(),
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
        
    except Exception as e:
        print(f"Error checking Gmail: {str(e)}")
        print(traceback.format_exc())
        
if __name__ == "__main__":
    # Run once when executed directly
    check_gmail_for_updates()