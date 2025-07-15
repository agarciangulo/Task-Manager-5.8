# Authentication System Setup Guide

This guide explains how to set up and use the complete authentication system for the Task Manager application.

## Overview

The authentication system provides:
- Secure user registration and login
- JWT-based authentication
- Role-based access control
- Password hashing with bcrypt
- Notion database integration for user storage
- Protected API endpoints

## Prerequisites

1. **Notion Setup**: You need a Notion database for storing user information
2. **Environment Variables**: Configure the required environment variables
3. **Dependencies**: Install the required Python packages

## 1. Notion Database Setup

Create a new database in Notion with the following properties:

### Required Properties:
- **UserID** (Title): The unique identifier for each user
- **PasswordHash** (Text): The hashed password (will be automatically populated)
- **FullName** (Text): The user's full name
- **Role** (Select): User role with options "user" and "admin"

### Optional Properties:
- **CreatedAt** (Date): When the user was created
- **UpdatedAt** (Date): When the user was last updated
- **LastLogin** (Date): When the user last logged in
- **IsActive** (Checkbox): Whether the user account is active

### Database Configuration:
1. Create a new page in Notion
2. Add a database block
3. Configure the properties as listed above
4. Copy the database ID from the URL (the part after the last slash)

## 2. Environment Variables

Add the following environment variables to your `.env` file:

```bash
# Authentication Settings
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ENABLE_AUTHENTICATION=True

# Notion Users Database
NOTION_USERS_DB_ID=your-notion-users-database-id

# Existing Notion Settings
NOTION_TOKEN=your-notion-api-token
NOTION_DATABASE_ID=your-notion-tasks-database-id
NOTION_FEEDBACK_DB_ID=your-notion-feedback-database-id
```

### JWT Secret Key Generation

Generate a secure JWT secret key:

```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using OpenSSL
openssl rand -base64 32
```

## 3. Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

The authentication system requires these additional packages:
- `PyJWT`: For JWT token handling
- `bcrypt`: For password hashing

## 4. Running the Application

Start the application with authentication enabled:

```bash
python app_auth.py
```

## 5. API Endpoints

### Public Endpoints (No Authentication Required)

#### Register User
```http
POST /api/register
Content-Type: application/json

{
    "user_id": "john_doe",
    "password": "securepassword123",
    "full_name": "John Doe",
    "role": "user"
}
```

#### Login
```http
POST /api/login
Content-Type: application/json

{
    "user_id": "john_doe",
    "password": "securepassword123"
}
```

Response:
```json
{
    "message": "Login successful",
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "user_id": "john_doe",
        "full_name": "John Doe",
        "role": "user",
        "created_at": "2024-01-01T00:00:00",
        "last_login": "2024-01-01T12:00:00",
        "is_active": true
    },
    "expires_in": 86400
}
```

#### Refresh Token
```http
POST /api/refresh
Authorization: Bearer <your-jwt-token>
```

### Protected Endpoints (Authentication Required)

All protected endpoints require the `Authorization` header:
```
Authorization: Bearer <your-jwt-token>
```

#### Get User Profile
```http
GET /api/profile
Authorization: Bearer <your-jwt-token>
```

#### Update User Profile
```http
PUT /api/profile
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
    "full_name": "John Smith",
    "password": "newpassword123"
}
```

#### Dashboard Data
```http
GET /api/dashboard_data
Authorization: Bearer <your-jwt-token>
```

#### Process Task Update
```http
POST /api/process_update
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
    "task_id": "123",
    "status": "completed"
}
```

#### Get Stale Tasks
```http
GET /api/stale_tasks
Authorization: Bearer <your-jwt-token>
```

#### Get Tasks by Category
```http
GET /api/tasks_by_category
Authorization: Bearer <your-jwt-token>
```

#### Get Categories
```http
GET /api/categories
Authorization: Bearer <your-jwt-token>
```

#### Chat with AI
```http
POST /api/chat
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
    "message": "What are my pending tasks?"
}
```

### Admin Endpoints (Admin Role Required)

#### Get All Users
```http
GET /api/users
Authorization: Bearer <admin-jwt-token>
```

