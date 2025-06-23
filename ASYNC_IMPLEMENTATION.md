# Asynchronous Processing Implementation

This document outlines the implementation of asynchronous processing in the Task Manager using Celery and Redis.

## Overview

The Task Manager now supports asynchronous processing for network operations that were previously synchronous, improving performance and user experience by:

- **Non-blocking operations**: Long-running tasks don't block the main application
- **Better scalability**: Multiple workers can process tasks concurrently
- **Improved reliability**: Automatic retries and error handling
- **Real-time monitoring**: Task progress tracking and status updates

## Architecture

### Components

1. **Celery**: Distributed task queue for handling async operations
2. **Redis**: Message broker and result backend for Celery
3. **Flower**: Web-based monitoring tool for Celery tasks
4. **Task Scheduler**: Periodic task management using Celery Beat

### Task Categories

The async system is organized into four main task categories:

#### 1. Notion Tasks (`core/tasks/notion_tasks.py`)
- `fetch_tasks_async()` - Asynchronously fetch tasks from Notion
- `insert_task_async()` - Asynchronously insert new tasks
- `update_task_async()` - Asynchronously update existing tasks
- `batch_insert_tasks_async()` - Asynchronously insert multiple tasks
- `identify_stale_tasks_async()` - Asynchronously identify stale tasks

#### 2. AI Tasks (`core/tasks/ai_tasks.py`)
- `generate_content_async()` - Asynchronously generate AI content
- `create_embeddings_async()` - Asynchronously create embeddings
- `batch_api_requests_async()` - Asynchronously process multiple AI requests
- `generate_coaching_insight_async()` - Asynchronously generate coaching insights
- `generate_project_insight_async()` - Asynchronously generate project insights
- `extract_tasks_async()` - Asynchronously extract tasks from text

#### 3. Email Tasks (`core/tasks/email_tasks.py`)
- `send_confirmation_email_async()` - Asynchronously send confirmation emails
- `process_gmail_updates_async()` - Asynchronously process Gmail updates
- `process_single_email_async()` - Asynchronously process individual emails
- `send_notification_email_async()` - Asynchronously send notification emails

#### 4. Dashboard Tasks (`core/tasks/dashboard_tasks.py`)
- `generate_dashboard_data_async()` - Asynchronously generate dashboard data
- `identify_stale_tasks_async()` - Asynchronously identify stale tasks for dashboard
- `generate_analytics_report_async()` - Asynchronously generate analytics reports
- `generate_performance_metrics_async()` - Asynchronously generate performance metrics

## Setup and Installation

### Prerequisites

1. **Redis**: Message broker and result backend
2. **Python Dependencies**: Celery, Redis, Flower

### Installation

1. **Install Dependencies**:
   ```bash
   pip install celery redis flower
   ```

2. **Start Redis**:
   ```bash
   # Using Docker
   docker run -d -p 6379:6379 redis:7-alpine
   
   # Or using docker-compose
   docker-compose up -d redis
   ```

3. **Start the Async System**:
   ```bash
   python start_async_system.py
   ```

### Docker Compose Setup

The `docker-compose.yml` file includes all necessary services:

```yaml
services:
  app:              # Flask application
  celery-worker:    # Celery worker processes
  celery-beat:      # Celery beat scheduler
  flower:           # Monitoring interface
  redis:            # Message broker
```

Start all services:
```bash
docker-compose up -d
```

## Usage

### Starting the System

#### Option 1: Using the Startup Script
```bash
python start_async_system.py
```

#### Option 2: Manual Startup
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker
celery -A celery_config worker --loglevel=info --concurrency=4

# Terminal 3: Start Celery Beat
celery -A celery_config beat --loglevel=info

# Terminal 4: Start Flower (optional)
celery -A celery_config flower --port=5555

# Terminal 5: Start Flask App
python app_flask.py
```

### Queuing Tasks

#### Basic Task Queuing
```python
from core.tasks.notion_tasks import fetch_tasks_async
from core.tasks.ai_tasks import generate_content_async

# Queue a task
result = fetch_tasks_async.delay(database_id="your_db_id", days_back=30)

# Get task status
print(f"Task ID: {result.id}")
print(f"Status: {result.status}")

# Wait for result
task_result = result.get(timeout=60)
if task_result['success']:
    print(f"Tasks fetched: {len(task_result['data'])}")
```

#### Task with Progress Tracking
```python
from core.tasks.ai_tasks import generate_content_async

# Queue task
result = generate_content_async.delay("Your prompt here", temperature=0.7)

# Monitor progress
while not result.ready():
    if result.state == 'PROGRESS':
        info = result.info
        print(f"Progress: {info['current']}/{info['total']} - {info['status']}")
    time.sleep(1)

# Get final result
final_result = result.get()
```

### Periodic Tasks

The system automatically schedules periodic tasks:

- **Gmail Check**: Every 5 minutes
- **Stale Task Identification**: Every hour
- **Daily Analytics**: Every day at 9 AM
- **Weekly Analytics**: Every Monday at 8 AM

### Monitoring

#### Flower Web Interface
Access the monitoring interface at: http://localhost:5555

Features:
- Real-time task monitoring
- Worker status
- Task history
- Performance metrics

#### Programmatic Monitoring
```python
from task_scheduler import get_task_status, cancel_task

