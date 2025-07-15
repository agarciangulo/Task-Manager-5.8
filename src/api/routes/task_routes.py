"""
Task API routes for AI Team Support.
Uses the service layer for business logic.
"""
from flask import Blueprint, request, jsonify
from src.core.container.service_container import get_task_service, get_insight_service
from src.core.exceptions.service_exceptions import (
    TaskServiceError, TaskValidationError, UserNotFoundError
)
from src.core.security.jwt_utils import require_auth
from src.api.models.request_models import (
    ProcessUpdateRequest, CreateTaskRequest, UpdateTaskRequest, GetStaleTasksRequest
)
from src.api.models.response_models import (
    create_success_response, create_error_response, ProcessUpdateResponse, TaskListResponse
)
from src.core.agents.notion_agent import NotionAgent
from src.core.agents.task_extraction_agent import TaskExtractionAgent
from src.core.agents.task_processing_agent import TaskProcessingAgent
from src.core.ai.insights import get_coaching_insight
import traceback

# Blueprint for task routes
task_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')

@task_bp.route('/process_update', methods=['POST'])
@require_auth
def process_update(current_user):
    """Process a text update using the service layer."""
    try:
        data = request.get_json()
        req = ProcessUpdateRequest(text=data.get("text", ""))
        errors = req.validate()
        if errors:
            return jsonify(create_error_response("Validation error", details={"errors": errors})), 400
        
        if not current_user.get('task_database_id'):
            return jsonify(create_error_response('User does not have a task database configured.')), 400
            
        user_task_db_id = current_user['task_database_id']
        task_service = get_task_service()
        
        # Process the update using the service layer
        result = task_service.process_user_update(
            req.text, 
            current_user['user_id']
        )
        
        return jsonify(create_success_response({
            "processed_tasks": result["processed_tasks"],
            "insights": result["insights"],
            "summary": result["summary"],
            "log": result.get("log", [])
        }, message=result["message"]))
        
    except TaskValidationError as e:
        return jsonify(create_error_response(str(e))), 400
    except UserNotFoundError as e:
        return jsonify(create_error_response(str(e))), 404
    except TaskServiceError as e:
        return jsonify(create_error_response(str(e))), 500
    except Exception as e:
        return jsonify(create_error_response("Internal server error")), 500

@task_bp.route('/user/tasks', methods=['GET'])
@require_auth
def get_user_tasks(current_user):
    """Get all tasks for the authenticated user."""
    try:
        task_service = get_task_service()
        tasks = task_service.get_user_tasks(current_user['user_id'])
        
        return jsonify(create_success_response({
            'tasks': tasks
        })), 200
        
    except UserNotFoundError as e:
        return jsonify(create_error_response(str(e))), 404
    except TaskServiceError as e:
        return jsonify(create_error_response(str(e))), 500
    except Exception as e:
        return jsonify(create_error_response("Internal server error")), 500

@task_bp.route('/user/tasks', methods=['POST'])
@require_auth
def create_user_task(current_user):
    """Create a new task for the authenticated user."""
    try:
        task_data = request.get_json()
        req = CreateTaskRequest(
            task=task_data.get('task', ''),
            status=task_data.get('status', 'Not Started'),
            employee=task_data.get('employee', ''),
            category=task_data.get('category', ''),
            priority=task_data.get('priority', 'Medium'),
            date=task_data.get('date', ''),
            description=task_data.get('description', '')
        )
        errors = req.validate()
        if errors:
            return jsonify(create_error_response("Validation error", details={"errors": errors})), 400
        
        task_service = get_task_service()
        success, message = task_service.create_task(
            current_user['user_id'], 
            task_data
        )
        
        if success:
            return jsonify(create_success_response(message="Task created successfully")), 201
        else:
            return jsonify(create_error_response(f'Failed to create task: {message}')), 500
            
    except TaskValidationError as e:
        return jsonify(create_error_response(str(e))), 400
    except UserNotFoundError as e:
        return jsonify(create_error_response(str(e))), 404
    except TaskServiceError as e:
        return jsonify(create_error_response(str(e))), 500
    except Exception as e:
        return jsonify(create_error_response("Internal server error")), 500

