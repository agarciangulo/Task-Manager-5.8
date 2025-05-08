"""
Notion API integration for Task Manager.
Handles all interactions with Notion databases.
"""
from notion_client import Client
from datetime import datetime, timedelta
from dateutil import parser
import pandas as pd
import traceback

from config import (
    NOTION_TOKEN, 
    NOTION_DATABASE_ID, 
    NOTION_FEEDBACK_DB_ID, 
    DEBUG_MODE, 
    DAYS_THRESHOLD
)

# Debug print for Notion configuration
print("\nNotion Configuration:")
print(f"NOTION_TOKEN: {NOTION_TOKEN[:8]}..." if NOTION_TOKEN else "Not found")
print(f"NOTION_DATABASE_ID: {NOTION_DATABASE_ID[:8]}..." if NOTION_DATABASE_ID else "Not found")
print(f"NOTION_FEEDBACK_DB_ID: {NOTION_FEEDBACK_DB_ID[:8]}..." if NOTION_FEEDBACK_DB_ID else "Not found")
print("----------------------------------------\n")

# Initialize Notion client
try:
    notion = Client(auth=NOTION_TOKEN)
    print("✅ Notion client initialized successfully!")
except Exception as e:
    print(f"❌ Error initializing Notion client: {e}")
    print(traceback.format_exc())
    notion = None

database_id = NOTION_DATABASE_ID
feedback_db_id = NOTION_FEEDBACK_DB_ID

def debug_print(message):
    """Print debug messages if DEBUG_MODE is True."""
    if DEBUG_MODE:
        print(message)

def validate_notion_connection():
    """Validate connection to Notion API."""
    try:
        response = notion.databases.query(database_id=database_id, page_size=1)
        print("✅ Notion connection successful!")
        return True
    except Exception as e:
        print(f"❌ Notion connection failed: {e}")
        return False

# Helper functions for safer Notion property access
def get_title_content(props, key):
    """Safely extract title content from Notion properties."""
    try:
        if key in props and props[key]["title"] and len(props[key]["title"]) > 0:
            return props[key]["title"][0]["text"]["content"]
        return ""
    except (KeyError, IndexError):
        return ""

def get_select_value(props, key, default=""):
    """Safely extract select value from Notion properties."""
    try:
        if key in props and props[key].get("select"):
            return props[key]["select"]["name"]
        return default
    except KeyError:
        return default

def get_rich_text_content(props, key):
    """Safely extract rich text content from Notion properties."""
    try:
        if key in props and props[key].get("rich_text") and len(props[key]["rich_text"]) > 0:
            return props[key]["rich_text"][0]["text"]["content"]
        return ""
    except (KeyError, IndexError):
        return ""

def get_date_value(props, key):
    """Safely extract date value from Notion properties."""
    try:
        if key in props and props[key].get("date") and props[key]["date"].get("start"):
            return parser.parse(props[key]["date"]["start"])
        return None
    except (KeyError, ValueError, TypeError):
        return None

def get_checkbox_value(props, key, default=False):
    """Safely extract checkbox value from Notion properties."""
    try:
        if key in props:
            return props[key]["checkbox"]
        return default
    except KeyError:
        return default

def fetch_notion_tasks():
    """Fetch tasks from Notion with pagination support."""
    all_pages = []
    has_more = True
    start_cursor = None

    while has_more:
        response = notion.databases.query(
            database_id=database_id,
            start_cursor=start_cursor,
            page_size=100  # Maximum allowed by Notion API
        )

        all_pages.extend(response["results"])
        has_more = response["has_more"]

        if has_more:
            start_cursor = response["next_cursor"]

    rows = []
    for page in all_pages:
        try:
            props = page["properties"]

            # Use safer property access
            task = {
                "id": page["id"],
                "task": get_title_content(props, "Task"),
                "status": get_select_value(props, "Status", "No Status"),
                "employee": get_rich_text_content(props, "Employee"),
                "date": get_date_value(props, "Date"),
                "reminder_sent": get_checkbox_value(props, "Reminder sent", False),  # Fixed casing
                "category": get_rich_text_content(props, "Category"),
            }
            rows.append(task)
        except Exception as e:
            debug_print(f"Error processing Notion page {page['id']}: {e}")
            continue

    return pd.DataFrame(rows)

def get_all_tasks():
    """Get all tasks as DataFrame for easier processing."""
    try:
        return fetch_notion_tasks()
    except Exception as e:
        debug_print(f"Error fetching all tasks: {e}")
        return None

def identify_stale_tasks(df, days_threshold=DAYS_THRESHOLD):
    """Identify tasks that need reminders."""
    now = datetime.now()
    # Handle potential None values in date column
    df["days_old"] = df["date"].apply(lambda d: (now - d).days if d else 0)

    # Basic stale task identification
    stale_tasks = df[(df["status"] != "Completed") & (df["days_old"] > days_threshold) & (~df["reminder_sent"])]

    return stale_tasks

def mark_task_as_reminded(task_id):
    """Mark a task as reminded in Notion."""
    try:
        notion.pages.update(
            page_id=task_id,
            properties={"Reminder sent": {"checkbox": True}}  # Fixed casing
        )
        return True
    except Exception as e:
        debug_print(f"Error marking task as reminded: {e}")
        return False

