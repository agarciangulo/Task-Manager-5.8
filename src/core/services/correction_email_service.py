"""
Simple email service for correction confirmations.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.core.logging_config import get_logger

logger = get_logger(__name__)

class CorrectionEmailService:
    """Enhanced email service for correction handler with rich templates and better UX."""
    
    def __init__(self):
        """Initialize email service with configuration."""
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@taskmanager.com')
        self.dashboard_url = os.getenv('DASHBOARD_URL', 'https://taskmanager.com/dashboard')
        
        if not all([self.smtp_username, self.smtp_password]):
            raise ValueError("Gmail credentials not configured. Set SMTP_USERNAME and SMTP_PASSWORD environment variables.")
    
    def send_correction_confirmation(self, user_email: str, applied_corrections: List[Dict], 
                                   failed_corrections: List[Dict], correlation_id: str) -> bool:
        """
        Send enhanced confirmation email with rich formatting and detailed information.
        
        Args:
            user_email: Recipient email address
            applied_corrections: List of successfully applied corrections
            failed_corrections: List of failed corrections
            correlation_id: Correlation ID for tracking
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            subject = "✅ Your Task Corrections Have Been Applied"
            
            # Create rich HTML content
            html_content = self._build_confirmation_html(
                applied_corrections, failed_corrections, correlation_id
            )
            
            # Create plain text fallback
            text_content = self._build_confirmation_text(
                applied_corrections, failed_corrections, correlation_id
            )
            
            # Send email
            success = self._send_email(user_email, subject, html_content, text_content)
            
            if success:
                logger.info(f"Sent correction confirmation email to {user_email}")
            else:
                logger.error(f"Failed to send correction confirmation email to {user_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending correction confirmation email: {e}")
            return False
    
    def send_clarification_email(self, user_email: str, correlation_id: str, 
                               ai_response: str = "") -> bool:
        """
        Send clarification request email with helpful guidance.
        
        Args:
            user_email: Recipient email address
            correlation_id: Correlation ID for tracking
            ai_response: AI's response explaining what wasn't understood
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            subject = "🤔 Need More Information About Your Correction Request"
            
            html_content = self._build_clarification_html(correlation_id, ai_response)
            text_content = self._build_clarification_text(correlation_id, ai_response)
            
            success = self._send_email(user_email, subject, html_content, text_content)
            
            if success:
                logger.info(f"Sent clarification email to {user_email}")
            else:
                logger.error(f"Failed to send clarification email to {user_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending clarification email: {e}")
            return False
    
    def send_error_email(self, user_email: str, correlation_id: str, error_message: str) -> bool:
        """
        Send error notification email with helpful information.
        
        Args:
            user_email: Recipient email address
            correlation_id: Correlation ID for tracking
            error_message: Error details
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            subject = "❌ Task Correction Processing Error"
            
            html_content = self._build_error_html(correlation_id, error_message)
            text_content = self._build_error_text(correlation_id, error_message)
            
            success = self._send_email(user_email, subject, html_content, text_content)
            
            if success:
                logger.info(f"Sent error email to {user_email}")
            else:
                logger.error(f"Failed to send error email to {user_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending error email: {e}")
            return False
    
    def send_security_violation_email(self, user_email: str, correlation_id: str) -> bool:
        """
        Send security violation notification email.
        
        Args:
            user_email: Recipient email address
            correlation_id: Correlation ID for tracking
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            subject = "🚨 Security Alert: Unauthorized Correction Request"
            
            html_content = self._build_security_violation_html(correlation_id)
            text_content = self._build_security_violation_text(correlation_id)
            
            success = self._send_email(user_email, subject, html_content, text_content)
            
            if success:
                logger.info(f"Sent security violation email to {user_email}")
            else:
                logger.error(f"Failed to send security violation email to {user_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending security violation email: {e}")
            return False
    
    def _build_confirmation_html(self, applied_corrections: List[Dict], 
                               failed_corrections: List[Dict], correlation_id: str) -> str:
        """Build rich HTML confirmation email."""
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        applied_section = ""
        if applied_corrections:
            applied_section = """
            <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 10px 0;">
                <h3 style="color: #155724; margin-top: 0;">✅ Successfully Applied Corrections</h3>
                <ul style="color: #155724;">
            """
            for correction in applied_corrections:
                task_id = correction.get('task_id', 'Unknown Task')
                correction_type = correction.get('correction_type', 'update')
                updates = correction.get('updates', {})
                
                if correction_type == 'update':
                    update_text = ", ".join([f"{k}: {v}" for k, v in updates.items()])
                    applied_section += f"<li><strong>{task_id}</strong>: Updated {update_text}</li>"
                elif correction_type == 'delete':
                    applied_section += f"<li><strong>{task_id}</strong>: Archived task</li>"
            
            applied_section += "</ul></div>"
        
        failed_section = ""
        if failed_corrections:
            failed_section = """
            <div style="background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 15px; margin: 10px 0;">
                <h3 style="color: #721c24; margin-top: 0;">❌ Failed Corrections</h3>
                <ul style="color: #721c24;">
            """
            for correction in failed_corrections:
                task_id = correction.get('task_id', 'Unknown Task')
                failed_section += f"<li><strong>{task_id}</strong>: Could not be processed</li>"
            
            failed_section += "</ul></div>"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Task Corrections Applied</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2c3e50; margin-bottom: 10px;">✅ Task Corrections Applied</h1>
                    <p style="color: #7f8c8d; font-size: 14px;">Processed on {timestamp}</p>
                </div>
                
                <div style="background: #f8f9fa; border-radius: 5px; padding: 20px; margin-bottom: 20px;">
                    <p style="margin: 0; color: #495057;">
                        Your correction request has been processed. Below is a summary of what was applied:
                    </p>
                </div>
                
                {applied_section}
                {failed_section}
                
                <div style="background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 5px; padding: 15px; margin: 20px 0;">
                    <h3 style="color: #1565c0; margin-top: 0;">📊 Summary</h3>
                    <ul style="color: #1565c0;">
                        <li>Successfully applied: <strong>{len(applied_corrections)}</strong> corrections</li>
                        <li>Failed to apply: <strong>{len(failed_corrections)}</strong> corrections</li>
                        <li>Reference ID: <strong>{correlation_id}</strong></li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="{self.dashboard_url}" style="background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        📋 View in Dashboard
                    </a>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ecf0f1; font-size: 12px; color: #7f8c8d;">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>If you have questions, contact support at support@taskmanager.com</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _build_confirmation_text(self, applied_corrections: List[Dict], 
                               failed_corrections: List[Dict], correlation_id: str) -> str:
        """Build plain text confirmation email."""
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        text = f"""
Task Corrections Applied
Processed on {timestamp}

