"""
Advanced metrics and monitoring service for correction handler.
"""
import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from src.core.logging_config import get_logger

logger = get_logger(__name__)

class MetricType(Enum):
    """Types of metrics that can be tracked."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    labels: Dict[str, str]
    description: str = ""

class CorrectionMetrics:
    """Advanced metrics collection for correction handler."""
    
    def __init__(self):
        """Initialize metrics service."""
        self.metrics_storage = {}
        self.enabled = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
        self.retention_days = int(os.getenv('METRICS_RETENTION_DAYS', '30'))
        
        if self.enabled:
            logger.info("Metrics collection enabled for correction handler")
        else:
            logger.info("Metrics collection disabled for correction handler")
    
    def record_correction_processed(self, correlation_id: str, processing_time: float, 
                                  success: bool, error_type: str = None):
        """Record a correction processing event."""
        if not self.enabled:
            return
        
        try:
            # Counter for total corrections
            self._record_metric(
                "corrections_processed_total",
                1,
                MetricType.COUNTER,
                {"success": str(success), "error_type": error_type or "none"}
            )
            
            # Histogram for processing time
            self._record_metric(
                "correction_processing_duration_seconds",
                processing_time,
                MetricType.HISTOGRAM,
                {"success": str(success)}
            )
            
            # Gauge for current processing rate
            self._record_metric(
                "correction_processing_rate_per_minute",
                self._calculate_processing_rate(),
                MetricType.GAUGE
            )
            
            logger.debug(f"Recorded metrics for correction {correlation_id}: success={success}, time={processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to record correction metrics: {e}")
    
    def record_ai_interpretation(self, correlation_id: str, interpretation_time: float, 
                               success: bool, requires_clarification: bool):
        """Record AI interpretation metrics."""
        if not self.enabled:
            return
        
        try:
            # Counter for AI interpretations
            self._record_metric(
                "ai_interpretations_total",
                1,
                MetricType.COUNTER,
                {
                    "success": str(success),
                    "requires_clarification": str(requires_clarification)
                }
            )
            
            # Histogram for interpretation time
            self._record_metric(
                "ai_interpretation_duration_seconds",
                interpretation_time,
                MetricType.HISTOGRAM,
                {"success": str(success)}
            )
            
            # Gauge for AI accuracy
            self._record_metric(
                "ai_interpretation_accuracy",
                self._calculate_ai_accuracy(),
                MetricType.GAUGE
            )
            
        except Exception as e:
            logger.error(f"Failed to record AI interpretation metrics: {e}")
    
    def record_database_operation(self, operation: str, duration: float, success: bool):
        """Record database operation metrics."""
        if not self.enabled:
            return
        
        try:
            # Counter for database operations
            self._record_metric(
                "database_operations_total",
                1,
                MetricType.COUNTER,
                {"operation": operation, "success": str(success)}
            )
            
            # Histogram for database operation duration
            self._record_metric(
                "database_operation_duration_seconds",
                duration,
                MetricType.HISTOGRAM,
                {"operation": operation, "success": str(success)}
            )
            
        except Exception as e:
            logger.error(f"Failed to record database metrics: {e}")
    
    def record_cache_operation(self, operation: str, hit: bool, duration: float = None):
        """Record cache operation metrics."""
        if not self.enabled:
            return
        
        try:
            # Counter for cache operations
            self._record_metric(
                "cache_operations_total",
                1,
                MetricType.COUNTER,
                {"operation": operation, "hit": str(hit)}
            )
            
            # Histogram for cache operation duration
            if duration is not None:
                self._record_metric(
                    "cache_operation_duration_seconds",
                    duration,
                    MetricType.HISTOGRAM,
                    {"operation": operation, "hit": str(hit)}
                )
            
            # Gauge for cache hit rate
            self._record_metric(
                "cache_hit_rate",
                self._calculate_cache_hit_rate(),
                MetricType.GAUGE
            )
            
        except Exception as e:
            logger.error(f"Failed to record cache metrics: {e}")
    
    def record_email_sent(self, email_type: str, success: bool, duration: float = None):
        """Record email sending metrics."""
        if not self.enabled:
            return
        
        try:
            # Counter for emails sent
            self._record_metric(
                "emails_sent_total",
                1,
                MetricType.COUNTER,
                {"email_type": email_type, "success": str(success)}
            )
            
            # Histogram for email sending duration
            if duration is not None:
                self._record_metric(
                    "email_sending_duration_seconds",
                    duration,
                    MetricType.HISTOGRAM,
                    {"email_type": email_type, "success": str(success)}
                )
            
        except Exception as e:
            logger.error(f"Failed to record email metrics: {e}")
    
    def record_security_event(self, event_type: str, severity: str, user_email: str = None):
        """Record security-related events."""
        if not self.enabled:
            return
        
        try:
            # Counter for security events
            self._record_metric(
                "security_events_total",
                1,
                MetricType.COUNTER,
                {
                    "event_type": event_type,
                    "severity": severity,
                    "user_email": user_email or "unknown"
                }
            )
            
            # Alert for high severity events
            if severity in ['high', 'critical']:
                self._record_security_alert(event_type, severity, user_email)
            
        except Exception as e:
            logger.error(f"Failed to record security metrics: {e}")
    
    def record_user_engagement(self, user_email: str, action: str, correlation_id: str = None):
        """Record user engagement metrics."""
        if not self.enabled:
            return
        
        try:
            # Counter for user actions
            self._record_metric(
                "user_actions_total",
                1,
                MetricType.COUNTER,
                {
                    "user_email": user_email,
                    "action": action,
                    "correlation_id": correlation_id or "none"
                }
            )
            
            # Track user activity patterns
            self._record_user_activity(user_email, action)
            
        except Exception as e:
            logger.error(f"Failed to record user engagement metrics: {e}")
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get metrics summary for the specified time period."""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Filter metrics by time
            recent_metrics = {
                name: [m for m in metrics if m.timestamp >= cutoff_time]
                for name, metrics in self.metrics_storage.items()
            }
            
            summary = {
                "period_hours": hours,
                "total_corrections": self._sum_counter_metrics(recent_metrics, "corrections_processed_total"),
                "success_rate": self._calculate_success_rate(recent_metrics),
                "avg_processing_time": self._calculate_average_time(recent_metrics, "correction_processing_duration_seconds"),
                "ai_accuracy": self._calculate_ai_accuracy(),
                "cache_hit_rate": self._calculate_cache_hit_rate(),
                "security_events": self._sum_counter_metrics(recent_metrics, "security_events_total"),
                "active_users": self._count_active_users(recent_metrics),
                "top_operations": self._get_top_operations(recent_metrics)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {"error": str(e)}
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format."""
        if not self.enabled:
            return "Metrics collection disabled"
        
        try:
            if format == "json":
                return json.dumps(self.metrics_storage, default=str, indent=2)
            elif format == "prometheus":
                return self._export_prometheus_format()
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            return f"Error exporting metrics: {e}"
    
    def cleanup_old_metrics(self, days: int = None) -> int:
        """Clean up metrics older than specified days."""
        if not self.enabled:
            return 0
        
        try:
            days = days or self.retention_days
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            
            cleaned_count = 0
            for metric_name, metrics in self.metrics_storage.items():
                original_count = len(metrics)
                self.metrics_storage[metric_name] = [
                    m for m in metrics if m.timestamp >= cutoff_time
                ]
                cleaned_count += original_count - len(self.metrics_storage[metric_name])
            
            logger.info(f"Cleaned up {cleaned_count} old metric points")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")
            return 0
    
    def _record_metric(self, name: str, value: float, metric_type: MetricType, 
                      labels: Dict[str, str] = None, description: str = ""):
        """Record a metric point."""
        if not self.enabled:
            return
        
        metric_point = MetricPoint(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=datetime.utcnow(),
            labels=labels or {},
            description=description
        )
        
        if name not in self.metrics_storage:
            self.metrics_storage[name] = []
        
        self.metrics_storage[name].append(metric_point)
    
    def _calculate_processing_rate(self) -> float:
        """Calculate current processing rate per minute."""
        try:
            recent_metrics = self._get_recent_metrics("corrections_processed_total", minutes=1)
            return len(recent_metrics)
        except Exception:
            return 0.0
    
    def _calculate_ai_accuracy(self) -> float:
        """Calculate AI interpretation accuracy."""
        try:
            total_interpretations = self._sum_counter_metrics({}, "ai_interpretations_total")
            successful_interpretations = self._sum_counter_metrics(
                {}, "ai_interpretations_total", {"success": "true"}
            )
            
            if total_interpretations > 0:
                return (successful_interpretations / total_interpretations) * 100
            return 0.0
        except Exception:
            return 0.0
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        try:
            total_operations = self._sum_counter_metrics({}, "cache_operations_total")
            cache_hits = self._sum_counter_metrics(
                {}, "cache_operations_total", {"hit": "true"}
            )
            
            if total_operations > 0:
                return (cache_hits / total_operations) * 100
            return 0.0
        except Exception:
            return 0.0
    
    def _calculate_success_rate(self, recent_metrics: Dict[str, List[MetricPoint]]) -> float:
        """Calculate success rate from recent metrics."""
        try:
            total_corrections = self._sum_counter_metrics(recent_metrics, "corrections_processed_total")
            successful_corrections = self._sum_counter_metrics(
                recent_metrics, "corrections_processed_total", {"success": "true"}
            )
            
            if total_corrections > 0:
                return (successful_corrections / total_corrections) * 100
            return 0.0
        except Exception:
            return 0.0
    
    def _calculate_average_time(self, recent_metrics: Dict[str, List[MetricPoint]], 
                              metric_name: str) -> float:
        """Calculate average time for a metric."""
        try:
            metrics = recent_metrics.get(metric_name, [])
            if metrics:
                return sum(m.value for m in metrics) / len(metrics)
            return 0.0
        except Exception:
            return 0.0
    
    def _sum_counter_metrics(self, recent_metrics: Dict[str, List[MetricPoint]], 
                           metric_name: str, labels: Dict[str, str] = None) -> int:
        """Sum counter metrics with optional label filtering."""
        try:
            metrics = recent_metrics.get(metric_name, [])
            if labels:
                metrics = [m for m in metrics if all(m.labels.get(k) == v for k, v in labels.items())]
            return len(metrics)
        except Exception:
            return 0
    
    def _get_recent_metrics(self, metric_name: str, minutes: int = 60) -> List[MetricPoint]:
        """Get recent metrics for a specific metric name."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
            metrics = self.metrics_storage.get(metric_name, [])
            return [m for m in metrics if m.timestamp >= cutoff_time]
        except Exception:
            return []
    
    def _record_security_alert(self, event_type: str, severity: str, user_email: str = None):
        """Record a security alert."""
        alert_message = f"Security alert: {event_type} (severity: {severity})"
        if user_email:
            alert_message += f" - User: {user_email}"
        
        logger.warning(alert_message)
        # In a real implementation, this could send to an alerting system
    
    def _record_user_activity(self, user_email: str, action: str):
        """Record user activity for engagement analysis."""
        # This could be used for user behavior analysis
        pass
    
    def _count_active_users(self, recent_metrics: Dict[str, List[MetricPoint]]) -> int:
        """Count active users in recent metrics."""
        try:
            user_actions = recent_metrics.get("user_actions_total", [])
            unique_users = set()
            for metric in user_actions:
                user_email = metric.labels.get("user_email", "unknown")
                if user_email != "unknown":
                    unique_users.add(user_email)
            return len(unique_users)
        except Exception:
            return 0
    
    def _get_top_operations(self, recent_metrics: Dict[str, List[MetricPoint]]) -> List[Dict[str, Any]]:
        """Get top operations by frequency."""
        try:
            operation_counts = {}
            db_operations = recent_metrics.get("database_operations_total", [])
            
            for metric in db_operations:
                operation = metric.labels.get("operation", "unknown")
                operation_counts[operation] = operation_counts.get(operation, 0) + 1
            
            return [
                {"operation": op, "count": count}
                for op, count in sorted(operation_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ]
        except Exception:
            return []
    
    def _export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format."""
        try:
            prometheus_lines = []
            
            for metric_name, metrics in self.metrics_storage.items():
                for metric in metrics:
                    # Build labels string
                    labels = []
                    for key, value in metric.labels.items():
                        labels.append(f'{key}="{value}"')
                    labels_str = "{" + ",".join(labels) + "}" if labels else ""
                    
                    # Format metric line
                    line = f"{metric_name}{labels_str} {metric.value}"
                    if metric.timestamp:
                        line += f" {int(metric.timestamp.timestamp() * 1000)}"
                    
                    prometheus_lines.append(line)
            
            return "\n".join(prometheus_lines)
        except Exception as e:
            logger.error(f"Failed to export Prometheus format: {e}")
            return f"# Error exporting metrics: {e}" 