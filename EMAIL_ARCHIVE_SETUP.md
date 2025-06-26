# Email Archive Database Setup

This document explains how to set up and use the PostgreSQL-based email archive system with hot and cold storage architecture for your email processing application.

## Overview

The email archive system provides:

- **Hot Storage**: Recent emails (default: 30 days) for fast access
- **Cold Storage**: Older emails (default: 365 days) for long-term retention
- **Automatic Migration**: Emails automatically move from hot to cold storage
- **Full-Text Search**: Search across email subjects and bodies
- **Attachment Management**: Deduplication and compression
- **Processing Logs**: Track email processing status and performance

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Hot Storage   │    │   Cold Storage  │    │   Attachments   │
│   (30 days)     │    │   (365 days)    │    │   (Compressed)  │
│                 │    │                 │    │                 │
│ - Recent emails │    │ - Older emails  │    │ - File dedup    │
│ - Fast access   │    │ - Compressed    │    │ - Compression   │
│ - Full search   │    │ - Slower access │    │ - Hash-based    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Processing     │
                    │     Logs        │
                    │                 │
                    │ - Status track  │
                    │ - Performance   │
                    │ - Error logs    │
                    └─────────────────┘
```

## Prerequisites

- Docker and Docker Compose
- Python 3.8+
- PostgreSQL 15+ (included in Docker setup)

## Quick Start

### 1. Environment Setup

Create a `.env` file in your project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/email_archive
EMAIL_ARCHIVE_ENABLED=True

# Email Archive Settings
HOT_STORAGE_DAYS=30
COLD_STORAGE_DAYS=365
EMAIL_COMPRESSION_ENABLED=True
ATTACHMENT_STORAGE_PATH=attachments

# Existing configuration...
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_database_id
# ... other existing vars
```

### 2. Start the Database

```bash
# Start PostgreSQL and other services
docker-compose up -d postgres redis

# Wait for PostgreSQL to be ready
docker-compose logs postgres
```

### 3. Initialize the Database

```bash
# Run the setup script
python setup_email_archive.py
```

### 4. Start the Full Application

```bash
# Start all services
docker-compose up -d
```

## Database Schema

### Hot Storage Table (`email_archive.hot_emails`)
- Recent emails for fast access
- Full-text search indexes
- Optimized for frequent queries

### Cold Storage Table (`email_archive.cold_emails`)
- Older emails for long-term retention
- Compressed storage
- Less frequent access patterns

### Attachments Table (`email_archive.email_attachments`)
- File deduplication using SHA-256 hashes
- Automatic compression for non-image files
- Storage path tracking

### Processing Logs (`email_archive.processing_logs`)
- Track email processing status
- Performance metrics
- Error logging

### Storage Statistics (`email_archive.storage_stats`)
- Real-time storage metrics
- Email counts and sizes
- Date ranges

## Usage Examples

### Basic Email Archiving

```python
from core.services.email_archive_service import EmailArchiveService
from datetime import datetime

# Initialize service
archive_service = EmailArchiveService()

# Store an email in hot storage
email_data = {
    'message_id': 'unique-message-id-123',
    'thread_id': 'thread-456',
    'sender_email': 'sender@example.com',
    'sender_name': 'John Doe',
    'recipient_email': 'recipient@example.com',
    'subject': 'Important Meeting Tomorrow',
    'body_text': 'Please join us for the quarterly review...',
    'body_html': '<p>Please join us for the quarterly review...</p>',
    'received_date': datetime.now(),
    'user_id': 'user-123',
    'task_database_id': 'notion-db-456',
    'email_size_bytes': 2048,
    'has_attachments': True,
    'attachment_count': 2,
    'priority': 'high',
    'labels': ['work', 'meeting'],
    'is_read': False,
    'is_archived': False,
    'processing_status': 'completed',
    'processing_metadata': {'ai_processed': True, 'tasks_extracted': 3}
}

email_id = archive_service.store_email(email_data, 'hot')
print(f"Stored email with ID: {email_id}")
```

### Searching Emails

```python
# Search by text
results = archive_service.search_emails(
    query='meeting tomorrow',
    storage_type='hot',
    limit=50
)

# Search by sender
results = archive_service.search_emails(
    sender_email='sender@example.com',
    storage_type='hot'
)

# Search by date range
from datetime import datetime, timedelta
date_from = datetime.now() - timedelta(days=7)
date_to = datetime.now()

results = archive_service.search_emails(
    date_from=date_from,
    date_to=date_to,
    storage_type='hot'
)
```

### Managing Storage

```python
# Move old emails to cold storage (30+ days)
moved_count = archive_service.move_to_cold_storage(days_threshold=30)
print(f"Moved {moved_count} emails to cold storage")

# Get storage statistics
stats = archive_service.get_storage_stats()
for storage_type, stat in stats.items():
    print(f"{storage_type}: {stat['total_emails']} emails, {stat['total_size_bytes']} bytes")

# Cleanup very old emails (365+ days) - use with caution!
deleted_count = archive_service.cleanup_old_emails(days_threshold=365)
print(f"Deleted {deleted_count} old emails")
```

### Working with Attachments

```python
# Store an attachment
with open('document.pdf', 'rb') as f:
    content = f.read()

attachment_id = archive_service.store_attachment(
    email_id=email_id,
    filename='document.pdf',
    content=content,
    content_type='application/pdf',
    storage_type='hot',
    compress=True
)
```

## Celery Tasks

The system includes asynchronous tasks for background processing:

