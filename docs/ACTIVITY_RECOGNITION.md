# Activity Recognition System

## Overview

The Activity Recognition System automatically identifies and tracks recurring activities performed by users. It uses AI-powered semantic analysis to group similar tasks together, providing insights into work patterns and productivity.

## Features

### 🧠 **Intelligent Pattern Recognition**
- Uses ChromaDB for semantic similarity search
- AI-powered task name normalization
- Automatic activity grouping and counting

### ⚡ **Background Processing**
- Asynchronous task processing with Celery
- No impact on task creation performance
- Automatic retry with exponential backoff

### 📊 **Activity Insights**
- Track how often activities are performed
- Monitor activity patterns over time
- Generate productivity insights

## Architecture

```
New Task Created → Background Analysis → ChromaDB Similarity Search → AI Normalization → Activity Grouping → Database Storage
```

### Components

1. **Database Layer** (`src/core/database/`)
   - Centralized database connection management
   - `TrackedActivity` model for storing activity data

2. **Data Service** (`src/core/services/activity_service.py`)
   - Database operations for tracked activities
   - Activity statistics and queries

3. **Recognition Service** (`src/core/activity_recognition/`)
   - AI-powered activity recognition logic
   - ChromaDB integration for similarity search

4. **Background Tasks** (`src/core/tasks/activity_tasks.py`)
   - Celery tasks for asynchronous processing
   - Activity summary generation

## Database Schema

### `tracked_activities` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `user_id` | VARCHAR(255) | User identifier |
| `normalized_name` | VARCHAR(255) | Normalized activity name (2-4 words) |
| `instance_count` | INTEGER | Number of times performed |
| `last_instance_date` | TIMESTAMP | Last occurrence date |
| `representative_tasks` | JSONB | Array of example task titles |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

## Configuration

### Environment Variables

```bash
# Enable/disable activity recognition
ACTIVITY_RECOGNITION_ENABLED=True

# Similarity threshold for activity matching
ACTIVITY_SIMILARITY_THRESHOLD=0.7

# Maximum number of representative tasks to store
ACTIVITY_MAX_REPRESENTATIVE_TASKS=10

# Days before cleaning up old activities
ACTIVITY_CLEANUP_DAYS=180
```

### Celery Configuration

The system uses a dedicated `activity` queue for background processing:

```python
# Task routing
'core.tasks.activity_tasks.*': {'queue': 'activity'}

# Rate limiting
'core.tasks.activity_tasks.*': {'rate_limit': '20/m'}
```

## Usage

### Automatic Processing

Activity recognition happens automatically when tasks are created:

```python
# In task_management_service.py
success, message = self.notion_agent.insert_task(
    database_id=user.task_database_id,
    task=task_data
)

if success:
    # Schedule activity recognition
    recognize_activity_for_task.delay(user_id, task_id, task_title)
```

### Manual Activity Recognition

```python
from src.core.database.connection import SessionLocal
from src.core.activity_recognition.recognition_service import ActivityRecognitionService

# Get database session
db_session = SessionLocal()

# Initialize service
recognition_service = ActivityRecognitionService(user_id, db_session)

# Process a task
result = recognition_service.process_new_task(task_id, task_title)

# Get activity summary
summary = recognition_service.get_user_activity_summary()
```

### Activity Data Service

```python
from src.core.services.activity_service import ActivityDataService

# Initialize service
activity_service = ActivityDataService(db_session)

# Get user activities
activities = activity_service.get_user_activities(user_id)

# Get activity statistics
stats = activity_service.get_activity_stats(user_id)
```

## API Endpoints

### Get User Activity Summary

```http
GET /api/activities/summary
Authorization: Bearer <token>
```

Response:
```json
{
  "total_activities": 5,
  "stats": {
    "total_activities": 5,
    "total_instances": 23,
    "most_frequent_activity": "Email Check",
    "most_frequent_count": 8
  },
  "recent_activities": [
    {
      "name": "Email Check",
      "count": 8,
      "last_done": "2024-01-15T10:30:00Z",
      "representative_tasks": ["Check email inbox", "Review emails"]
    }
  ]
}
```

## Testing

Run the test script to verify the implementation:

```bash
python test_activity_recognition.py
```

This will:
1. Test database connection and table creation
2. Process sample tasks through the recognition system
3. Generate activity summaries
4. Verify all components work correctly

## Database Migration

To create the required database table:

```bash
# Run the SQL migration
psql -d your_database -f migrations/create_tracked_activities_table.sql
```

Or use the Python script:

```python
from src.core.database.connection import engine
from src.core.database.models import Base

# Create tables
Base.metadata.create_all(bind=engine)
```

## Monitoring

### Logs

The system logs all activity recognition events:

```
INFO: Processing new task for user user123: Review weekly sales report...
INFO: Created new activity: Weekly Sales Review for task: Review weekly sales report
INFO: Activity recognition completed successfully for task task_1
```

### Metrics

Track these key metrics:
- Activity recognition success rate
- Processing time per task
- Number of activities per user
- Most frequent activities

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify `DATABASE_URL` environment variable
   - Check PostgreSQL server is running
   - Ensure database exists and is accessible

2. **ChromaDB Issues**
   - Check `chroma_db/` directory permissions
   - Verify ChromaDB is properly initialized
   - Check embedding model availability

3. **Celery Task Failures**
   - Check Redis connection
   - Verify Celery worker is running
   - Check task queue configuration

### Debug Mode

Enable debug logging:

```bash
export DEBUG_MODE=True
```

This will provide detailed logs for troubleshooting.

## Future Enhancements

### Planned Features

1. **Activity Templates**
   - Pre-defined activity templates
   - Custom activity categories
   - Activity hierarchies

2. **Predictive Analytics**
   - Activity scheduling predictions
   - Workload forecasting
   - Productivity recommendations

3. **Integration Enhancements**
   - Calendar integration
   - Time tracking integration
   - Team activity insights

4. **Advanced AI Features**
   - Activity pattern learning
   - Smart activity suggestions
   - Automated task categorization

## Contributing

When contributing to the activity recognition system:

1. Follow the existing code structure
2. Add comprehensive logging
3. Include error handling
4. Write tests for new features
5. Update documentation

## Support

For issues or questions about the activity recognition system:

1. Check the logs for error messages
2. Verify configuration settings
3. Test with the provided test script
4. Review this documentation 