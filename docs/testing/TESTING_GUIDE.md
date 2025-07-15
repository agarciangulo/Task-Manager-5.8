# Testing Guide for Task Manager

This guide explains how to test the complete end-to-end workflow of the Task Manager application.

## Overview

The Task Manager has a comprehensive workflow that includes:
1. **User Creation** - Register new users with automatic task database creation
2. **Email Processing** - Extract tasks from email content
3. **Task Management** - Insert and manage tasks in Notion databases
4. **AI Insights** - Generate coaching insights using AI
5. **Email Confirmation** - Send confirmation emails with processed tasks and insights

## Test Scripts

### 1. Core Workflow Test (`test_core_workflow.py`)

**Purpose**: Tests the essential workflow without requiring the Flask app to be running.

**What it tests**:
- ✅ User creation via AuthService
- ✅ Automatic task database creation
- ✅ Task extraction from email content
- ✅ Task insertion into user's database
- ✅ Coaching insights generation
- ✅ Email simulation (without sending)

**Usage**:
```bash
python test_core_workflow.py
```

**Requirements**:
- All environment variables set in `.env`
- Notion API access
- Gmail credentials (for email simulation)

### 2. End-to-End Test (`test_end_to_end_workflow.py`)

**Purpose**: Tests the complete workflow including the Flask API and actual email sending.

**What it tests**:
- ✅ User creation via Flask API
- ✅ Automatic task database creation
- ✅ Email processing simulation
- ✅ Task extraction from email content
- ✅ Task insertion into user's database
- ✅ Coaching insights generation
- ✅ Actual confirmation email sending
- ✅ Final state verification

**Usage**:
```bash
python test_end_to_end_workflow.py
```

**Requirements**:
- Flask app running on `http://localhost:5001`
- All environment variables set in `.env`
- Notion API access
- Gmail credentials (for actual email sending)

## Prerequisites

### Environment Variables

Ensure your `.env` file contains all required variables:

```bash
# Notion Configuration
NOTION_TOKEN=your-notion-api-token
NOTION_USERS_DB_ID=your-users-database-id
NOTION_PARENT_PAGE_ID=your-parent-page-id
NOTION_DATABASE_ID=your-tasks-database-id
NOTION_FEEDBACK_DB_ID=your-feedback-database-id

# Gmail Configuration
GMAIL_ADDRESS=your-gmail-address@gmail.com
GMAIL_APP_PASSWORD=your-gmail-app-password

# AI Configuration
GEMINI_API_KEY=your-gemini-api-key
AI_PROVIDER=gemini

# Authentication
JWT_SECRET_KEY=your-jwt-secret-key
ENABLE_AUTHENTICATION=True
```

### Notion Setup

1. **Users Database**: Must have the required properties:
   - `UserID` (Title)
   - `PasswordHash` (Text)
   - `FullName` (Text)
   - `Role` (Select)
   - `TaskDatabaseID` (Text)

2. **Parent Page**: A Notion page where user task databases will be created

3. **Integration**: Your Notion integration must have access to:
   - Users database
   - Parent page
   - Ability to create databases

### Gmail Setup

1. **App Password**: Generate an app password for your Gmail account
2. **IMAP Access**: Enable IMAP in Gmail settings
3. **Less Secure Apps**: Or use app-specific passwords

## Running the Tests

### Step 1: Core Workflow Test (Recommended First)

```bash
# Run the core workflow test
python test_core_workflow.py
```

This test will:
1. Create a test user with a unique email
2. Verify the task database was created automatically
3. Extract tasks from simulated email content
4. Insert tasks into the user's database
5. Generate coaching insights
6. Simulate email sending (without actually sending)

