from flask import Blueprint, request, jsonify
from src.core.security.jwt_utils import require_auth
from src.core.services.auth_service import AuthService
from src.config.settings import (
    NOTION_TOKEN, NOTION_USERS_DB_ID, JWT_EXPIRATION_HOURS, JWT_SECRET_KEY, JWT_ALGORITHM, NOTION_PARENT_PAGE_ID
)
from src.api.models.request_models import LoginRequest, RegisterRequest
from src.api.models.response_models import create_success_response, create_error_response
from src.core.security.jwt_utils import JWTManager

# Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Initialize AuthService and JWTManager
jwt_manager = JWTManager(secret_key=JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, NOTION_PARENT_PAGE_ID)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    req = RegisterRequest(
        email=data.get('email', ''),
        password=data.get('password', ''),
        full_name=data.get('full_name', ''),
        company=data.get('company', '')
    )
    errors = req.validate()
    if errors:
        return jsonify(create_error_response("Validation error", details={"errors": errors})), 400
    try:
        user = auth_service.register_user(req.email, req.password, req.full_name, role='user')
        final_user = auth_service.get_user_by_email(req.email)
        return jsonify(create_success_response({
            'user': final_user.to_public_dict() if final_user else user.to_public_dict()
        }, message='User registered successfully')), 201
    except ValueError as e:
        return jsonify(create_error_response(str(e))), 400
    except Exception as e:
        return jsonify(create_error_response('Internal server error')), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    req = LoginRequest(
        email=data.get('email', ''),
        password=data.get('password', '')
    )
    errors = req.validate()
    if errors:
        return jsonify(create_error_response("Validation error", details={"errors": errors})), 400
    try:
        token = auth_service.authenticate_user(req.email, req.password)
        if not token:
            return jsonify(create_error_response('Invalid credentials')), 401
        user = auth_service.get_user_by_email(req.email)
        return jsonify(create_success_response({
            'token': token,
            'user': user.to_public_dict() if user else None,
            'expires_in': JWT_EXPIRATION_HOURS * 3600
        }, message='Login successful')), 200
    except Exception as e:
        return jsonify(create_error_response('Internal server error')), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify(create_error_response('Authorization header required')), 401
    token = auth_header.split(' ')[1]
    try:
        new_token = jwt_manager.refresh_token(token, JWT_EXPIRATION_HOURS * 3600)
        return jsonify(create_success_response({
            'token': new_token,
            'expires_in': JWT_EXPIRATION_HOURS * 3600
        }, message='Token refreshed successfully')), 200
    except Exception as e:
        return jsonify(create_error_response('Invalid token')), 401

@auth_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile(current_user):
    try:
        user = auth_service.get_user_by_id(current_user['user_id'])
        if not user:
            return jsonify(create_error_response('User not found')), 404
        return jsonify(create_success_response({
            'user': user.to_public_dict()
        })), 200
    except Exception as e:
        return jsonify(create_error_response('Internal server error')), 500

@auth_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile(current_user):
    data = request.get_json()
    allowed_updates = ['full_name', 'password']
    updates = {k: v for k, v in data.items() if k in allowed_updates}
    if not updates:
        return jsonify(create_error_response('No valid fields to update')), 400
    try:
        updated_user = auth_service.update_user(current_user['user_id'], updates)
        if not updated_user:
            return jsonify(create_error_response('User not found')), 404
        return jsonify(create_success_response({
            'user': updated_user.to_public_dict()
        }, message='Profile updated successfully')), 200
    except ValueError as e:
        return jsonify(create_error_response(str(e))), 400
    except Exception as e:
        return jsonify(create_error_response('Internal server error')), 500 