"""
Swagger/OpenAPI configuration for AI Team Support API.
Provides API documentation and interactive explorer.
"""
from flask_restx import Api, Resource, fields
from flask import Blueprint

# Create API documentation blueprint
docs_bp = Blueprint('docs', __name__, url_prefix='/api/docs')

# Initialize Flask-RESTX API
api = Api(
    docs_bp,
    title='AI Team Support API',
    version='1.0.0',
    description='API for AI-powered team task management and insights',
    doc='/',
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'JWT token in format: Bearer <token>'
        }
    },
    security='Bearer'
)

# Define common response models
error_model = api.model('Error', {
    'success': fields.Boolean(required=True, description='Operation success status'),
    'message': fields.String(required=True, description='Error message'),
    'error_code': fields.String(description='Error code'),
    'details': fields.Raw(description='Additional error details'),
    'timestamp': fields.String(description='Error timestamp')
})

success_model = api.model('Success', {
    'success': fields.Boolean(required=True, description='Operation success status'),
    'message': fields.String(required=True, description='Success message'),
    'data': fields.Raw(description='Response data'),
    'timestamp': fields.String(description='Response timestamp')
})

# Define request models
login_request = api.model('LoginRequest', {
    'email': fields.String(required=True, description='User email address'),
    'password': fields.String(required=True, description='User password')
})

register_request = api.model('RegisterRequest', {
    'email': fields.String(required=True, description='User email address'),
    'password': fields.String(required=True, description='User password'),
    'full_name': fields.String(required=True, description='User full name'),
    'company': fields.String(description='User company')
})

process_update_request = api.model('ProcessUpdateRequest', {
    'text': fields.String(required=True, description='Text update to process')
})

create_task_request = api.model('CreateTaskRequest', {
    'task': fields.String(required=True, description='Task description'),
    'status': fields.String(description='Task status', enum=['Not Started', 'In Progress', 'Completed', 'On Hold']),
    'employee': fields.String(description='Assigned employee'),
    'category': fields.String(description='Task category'),
    'priority': fields.String(description='Task priority', enum=['Low', 'Medium', 'High', 'Urgent']),
    'date': fields.String(description='Task due date'),
    'description': fields.String(description='Additional task description')
})

# Define response models
user_model = api.model('User', {
    'user_id': fields.String(description='User ID'),
    'email': fields.String(description='User email'),
    'full_name': fields.String(description='User full name'),
    'role': fields.String(description='User role'),
    'is_active': fields.Boolean(description='User active status'),
    'task_database_id': fields.String(description='User task database ID')
})

auth_response = api.model('AuthResponse', {
    'success': fields.Boolean(required=True),
    'message': fields.String(required=True),
    'token': fields.String(description='JWT token'),
    'user': fields.Nested(user_model),
    'expires_in': fields.Integer(description='Token expiration time in seconds')
})

task_model = api.model('Task', {
    'id': fields.String(description='Task ID'),
    'task': fields.String(description='Task description'),
    'status': fields.String(description='Task status'),
    'employee': fields.String(description='Assigned employee'),
    'category': fields.String(description='Task category'),
    'priority': fields.String(description='Task priority'),
    'date': fields.String(description='Task due date'),
    'description': fields.String(description='Additional description')
})

process_update_response = api.model('ProcessUpdateResponse', {
    'success': fields.Boolean(required=True),
    'message': fields.String(required=True),
    'processed_tasks': fields.List(fields.Raw, description='List of processed tasks'),
    'insights': fields.String(description='AI-generated insights'),
    'summary': fields.Raw(description='Processing summary'),
    'log': fields.List(fields.String, description='Processing log')
})

# Namespace definitions
auth_ns = api.namespace('auth', description='Authentication operations')
tasks_ns = api.namespace('tasks', description='Task management operations')
insights_ns = api.namespace('insights', description='AI insights operations')
misc_ns = api.namespace('misc', description='Utility operations')

def init_documentation(app):
    """Initialize API documentation with the Flask app."""
    app.register_blueprint(docs_bp)
    return api 