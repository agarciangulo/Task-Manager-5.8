"""
JWT utilities for authentication system.
"""
import jwt
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from functools import wraps
from flask import request, jsonify, current_app, redirect, url_for


class JWTManager:
    """Manages JWT token operations."""
    
    def __init__(self, secret_key: Optional[str] = None, algorithm: str = 'HS256'):
        """
        Initialize JWT manager.
        
        Args:
            secret_key: Secret key for JWT signing. If None, will use environment variable.
            algorithm: JWT algorithm to use.
        """
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY')
        if not self.secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable must be set")
        self.algorithm = algorithm
    
    def generate_token(self, user_id: str, role: str, email: str, expires_in: int = 3600) -> str:
        """
        Generate a JWT token for a user.
        
        Args:
            user_id: The user's internal ID (UUID).
            role: The user's role.
            email: The user's email address.
            expires_in: Token expiration time in seconds (default: 1 hour).
            
        Returns:
            str: The JWT token.
        """
        payload = {
            'user_id': user_id,
            'role': role,
            'email': email,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: The JWT token to decode.
            
        Returns:
            Dict[str, Any]: The decoded token payload.
            
        Raises:
            jwt.ExpiredSignatureError: If token has expired.
            jwt.InvalidTokenError: If token is invalid.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")
    
    def refresh_token(self, token: str, expires_in: int = 3600) -> str:
        """
        Refresh a JWT token.
        
        Args:
            token: The current JWT token.
            expires_in: New token expiration time in seconds.
            
        Returns:
            str: The new JWT token.
        """
        try:
            # Decode the current token to get user info
            payload = self.decode_token(token)
            
            # Remove exp and iat from payload
            payload.pop('exp', None)
            payload.pop('iat', None)
            
            # Generate new token
            return self.generate_token(payload['user_id'], payload['role'], payload['email'], expires_in)
            
        except jwt.InvalidTokenError:
            raise jwt.InvalidTokenError("Cannot refresh invalid token")


def require_auth(f):
    """
    Decorator to require authentication for Flask routes.
    
    This decorator handles both browser-based and API-based authentication.
    - For browser requests (HTML), it redirects to the login page.
    - For API requests (JSON), it returns a 401 error.
    
    Args:
        f: The Flask route function to protect.
        
    Returns:
        function: The wrapped function.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Determine if it's a browser or API request
        is_browser_request = 'text/html' in request.headers.get('Accept', '')

        # Helper function to handle unauthenticated requests
        def handle_unauthenticated():
            if is_browser_request:
                return redirect(url_for('login_page'))
            else:
                return jsonify({'error': 'Authorization header missing'}), 401

        # Get the token from the Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return handle_unauthenticated()
        
        # Check if the header starts with 'Bearer '
        if not auth_header.startswith('Bearer '):
            return handle_unauthenticated()
        
        # Extract the token
        token = auth_header.split(' ')[1]
        
        try:
            # Get JWT manager from app context
            jwt_manager = current_app.jwt_manager
            
            # Debug: Print token and secret key
            print(f"Token: {token[:20]}...")
            print(f"JWT Manager Secret: {jwt_manager.secret_key[:8]}..." if jwt_manager.secret_key else "Not found")
            
            # Decode and validate the token
            payload = jwt_manager.decode_token(token)
            
            print(f"Token payload: {payload}")
            
            # Add user info to request context
            request.user_id = payload['user_id']
            request.user_role = payload['role']
            request.user_email = payload.get('email')
            
            return f(*args, **kwargs)
            
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
            print(f"JWT Error: {str(e)}")
            return handle_unauthenticated()
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            if is_browser_request:
                return redirect(url_for('login_page'))
            else:
                return jsonify({'error': f'Authentication error: {str(e)}'}), 401
    
    return decorated_function


def require_role(required_role: str):
    """
    Decorator to require a specific role for Flask routes.
    
    Args:
        required_role: The role required to access the route.
        
    Returns:
        function: The decorator function.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # First check authentication
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                return jsonify({'error': 'Authorization header missing'}), 401
            
            if not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Invalid authorization header format'}), 401
            
            token = auth_header.split(' ')[1]
            
            try:
                jwt_manager = current_app.jwt_manager
                payload = jwt_manager.decode_token(token)
                
                # Check if user has the required role
                if payload.get('role') != required_role:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                # Add user info to request context
                request.user_id = payload['user_id']
                request.user_role = payload['role']
                request.user_email = payload.get('email')
                
                return f(*args, **kwargs)
                
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401
            except Exception as e:
                return jsonify({'error': f'Authentication error: {str(e)}'}), 401
        
        return decorated_function
    return decorator 