"""
Email router for classifying and routing different types of emails.
"""
import re
from typing import Tuple, Optional
from email.message import Message
from email.header import decode_header

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class EmailRouter:
    """Router for classifying and routing different types of emails."""
    
    def __init__(self):
        """Initialize the email router."""
        self.correction_keywords = [
            'correction', 'fix', 'update', 'change', 'modify', 'edit',
            'wrong', 'incorrect', 'mistake', 'error', 'delete', 'remove'
        ]
    
    def classify_email(self, msg: Message, subject: str, body: str, sender_email: str) -> Tuple[str, Optional[str]]:
        """
        Classify an email and return its type and any relevant ID.
        
        Args:
            msg: Email message object
            subject: Email subject
            body: Email body
            sender_email: Sender email address
            
        Returns:
            Tuple[str, Optional[str]]: (email_type, correlation_id)
            email_type can be: 'correction', 'context_response', 'new_task'
        """
        # Check for correction email first (only after context verification is complete)
        is_correction, correlation_id = self._is_correction_email(subject, body)
        if is_correction:
            logger.info(f"Classified email as correction with correlation_id: {correlation_id}")
            return 'correction', correlation_id
        
        # Check for context response (existing context verification system)
        is_context_response, conversation_id = self._is_context_response_email(subject, body)
        if is_context_response:
            logger.info(f"Classified email as context response with conversation_id: {conversation_id}")
            return 'context_response', conversation_id
        
        # Default to new task email
        logger.info("Classified email as new task")
        return 'new_task', None
    
    def _is_correction_email(self, subject: str, body: str) -> Tuple[bool, Optional[str]]:
        """
        Check if an email is a correction request.
        Only valid after context verification is complete.
        
        Args:
            subject: Email subject
            body: Email body
            
        Returns:
            Tuple[bool, Optional[str]]: (is_correction, correlation_id)
        """
        # Check for correlation ID in subject (only present in confirmation emails)
        correlation_pattern = r'\[Ref: (corr-[a-f0-9-]{36})\]'
        match = re.search(correlation_pattern, subject)
        if match:
            return True, match.group(1)
        
        # Check for correlation ID in body
        match = re.search(correlation_pattern, body)
        if match:
            return True, match.group(1)
        
        # Check for correction keywords in subject (only for replies to confirmation emails)
        subject_lower = subject.lower()
        if re.search(r'^re:', subject, re.IGNORECASE):
            # Look for correlation ID in body first
            match = re.search(correlation_pattern, body)
            if match:
                return True, match.group(1)
            
            # Check for correction keywords in body
            body_lower = body.lower()
            if any(keyword in body_lower for keyword in self.correction_keywords):
                return True, None
        
        return False, None
    
    def _is_context_response_email(self, subject: str, body: str) -> Tuple[bool, Optional[str]]:
        """
        Check if an email is a context response.
        This happens BEFORE corrections are possible.
        
        Args:
            subject: Email subject
            body: Email body
            
        Returns:
            Tuple[bool, Optional[str]]: (is_context_response, conversation_id)
        """
        # Check for conversation ID in subject
        conversation_pattern = r'\[Context Request: (conv-[a-f0-9-]{36})\]'
        match = re.search(conversation_pattern, subject)
        if match:
            return True, match.group(1)
        
        # Check for conversation ID in body
        match = re.search(conversation_pattern, body)
        if match:
            return True, match.group(1)
        
        # Check for reply to context request
        if re.search(r'^re:', subject, re.IGNORECASE):
            # Look for conversation ID in body
            match = re.search(conversation_pattern, body)
            if match:
                return True, match.group(1)
        
        return False, None
    
    def extract_correlation_id(self, subject: str, body: str) -> Optional[str]:
        """
        Extract correlation ID from email subject or body.
        Only present in confirmation emails (after context verification).
        
        Args:
            subject: Email subject
            body: Email body
            
        Returns:
            Optional[str]: Correlation ID if found
        """
        # Check subject first
        correlation_pattern = r'\[Ref: (corr-[a-f0-9-]{36})\]'
        match = re.search(correlation_pattern, subject)
        if match:
            return match.group(1)
        
        # Check body
        match = re.search(correlation_pattern, body)
        if match:
            return match.group(1)
        
        return None
    
    def extract_conversation_id(self, subject: str, body: str) -> Optional[str]:
        """
        Extract conversation ID from email subject or body.
        Used for context verification (before corrections).
        
        Args:
            subject: Email subject
            body: Email body
            
        Returns:
            Optional[str]: Conversation ID if found
        """
        # Check subject first
        conversation_pattern = r'\[Context Request: (conv-[a-f0-9-]{36})\]'
        match = re.search(conversation_pattern, subject)
        if match:
            return match.group(1)
        
        # Check body
        match = re.search(conversation_pattern, body)
        if match:
            return match.group(1)
        
        return None 