"""
Enhanced security service for correction handler with multi-factor validation.
"""
import os
import time
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from src.core.services.correction_service import CorrectionService
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class SecurityLevel(Enum):
    """Security levels for different operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    """Security event record."""
    timestamp: datetime
    event_type: str
    severity: SecurityLevel
    user_email: str
    correlation_id: str
    ip_address: str
    user_agent: str
    details: Dict[str, Any]

class SecureCorrectionService(CorrectionService):
    """Enhanced correction service with comprehensive security measures."""
    
    def __init__(self):
        """Initialize secure correction service."""
        super().__init__()
        
        # Security configuration
        self.security_enabled = os.getenv('ENABLE_SECURITY', 'true').lower() == 'true'
        self.rate_limit_enabled = os.getenv('ENABLE_RATE_LIMITING', 'true').lower() == 'true'
        self.signature_validation = os.getenv('ENABLE_SIGNATURE_VALIDATION', 'true').lower() == 'true'
        
        # Rate limiting configuration
        self.rate_limits = {
            'corrections_per_hour': int(os.getenv('RATE_LIMIT_CORRECTIONS_PER_HOUR', '10')),
            'corrections_per_day': int(os.getenv('RATE_LIMIT_CORRECTIONS_PER_DAY', '50')),
            'failed_attempts_per_hour': int(os.getenv('RATE_LIMIT_FAILED_ATTEMPTS_PER_HOUR', '5'))
        }
        
        # Security storage (in production, use Redis or database)
        self.security_events = []
        self.rate_limit_cache = {}
        self.blocked_ips = set()
        self.suspicious_users = set()
        
        if self.security_enabled:
            logger.info("Enhanced security enabled for correction service")
        else:
            logger.info("Enhanced security disabled for correction service")
    
    def validate_correction_request(self, correlation_id: str, sender_email: str, 
                                  request_signature: str, ip_address: str, 
                                  user_agent: str, request_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Comprehensive validation of correction requests.
        
        Args:
            correlation_id: Correlation ID for the correction
            sender_email: Email of the sender
            request_signature: Cryptographic signature of the request
            ip_address: IP address of the request
            user_agent: User agent string
            request_data: Request data for validation
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.security_enabled:
            return True, ""
        
        try:
            # Step 1: Basic validation
            basic_valid, basic_error = self._validate_basic_request(
                correlation_id, sender_email, ip_address
            )
            if not basic_valid:
                return False, basic_error
            
            # Step 2: Rate limiting
            rate_valid, rate_error = self._validate_rate_limits(sender_email, ip_address)
            if not rate_valid:
                return False, rate_error
            
            # Step 3: Signature validation
            if self.signature_validation:
                sig_valid, sig_error = self._validate_request_signature(
                    correlation_id, sender_email, request_signature, request_data
                )
                if not sig_valid:
                    return False, sig_error
            
            # Step 4: Advanced security checks
            advanced_valid, advanced_error = self._validate_advanced_security(
                sender_email, ip_address, user_agent, request_data
            )
            if not advanced_valid:
                return False, advanced_error
            
            # Step 5: Log security event
            self._log_security_event(
                "correction_request_validated",
                SecurityLevel.LOW,
                sender_email,
                correlation_id,
                ip_address,
                user_agent,
                {"validation_passed": True}
            )
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Security validation error: {e}")
            return False, f"Security validation failed: {str(e)}"
    
    def _validate_basic_request(self, correlation_id: str, sender_email: str, 
                              ip_address: str) -> Tuple[bool, str]:
        """Basic request validation."""
        # Check if IP is blocked
        if ip_address in self.blocked_ips:
            self._log_security_event(
                "blocked_ip_attempt",
                SecurityLevel.HIGH,
                sender_email,
                correlation_id,
                ip_address,
                "",
                {"reason": "IP address is blocked"}
            )
            return False, "Access denied: IP address is blocked"
        
        # Check if user is suspicious
        if sender_email in self.suspicious_users:
            self._log_security_event(
                "suspicious_user_attempt",
                SecurityLevel.MEDIUM,
                sender_email,
                correlation_id,
                ip_address,
                "",
                {"reason": "User marked as suspicious"}
            )
            return False, "Access denied: User account is under review"
        
        # Validate correlation ID format
        if not self._is_valid_correlation_id(correlation_id):
            return False, "Invalid correlation ID format"
        
        # Validate email format
        if not self._is_valid_email(sender_email):
            return False, "Invalid email format"
        
        return True, ""
    
    def _validate_rate_limits(self, sender_email: str, ip_address: str) -> Tuple[bool, str]:
        """Validate rate limits for requests."""
        if not self.rate_limit_enabled:
            return True, ""
        
        current_time = time.time()
        
        # Check corrections per hour
        hourly_key = f"corrections_hourly:{sender_email}"
        hourly_count = self._get_rate_limit_count(hourly_key, current_time, 3600)
        
        if hourly_count >= self.rate_limits['corrections_per_hour']:
            self._log_security_event(
                "rate_limit_exceeded",
                SecurityLevel.MEDIUM,
                sender_email,
                "",
                ip_address,
                "",
                {"limit_type": "hourly", "count": hourly_count}
            )
            return False, f"Rate limit exceeded: Maximum {self.rate_limits['corrections_per_hour']} corrections per hour"
        
        # Check corrections per day
        daily_key = f"corrections_daily:{sender_email}"
        daily_count = self._get_rate_limit_count(daily_key, current_time, 86400)
        
        if daily_count >= self.rate_limits['corrections_per_day']:
            self._log_security_event(
                "rate_limit_exceeded",
                SecurityLevel.MEDIUM,
                sender_email,
                "",
                ip_address,
                "",
                {"limit_type": "daily", "count": daily_count}
            )
            return False, f"Rate limit exceeded: Maximum {self.rate_limits['corrections_per_day']} corrections per day"
        
        # Update rate limit counters
        self._increment_rate_limit(hourly_key, current_time)
        self._increment_rate_limit(daily_key, current_time)
        
        return True, ""
    
    def _validate_request_signature(self, correlation_id: str, sender_email: str, 
                                  request_signature: str, request_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate cryptographic signature of the request."""
        try:
            # Generate expected signature
            expected_signature = self._generate_request_signature(
                correlation_id, sender_email, request_data
            )
            
            # Compare signatures using constant-time comparison
            if not hmac.compare_digest(request_signature, expected_signature):
                self._log_security_event(
                    "invalid_signature",
                    SecurityLevel.HIGH,
                    sender_email,
                    correlation_id,
                    "",
                    "",
                    {"provided_signature": request_signature[:10] + "..."}
                )
                return False, "Invalid request signature"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Signature validation error: {e}")
            return False, "Signature validation failed"
    
    def _validate_advanced_security(self, sender_email: str, ip_address: str, 
                                  user_agent: str, request_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Advanced security checks."""
        # Check for suspicious patterns
        if self._is_suspicious_pattern(request_data):
            self._log_security_event(
                "suspicious_pattern_detected",
                SecurityLevel.MEDIUM,
                sender_email,
                "",
                ip_address,
                user_agent,
                {"pattern_type": "request_content"}
            )
            return False, "Suspicious request pattern detected"
        
        # Check user agent for known malicious patterns
        if self._is_suspicious_user_agent(user_agent):
            self._log_security_event(
                "suspicious_user_agent",
                SecurityLevel.MEDIUM,
                sender_email,
                "",
                ip_address,
                user_agent,
                {"user_agent": user_agent}
            )
            return False, "Suspicious user agent detected"
        
        # Check for rapid successive requests
        if self._is_rapid_succession(sender_email, ip_address):
            self._log_security_event(
                "rapid_succession_detected",
                SecurityLevel.HIGH,
                sender_email,
                "",
                ip_address,
                user_agent,
                {"timeframe": "last_5_minutes"}
            )
            return False, "Too many requests in short time period"
        
        return True, ""
    
    def _generate_request_signature(self, correlation_id: str, sender_email: str, 
                                  request_data: Dict[str, Any]) -> str:
        """Generate cryptographic signature for request validation."""
        # In production, use a proper secret key from environment
        secret_key = os.getenv('SIGNATURE_SECRET_KEY', 'default-secret-key-change-in-production')
        
        # Create signature payload
        payload = f"{correlation_id}:{sender_email}:{json.dumps(request_data, sort_keys=True)}"
        
        # Generate HMAC signature
        signature = hmac.new(
            secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _is_valid_correlation_id(self, correlation_id: str) -> bool:
        """Validate correlation ID format."""
        import re
        pattern = r'^corr-[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
        return bool(re.match(pattern, correlation_id))
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _get_rate_limit_count(self, key: str, current_time: float, window: int) -> int:
        """Get rate limit count for a key within the time window."""
        if key not in self.rate_limit_cache:
            return 0
        
        # Clean old entries
        cutoff_time = current_time - window
        self.rate_limit_cache[key] = [
            timestamp for timestamp in self.rate_limit_cache[key]
            if timestamp > cutoff_time
        ]
        
        return len(self.rate_limit_cache[key])
    
    def _increment_rate_limit(self, key: str, current_time: float):
        """Increment rate limit counter."""
        if key not in self.rate_limit_cache:
            self.rate_limit_cache[key] = []
        
        self.rate_limit_cache[key].append(current_time)
    
    def _is_suspicious_pattern(self, request_data: Dict[str, Any]) -> bool:
        """Check for suspicious patterns in request data."""
        # Check for SQL injection patterns
        sql_patterns = ["'", "DROP", "DELETE", "INSERT", "UPDATE", "SELECT", "UNION"]
        request_str = str(request_data).upper()
        
        for pattern in sql_patterns:
            if pattern in request_str:
                return True
        
        # Check for XSS patterns
        xss_patterns = ["<script>", "javascript:", "onload=", "onerror="]
        for pattern in xss_patterns:
            if pattern.lower() in request_str.lower():
                return True
        
        return False
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check for suspicious user agent patterns."""
        suspicious_patterns = [
            "bot", "crawler", "spider", "scraper", "curl", "wget",
            "python-requests", "masscan", "nmap"
        ]
        
        user_agent_lower = user_agent.lower()
        for pattern in suspicious_patterns:
            if pattern in user_agent_lower:
                return True
        
        return False
    
    def _is_rapid_succession(self, sender_email: str, ip_address: str) -> bool:
        """Check for rapid successive requests."""
        current_time = time.time()
        window = 300  # 5 minutes
        
        # Check recent requests for this user/IP combination
        key = f"recent_requests:{sender_email}:{ip_address}"
        recent_requests = self._get_rate_limit_count(key, current_time, window)
        
        # Allow maximum 3 requests in 5 minutes
        if recent_requests >= 3:
            return True
        
        # Update counter
        self._increment_rate_limit(key, current_time)
        return False
    
    def _log_security_event(self, event_type: str, severity: SecurityLevel, 
                           user_email: str, correlation_id: str, ip_address: str, 
                           user_agent: str, details: Dict[str, Any]):
        """Log a security event."""
        security_event = SecurityEvent(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            severity=severity,
            user_email=user_email,
            correlation_id=correlation_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )
        
        self.security_events.append(security_event)
        
        # Log based on severity
        if severity == SecurityLevel.CRITICAL:
            logger.critical(f"CRITICAL SECURITY EVENT: {event_type} - User: {user_email}, IP: {ip_address}")
        elif severity == SecurityLevel.HIGH:
            logger.error(f"HIGH SECURITY EVENT: {event_type} - User: {user_email}, IP: {ip_address}")
        elif severity == SecurityLevel.MEDIUM:
            logger.warning(f"MEDIUM SECURITY EVENT: {event_type} - User: {user_email}, IP: {ip_address}")
        else:
            logger.info(f"LOW SECURITY EVENT: {event_type} - User: {user_email}, IP: {ip_address}")
    
    def block_ip(self, ip_address: str, reason: str = "Manual block"):
        """Block an IP address."""
        self.blocked_ips.add(ip_address)
        self._log_security_event(
            "ip_blocked",
            SecurityLevel.HIGH,
            "",
            "",
            ip_address,
            "",
            {"reason": reason, "action": "manual_block"}
        )
        logger.warning(f"IP address {ip_address} has been blocked: {reason}")
    
    def unblock_ip(self, ip_address: str):
        """Unblock an IP address."""
        self.blocked_ips.discard(ip_address)
        logger.info(f"IP address {ip_address} has been unblocked")
    
    def mark_user_suspicious(self, user_email: str, reason: str = "Suspicious activity"):
        """Mark a user as suspicious."""
        self.suspicious_users.add(user_email)
        self._log_security_event(
            "user_marked_suspicious",
            SecurityLevel.MEDIUM,
            user_email,
            "",
            "",
            "",
            {"reason": reason, "action": "manual_mark"}
        )
        logger.warning(f"User {user_email} has been marked as suspicious: {reason}")
    
    def unmark_user_suspicious(self, user_email: str):
        """Remove suspicious mark from user."""
        self.suspicious_users.discard(user_email)
        logger.info(f"User {user_email} has been unmarked as suspicious")
    
    def get_security_report(self, hours: int = 24) -> Dict[str, Any]:
        """Get security report for the specified time period."""
        if not self.security_enabled:
            return {"enabled": False}
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Filter events by time
            recent_events = [
                event for event in self.security_events
                if event.timestamp >= cutoff_time
            ]
            
            # Count events by type and severity
            event_counts = {}
            severity_counts = {}
            
            for event in recent_events:
                event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
                severity_counts[event.severity.value] = severity_counts.get(event.severity.value, 0) + 1
            
            # Get top suspicious IPs
            ip_counts = {}
            for event in recent_events:
                if event.ip_address:
                    ip_counts[event.ip_address] = ip_counts.get(event.ip_address, 0) + 1
            
            top_suspicious_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "period_hours": hours,
                "total_events": len(recent_events),
                "event_counts": event_counts,
                "severity_counts": severity_counts,
                "top_suspicious_ips": top_suspicious_ips,
                "blocked_ips_count": len(self.blocked_ips),
                "suspicious_users_count": len(self.suspicious_users),
                "recent_events": [
                    {
                        "timestamp": event.timestamp.isoformat(),
                        "event_type": event.event_type,
                        "severity": event.severity.value,
                        "user_email": event.user_email,
                        "ip_address": event.ip_address,
                        "details": event.details
                    }
                    for event in recent_events[-10:]  # Last 10 events
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate security report: {e}")
            return {"error": str(e)}
    
    def cleanup_old_security_events(self, days: int = 30) -> int:
        """Clean up old security events."""
        if not self.security_enabled:
            return 0
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            original_count = len(self.security_events)
            
            self.security_events = [
                event for event in self.security_events
                if event.timestamp >= cutoff_time
            ]
            
            cleaned_count = original_count - len(self.security_events)
            logger.info(f"Cleaned up {cleaned_count} old security events")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old security events: {e}")
            return 0 