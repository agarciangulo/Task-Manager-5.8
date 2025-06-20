"""
Flask application with complete authentication system.
This provides secure user registration, login, and JWT-based authentication.
"""
import os
import sys
import subprocess
import traceback
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
import logging

# Load environment variables first
load_dotenv()

# Debug: Print environment variables (only first few characters for security)
print("\nEnvironment Variables Loaded:")
print(f"GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY')[:8]}..." if os.getenv('GEMINI_API_KEY') else "Not found")
print(f"NOTION_TOKEN: {os.getenv('NOTION_TOKEN')[:8]}..." if os.getenv('NOTION_TOKEN') else "Not found")
print(f"NOTION_DATABASE_ID: {os.getenv('NOTION_DATABASE_ID')[:8]}..." if os.getenv('NOTION_DATABASE_ID') else "Not found")
print(f"NOTION_FEEDBACK_DB_ID: {os.getenv('NOTION_FEEDBACK_DB_ID')[:8]}..." if os.getenv('NOTION_FEEDBACK_DB_ID') else "Not found")
print(f"NOTION_USERS_DB_ID: {os.getenv('NOTION_USERS_DB_ID')[:8]}..." if os.getenv('NOTION_USERS_DB_ID') else "Not found")
print(f"JWT_SECRET_KEY: {os.getenv('JWT_SECRET_KEY')[:8]}..." if os.getenv('JWT_SECRET_KEY') else "Not found")
print(f"DEBUG_MODE: {os.getenv('DEBUG_MODE')}")
print("----------------------------------------\n")

# First make sure setuptools is installed
try:
    import pkg_resources
