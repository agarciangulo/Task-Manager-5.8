"""
Simplified service for managing correction handler operations.
"""
import os
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, DisconnectionError
from sqlalchemy.pool import QueuePool
import psycopg2
from psycopg2.extras import RealDictCursor

from src.core.models.correction_models import TaskCorrectionLog, TaskCorrection, Base
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class CorrectionService:
    """Enhanced correction service with connection resilience and fallback mechanisms."""
    
    def __init__(self):
        """Initialize with PostgreSQL database connection."""
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required for CorrectionService. Set DATABASE_URL to your PostgreSQL connection string.")
        
        # Initialize health check attributes
        self._last_health_check = datetime.utcnow()
        self._health_check_interval = timedelta(minutes=5)
        
        # Enhanced connection pooling configuration for PostgreSQL
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=10,  # Number of connections to maintain
            max_overflow=20,  # Additional connections when pool is full
            pool_pre_ping=True,  # Test connections before use
            pool_recycle=3600,  # Recycle connections every hour
            pool_timeout=30,  # Timeout for getting connection from pool
            echo=False  # Set to True for SQL debugging
        )
        
        # Create session factory with retry logic
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )
        
        # Initialize database tables with retry
        self._initialize_database_with_retry()
        
        logger.info("✅ PostgreSQL correction service initialized successfully")
    
    def _initialize_database_with_retry(self, max_retries=3):
        """Initialize database tables with retry logic."""
        for attempt in range(max_retries):
            try:
                Base.metadata.create_all(bind=self.engine)
                logger.info("Database tables initialized successfully")
                break
            except (OperationalError, DisconnectionError) as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to initialize database after {max_retries} attempts: {e}")
                    raise
                logger.warning(f"Database initialization attempt {attempt + 1} failed, retrying...")
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def _get_session(self):
        """Get database session with health check and retry logic."""
        # Health check
        if datetime.utcnow() - self._last_health_check > self._health_check_interval:
            self._check_connection_health()
            self._last_health_check = datetime.utcnow()
        
        return self.SessionLocal()
    
    def _check_connection_health(self):
        """Check database connection health."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.debug("Database connection health check passed")
        except Exception as e:
            logger.warning(f"Database connection health check failed: {e}")
            # Could implement connection refresh logic here
    
    def _execute_with_retry(self, operation, max_retries=3):
        """Execute database operation with retry logic."""
        for attempt in range(max_retries):
            try:
                return operation()
            except (OperationalError, DisconnectionError) as e:
                if attempt == max_retries - 1:
                    logger.error(f"Database operation failed after {max_retries} attempts: {e}")
                    raise
                logger.warning(f"Database operation attempt {attempt + 1} failed, retrying...")
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def create_correction_log(self, correlation_id: str, user_email: str, task_ids: List[str], 
                             email_subject: str = None) -> str:
        """Create a correction log entry with enhanced error handling."""
        def operation():
            session = self._get_session()
            try:
                correction_log = TaskCorrectionLog(
                    correlation_id=correlation_id,
                    user_email=user_email,
                    task_ids=task_ids,
                    email_subject=email_subject,
                    status='pending'
                )
                session.add(correction_log)
                session.commit()
                logger.info(f"Created correction log for correlation_id: {correlation_id}")
                return correlation_id
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to create correction log: {e}")
                raise
            finally:
                session.close()
        
        return self._execute_with_retry(operation)
    
    def get_correction_log(self, correlation_id: str) -> Optional[Dict[str, Any]]:
        """Get correction log with enhanced error handling."""
        def operation():
            session = self._get_session()
            try:
                correction_log = session.query(TaskCorrectionLog).filter(
                    TaskCorrectionLog.correlation_id == correlation_id
                ).first()
                
                if not correction_log:
                    logger.warning(f"Correction log not found for correlation_id: {correlation_id}")
                    return None
                
                return {
                    'id': str(correction_log.id),
                    'correlation_id': correction_log.correlation_id,
                    'user_email': correction_log.user_email,
                    'task_ids': correction_log.task_ids,
                    'email_subject': correction_log.email_subject,
                    'status': correction_log.status,
                    'created_at': correction_log.created_at.isoformat() if correction_log.created_at else None
                }
            except Exception as e:
                logger.error(f"Failed to get correction log: {e}")
                raise
            finally:
                session.close()
        
        return self._execute_with_retry(operation)
    
    def update_correction_log_status(self, correlation_id: str, status: str, error_message: str = None):
        """Update correction log status with enhanced error handling."""
        def operation():
            session = self._get_session()
            try:
                correction_log = session.query(TaskCorrectionLog).filter(
                    TaskCorrectionLog.correlation_id == correlation_id
                ).first()
                
                if correction_log:
                    correction_log.status = status
                    if error_message:
                        correction_log.error_message = error_message
                    correction_log.updated_at = datetime.utcnow()
                    session.commit()
                    logger.info(f"Updated correction log status to {status} for correlation_id: {correlation_id}")
                else:
                    logger.warning(f"Correction log not found for status update: {correlation_id}")
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to update correction log status: {e}")
                raise
            finally:
                session.close()
        
        return self._execute_with_retry(operation)
    
    def log_correction_application(self, correction_log_id: str, task_id: str, 
                                 correction_type: str, original_data: Dict, corrected_data: Dict,
                                 success: bool = True, error_message: str = None):
        """Log correction application with enhanced error handling."""
        def operation():
            session = self._get_session()
            try:
                correction = TaskCorrection(
                    correction_log_id=correction_log_id,
                    task_id=task_id,
                    correction_type=correction_type,
                    original_data=original_data,
                    corrected_data=corrected_data,
                    success=success,
                    error_message=error_message
                )
                session.add(correction)
                session.commit()
                logger.info(f"Logged correction application for task_id: {task_id}")
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to log correction application: {e}")
                raise
            finally:
                session.close()
        
        return self._execute_with_retry(operation)
    
    def cleanup_old_logs(self, days_old: int = 30):
        """Clean up old correction logs with enhanced error handling."""
        def operation():
            session = self._get_session()
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days_old)
                
                # Delete old correction records first (foreign key constraint)
                deleted_corrections = session.query(TaskCorrection).join(
                    TaskCorrectionLog
                ).filter(
                    TaskCorrectionLog.created_at < cutoff_date
                ).delete(synchronize_session=False)
                
                # Delete old correction logs
                deleted_logs = session.query(TaskCorrectionLog).filter(
                    TaskCorrectionLog.created_at < cutoff_date
                ).delete(synchronize_session=False)
                
                session.commit()
                logger.info(f"Cleaned up {deleted_logs} old correction logs and {deleted_corrections} corrections")
                return deleted_logs
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to cleanup old logs: {e}")
                raise
            finally:
                session.close()
        
        return self._execute_with_retry(operation)
    
    def get_correction_stats(self) -> Dict[str, Any]:
        """Get correction statistics with enhanced error handling."""
        def operation():
            session = self._get_session()
            try:
                total_logs = session.query(TaskCorrectionLog).count()
                pending_logs = session.query(TaskCorrectionLog).filter(
                    TaskCorrectionLog.status == 'pending'
                ).count()
                completed_logs = session.query(TaskCorrectionLog).filter(
                    TaskCorrectionLog.status == 'completed'
                ).count()
                failed_logs = session.query(TaskCorrectionLog).filter(
                    TaskCorrectionLog.status == 'failed'
                ).count()
                
                total_corrections = session.query(TaskCorrection).count()
                successful_corrections = session.query(TaskCorrection).filter(
                    TaskCorrection.success == True
                ).count()
                
                return {
                    'total_logs': total_logs,
                    'pending_logs': pending_logs,
                    'completed_logs': completed_logs,
                    'failed_logs': failed_logs,
                    'total_corrections': total_corrections,
                    'successful_corrections': successful_corrections,
                    'success_rate': (successful_corrections / total_corrections * 100) if total_corrections > 0 else 0
                }
            except Exception as e:
                logger.error(f"Failed to get correction stats: {e}")
                raise
            finally:
                session.close()
        
        return self._execute_with_retry(operation)
    
    def _validate_sender(self, sender_email: str, expected_email: str) -> bool:
        """Validate sender email with enhanced security."""
        if not sender_email or not expected_email:
            return False
        
        # Case-insensitive comparison
        return sender_email.lower().strip() == expected_email.lower().strip()
    
    def close(self):
        """Properly close database connections."""
        if hasattr(self, 'engine'):
            self.engine.dispose()
            logger.info("Database connections closed") 