**Expected Output**:
```
🚀 Starting Core Workflow Test
============================================================
📧 Test User Email: core_test_20250120_143022@example.com
👤 Test User Name: Core Test User 143022

1️⃣ Testing User Creation
------------------------------
✅ User created successfully!
   User ID: 12345678-1234-1234-1234-123456789012
   Full Name: Core Test User 143022
   Task Database ID: 87654321-4321-4321-4321-210987654321

2️⃣ Testing Task Database Creation
------------------------------
✅ Task database created successfully!
   Database ID: 87654321-4321-4321-4321-210987654321

3️⃣ Testing Task Extraction
------------------------------
📧 Test email content:
From: Core Test User 143022
Date: 2025-01-20

Subject: Daily Work Update

Hi team,

Here's my update for today:

- Completed the quarterly report analysis
- Started working on the new authentication feature
- Had a productive meeting with the development team about project timeline
- Fixed three critical bugs in the user interface
- Updated documentation for the API endpoints

Looking forward to tomorrow's sprint planning session.

Best regards,
Core Test User 143022

📋 Extracted 5 tasks:
   1. Completed the quarterly report analysis
      Status: Completed
      Category: Reporting
      Employee: Core Test User 143022

   2. Started working on the new authentication feature
      Status: In Progress
      Category: Development
      Employee: Core Test User 143022

   ...

✅ Task extraction successful

4️⃣ Testing Task Insertion
------------------------------
📊 Found 0 existing tasks in database
   Processing task 1: Completed the quarterly report analysis
      ✅ Success: Task inserted successfully
   Processing task 2: Started working on the new authentication feature
      ✅ Success: Task inserted successfully
   ...

✅ Successfully processed 5 tasks

5️⃣ Testing Coaching Insights Generation
------------------------------
✅ Coaching insights generated successfully
📝 Insights preview:
   Based on your recent work, I can see you've been making excellent progress...

6️⃣ Testing Email Simulation
------------------------------
📧 Simulating confirmation email:
   Recipient: core_test_20250120_143022@example.com
   Tasks included: 5
   Coaching insights: Yes

📄 Email content preview:
Subject: Task Manager: 5 Tasks Processed
To: core_test_20250120_143022@example.com
From: your-gmail@gmail.com

Tasks processed:
  1. Completed the quarterly report analysis (Completed)
  2. Started working on the new authentication feature (In Progress)
  ...

Coaching Insights:
Based on your recent work, I can see you've been making excellent progress...

✅ Email simulation completed

📊 Test Results Summary
============================================================
User Creation: ✅ PASS
Task Database Creation: ✅ PASS
Task Extraction: ✅ PASS
Task Insertion: ✅ PASS
Coaching Insights: ✅ PASS
Email Simulation: ✅ PASS

Overall Result: 6/6 tests passed
🎉 All tests passed! Core workflow is working correctly.

📄 Detailed results saved to: core_workflow_results_20250120_143022.json
```

### Step 2: End-to-End Test (Optional)

If the core test passes and you want to test the complete workflow including the Flask API:

```bash
# Start the Flask app first
python app_flask.py

# In another terminal, run the end-to-end test
python test_end_to_end_workflow.py
```

This test will additionally:
- Test the Flask API endpoints
- Send actual confirmation emails
- Verify the complete user experience

## Test Results

### Success Indicators

✅ **All tests pass**: The complete workflow is working correctly
✅ **User creation**: New users are registered with task databases
✅ **Task extraction**: AI correctly identifies tasks from email content
✅ **Task insertion**: Tasks are properly stored in Notion
✅ **Coaching insights**: AI generates meaningful insights
✅ **Email simulation**: Email content is properly formatted

### Common Issues and Solutions

#### 1. Environment Variables Missing
```
❌ Missing required environment variables:
   - NOTION_TOKEN
   - NOTION_USERS_DB_ID
```
**Solution**: Check your `.env` file and ensure all variables are set.

#### 2. Notion API Errors
```
❌ Error in user creation: Failed to create user in Notion
```
**Solution**: 
- Verify your Notion token is valid
- Check that your integration has access to the users database
- Ensure the database has the required properties

#### 3. Task Database Creation Fails
```
❌ User does not have task database
```
**Solution**:
- Verify `NOTION_PARENT_PAGE_ID` is set correctly
- Check that your integration has access to the parent page
- Ensure the parent page exists and is shared with your integration

#### 4. Task Extraction Fails
```
❌ No tasks extracted
```
**Solution**:
- Check that the AI provider (Gemini) is configured correctly
- Verify your `GEMINI_API_KEY` is valid
- Check the email content format

#### 5. Flask App Not Running
```
❌ Flask app is not running at http://localhost:5001
```
**Solution**: Start the Flask application first with `python app_flask.py`

## Manual Verification

After running the tests, you can manually verify the results:

### 1. Check Notion Users Database
- Look for the test user with the generated email
- Verify the `TaskDatabaseID` field is populated

### 2. Check User's Task Database
- Navigate to the task database using the ID from the test results
- Verify that the extracted tasks are present
- Check that task properties (status, category, employee) are correct

### 3. Check Gmail (End-to-End Test Only)
- Look for the confirmation email in the test user's inbox
- Verify the email contains the processed tasks and coaching insights

## Cleanup

The test scripts leave the test data in place for manual inspection. To clean up:

1. **Delete test user** from the Notion users database
2. **Delete task database** using the database ID from test results
3. **Delete confirmation email** from Gmail (if sent)

## Troubleshooting

### Debug Mode
Enable debug mode to see more detailed output:
```bash
export DEBUG_MODE=True
python test_core_workflow.py
```

### Verbose Logging
Check the application logs for detailed error information:
```bash
tail -f logs/app.log
```

### API Testing
Test individual API endpoints:
```bash
# Test health endpoint
curl http://localhost:5001/api/health

# Test user registration
curl -X POST http://localhost:5001/api/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","full_name":"Test User"}'
```

## Next Steps

After successful testing:

1. **Production Setup**: Configure the system for production use
2. **User Training**: Train users on how to send emails for task processing
3. **Monitoring**: Set up monitoring for the email processing system
4. **Scaling**: Consider scaling options for multiple users

## Support

If you encounter issues:

1. Check the test results file for detailed error information
2. Review the application logs
3. Verify all environment variables are set correctly
4. Test individual components separately
5. Check Notion and Gmail API documentation for any changes 