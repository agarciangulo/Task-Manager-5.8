"""
Miscellaneous API routes for AI Team Support.
Includes admin routes, health checks, and utility endpoints.
"""
from flask import Blueprint, jsonify, request
from src.core.security.jwt_utils import require_role
from src.core.services.auth_service import AuthService
from src.config.settings import (
    NOTION_TOKEN, NOTION_USERS_DB_ID, JWT_SECRET_KEY, JWT_ALGORITHM, NOTION_PARENT_PAGE_ID
)
from src.api.models.response_models import create_success_response, create_error_response
from src.core.security.jwt_utils import JWTManager

# Blueprint for miscellaneous routes
misc_bp = Blueprint('misc', __name__, url_prefix='/api')

# Initialize AuthService and JWTManager
jwt_manager = JWTManager(secret_key=JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, NOTION_PARENT_PAGE_ID)

# Health check endpoint
@misc_bp.route('/health', methods=['GET'])
def health():
    return jsonify(create_success_response({"status": "ok"})), 200

# Version endpoint
@misc_bp.route('/version', methods=['GET'])
def version():
    return jsonify(create_success_response({"version": "1.0.0"})), 200

# Admin Routes (admin role required)
@misc_bp.route('/users', methods=['GET'])
@require_role('admin')
def get_users():
    """Get all users (admin only)."""
    try:
        users = auth_service.get_all_users()
        return jsonify(create_success_response({
            'users': [user.to_public_dict() for user in users]
        })), 200
        
    except Exception as e:
        return jsonify(create_error_response('Failed to fetch users')), 500

@misc_bp.route('/users/<user_id>', methods=['PUT'])
@require_role('admin')
def update_user(user_id):
    """Update a user by their internal ID (admin only)."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify(create_error_response('No data provided')), 400
        
        # Allow admin to update any field except user_id
        allowed_updates = ['full_name', 'password', 'role', 'is_active', 'email']
        updates = {k: v for k, v in data.items() if k in allowed_updates}
        
        if not updates:
            return jsonify(create_error_response('No valid fields to update')), 400
        
        # Update the user
        updated_user = auth_service.update_user(user_id, updates)
        
        if not updated_user:
            return jsonify(create_error_response('User not found')), 404
        
        return jsonify(create_success_response({
            'user': updated_user.to_public_dict()
        }, message='User updated successfully')), 200
        
    except ValueError as e:
        return jsonify(create_error_response(str(e))), 400
    except Exception as e:
        return jsonify(create_error_response('Internal server error')), 500

@misc_bp.route('/users/<user_id>/deactivate', methods=['POST'])
@require_role('admin')
def deactivate_user(user_id):
    """Deactivate a user by their internal ID (admin only)."""
    try:
        success = auth_service.deactivate_user(user_id)
        
        if not success:
            return jsonify(create_error_response('User not found')), 404
        
        return jsonify(create_success_response(message='User deactivated successfully')), 200
        
    except Exception as e:
        return jsonify(create_error_response('Internal server error')), 500

# Test authentication endpoint
@misc_bp.route('/test_auth')
def test_auth():
    """Test endpoint to verify authentication is working."""
    return jsonify(create_success_response({
        'message': 'Authentication test endpoint',
        'timestamp': '2024-01-01T00:00:00Z'
    })), 200 