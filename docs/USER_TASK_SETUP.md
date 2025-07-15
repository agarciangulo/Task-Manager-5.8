# User-Specific Task System Setup Guide

This guide explains how to set up and use the user-specific task management system that allows each user to have their own private Notion task database.

## Overview

The user-specific task system provides:
- Individual Notion task databases for each user
- Secure task isolation (users can only see their own tasks)
- Full CRUD operations (Create, Read, Update, Delete)
- Modern web interface for task management
- Integration with the existing authentication system

## Architecture

### 1. User Profile Enhancement
- Each user now has a `TaskDatabaseID` field in their profile
- This field stores the Notion database ID for their personal task database
- The field is automatically populated when a user registers (if configured)

### 2. Task Database Structure
Each user's task database contains the following properties:
- **Task** (Title): The task description
- **Status** (Select): Not Started, In Progress, Completed, On Hold
- **Priority** (Select): Low, Medium, High, Urgent
- **Category** (Text): Task category/project
- **Due Date** (Date): When the task is due
- **Created** (Date): When the task was created
- **Notes** (Text): Additional notes/description
- **Assigned To** (Text): Who the task is assigned to (defaults to user's name)

### 3. API Endpoints
- `GET /api/user/tasks` - Get all tasks for the current user
- `POST /api/user/tasks` - Create a new task for the current user
- `PUT /api/user/tasks/<task_id>` - Update a task for the current user
- `DELETE /api/user/tasks/<task_id>` - Delete a task for the current user
- `POST /api/user/task-database` - Create a task database for the current user

## Setup Instructions

### 1. Environment Configuration

Add the following environment variable to your `.env` file:

```bash
# Notion Parent Page ID (where user task databases will be created)
NOTION_PARENT_PAGE_ID=your-notion-parent-page-id
```

**Important**: The parent page ID should be a Notion page where you want all user task databases to be created. This page should be shared with your Notion integration.

### 2. Update User Database Schema

Add a new property to your Notion users database:

**Property Name**: `TaskDatabaseID`
**Type**: Text
**Description**: Stores the Notion database ID for the user's personal task database

### 3. Update Application Configuration

The system will automatically:
- Create task databases for new users during registration
- Store the database ID in the user's profile
- Use the user's specific database for all task operations

### 4. Access the User Task Interface

Users can access their personal task manager at:
```
http://localhost:5001/user/tasks
```

## Usage Guide

### For Users

#### 1. Accessing Your Tasks
- Log in to the application
- Navigate to "My Tasks" from the dashboard or directly visit `/user/tasks`
- Your personal task database will be automatically created if it doesn't exist

#### 2. Creating Tasks
- Click the "Add Task" button
- Fill in the task details:
  - **Task Title** (required): Brief description of the task
  - **Description**: Detailed notes about the task
  - **Status**: Current status (Not Started, In Progress, etc.)
  - **Priority**: Task priority level
  - **Category**: Project or category the task belongs to
  - **Due Date**: When the task should be completed

#### 3. Managing Tasks
- **View**: All your tasks are displayed in a clean card layout
- **Filter**: Use the filters to find specific tasks by status, priority, or search terms
- **Edit**: Click the "Edit" button to modify task details
- **Delete**: Click the "Delete" button to remove tasks (with confirmation)

#### 4. Task Organization
- Use categories to group related tasks
- Set priorities to focus on important tasks first
- Update status to track progress
- Set due dates to manage deadlines

### For Administrators

#### 1. Monitoring User Databases
- Each user's task database is created as a separate database in Notion
- Database names follow the pattern: "Tasks - [User Full Name]"
- All databases are created under the specified parent page

#### 2. Database Management
- Users can only access their own task databases
- Administrators can view all databases through the Notion interface
- Database IDs are stored in the user's profile for easy reference

#### 3. Backup and Maintenance
- Each user's tasks are isolated, making backup and maintenance easier
- Individual databases can be archived or deleted as needed
- No cross-contamination between user data

## API Reference

### Authentication
All user task endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <jwt-token>
```

### Endpoints

#### GET /api/user/tasks
Get all tasks for the current user.

**Response**:
```json
{
  "tasks": [
    {
      "id": "task-id",
      "task": "Task description",
      "status": "In Progress",
      "priority": "High",
      "category": "Project A",
      "due_date": "2024-01-15",
      "notes": "Additional notes",
      "assigned_to": "John Doe",
      "created_time": "2024-01-01T10:00:00Z",
      "last_edited_time": "2024-01-01T10:00:00Z"
    }
  ],
  "count": 1
}
```

#### POST /api/user/tasks
Create a new task for the current user.

**Request Body**:
```json
{
  "task": "Task description",
  "notes": "Additional notes",
  "status": "Not Started",
  "priority": "Medium",
  "category": "Project A",
  "due_date": "2024-01-15"
}
```

**Response**:
```json
{
  "message": "Task created successfully",
  "task": {
    "id": "task-id",
    "task": "Task description",
    "status": "Not Started",
    "priority": "Medium",
    "category": "Project A",
    "due_date": "2024-01-15",
    "notes": "Additional notes",
    "assigned_to": "John Doe",
    "created_time": "2024-01-01T10:00:00Z",
    "last_edited_time": "2024-01-01T10:00:00Z"
  }
}
```

#### PUT /api/user/tasks/<task_id>
Update a task for the current user.

**Request Body**:
```json
{
  "task": "Updated task description",
  "status": "Completed",
  "priority": "High"
}
```

**Response**:
```json
{
  "message": "Task updated successfully"
}
```

#### DELETE /api/user/tasks/<task_id>
Delete a task for the current user.

**Response**:
```json
{
  "message": "Task deleted successfully"
}
```

#### POST /api/user/task-database
Create a task database for the current user (if they don't have one).

**Request Body**:
```json
{
  "parent_page_id": "notion-page-id"
}
```

**Response**:
```json
{
  "message": "Task database created successfully",
  "database_id": "database-id"
}
```

## Security Features

### Data Isolation
- Users can only access their own task databases
- Task operations are scoped to the authenticated user
- No cross-user data access is possible

### Authentication
- All endpoints require valid JWT authentication
- Token validation ensures user identity
- Automatic logout on token expiration

### Input Validation
- Task titles are required
- Status and priority values are validated against allowed options
- Date formats are validated
- HTML injection is prevented

## Troubleshooting

### Common Issues

#### 1. "No task database configured for user"
**Cause**: User doesn't have a task database assigned
**Solution**: 
- Ensure the `NOTION_PARENT_PAGE_ID` environment variable is set
- The database will be created automatically on next login
- Or manually create one using the `/api/user/task-database` endpoint

#### 2. "Failed to create task database"
**Cause**: Notion API permissions or parent page access issues
**Solution**:
- Verify the Notion integration has access to the parent page
- Check that the `NOTION_PARENT_PAGE_ID` is correct
- Ensure the Notion token has sufficient permissions

#### 3. "User not found" errors
**Cause**: Authentication or user profile issues
**Solution**:
- Verify the user exists in the users database
- Check that the JWT token is valid
- Ensure the user profile has the required fields

#### 4. Task operations failing
**Cause**: Database access or permission issues
**Solution**:
- Verify the user's task database ID is correct
- Check that the Notion integration has access to the user's database
- Ensure the database schema matches the expected format

### Debug Mode

Enable debug mode to see detailed error messages:

```bash
DEBUG_MODE=True python app_auth.py
```

### Logs

Check the application logs for detailed error information:
- Authentication errors
- Notion API errors
- Database creation failures
- Task operation errors

## Best Practices

### For Users
1. **Use Categories**: Organize tasks by project or category
2. **Set Priorities**: Focus on high-priority tasks first
3. **Update Status**: Keep task status current for better tracking
4. **Add Notes**: Include relevant details in task notes
5. **Set Due Dates**: Use due dates to manage deadlines

### For Administrators
1. **Monitor Usage**: Check Notion for database creation and usage
2. **Backup Data**: Regularly backup user databases
3. **Clean Up**: Archive or delete unused databases
4. **User Management**: Deactivate users who no longer need access
5. **Security**: Regularly review access permissions

## Migration from Shared Database

If you're migrating from a shared task database:

1. **Export Data**: Export existing tasks from the shared database
2. **User Assignment**: Identify which tasks belong to which users
3. **Create User Databases**: Use the system to create individual databases
4. **Import Tasks**: Import user-specific tasks into their databases
5. **Verify**: Ensure all tasks are properly assigned and accessible

## Support

For issues or questions about the user-specific task system:

1. Check the application logs for error messages
2. Verify your environment variable configuration
3. Test Notion API connectivity
4. Review the troubleshooting section above
5. Check the API documentation for endpoint details

The user-specific task system provides a secure, scalable solution for individual task management while maintaining the benefits of Notion's powerful database features. 