### Archive Email Task
```python
from core.tasks.email_archive_tasks import archive_email_async

# Archive email asynchronously
task = archive_email_async.delay(email_data, 'hot')
result = task.get()  # Wait for completion
```

### Storage Management Tasks
```python
from core.tasks.email_archive_tasks import (
    move_to_cold_storage_async,
    cleanup_old_emails_async,
    get_storage_stats_async
)

# Move emails to cold storage
task = move_to_cold_storage_async.delay(days_threshold=30)

# Get storage statistics
task = get_storage_stats_async.delay()
stats = task.get()
```

### Search Task
```python
from core.tasks.email_archive_tasks import search_emails_async

# Search emails asynchronously
task = search_emails_async.delay(
    query='important',
    storage_type='hot',
    limit=100
)
results = task.get()
```

## Monitoring

### Flower Dashboard
Monitor Celery tasks at: http://localhost:5555

### Database Monitoring
```sql
-- Check storage statistics
SELECT * FROM email_archive.storage_stats;

-- Check processing logs
SELECT * FROM email_archive.processing_logs 
ORDER BY created_at DESC LIMIT 10;

-- Check hot storage usage
SELECT COUNT(*) as email_count, 
       SUM(email_size_bytes) as total_size
FROM email_archive.hot_emails;

-- Check cold storage usage
SELECT COUNT(*) as email_count, 
       SUM(email_size_bytes) as total_size
FROM email_archive.cold_emails;
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/email_archive` | PostgreSQL connection URL |
| `EMAIL_ARCHIVE_ENABLED` | `True` | Enable/disable email archiving |
| `HOT_STORAGE_DAYS` | `30` | Days to keep emails in hot storage |
| `COLD_STORAGE_DAYS` | `365` | Days to keep emails in cold storage |
| `EMAIL_COMPRESSION_ENABLED` | `True` | Enable attachment compression |
| `ATTACHMENT_STORAGE_PATH` | `attachments` | Path for storing attachments |

### Performance Tuning

```sql
-- Create additional indexes for specific queries
CREATE INDEX idx_hot_emails_priority ON email_archive.hot_emails(priority);
CREATE INDEX idx_hot_emails_labels ON email_archive.hot_emails USING gin(labels);

-- Partition tables for very large datasets
-- (Advanced: Consider table partitioning for millions of emails)
```

## Integration with Existing Email Processing

To integrate with your existing Gmail processing:

1. **Modify your email processing workflow** to store emails in the archive
2. **Add archive calls** after successful email processing
3. **Use the archive for search** instead of re-processing emails
4. **Schedule maintenance tasks** for automatic storage management

Example integration:

```python
# In your existing email processing code
def process_email(email_data):
    # Your existing processing logic
    tasks = extract_tasks_from_email(email_data)
    
    # Archive the email
    if config.EMAIL_ARCHIVE_ENABLED:
        archive_service = EmailArchiveService()
        email_id = archive_service.store_email(email_data, 'hot')
        
        # Store tasks in Notion (existing logic)
        store_tasks_in_notion(tasks)
    
    return tasks
```

## Maintenance

### Scheduled Tasks

Set up periodic tasks for maintenance:

```python
# In your Celery beat schedule
CELERY_BEAT_SCHEDULE = {
    'move-to-cold-storage': {
        'task': 'core.tasks.email_archive_tasks.move_to_cold_storage_async',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'args': (30,)
    },
    'cleanup-old-emails': {
        'task': 'core.tasks.email_archive_tasks.cleanup_old_emails_async',
        'schedule': crontab(0, 0, day_of_month='1'),  # Monthly
        'args': (365,)
    },
    'update-storage-stats': {
        'task': 'core.tasks.email_archive_tasks.get_storage_stats_async',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    }
}
```

### Backup Strategy

```bash
# Backup the database
docker exec -t your_postgres_container pg_dump -U postgres email_archive > backup.sql

# Backup attachments
tar -czf attachments_backup.tar.gz attachments/
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check if PostgreSQL is running: `docker-compose ps`
   - Verify DATABASE_URL format
   - Check network connectivity

2. **Permission Errors**
   - Ensure PostgreSQL user has proper permissions
   - Check file permissions for attachment storage

3. **Performance Issues**
   - Monitor query performance with `EXPLAIN ANALYZE`
   - Consider adding indexes for frequent queries
   - Check if hot storage is getting too large

### Logs

```bash
# Check application logs
docker-compose logs app

# Check Celery worker logs
docker-compose logs celery-worker

# Check database logs
docker-compose logs postgres
```

## Security Considerations

1. **Database Security**
   - Use strong passwords for PostgreSQL
   - Restrict database access to application only
   - Enable SSL connections in production

2. **File Storage**
   - Consider using cloud storage (S3, GCS) for attachments
   - Implement proper file access controls
   - Regular security audits

3. **Data Privacy**
   - Implement data retention policies
   - Ensure GDPR compliance if applicable
   - Regular data cleanup of old emails

## Production Deployment

For production deployment:

1. **Use managed PostgreSQL** (AWS RDS, Google Cloud SQL, etc.)
2. **Implement proper backup strategies**
3. **Use cloud storage** for attachments
4. **Set up monitoring and alerting**
5. **Configure proper logging levels**
6. **Implement rate limiting** for archive operations

## Support

For issues or questions:

1. Check the logs for error messages
2. Verify database connectivity
3. Test with the setup script: `python setup_email_archive.py`
4. Review the configuration settings
5. Check Celery task status in Flower dashboard 