Your correction request has been processed. Below is a summary of what was applied:

SUCCESSFULLY APPLIED CORRECTIONS:
"""
        
        for correction in applied_corrections:
            task_id = correction.get('task_id', 'Unknown Task')
            correction_type = correction.get('correction_type', 'update')
            updates = correction.get('updates', {})
            
            if correction_type == 'update':
                update_text = ", ".join([f"{k}: {v}" for k, v in updates.items()])
                text += f"- {task_id}: Updated {update_text}\n"
            elif correction_type == 'delete':
                text += f"- {task_id}: Archived task\n"
        
        if failed_corrections:
            text += "\nFAILED CORRECTIONS:\n"
            for correction in failed_corrections:
                task_id = correction.get('task_id', 'Unknown Task')
                text += f"- {task_id}: Could not be processed\n"
        
        text += f"""
SUMMARY:
- Successfully applied: {len(applied_corrections)} corrections
- Failed to apply: {len(failed_corrections)} corrections
- Reference ID: {correlation_id}

View your tasks in the dashboard: {self.dashboard_url}

This is an automated message. Please do not reply to this email.
If you have questions, contact support at support@taskmanager.com
"""
        
        return text
    
    def _build_clarification_html(self, correlation_id: str, ai_response: str) -> str:
        """Build rich HTML clarification email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Clarification Needed</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #f39c12; margin-bottom: 10px;">🤔 Need More Information</h1>
                    <p style="color: #7f8c8d;">I couldn't understand your correction request clearly</p>
                </div>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 20px; margin-bottom: 20px;">
                    <h3 style="color: #856404; margin-top: 0;">What I understood:</h3>
                    <p style="color: #856404; font-style: italic;">{ai_response or 'Your request was unclear. Please provide more specific instructions.'}</p>
                </div>
                
                <div style="background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 5px; padding: 15px; margin: 20px 0;">
                    <h3 style="color: #1565c0; margin-top: 0;">💡 How to help me understand:</h3>
                    <ul style="color: #1565c0;">
                        <li>Be specific about which task you want to change</li>
                        <li>Use clear language like "Change task 1 status to completed"</li>
                        <li>Mention the task ID or name if possible</li>
                        <li>Specify what field to update (status, due date, etc.)</li>
                    </ul>
                </div>
                
                <div style="background: #f8f9fa; border-radius: 5px; padding: 15px; margin: 20px 0;">
                    <h3 style="color: #495057; margin-top: 0;">📝 Examples of clear requests:</h3>
                    <ul style="color: #495057;">
                        <li>"Change task 1 status to completed"</li>
                        <li>"Update task 2 due date to 2024-01-15"</li>
                        <li>"Delete task 3"</li>
                        <li>"Mark task 'Follow up with client' as done"</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <p style="color: #7f8c8d; font-size: 14px;">
                        Reply to this email with your clarification. Reference ID: {correlation_id}
                    </p>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ecf0f1; font-size: 12px; color: #7f8c8d;">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>If you have questions, contact support at support@taskmanager.com</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _build_clarification_text(self, correlation_id: str, ai_response: str) -> str:
        """Build plain text clarification email."""
        return f"""
Need More Information

I couldn't understand your correction request clearly.

What I understood:
{ai_response or 'Your request was unclear. Please provide more specific instructions.'}

How to help me understand:
- Be specific about which task you want to change
- Use clear language like "Change task 1 status to completed"
- Mention the task ID or name if possible
- Specify what field to update (status, due date, etc.)

Examples of clear requests:
- "Change task 1 status to completed"
- "Update task 2 due date to 2024-01-15"
- "Delete task 3"
- "Mark task 'Follow up with client' as done"

Reply to this email with your clarification. Reference ID: {correlation_id}

This is an automated message. Please do not reply to this email.
If you have questions, contact support at support@taskmanager.com
"""
    
    def _build_error_html(self, correlation_id: str, error_message: str) -> str:
        """Build rich HTML error email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Processing Error</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #e74c3c; margin-bottom: 10px;">❌ Processing Error</h1>
                    <p style="color: #7f8c8d;">We encountered an issue processing your correction request</p>
                </div>
                
                <div style="background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 20px; margin-bottom: 20px;">
                    <h3 style="color: #721c24; margin-top: 0;">Error Details:</h3>
                    <p style="color: #721c24;">{error_message}</p>
                </div>
                
                <div style="background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 5px; padding: 15px; margin: 20px 0;">
                    <h3 style="color: #1565c0; margin-top: 0;">🛠️ What you can do:</h3>
                    <ul style="color: #1565c0;">
                        <li>Try your request again in a few minutes</li>
                        <li>Contact support if the issue persists</li>
                        <li>Check that your tasks still exist in the system</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <p style="color: #7f8c8d; font-size: 14px;">
                        Reference ID: {correlation_id}
                    </p>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ecf0f1; font-size: 12px; color: #7f8c8d;">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>If you have questions, contact support at support@taskmanager.com</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _build_error_text(self, correlation_id: str, error_message: str) -> str:
        """Build plain text error email."""
        return f"""
