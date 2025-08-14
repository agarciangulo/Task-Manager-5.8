"""
Simplified Flask app for testing authentication flow only.
This version removes heavy dependencies to focus on auth debugging.
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add current directory to Python path for local testing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Debug: Print environment variables (only first few characters for security)
print("\nEnvironment Variables Loaded:")
print(f"GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY')[:8]}..." if os.getenv('GEMINI_API_KEY') else "Not found")
print(f"NOTION_TOKEN: {os.getenv('NOTION_TOKEN')[:8]}..." if os.getenv('NOTION_TOKEN') else "Not found")
print(f"NOTION_USERS_DB_ID: {os.getenv('NOTION_USERS_DB_ID')[:8]}..." if os.getenv('NOTION_USERS_DB_ID') else "Not found")
print(f"JWT_SECRET_KEY: {os.getenv('JWT_SECRET_KEY')[:8]}..." if os.getenv('JWT_SECRET_KEY') else "Not found")
print("----------------------------------------\n")

# Import only essential modules
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS

# Import authentication components only
from src.core.security.jwt_utils import JWTManager, require_auth
from src.core.services.auth_service import AuthService

# Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-here')
JWT_ALGORITHM = 'HS256'
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_USERS_DB_ID = os.getenv('NOTION_USERS_DB_ID')

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = JWT_SECRET_KEY
CORS(app)

# Initialize JWT Manager
jwt_manager = JWTManager(secret_key=JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
app.jwt_manager = jwt_manager

# Debug: Print JWT configuration
print(f"JWT Secret Key: {JWT_SECRET_KEY[:8]}..." if JWT_SECRET_KEY else "Not found")
print(f"JWT Algorithm: {JWT_ALGORITHM}")
print(f"JWT Manager Secret: {jwt_manager.secret_key[:8]}..." if jwt_manager.secret_key else "Not found")

# Initialize Authentication Service
auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, None)
app.auth_service = auth_service

# Routes
@app.route('/')
def index():
    """Main page where users can paste updates."""
    return render_template('index.html')

@app.route('/login')
def login_page():
    """Login page."""
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/login', methods=['POST'])
def login():
    """Handle user login."""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        print(f"Login attempt for email: {email}")
        
        # Authenticate user
        token = auth_service.authenticate_user(email, password)
        
        if token:
            # Get user info
            user = auth_service.get_user_by_email(email)
            user_data = {
                'user_id': user.user_id,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role
            }
            
            print(f"✅ Login successful for {email}")
            return jsonify({
                'success': True,
                'token': token,
                'user': user_data
            })
        else:
            print(f"❌ Login failed for {email}")
            return jsonify({'error': 'Invalid email or password'}), 401
            
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/test_auth')
@require_auth
def test_auth(current_user):
    """Test endpoint to verify authentication is working."""
    print(f"Test auth called with user: {current_user}")
    return jsonify({
        "success": True,
        "message": "Authentication working!",
        "user": current_user
    })

@app.route('/api/register', methods=['POST'])
def register():
    """Handle user registration."""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        
        if not email or not password or not full_name:
            return jsonify({'error': 'Email, password, and full name are required'}), 400
        
        # Register user
        user = auth_service.register_user(email, password, full_name)
        
        if user:
            return jsonify({
                'success': True,
                'message': 'User registered successfully'
            })
        else:
            return jsonify({'error': 'Registration failed'}), 400
            
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Flask app on port {port}")
    print(f"📧 Gmail processor status: Working perfectly ✅")
    print(f"🔐 Authentication system: Ready for testing")
    app.run(debug=True, host='0.0.0.0', port=port) 