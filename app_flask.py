"""
Alternative web application version using Flask instead of Gradio.
This provides a more traditional web interface that can be hosted as a regular web application.
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
    "flask-cors==4.0.0"
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
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# Import from the new structure
from core.agents.notion_agent import NotionAgent
from core.agents.task_extraction_agent import TaskExtractionAgent
from core.agents.task_processing_agent import TaskProcessingAgent
from core.ai.analyzers import TaskAnalyzer, ProjectAnalyzer
from core.ai.insights import get_project_insight
from core import identify_stale_tasks, list_all_categories

# Import from plugins
from plugins import initialize_all_plugins, plugin_manager

# Import from config
from config import (
    GEMINI_API_KEY,
    NOTION_TOKEN,
    NOTION_DATABASE_ID,
    NOTION_FEEDBACK_DB_ID,
    SIMILARITY_THRESHOLD,
    ENABLE_TASK_VALIDATION,
    ENABLE_CHAT_VERIFICATION,
    DEBUG_MODE
)

# Initialize plugins
initialize_all_plugins()

# Initialize Flask app
app = Flask(__name__, 
            static_folder="static",
            template_folder="templates")

# Enable CORS
CORS(app)

# Initialize the TaskAnalyzer
task_analyzer = TaskAnalyzer()

# Initialize NotionAgent
notion_agent = NotionAgent()

# Initialize TaskExtractionAgent
task_extraction_agent = TaskExtractionAgent()

# Initialize TaskProcessingAgent
task_processing_agent = TaskProcessingAgent()

# Validate Notion connection at startup
print("\nValidating Notion connection...")
notion_connected = notion_agent.validate_connection()
if not notion_connected:
    print("⚠️ Warning: Notion connection failed. Some features may not work.")
else:
    print("✅ Notion connection successful!")

@app.route('/')
def index():
    """Render main page."""
    try:
        print("\nFetching categories...")
        # For the public index page, we'll use a default database or empty list
        # since we don't have a specific user context
        categories = []
        print(f"Categories found: {categories}")
        return render_template('index.html', categories=categories)
    except Exception as e:
        print(f"Error in index route: {e}")
        print(traceback.format_exc())
        return str(e), 500

@app.route('/dashboard')
def dashboard():
    """Render dashboard page."""
    # For the public dashboard page, we'll use a default database or empty list
    # since we don't have a specific user context
    categories = []
    return render_template('dashboard.html', categories=categories)

@app.route('/api/dashboard_data')
def api_dashboard_data():
    """API endpoint to get dashboard data with filtering support."""
    try:
        # Get filter parameters
        employee_filter = request.args.get('employee', 'all')
        project_filter = request.args.get('project', 'all')
        
        # Get all tasks
        df = notion_agent.fetch_tasks()
        
        # Apply filters
        filtered_df = df.copy()
        
        if employee_filter != 'all':
            filtered_df = filtered_df[filtered_df['employee'] == employee_filter]
            
        if project_filter != 'all':
            filtered_df = filtered_df[filtered_df['category'] == project_filter]
        
        # Calculate overall metrics
        total_tasks = len(filtered_df)
        completed_tasks = len(filtered_df[filtered_df['status'] == 'Completed'])
        in_progress_tasks = len(filtered_df[filtered_df['status'] == 'In Progress'])
        pending_tasks = len(filtered_df[filtered_df['status'] == 'Pending'])
        blocked_tasks = len(filtered_df[filtered_df['status'] == 'Blocked'])
        
        completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0
        
        # Calculate tasks by category
        category_counts = filtered_df['category'].value_counts().to_dict()
        
        # Calculate task trend (completed tasks over time)
        # Make sure to handle date conversion properly
        filtered_df['date'] = pd.to_datetime(filtered_df['date'])
        df_completed = filtered_df[filtered_df['status'] == 'Completed']
        
        # Group by date and count
        if not df_completed.empty:
            trend_data = df_completed.groupby(df_completed['date'].dt.strftime('%Y-%m-%d')).size().to_dict()
            # Sort by date
            trend_data = {k: trend_data[k] for k in sorted(trend_data.keys())}
        else:
            trend_data = {}
        
        # Calculate project health scores
        project_health = {}
        
        # Use only the filtered dataframe when calculating project health
        if project_filter != 'all':
            # If filtering by project, only calculate health for that project
            categories = [project_filter]
        else:
            # Otherwise, get all unique categories from the filtered dataframe
            categories = filtered_df['category'].unique()
        
        from core.ai.analyzers import ProjectAnalyzer
        analyzer = ProjectAnalyzer()
        
        for category in categories:
            if not category or category == '':
                continue
                
            # For project health, we need to consider all tasks in that project
            # (not just the filtered employee's tasks)
            if employee_filter != 'all':
                # When filtering by employee, show the project health of the
                # projects they're working on, but based on all tasks in that project
                category_tasks = df[df['category'] == category]
            else:
                category_tasks = filtered_df[filtered_df['category'] == category]
                
            if len(category_tasks) > 0:
                health_check = analyzer.analyze(category_tasks, category, "health_check")
                project_health[category] = {
                    "score": round(health_check.get("health_score", 50), 1),
                    "status": health_check.get("health_status", "Unknown"),
                    "task_count": health_check.get("task_count", 0)
                }
        
        return jsonify({
            'success': True,
            'metrics': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'in_progress_tasks': in_progress_tasks,
                'pending_tasks': pending_tasks,
                'blocked_tasks': blocked_tasks,
                'completion_rate': completion_rate
            },
            'category_counts': category_counts,
            'trend_data': trend_data,
            'project_health': project_health
        })
        
    except Exception as e:
        print(f"Error in api_dashboard_data: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f"Error fetching dashboard data: {e}"
        })

@app.route('/api/process_update', methods=['POST'])
def process_update():
    """Process a task update and return insights."""
    logger = logging.getLogger("process_update")
    try:
        logger.info("Received process_update request")
        data = request.get_json()
        print(f"Request data: {data}")  # Debug log
        if not data or 'text' not in data:
            logger.error("No text provided in request")
            return jsonify({"error": "No text provided"}), 400

        text = data['text']

        logger.info("Extracting tasks from input text")
        processed_tasks = task_extraction_agent.extract_tasks(text)
        logger.info(f"Extracted {len(processed_tasks) if processed_tasks else 0} tasks: {processed_tasks}")
        if not processed_tasks:
            logger.error("No tasks found in the update")
            return jsonify({"error": "No tasks found in the update"}), 400

        logger.info("Fetching existing tasks from Notion")
        recent_tasks = notion_agent.fetch_tasks()
        logger.info(f"Fetched {len(recent_tasks) if hasattr(recent_tasks, '__len__') else 'unknown'} existing tasks")

        # Insert or update each task and log the result
        results = []
        print("[DEBUG] Starting task processing loop")
        for i, task in enumerate(processed_tasks):
            try:
                print(f"[DEBUG] Processing task {i+1}/{len(processed_tasks)}: {task}")
                result = task_processing_agent.process_task(task, recent_tasks)
                print(f"[DEBUG] Result for task {i+1}: {result}")
                results.append({"task": task, "result": result})
            except Exception as e:
                print(f"[DEBUG] Exception while processing task {i+1}: {e}")
                logger.error(f"Exception while processing task {i+1}: {e}", exc_info=True)
                results.append({"task": task, "error": str(e)})

        print("[DEBUG] Finished task processing loop. Results:", results)

        # Get person name from the first task if available
        person_name = processed_tasks[0].get("employee", "Unknown") if processed_tasks else "Unknown"

        logger.info(f"Fetching peer feedback for {person_name}")
        print(f"[DEBUG] Fetching peer feedback for {person_name}")
        peer_feedback = notion_agent.fetch_peer_feedback(person_name=person_name)
        print(f"[DEBUG] Peer feedback: {peer_feedback}")

        print("[DEBUG] Generating coaching insights using TaskAnalyzer")
        logger.info("Generating coaching insights using TaskAnalyzer")
        coaching_result = task_analyzer.analyze(
            tasks=processed_tasks,
            analysis_type="ai_insights",
            person_name=person_name,
            recent_tasks=recent_tasks,
            peer_feedback=peer_feedback
        )
        print(f"[DEBUG] Coaching result: {coaching_result}")
        coaching = coaching_result.get("insight", "Unable to generate coaching insights at this time.")
        logger.info(f"Successfully generated coaching insights: {coaching}")

        response = {
            "success": True,
            "tasks": processed_tasks,
            "coaching": coaching,
            "results": results,
            "needs_verification": any(task.get("needs_verification", False) for task in processed_tasks),
            "complete_count": len([t for t in processed_tasks if not t.get("needs_verification", False)]),
            "incomplete_count": len([t for t in processed_tasks if t.get("needs_verification", False)]),
            "verification_message": "Some tasks need more information. Please provide additional details.",
            "has_pending_tasks": False,
            "processed_tasks": [{
                "task": task["task"],
                "status": task.get("status", "Not Started"),
                "employee": task.get("employee", ""),
                "category": task.get("category", "")
            } for task in processed_tasks]
        }
        print(f"[DEBUG] Returning response: {response}")
        logger.info(f"Returning response: {response}")
        return jsonify(response)

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error processing update: {e}\n{tb}")
        print(f"Error processing update: {e}")
        print(tb)
        error_response = {
            "error": f"An error occurred while processing your update: {e}",
            "traceback": tb
        }
        print(f"Error response: {error_response}")  # Debug log
        return jsonify(error_response), 500

@app.route('/api/stale_tasks')
def api_stale_tasks():
    """API endpoint to get stale tasks."""
    try:
        stale = identify_stale_tasks(days=7)
        if not stale:
            return jsonify({
                'success': True,
                'has_stale': False,
                'message': 'No overdue tasks!'
            })
        # Format stale tasks by employee
        stale_tasks_by_employee = {}
        for task in stale:
            employee = task.get('employee', 'Unknown')
            if employee not in stale_tasks_by_employee:
                stale_tasks_by_employee[employee] = []
            date_str = task.get('due_date') or task.get('date') or 'No date'
            status = task.get('status', 'Unknown')
            stale_tasks_by_employee[employee].append({
                'task': task.get('task', ''),
                'status': status,
                'date': date_str,
                'days_old': None  # Placeholder, can be improved later
            })
        return jsonify({
            'success': True,
            'has_stale': True,
            'tasks_by_employee': stale_tasks_by_employee
        })
    except Exception as e:
        import traceback
        print(f"Error in api_stale_tasks: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f"Error checking overdue tasks: {e}"
        })

@app.route('/api/tasks_by_category')
def api_tasks_by_category():
    """API endpoint to get tasks by category."""
    try:
        category = request.args.get('category', '')
        if not category:
            return jsonify({
                'success': False,
                'message': 'No category specified'
            })
            
        df = notion_agent.fetch_tasks()
        filtered = df[(df["category"] == category) & (df["status"] != "Completed")]
        
        if filtered.empty:
            return jsonify({
                'success': True,
                'has_tasks': False,
                'message': f"No open tasks in project '{category}'"
            })
            
        # Format tasks by employee
        tasks_by_employee = {}
        for _, row in filtered.iterrows():
            employee = row['employee']
            if employee not in tasks_by_employee:
                tasks_by_employee[employee] = []
                
            date_str = row['date'].strftime('%Y-%m-%d') if row['date'] else "No date"
            tasks_by_employee[employee].append({
                'task': row['task'],
                'status': row['status'],
                'date': date_str
            })
            
        # Get status summary
        status_summary = filtered["status"].value_counts().to_dict()
        
        # Get AI insight
        try:
            insight = get_project_insight(category, filtered)
        except Exception as e:
            insight = f"Unable to generate AI insight: {e}"
            
        return jsonify({
            'success': True,
            'has_tasks': True,
            'tasks_by_employee': tasks_by_employee,
            'status_summary': status_summary,
            'insight': insight
        })
        
    except Exception as e:
        print(f"Error in api_tasks_by_category: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f"Error getting project tasks: {e}"
        })

@app.route('/api/categories')
def api_categories():
    """API endpoint to get all categories."""
    try:
        # For the public API, we'll use a default database or empty list
        # since we don't have a specific user context
        categories = []
        return jsonify({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        print(f"Error in api_categories: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f"Error fetching categories: {e}"
        })
    
@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    """API endpoint for chat interactions."""
    try:
        # Get data from request
        if request.is_json:
            data = request.get_json()
            message = data.get('message', '')
            user_id = data.get('user_id', '')
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid request format'
            })
                
        if not message:
            return jsonify({
                'success': False,
                'message': 'No message provided'
            })

        # Get or create session manager
        from core.chat.session import get_session_manager
        session_manager = get_session_manager()
        
        # Get chat session
        chat_session = session_manager.get_session(user_id)
        chat_context = chat_session.get_context()
        
        # Import chat handler
        from core.chat.handler import handle_chat_message
        
        # Process message
        result = handle_chat_message(message, user_id, chat_context)
        
        # Check if it's a structured result or just a string
        if isinstance(result, dict):
            response_message = result.get("message", "")
            if result.get("follow_up"):
                response_message += "\n\n" + result.get("follow_up")
                
            response = {
                'success': True,
                'message': response_message,
                'user_id': user_id,
                'context': chat_context
            }
        else:
            response = {
                'success': True,
                'message': result,
                'user_id': user_id,
                'context': chat_context
            }
            
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in chat_endpoint: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f"Error processing chat message: {e}"
        })

@app.route('/chat')
def chat_page():
    """Render chat page."""
    return render_template('chat.html')

if __name__ == '__main__':
    app.run(debug=DEBUG_MODE, port=5000)