@task_bp.route('/user/tasks/<task_id>', methods=['PUT'])
@require_auth
def update_user_task(current_user, task_id):
    """Update a specific task for the authenticated user."""
    try:
        task_updates = request.get_json()
        if not task_updates:
            return jsonify(create_error_response('No update data provided')), 400
        
        task_service = get_task_service()
        success, message = task_service.update_task(task_id, task_updates)
        
        if success:
            return jsonify(create_success_response(message="Task updated successfully")), 200
        else:
            return jsonify(create_error_response(f'Failed to update task: {message}')), 500
            
    except TaskServiceError as e:
        return jsonify(create_error_response(str(e))), 500
    except Exception as e:
        return jsonify(create_error_response("Internal server error")), 500

@task_bp.route('/user/tasks/<task_id>', methods=['DELETE'])
@require_auth
def delete_user_task(current_user, task_id):
    """Delete (archive) a specific task for the authenticated user."""
    try:
        task_service = get_task_service()
        success, message = task_service.delete_task(task_id)
        
        if success:
            return jsonify(create_success_response(message="Task archived successfully")), 200
        else:
            return jsonify(create_error_response(f'Failed to delete task: {message}')), 500
            
    except TaskServiceError as e:
        return jsonify(create_error_response(str(e))), 500
    except Exception as e:
        return jsonify(create_error_response("Internal server error")), 500

@task_bp.route('/user/tasks/by-category', methods=['GET'])
@require_auth
def get_tasks_by_category(current_user):
    """Get tasks grouped by category for the authenticated user."""
    try:
        task_service = get_task_service()
        tasks_by_category = task_service.get_tasks_by_category(current_user['user_id'])
        
        return jsonify(create_success_response(tasks_by_category)), 200
        
    except UserNotFoundError as e:
        return jsonify(create_error_response(str(e))), 404
    except TaskServiceError as e:
        return jsonify(create_error_response(str(e))), 500
    except Exception as e:
        return jsonify(create_error_response("Internal server error")), 500

@task_bp.route('/user/stale-tasks', methods=['GET'])
@require_auth
def get_stale_tasks(current_user):
    """Get stale tasks for the authenticated user."""
    try:
        days = request.args.get('days', 7, type=int)
        req = GetStaleTasksRequest(days=days)
        errors = req.validate()
        if errors:
            return jsonify(create_error_response("Validation error", details={"errors": errors})), 400
        
        task_service = get_task_service()
        stale_tasks = task_service.get_stale_tasks(current_user['user_id'], days)
        
        return jsonify(create_success_response(stale_tasks)), 200
        
    except UserNotFoundError as e:
        return jsonify(create_error_response(str(e))), 404
    except TaskServiceError as e:
        return jsonify(create_error_response(str(e))), 500
    except Exception as e:
        return jsonify(create_error_response("Internal server error")), 500

@task_bp.route('/user/task-database', methods=['POST'])
@require_auth
def create_user_task_database(current_user):
    """Create a task database for the authenticated user."""
    try:
        if not current_user.get('task_database_id'):
            return jsonify(create_error_response('User does not have a task database configured.')), 400
            
        user_task_db_id = current_user['task_database_id']
        
        # Instantiate agent for this request
        notion_agent = NotionAgent()
        
        # Check if database exists and is accessible
        try:
            tasks_df = notion_agent.fetch_tasks(database_id=user_task_db_id)
            return jsonify(create_success_response({
                'database_id': user_task_db_id,
                'task_count': len(tasks_df)
            }, message="Task database is accessible")), 200
        except Exception as e:
            return jsonify(create_error_response(f'Failed to access task database: {str(e)}')), 500
            
    except Exception as e:
        return jsonify(create_error_response("Internal server error")), 500 