Processing Error

We encountered an issue processing your correction request.

Error Details:
{error_message}

What you can do:
- Try your request again in a few minutes
- Contact support if the issue persists
- Check that your tasks still exist in the system

Reference ID: {correlation_id}

This is an automated message. Please do not reply to this email.
If you have questions, contact support at support@taskmanager.com
"""
    
    def _build_security_violation_html(self, correlation_id: str) -> str:
        """Build rich HTML security violation email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Security Alert</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #e74c3c; margin-bottom: 10px;">🚨 Security Alert</h1>
                    <p style="color: #7f8c8d;">Unauthorized correction request detected</p>
                </div>
                
                <div style="background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 20px; margin-bottom: 20px;">
                    <h3 style="color: #721c24; margin-top: 0;">Security Violation:</h3>
                    <p style="color: #721c24;">
                        A correction request was received from an email address that doesn't match the original task owner. 
                        This request has been blocked for security reasons.
                    </p>
                </div>
                
                <div style="background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 5px; padding: 15px; margin: 20px 0;">
                    <h3 style="color: #1565c0; margin-top: 0;">🔒 Security Measures:</h3>
                    <ul style="color: #1565c0;">
                        <li>Only the original task owner can make corrections</li>
                        <li>All correction attempts are logged for security</li>
                        <li>Contact support if you believe this is an error</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <p style="color: #7f8c8d; font-size: 14px;">
                        Reference ID: {correlation_id}
                    </p>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ecf0f1; font-size: 12px; color: #7f8c8d;">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>If you have questions, contact support at support@taskmanager.com</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _build_security_violation_text(self, correlation_id: str) -> str:
        """Build plain text security violation email."""
        return f"""
Security Alert

Unauthorized correction request detected.

Security Violation:
A correction request was received from an email address that doesn't match the original task owner. 
This request has been blocked for security reasons.

Security Measures:
- Only the original task owner can make corrections
- All correction attempts are logged for security
- Contact support if you believe this is an error

Reference ID: {correlation_id}

This is an automated message. Please do not reply to this email.
If you have questions, contact support at support@taskmanager.com
"""
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send email with both HTML and text content."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False 