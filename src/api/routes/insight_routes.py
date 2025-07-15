"""
Insight API routes for AI Team Support.
Uses the service layer for business logic.
"""
from flask import Blueprint, request, jsonify
from src.core.container.service_container import get_insight_service
from src.core.exceptions.service_exceptions import (
    TaskServiceError, UserNotFoundError
)
from src.core.security.jwt_utils import require_auth
from src.api.models.response_models import (
    create_success_response, create_error_response, InsightResponse, ProjectInsightResponse
)
from src.core.ai.analyzers import TaskAnalyzer
from src.core.agents.notion_agent import NotionAgent
from src.core.chat.handler import handle_chat_message
import traceback

# Blueprint for insight routes
insight_bp = Blueprint('insights', __name__, url_prefix='/api/insights')

# Initialize TaskAnalyzer
task_analyzer = TaskAnalyzer()

@insight_bp.route('/user/insights', methods=['GET'])
@require_auth
def get_user_insights(current_user):
    """Get AI insights for the authenticated user."""
    try:
        insight_service = get_insight_service()
        insights = insight_service.analyze_task_patterns(current_user['user_id'])
        
        return jsonify(create_success_response(insights)), 200
        
    except UserNotFoundError as e:
        return jsonify(create_error_response(str(e))), 404
    except TaskServiceError as e:
        return jsonify(create_error_response(str(e))), 500
    except Exception as e:
        return jsonify(create_error_response("Internal server error")), 500

@insight_bp.route('/user/project-insights/<project_name>', methods=['GET'])
@require_auth
def get_project_insights(current_user, project_name):
    """Get insights for a specific project."""
    try:
        insight_service = get_insight_service()
        insights = insight_service.get_project_insights(
            current_user['user_id'], 
            project_name
        )
        
        return jsonify(create_success_response(insights)), 200
        
    except UserNotFoundError as e:
        return jsonify(create_error_response(str(e))), 404
    except TaskServiceError as e:
        return jsonify(create_error_response(str(e))), 500
    except Exception as e:
        return jsonify(create_error_response("Internal server error")), 500

@insight_bp.route('/chat', methods=['POST'])
@require_auth
def chat_endpoint(current_user):
    """Chat endpoint for AI interactions."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify(create_error_response('No data provided')), 400
        
        message = data.get('message')
        if not message:
            return jsonify(create_error_response('Message is required')), 400
            
        # Check if user has a task database
        if not current_user.get('task_database_id'):
            return jsonify(create_error_response('User does not have a task database configured.')), 400
            
        user_task_db_id = current_user['task_database_id']
        user_id = current_user.get('user_id')
        
        # Get or create chat context for this user
        if not hasattr(insight_bp, 'chat_contexts'):
            insight_bp.chat_contexts = {}
            
        if user_id not in insight_bp.chat_contexts:
            insight_bp.chat_contexts[user_id] = {}
            
        chat_context = insight_bp.chat_contexts[user_id]
        
        # Process the chat message with user context
        response = handle_chat_message(message, user_id, chat_context, user_task_db_id)
        
        return jsonify(create_success_response({
            'response': response
        })), 200
        
    except Exception as e:
        print(f"Chat error: {str(e)}")
        traceback.print_exc()
        return jsonify(create_error_response('Failed to process chat message')), 500

@insight_bp.route('/dashboard-data', methods=['GET'])
@require_auth
def get_dashboard_data(current_user):
    """Provide data for the dashboard."""
    try:
        # Ensure user has a task database
        if not current_user.get('task_database_id'):
            return jsonify(create_error_response('User does not have a task database configured.')), 400

        user_task_db_id = current_user['task_database_id']
        
        # Instantiate agent for this request
        notion_agent = NotionAgent()
        
        # Fetch tasks from the user-specific database
        tasks_df = notion_agent.fetch_tasks(database_id=user_task_db_id)

        if tasks_df.empty:
            return jsonify(create_success_response({
                "summary_stats": {},
                "tasks_by_status": {},
                "tasks_by_category": {},
                "upcoming_deadlines": [],
                "recent_tasks": []
            })), 200

        # Process data
        summary_stats = task_analyzer.get_summary_statistics(tasks_df)
        
        return jsonify(create_success_response({
            "summary_stats": summary_stats,
            "tasks_by_status": task_analyzer.get_tasks_by_status(tasks_df),
            "tasks_by_category": task_analyzer.get_tasks_by_category(tasks_df),
            "upcoming_deadlines": task_analyzer.get_upcoming_deadlines(tasks_df),
            "recent_tasks": tasks_df.head().to_dict('records')
        })), 200

    except Exception as e:
        print(f"Dashboard data error: {e}")
        traceback.print_exc()
        return jsonify(create_error_response(f"An error occurred: {e}")), 500

@insight_bp.route('/categories', methods=['GET'])
@require_auth
def get_categories(current_user):
    """Get all unique categories from user's database."""
    try:
        if not current_user.get('task_database_id'):
            return jsonify(create_error_response('User does not have a task database configured.')), 400
            
        user_task_db_id = current_user['task_database_id']
        
        # Instantiate agent for this request
        notion_agent = NotionAgent()
        tasks_df = notion_agent.fetch_tasks(database_id=user_task_db_id)
        
        if tasks_df.empty:
            return jsonify(create_success_response([])), 200
            
        # Get unique categories
        categories = tasks_df['Category'].dropna().unique().tolist()
        
        return jsonify(create_success_response(categories)), 200
        
    except Exception as e:
        return jsonify(create_error_response(f"An error occurred: {e}")), 500 