#### Update User
```http
PUT /api/users/<user_id>
Authorization: Bearer <admin-jwt-token>
Content-Type: application/json

{
    "full_name": "Jane Doe",
    "role": "admin",
    "is_active": true
}
```

#### Deactivate User
```http
POST /api/users/<user_id>/deactivate
Authorization: Bearer <admin-jwt-token>
```

## 6. Frontend Integration

### Include Authentication Script

Add the authentication script to your HTML pages:

```html
<script src="/static/js/auth.js"></script>
```

### Check Authentication Status

```javascript
if (!authManager.isAuthenticated()) {
    window.location.href = '/login';
}
```

### Make Authenticated API Requests

```javascript
// Using the auth manager
const response = await authManager.apiRequest('/api/dashboard_data');
const data = await response.json();

// Or manually with fetch
const response = await fetch('/api/dashboard_data', {
    headers: {
        'Authorization': `Bearer ${authManager.getToken()}`
    }
});
```

### Handle Logout

```javascript
authManager.logout();
```

### Check User Role

```javascript
if (authManager.isAdmin()) {
    // Show admin features
}

if (authManager.hasRole('user')) {
    // Show user features
}
```

## 7. Security Features

### Password Security
- Passwords are hashed using bcrypt with salt
- Minimum password length: 8 characters
- Passwords are never stored in plain text

### JWT Security
- Tokens expire after 24 hours (configurable)
- Automatic token refresh
- Secure token validation

### Role-Based Access Control
- User roles: "user" and "admin"
- Admin users can manage other users
- Regular users can only access their own data

### API Protection
- All sensitive endpoints require authentication
- 401 Unauthorized responses for invalid tokens
- Automatic redirect to login on token expiration

## 8. Error Handling

### Common Error Responses

#### 401 Unauthorized
```json
{
    "error": "Authorization header missing"
}
```

#### 403 Forbidden
```json
{
    "error": "Insufficient permissions"
}
```

#### 400 Bad Request
```json
{
    "error": "user_id, password, and full_name are required"
}
```

## 9. Testing the System

### 1. Create an Admin User

First, register an admin user:

```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "admin",
    "password": "adminpassword123",
    "full_name": "System Administrator",
    "role": "admin"
  }'
```

### 2. Login and Get Token

```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "admin",
    "password": "adminpassword123"
  }'
```

### 3. Use Token for Protected Endpoints

```bash
curl -X GET http://localhost:5000/api/dashboard_data \
  -H "Authorization: Bearer <your-jwt-token>"
```

## 10. Troubleshooting

### Common Issues

1. **"JWT_SECRET_KEY environment variable is required"**
   - Make sure you've set the JWT_SECRET_KEY in your .env file

2. **"NOTION_USERS_DB_ID environment variable is required"**
   - Verify your Notion users database ID is correct

3. **"Failed to create user in Notion"**
   - Check your Notion API token and database permissions
   - Ensure the database properties match the expected format

4. **"Invalid token" errors**
   - Check that the JWT_SECRET_KEY is consistent
   - Verify token expiration settings

5. **CORS issues**
   - The application includes CORS support, but you may need to configure it for your specific domain

### Debug Mode

Enable debug mode to see detailed error messages:

```bash
DEBUG_MODE=True python app_auth.py
```

## 11. Production Considerations

### Security Best Practices

1. **Use HTTPS in production**
2. **Set a strong JWT secret key**
3. **Configure appropriate token expiration times**
4. **Implement rate limiting**
5. **Use environment variables for all secrets**
6. **Regular security audits**

### Environment Variables for Production

```bash
# Production settings
DEBUG_MODE=False
JWT_EXPIRATION_HOURS=8  # Shorter expiration for production
ENABLE_AUTHENTICATION=True
```

### Database Considerations

- Consider backing up your Notion users database regularly
- Monitor API rate limits for Notion
- Implement user account lockout after failed login attempts

## Support

For issues or questions about the authentication system, please check:
1. The application logs for error messages
2. Your environment variable configuration
3. Your Notion database setup
4. The API documentation above 