def normalize_date_for_notion(date_obj):
    """
    Normalize a date object or string for Notion.
    Ensures the date uses the current year and is formatted properly.
    """
    try:
        # Convert string to datetime if needed
        if isinstance(date_obj, str):
            date_obj = parser.parse(date_obj)
            
        # Make sure we have a datetime object
        if not isinstance(date_obj, datetime):
            # Default to today if we can't parse the date
            date_obj = datetime.now()
            
        # Get current year
        current_year = datetime.now().year
        
        # If the year is significantly different from current year,
        # replace it with current year
        if abs(date_obj.year - current_year) > 2:
            date_obj = date_obj.replace(year=current_year)
            
        # Format for Notion API (ISO format)
        return date_obj.strftime("%Y-%m-%d")
    except Exception as e:
        debug_print(f"Error normalizing date: {e}")
        # Default to today
        return datetime.now().strftime("%Y-%m-%d")
    
def insert_task_to_notion(task):
    """Insert a new task into Notion."""
    try:
        # Debug output
        print(f"\n==== ATTEMPTING TO INSERT TASK TO NOTION ====")
        print(f"Task data: {task}")
        
        # Make sure date is in the right format for Notion and uses current year
        date_str = normalize_date_for_notion(task["date"])
        
        # Debug output
        print(f"Formatted date: {date_str}")
        print(f"Using database_id: {database_id}")

        # Create the properties for Notion
        properties = {
            "Task": {
                "title": [{"text": {"content": task["task"]}}]
            },
            "Status": {
                "select": {"name": task["status"]}
            },
            "Date": {
                "date": {"start": date_str}
            },
            "Employee": {
                "rich_text": [{"text": {"content": task["employee"]}}]
            },
            "Reminder sent": {  # Fixed casing to match Notion schema
                "checkbox": False
            },
            "Category": {
                "rich_text": [{"text": {"content": task["category"]}}]
            }
        }
        
        # Debug output
        print(f"Notion properties: {properties}")
        
        # Make the API call
        try:
            response = notion.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            print(f"✅ SUCCESS: Task created in Notion. Response ID: {response['id']}")
            return True, f"✅ Added new task: {task['task']}"
        except Exception as e:
            print(f"❌ ERROR: Notion API call failed. Exception details:")
            print(f"Exception type: {type(e).__name__}")
            print(f"Exception message: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return False, f"❌ Error creating task: {e}"
    except Exception as e:
        print(f"❌ ERROR in insert_task_to_notion function:")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return False, f"❌ Error creating task: {e}"

def update_task_in_notion(task_id, task):
    """Update task with intelligent field updates."""
    try:
        # Debug output
        print(f"\n==== ATTEMPTING TO UPDATE TASK IN NOTION ====")
        print(f"Task ID: {task_id}")
        print(f"Task data: {task}")
        
        # Build update properties
        update_props = {
            # Always update status
            "Status": {"select": {"name": task["status"]}}
        }
        
        # If date is provided, normalize it
        if "date" in task and task["date"]:
            date_str = normalize_date_for_notion(task["date"])
            update_props["Date"] = {"date": {"start": date_str}}
            print(f"Updating with date: {date_str}")
            
        # If category is provided, update it too
        if "category" in task and task["category"]:
            update_props["Category"] = {
                "rich_text": [{"text": {"content": task["category"]}}]
            }
            print(f"Updating with category: {task['category']}")

        # Debug output
        print(f"Notion properties for update: {update_props}")
        
        # Make the API call
        try:
            response = notion.pages.update(
                page_id=task_id,
                properties=update_props
            )
            print(f"✅ SUCCESS: Task updated in Notion. Response ID: {response['id']}")
            return True, f"✅ Updated task: {task['task'] if 'task' in task else 'ID: ' + task_id}"
        except Exception as e:
            print(f"❌ ERROR: Notion API call failed. Exception details:")
            print(f"Exception type: {type(e).__name__}")
            print(f"Exception message: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return False, f"❌ Error updating task: {e}"
    except Exception as e:
        print(f"❌ ERROR in update_task_in_notion function:")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return False, f"❌ Error updating task: {e}"
    
def fetch_peer_feedback(person_name, days_back=14):
    """Fetch peer feedback for a specific person."""
    if not person_name or not feedback_db_id:
        return []

    recent_cutoff = datetime.now() - timedelta(days=days_back)

    try:
        all_results = []
        has_more = True
        start_cursor = None

        while has_more:
            response = notion.databases.query(
                database_id=feedback_db_id,
                start_cursor=start_cursor,
                page_size=100
            )

            all_results.extend(response["results"])
            has_more = response["has_more"]

            if has_more:
                start_cursor = response["next_cursor"]

        entries = []
        for row in all_results:
            try:
                props = row["properties"]
                name = get_title_content(props, "Name")
                feedback = get_rich_text_content(props, "Feedback")
                date = get_date_value(props, "Date")

                if name.lower() == person_name.lower() and date and date >= recent_cutoff:
                    entries.append({"date": date.strftime("%Y-%m-%d"), "feedback": feedback})
            except Exception as e:
                debug_print(f"Error processing feedback entry: {e}")
                continue

        return entries
    except Exception as e:
        debug_print(f"Error fetching peer feedback: {e}")
        return []

def list_all_categories():
    """Get all unique categories from existing tasks."""
    try:
        df = fetch_notion_tasks()
        categories = sorted(df["category"].dropna().unique().tolist())
        # Add "Uncategorized" if it doesn't exist
        if not categories:
            categories = ["Uncategorized"]
        return categories
    except Exception as e:
        debug_print(f"Error listing categories: {e}")
        return ["Uncategorized"]  # Fallback