except ImportError:
    print("Installing setuptools...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "setuptools"])
    import pkg_resources
    print("setuptools installed successfully.")

# Required packages for the application
REQUIRED_PACKAGES = [
    "flask",
    "pandas",
    "openai",
    "python-dotenv",
    "requests",
    "flask-cors==4.0.0",
    "PyJWT",
    "bcrypt"
]

# Check and install required packages
def check_and_install_packages():
    """Check if required packages are installed and install them if needed."""
    import pkg_resources
    import subprocess
    import sys
    
    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = []
    
    # Check other packages
    for pkg in REQUIRED_PACKAGES:
        if pkg.split('==')[0].lower() not in installed:
            missing.append(pkg)
    
    if missing:
        print("Installing missing packages:", missing)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            print("All required packages installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Error installing packages: {e}")
            print("Please install the following packages manually:")
            for pkg in missing:
                print(f"  - {pkg}")
            sys.exit(1)
    else:
        print("All required packages are already installed!")

# Check packages before importing other modules
check_and_install_packages()

# Now import other modules
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS

# Import from the new structure
from core.agents.notion_agent import NotionAgent
from core.agents.task_extraction_agent import TaskExtractionAgent
from core.agents.task_processing_agent import TaskProcessingAgent
from core.ai.analyzers import TaskAnalyzer, ProjectAnalyzer
from core.ai.insights import get_project_insight
from core import identify_stale_tasks, list_all_categories

# Import authentication components
from core.security.jwt_utils import JWTManager, require_auth, require_role
from core.services.auth_service import AuthService

# Import from plugins
from plugins import initialize_all_plugins, plugin_manager

# Import from config
from config import (
    GEMINI_API_KEY,
    NOTION_TOKEN,
    NOTION_DATABASE_ID,
    NOTION_FEEDBACK_DB_ID,
    NOTION_USERS_DB_ID,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_EXPIRATION_HOURS,
    ENABLE_AUTHENTICATION,
    SIMILARITY_THRESHOLD,
    ENABLE_TASK_VALIDATION,
    ENABLE_CHAT_VERIFICATION,
    DEBUG_MODE,
    NOTION_PARENT_PAGE_ID
)

# Initialize plugins
initialize_all_plugins()

# Initialize Flask app
app = Flask(__name__, 
            static_folder="static",
            template_folder="templates")

# Enable CORS
CORS(app)

# Initialize JWT Manager
jwt_manager = JWTManager(secret_key=JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
app.jwt_manager = jwt_manager

# Initialize Authentication Service
auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, NOTION_PARENT_PAGE_ID)

# Initialize User Task Service
from core.services.user_task_service import UserTaskService
user_task_service = UserTaskService(NOTION_TOKEN)

# Initialize the TaskAnalyzer
task_analyzer = TaskAnalyzer()

# Validate Notion connection at startup
# We create a temporary service instance for this
print("\nValidating Notion connection...")
try:
    from core.notion_service import NotionService
    validation_service = NotionService()
    notion_connected = validation_service.validate_connection()
    if not notion_connected:
        print("⚠️ Warning: Notion connection failed. Some features may not work.")
    else:
        print("✅ Notion connection successful!")
except Exception as e:
    print(f"⚠️ Warning: Notion connection validation failed: {e}")

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        role = data.get('role', 'user')
        
        if not email or not password or not full_name:
            return jsonify({'error': 'email, password, and full_name are required'}), 400
        
        # Register the user
        user = auth_service.register_user(email, password, full_name, role)
        
        # Re-fetch user to ensure task_database_id is present
        final_user = auth_service.get_user_by_email(email)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': final_user.to_public_dict() if final_user else user.to_public_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Authenticate a user and return JWT token."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'email and password are required'}), 400
        
        # Authenticate the user
        token = auth_service.authenticate_user(email, password)
        
        if not token:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Get user info for response
        user = auth_service.get_user_by_email(email)
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': user.to_public_dict() if user else None,
            'expires_in': JWT_EXPIRATION_HOURS * 3600
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/refresh', methods=['POST'])
def refresh_token():
    """Refresh a JWT token."""
    try:
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header required'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Refresh the token
        new_token = jwt_manager.refresh_token(token, JWT_EXPIRATION_HOURS * 3600)
        
        return jsonify({
            'message': 'Token refreshed successfully',
            'token': new_token,
            'expires_in': JWT_EXPIRATION_HOURS * 3600
        }), 200
        
    except Exception as e:
        print(f"Token refresh error: {str(e)}")
        return jsonify({'error': 'Invalid token'}), 401

@app.route('/api/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get the current user's profile."""
    try:
        user_id = request.user_id
        user = auth_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_public_dict()
        }), 200
        
    except Exception as e:
        print(f"Profile error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update current user's profile."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Only allow updating certain fields
        allowed_updates = ['full_name', 'password']
        updates = {k: v for k, v in data.items() if k in allowed_updates}
        
        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Update the user
        updated_user = auth_service.update_user(request.user_id, updates)
        
        if not updated_user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': updated_user.to_public_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Profile update error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Public Routes (no authentication required, but guarded by client-side scripts)
@app.route('/')
def index():
    """
    Render main page. This is the home page.
    This route is public, but the page content is protected by a client-side auth guard.
    """
    try:
        categories = list_all_categories()
        return render_template('index.html', categories=categories)
    except Exception as e:
        print(f"Error in index route: {e}")
        return str(e), 500

@app.route('/login')
def login_page():
    """Render login page."""
    return render_template('login.html')

@app.route('/register')
def register_page():
    """Render register page."""
    return render_template('register.html')

# Protected Routes (authentication required)
@app.route('/dashboard')
def dashboard():
    """
    Render dashboard page.
    This route is public, but the page content is protected by a client-side auth guard.
    """
    return render_template('dashboard.html')

@app.route('/api/dashboard_data')
@require_auth
def api_dashboard_data(current_user):
    """
    Provide data for the dashboard.
    This now fetches tasks from the user's own database.
    """
    try:
        # Ensure user has a task database
        if not current_user.get('task_database_id'):
            return jsonify({'error': 'User does not have a task database configured.'}), 400

        user_task_db_id = current_user['task_database_id']
        
        # Instantiate agent for this request
        notion_agent = NotionAgent()
        
        # Fetch tasks from the user-specific database
        tasks_df = notion_agent.fetch_tasks(database_id=user_task_db_id)

        if tasks_df.empty:
            return jsonify({
                "summary_stats": {},
                "tasks_by_status": {},
                "tasks_by_category": {},
                "upcoming_deadlines": [],
                "recent_tasks": []
            })

        # Process data
        summary_stats = task_analyzer.get_summary_statistics(tasks_df)
        
        return jsonify({
            "summary_stats": summary_stats,
            "tasks_by_status": task_analyzer.get_tasks_by_status(tasks_df),
            "tasks_by_category": task_analyzer.get_tasks_by_category(tasks_df),
            "upcoming_deadlines": task_analyzer.get_upcoming_deadlines(tasks_df),
            "recent_tasks": tasks_df.head().to_dict('records')
        })

    except Exception as e:
        print(f"Dashboard data error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/api/process_update', methods=['POST'])
@require_auth
def process_update(current_user):
    """
    Process a text update to extract and handle tasks for the logged-in user.
    """
    data = request.get_json()
    text_update = data.get("text")

    if not text_update:
        return jsonify({"error": "No text provided"}), 400
        
    if not current_user.get('task_database_id'):
        return jsonify({'error': 'User does not have a task database configured.'}), 400
        
    user_task_db_id = current_user['task_database_id']

    log_output = []
    try:
        # Instantiate agents for this request
        task_extraction_agent = TaskExtractionAgent()
        task_processing_agent = TaskProcessingAgent()
        notion_agent = NotionAgent()
        
        # Step 1: Extract tasks from text
        extracted_tasks = task_extraction_agent.extract_tasks(text_update)
        log_output.append(f"Extracted {len(extracted_tasks)} tasks.")

        if not extracted_tasks:
            return jsonify({"message": "No tasks to process.", "log": log_output})

        # Step 2: Fetch existing tasks from user's DB to check for duplicates
        existing_tasks = notion_agent.fetch_tasks(database_id=user_task_db_id)
        log_output.append("Fetched existing tasks for similarity check.")

        # Step 3: Process each extracted task
        for task in extracted_tasks:
            success, message = task_processing_agent.process_task(
                database_id=user_task_db_id,
                task=task,
                existing_tasks=existing_tasks,
                log_output=log_output
            )
            if success:
                log_output.append(f"Successfully processed task: {task.get('task')}")
            else:
                log_output.append(f"Failed to process task: {task.get('task')} - {message}")

        return jsonify({"message": "Update processed successfully", "log": log_output})

    except Exception as e:
        log_output.append(f"An error occurred: {e}")
        traceback.print_exc()
        return jsonify({"error": f"An error occurred: {e}", "log": log_output}), 500

@app.route('/api/stale_tasks')
@require_auth
def api_stale_tasks(current_user):
    """API endpoint to get stale tasks from the user's database."""
    if not current_user.get('task_database_id'):
        return jsonify({'error': 'User does not have a task database configured.'}), 400
        
    user_task_db_id = current_user['task_database_id']
    
    try:
        days = request.args.get('days', 7, type=int)
        stale_tasks = identify_stale_tasks(user_task_db_id, days)
        return jsonify(stale_tasks)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/api/tasks_by_category')
@require_auth
def api_tasks_by_category(current_user):
    """API endpoint to get tasks grouped by category from user's database."""
    if not current_user.get('task_database_id'):
        return jsonify({'error': 'User does not have a task database configured.'}), 400
        
    user_task_db_id = current_user['task_database_id']
    
    try:
        # Instantiate agent for this request
        notion_agent = NotionAgent()
        tasks_df = notion_agent.fetch_tasks(database_id=user_task_db_id)
        
        if tasks_df.empty:
            return jsonify({})
            
        tasks_by_cat = task_analyzer.get_tasks_by_category(tasks_df)
        return jsonify(tasks_by_cat)
        
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/api/categories')
@require_auth
def api_categories(current_user):
    """API endpoint to get all unique categories from user's database."""
    if not current_user.get('task_database_id'):
        return jsonify({'error': 'User does not have a task database configured.'}), 400
        
    user_task_db_id = current_user['task_database_id']
    
    try:
        categories = list_all_categories(user_task_db_id)
        return jsonify(categories)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/api/chat', methods=['POST'])
@require_auth
def chat_endpoint(current_user):
    """Chat endpoint for AI interactions."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        message = data.get('message')
        if not message:
            return jsonify({'error': 'Message is required'}), 400
            
        # Check if user has a task database
        if not current_user.get('task_database_id'):
            return jsonify({'error': 'User does not have a task database configured.'}), 400
            
        user_task_db_id = current_user['task_database_id']
        user_id = current_user.get('user_id')
        
        # Get or create chat context for this user
        if not hasattr(app, 'chat_contexts'):
            app.chat_contexts = {}
            
        if user_id not in app.chat_contexts:
            app.chat_contexts[user_id] = {}
            
        chat_context = app.chat_contexts[user_id]
        
        # Import and use the updated chat handler
        from core.chat.handler import handle_chat_message
        
        # Process the chat message with user context
        response = handle_chat_message(message, user_id, chat_context, user_task_db_id)
        
        return jsonify({
            'response': response
        }), 200
        
    except Exception as e:
        print(f"Chat error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Failed to process chat message'}), 500

@app.route('/chat')
def chat():
    """Chat page."""
    return render_template('chat.html')

@app.route('/user/tasks')
def user_tasks():
    """User tasks page."""
    return render_template('user_tasks.html')

# Admin Routes (admin role required)
@app.route('/api/users', methods=['GET'])
@require_role('admin')
def get_users():
    """Get all users (admin only)."""
    try:
        users = auth_service.get_all_users()
        return jsonify({
            'users': [user.to_public_dict() for user in users]
        }), 200
        
    except Exception as e:
        print(f"Get users error: {str(e)}")
        return jsonify({'error': 'Failed to fetch users'}), 500

@app.route('/api/users/<user_id>', methods=['PUT'])
@require_role('admin')
def update_user(user_id):
    """Update a user by their internal ID (admin only)."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Allow admin to update any field except user_id
        allowed_updates = ['full_name', 'password', 'role', 'is_active', 'email']
        updates = {k: v for k, v in data.items() if k in allowed_updates}
        
        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Update the user
        updated_user = auth_service.update_user(user_id, updates)
        
        if not updated_user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'message': 'User updated successfully',
            'user': updated_user.to_public_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Update user error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/<user_id>/deactivate', methods=['POST'])
@require_role('admin')
def deactivate_user(user_id):
    """Deactivate a user by their internal ID (admin only)."""
    try:
        success = auth_service.deactivate_user(user_id)
        
        if not success:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'message': 'User deactivated successfully'
        }), 200
        
    except Exception as e:
        print(f"Deactivate user error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# User-specific Task Management Endpoints
@app.route('/api/user/tasks', methods=['GET'])
@require_auth
def get_user_tasks(current_user):
    """Fetch all tasks for the authenticated user."""
    if not current_user.get('task_database_id'):
        return jsonify({'error': 'User does not have a task database configured.'}), 400
        
    user_task_db_id = current_user['task_database_id']

    try:
        # Instantiate agent for this request
        notion_agent = NotionAgent()
        
        tasks = notion_agent.fetch_tasks(database_id=user_task_db_id)
        
        # Convert DataFrame to list of dictionaries for JSON response
        tasks_list = tasks.to_dict('records')
        
        return jsonify({'tasks': tasks_list}), 200
        
    except Exception as e:
        print(f"Error fetching user tasks: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Failed to fetch tasks'}), 500

@app.route('/api/user/tasks', methods=['POST'])
@require_auth
def create_user_task(current_user):
    """Create a new task for the authenticated user."""
    if not current_user.get('task_database_id'):
        return jsonify({'error': 'User does not have a task database configured.'}), 400
        
    user_task_db_id = current_user['task_database_id']
    
    try:
        task_data = request.get_json()
        if not task_data or 'task' not in task_data:
            return jsonify({'error': 'Task content is required'}), 400
            
        # Instantiate agent for this request
        notion_agent = NotionAgent()

        # Insert the task into the user's database
        success, message = notion_agent.insert_task(
            database_id=user_task_db_id, 
            task=task_data
        )

        if success:
            return jsonify({'message': 'Task created successfully'}), 201
        else:
            return jsonify({'error': f'Failed to create task: {message}'}), 500

    except Exception as e:
        print(f"Error creating task: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/tasks/<task_id>', methods=['PUT'])
@require_auth
def update_user_task(current_user, task_id):
    """Update a specific task for the authenticated user."""
    # Note: We don't need the user's task_database_id for updating, 
    # as the task_id is globally unique and Notion's API doesn't require the parent DB for updates.
    
    try:
        task_updates = request.get_json()
        if not task_updates:
            return jsonify({'error': 'No update data provided'}), 400
            
        # Instantiate agent for this request
        notion_agent = NotionAgent()

        # Update the task
        success, message = notion_agent.update_task(task_id=task_id, task=task_updates)

        if success:
            return jsonify({'message': 'Task updated successfully'}), 200
        else:
            return jsonify({'error': f'Failed to update task: {message}'}), 500

    except Exception as e:
        print(f"Error updating task: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/tasks/<task_id>', methods=['DELETE'])
@require_auth
def delete_user_task(current_user, task_id):
    """Delete a specific task for the authenticated user."""
    # This endpoint is a placeholder. A 'delete' operation in Notion is typically
    # done by setting the page's 'archived' status to true.
    
    try:
        # Instantiate agent for this request
        notion_agent = NotionAgent()

        # To "delete", we archive the page
        success, message = notion_agent.update_task(
            task_id=task_id,
            task={"archived": True}
        )

        if success:
            return jsonify({'message': 'Task archived (deleted) successfully'}), 200
        else:
            return jsonify({'error': f'Failed to delete task: {message}'}), 500

    except Exception as e:
        print(f"Error deleting task: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/task-database', methods=['POST'])
@require_auth
def create_user_task_database(current_user):
    """Create a task database for the current user (if they don't have one)."""
    try:
        user_id = request.user_id
        user = auth_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.task_database_id:
            return jsonify({'error': 'User already has a task database'}), 400
        
        # Get parent page ID from environment or request
        parent_page_id = request.get_json().get('parent_page_id') if request.get_json() else None
        
        if not parent_page_id:
            return jsonify({'error': 'Parent page ID is required'}), 400
        
        # Create task database for user
        database_id = user_task_service.create_user_task_database(user, parent_page_id)
        
        # Update user with task database ID
        user.task_database_id = database_id
        user_page = auth_service._get_notion_page_by_id(user_id)
        if user_page:
            auth_service._update_user_page(user_page['id'], {"task_database_id": database_id})
        
        return jsonify({
            'message': 'Task database created successfully',
            'database_id': database_id
        }), 201
        
    except Exception as e:
        print(f"Create user task database error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Validate authentication setup
    if ENABLE_AUTHENTICATION:
        if not JWT_SECRET_KEY:
            print("❌ Error: JWT_SECRET_KEY environment variable is required when authentication is enabled")
            sys.exit(1)
        
        if not NOTION_USERS_DB_ID:
            print("❌ Error: NOTION_USERS_DB_ID environment variable is required when authentication is enabled")
            sys.exit(1)
        
        print("✅ Authentication system initialized successfully!")
    
    # Run the application
    app.run(debug=DEBUG_MODE, host='0.0.0.0', port=5001) 