# Get task status
status = get_task_status("task_id_here")
print(f"Status: {status['status']}")

# Cancel running task
result = cancel_task("task_id_here")
```

## API Integration

### Updated Flask Endpoints

The Flask application now uses async tasks for heavy operations:

#### Dashboard Data
```python
@app.route('/api/dashboard_data')
def api_dashboard_data():
    # Queue async task instead of blocking
    result = generate_dashboard_data_async.delay(
        database_id=user.task_database_id,
        employee_filter=request.args.get('employee', 'all'),
        project_filter=request.args.get('project', 'all')
    )
    
    return jsonify({
        'success': True,
        'task_id': result.id,
        'message': 'Dashboard data generation started'
    })
```

#### Task Processing
```python
@app.route('/api/process_update', methods=['POST'])
def process_update():
    # Queue async task processing
    result = extract_tasks_async.delay(update_text)
    
    return jsonify({
        'success': True,
        'task_id': result.id,
        'message': 'Task extraction started'
    })
```

### Task Status Endpoints

```python
@app.route('/api/task_status/<task_id>')
def get_task_status_api(task_id):
    from task_scheduler import get_task_status
    return jsonify(get_task_status(task_id))

@app.route('/api/cancel_task/<task_id>', methods=['POST'])
def cancel_task_api(task_id):
    from task_scheduler import cancel_task
    return jsonify(cancel_task(task_id))
```

## Configuration

### Celery Configuration (`celery_config.py`)

Key settings:
- **Broker URL**: Redis connection string
- **Result Backend**: Redis for storing task results
- **Task Routing**: Separate queues for different task types
- **Rate Limiting**: Prevents API overload
- **Retry Logic**: Automatic retries with exponential backoff

### Environment Variables

```bash
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Performance Benefits

### Before (Synchronous)
- User submits task → Application blocks → API calls → User waits
- Gmail processing blocks main thread
- Dashboard data aggregation causes timeouts
- No progress feedback

### After (Asynchronous)
- User submits task → Task queued → Immediate response
- Background processing with progress updates
- Non-blocking operations
- Real-time status monitoring

## Error Handling

### Automatic Retries
- Failed tasks are automatically retried
- Exponential backoff prevents API overload
- Maximum retry limits prevent infinite loops

### Error Reporting
- Detailed error logs with stack traces
- Task failure notifications
- Graceful degradation for critical failures

## Monitoring and Debugging

### Logs
- Celery worker logs: `celery -A celery_config worker --loglevel=debug`
- Task-specific logs in application logs
- Redis connection logs

### Common Issues

1. **Redis Connection Failed**
   - Check if Redis is running: `redis-cli ping`
   - Verify connection string in configuration

2. **Tasks Not Processing**
   - Check worker status in Flower
   - Verify task routing configuration
   - Check worker logs for errors

3. **Memory Issues**
   - Monitor worker memory usage
   - Adjust concurrency settings
   - Implement task result cleanup

## Migration Guide

### From Synchronous to Asynchronous

1. **Identify blocking operations**:
   - Network API calls
   - Database operations
   - File processing
   - Email sending

2. **Create async task**:
   ```python
   @celery_app.task(bind=True, name='your.task.name')
   def your_async_task(self, *args, **kwargs):
       # Your async logic here
       pass
   ```

3. **Update API endpoints**:
   ```python
   # Before
   result = sync_function(data)
   return jsonify(result)
   
   # After
   task_result = your_async_task.delay(data)
   return jsonify({'task_id': task_result.id})
   ```

4. **Add status endpoints**:
   ```python
   @app.route('/api/status/<task_id>')
   def get_status(task_id):
       return jsonify(get_task_status(task_id))
   ```

## Best Practices

1. **Task Design**
   - Keep tasks focused and single-purpose
   - Use meaningful task names
   - Implement proper error handling

2. **Resource Management**
   - Monitor memory usage
   - Implement task cleanup
   - Use appropriate concurrency settings

3. **Monitoring**
   - Set up alerts for failed tasks
   - Monitor queue lengths
   - Track task performance metrics

4. **Security**
   - Validate task inputs
   - Implement rate limiting
   - Secure Redis access

## Future Enhancements

1. **Advanced Scheduling**
   - Dynamic task scheduling
   - Conditional task execution
   - Task dependencies

2. **Enhanced Monitoring**
   - Custom dashboards
   - Performance analytics
   - Predictive scaling

3. **Integration**
   - Webhook notifications
   - External monitoring tools
   - API rate limiting

## Troubleshooting

### Common Commands

```bash
# Check Redis status
redis-cli ping

# Check Celery worker status
celery -A celery_config inspect active

# Check scheduled tasks
celery -A celery_config inspect scheduled

# Purge all queues
celery -A celery_config purge

# Monitor tasks in real-time
celery -A celery_config events
```

### Debug Mode

Enable debug mode for detailed logging:
```python
# In celery_config.py
if DEBUG_MODE:
    celery_app.conf.update(
        task_always_eager=False,
        task_eager_propagates=True,
    )
```

This implementation provides a robust foundation for asynchronous processing while maintaining backward compatibility with existing synchronous operations. 