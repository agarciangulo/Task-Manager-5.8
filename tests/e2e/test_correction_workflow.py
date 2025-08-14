"""
End-to-end tests for the correction handler workflow.
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from email.message import Message
from email.mime.text import MIMEText

from src.core.services.correction_service import CorrectionService
from src.core.agents.correction_agent import CorrectionAgent
from src.core.services.correction_email_service import CorrectionEmailService
from src.core.services.email_router import EmailRouter
from src.core.tasks.correction_tasks import process_correction
from src.utils.gmail_processor_enhanced import send_confirmation_email_with_correction_support


class TestCorrectionWorkflowE2E:
    """End-to-end tests for the complete correction workflow."""
    
    @pytest.fixture
    def sample_email_message(self):
        """Create a sample email message for testing."""
        msg = Message()
        msg['From'] = 'test@example.com'
        msg['To'] = 'taskmanager@example.com'
        msg['Subject'] = 'Re: Your Daily Summary [Ref: corr-test-123]'
        msg.set_payload('Change task 1 status to completed')
        return msg
    
    @pytest.fixture
    def sample_tasks(self):
        """Sample tasks for testing."""
        return [
            {
                'id': 'task-1',
                'task': 'Complete project proposal',
                'status': 'In Progress',
                'category': 'Work',
                'priority': 'High'
            },
            {
                'id': 'task-2',
                'task': 'Review quarterly reports',
                'status': 'Not Started',
                'category': 'Work',
                'priority': 'Medium'
            }
        ]
    
    def test_complete_correction_workflow(self, sample_tasks):
        """Test the complete correction workflow from email to task update."""
        
        # Step 1: Send confirmation email with correction support
        with patch('src.core.services.correction_service.CorrectionService') as mock_service_class:
            with patch('src.core.services.correction_email_service.smtplib.SMTP_SSL') as mock_smtp:
                
                mock_service = Mock()
                mock_service.create_correction_log.return_value = 'corr-test-123'
                mock_service_class.return_value = mock_service
                
                mock_server = Mock()
                mock_smtp.return_value.__enter__.return_value = mock_server
                
                # Send confirmation email
                send_confirmation_email_with_correction_support(
                    recipient='test@example.com',
                    tasks=sample_tasks,
                    coaching_insights='Great progress on your tasks!',
                    user_database_id='test-db-id'
                )
                
                # Verify correlation log was created
                mock_service.create_correction_log.assert_called_once()
                call_args = mock_service.create_correction_log.call_args
                assert call_args[1]['user_email'] == 'test@example.com'
                assert call_args[1]['task_ids'] == ['task-1', 'task-2']
                
                # Verify email was sent
                mock_server.login.assert_called_once()
                mock_server.send_message.assert_called_once()
    
    def test_email_processing_workflow(self, sample_email_message):
        """Test email processing workflow."""
        
        # Step 1: Email classification
        router = EmailRouter()
        subject = sample_email_message['Subject']
        body = sample_email_message.get_payload()
        
        email_type, correlation_id = router.classify_email(
            sample_email_message, subject, body, 'test@example.com'
        )
        
        assert email_type == 'correction'
        assert correlation_id == 'corr-test-123'
        
        # Step 2: AI interpretation
        agent = CorrectionAgent()
        task_ids = ['task-1', 'task-2']
        
        with patch.object(agent.ai_client, 'generate_response') as mock_response:
            mock_response.return_value = '''
            {
                "corrections": [
                    {
                        "task_index": 1,
                        "type": "update",
                        "changes": {"status": "Completed"}
                    }
                ]
            }
            '''
            
            result = agent.interpret_corrections(body, task_ids)
            
            assert len(result['corrections']) == 1
            assert result['corrections'][0]['task_id'] == 'task-1'
            assert result['corrections'][0]['correction_type'] == 'update'
            assert result['corrections'][0]['updates']['status'] == 'Completed'
    
    def test_correction_task_processing_workflow(self):
        """Test the complete correction task processing workflow."""
        
        with patch('src.core.services.correction_service.CorrectionService') as mock_service_class:
            with patch('src.core.agents.correction_agent.CorrectionAgent') as mock_agent_class:
                with patch('src.core.services.correction_email_service.CorrectionEmailService') as mock_email_class:
                    with patch('src.core.tasks.correction_tasks.NotionService') as mock_notion_class:
                        
                        # Mock all services
                        mock_service = Mock()
                        mock_service.get_correction_log.return_value = {
                            'id': 'test-id',
                            'correlation_id': 'corr-test-123',
                            'user_email': 'test@example.com',
                            'task_ids': ['task-1', 'task-2'],
                            'status': 'pending'
                        }
                        mock_service_class.return_value = mock_service
                        
                        mock_agent = Mock()
                        mock_agent.interpret_corrections.return_value = {
                            'corrections': [
                                {
                                    'task_id': 'task-1',
                                    'correction_type': 'update',
                                    'updates': {'status': 'Completed'}
                                }
                            ],
                            'requires_clarification': False,
                            'confidence_score': 0.9
                        }
                        mock_agent_class.return_value = mock_agent
                        
                        mock_email = Mock()
                        mock_email_class.return_value = mock_email
                        
                        mock_notion = Mock()
                        mock_notion.update_task.return_value = (True, "Success")
                        mock_notion_class.return_value = mock_notion
                        
                        # Process correction
                        result = process_correction(
                            'corr-test-123',
                            'Change task 1 status to completed',
                            'test@example.com'
                        )
                        
                        # Verify results
                        assert result['status'] == 'success'
                        assert result['applied_corrections'] == 1
                        assert result['failed_corrections'] == 0
                        
                        # Verify service calls
                        mock_service.get_correction_log.assert_called_once()
                        mock_agent.interpret_corrections.assert_called_once()
                        mock_notion.update_task.assert_called_once()
                        mock_email.send_correction_confirmation.assert_called_once()
                        mock_service.update_correction_log_status.assert_called_with(
                            'corr-test-123', 'processed'
                        )
    
    def test_security_violation_workflow(self):
        """Test security violation handling workflow."""
        
        with patch('src.core.services.correction_service.CorrectionService') as mock_service_class:
            with patch('src.core.services.correction_email_service.CorrectionEmailService') as mock_email_class:
                
                mock_service = Mock()
                mock_service.get_correction_log.return_value = {
                    'id': 'test-id',
                    'correlation_id': 'corr-test-123',
                    'user_email': 'authorized@example.com',  # Different from sender
                    'task_ids': ['task-1', 'task-2'],
                    'status': 'pending'
                }
                mock_service_class.return_value = mock_service
                
                mock_email = Mock()
                mock_email_class.return_value = mock_email
                
                # Try to process correction with wrong email
                result = process_correction(
                    'corr-test-123',
                    'Change task 1 status to completed',
                    'unauthorized@example.com'  # Different email
                )
                
                # Verify security violation
                assert result['status'] == 'security_violation'
                mock_service.update_correction_log_status.assert_called_with(
                    'corr-test-123', 'failed', pytest.approx(any(str))
                )
                mock_email.send_correction_error.assert_called_once()
    
    def test_clarification_workflow(self):
        """Test clarification request workflow."""
        
        with patch('src.core.services.correction_service.CorrectionService') as mock_service_class:
            with patch('src.core.agents.correction_agent.CorrectionAgent') as mock_agent_class:
                with patch('src.core.services.correction_email_service.CorrectionEmailService') as mock_email_class:
                    
                    mock_service = Mock()
                    mock_service.get_correction_log.return_value = {
                        'id': 'test-id',
                        'correlation_id': 'corr-test-123',
                        'user_email': 'test@example.com',
                        'task_ids': ['task-1', 'task-2'],
                        'status': 'pending'
                    }
                    mock_service_class.return_value = mock_service
                    
                    mock_agent = Mock()
                    mock_agent.interpret_corrections.return_value = {
                        'corrections': [],
                        'requires_clarification': True,
                        'confidence_score': 0.1
                    }
                    mock_agent_class.return_value = mock_agent
                    
                    mock_email = Mock()
                    mock_email_class.return_value = mock_email
                    
                    # Process ambiguous correction request
                    result = process_correction(
                        'corr-test-123',
                        'Please fix the tasks',  # Ambiguous request
                        'test@example.com'
                    )
                    
                    # Verify clarification request
                    assert result['status'] == 'clarification_requested'
                    mock_service.update_correction_log_status.assert_called_with(
                        'corr-test-123', 'clarification_requested'
                    )
                    mock_email.send_correction_error.assert_called_once()
    
    def test_multiple_corrections_workflow(self):
        """Test workflow with multiple corrections."""
        
        with patch('src.core.services.correction_service.CorrectionService') as mock_service_class:
            with patch('src.core.agents.correction_agent.CorrectionAgent') as mock_agent_class:
                with patch('src.core.services.correction_email_service.CorrectionEmailService') as mock_email_class:
                    with patch('src.core.tasks.correction_tasks.NotionService') as mock_notion_class:
                        
                        mock_service = Mock()
                        mock_service.get_correction_log.return_value = {
                            'id': 'test-id',
                            'correlation_id': 'corr-test-123',
                            'user_email': 'test@example.com',
                            'task_ids': ['task-1', 'task-2', 'task-3'],
                            'status': 'pending'
                        }
                        mock_service_class.return_value = mock_service
                        
                        mock_agent = Mock()
                        mock_agent.interpret_corrections.return_value = {
                            'corrections': [
                                {
                                    'task_id': 'task-1',
                                    'correction_type': 'update',
                                    'updates': {'status': 'Completed'}
                                },
                                {
                                    'task_id': 'task-2',
                                    'correction_type': 'delete',
                                    'updates': {}
                                },
                                {
                                    'task_id': 'task-3',
                                    'correction_type': 'update',
                                    'updates': {'priority': 'High'}
                                }
                            ],
                            'requires_clarification': False,
                            'confidence_score': 0.9
                        }
                        mock_agent_class.return_value = mock_agent
                        
                        mock_email = Mock()
                        mock_email_class.return_value = mock_email
                        
                        mock_notion = Mock()
                        mock_notion.update_task.return_value = (True, "Success")
                        mock_notion_class.return_value = mock_notion
                        
                        # Process multiple corrections
                        result = process_correction(
                            'corr-test-123',
                            'Change task 1 status to completed, delete task 2, and update task 3 priority to high',
                            'test@example.com'
                        )
                        
                        # Verify results
                        assert result['status'] == 'success'
                        assert result['applied_corrections'] == 3
                        assert result['failed_corrections'] == 0
                        
                        # Verify multiple service calls
                        assert mock_notion.update_task.call_count == 3
    
    def test_error_recovery_workflow(self):
        """Test error recovery workflow."""
        
        with patch('src.core.services.correction_service.CorrectionService') as mock_service_class:
            with patch('src.core.services.correction_email_service.CorrectionEmailService') as mock_email_class:
                
                mock_service = Mock()
                mock_service.get_correction_log.side_effect = Exception("Database connection failed")
                mock_service_class.return_value = mock_service
                
                mock_email = Mock()
                mock_email_class.return_value = mock_email
                
                # Process correction with database error
                result = process_correction(
                    'corr-test-123',
                    'Change task 1 status to completed',
                    'test@example.com'
                )
                
                # Verify error handling
                assert result['status'] == 'error'
                assert 'Database connection failed' in result['error']
                mock_email.send_correction_error.assert_called_once()
    
    def test_cleanup_workflow(self):
        """Test cleanup workflow."""
        
        with patch('src.core.services.correction_service.CorrectionService') as mock_service_class:
            from src.core.tasks.correction_tasks import cleanup_old_correction_logs
            
            mock_service = Mock()
            mock_service.cleanup_old_logs.return_value = 5
            mock_service_class.return_value = mock_service
            
            # Run cleanup
            result = cleanup_old_correction_logs()
            
            # Verify cleanup
            assert result['status'] == 'success'
            assert result['deleted_count'] == 5
            mock_service.cleanup_old_logs.assert_called_with(days_old=30)
    
    def test_email_content_workflow(self):
        """Test email content generation workflow."""
        
        email_service = CorrectionEmailService()
        
        # Test successful corrections
        applied_corrections = [
            {
                'task_id': 'task-1',
                'correction_type': 'update',
                'updates': {'status': 'Completed', 'priority': 'High'}
            },
            {
                'task_id': 'task-2',
                'correction_type': 'delete',
                'updates': {}
            }
        ]
        
        failed_corrections = [
            {
                'task_id': 'task-3',
                'correction_type': 'update',
                'updates': {'status': 'Completed'},
                'error_message': 'Task not found'
            }
        ]
        
        with patch('src.core.services.correction_email_service.smtplib.SMTP_SSL') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            # Send confirmation email
            success = email_service.send_correction_confirmation(
                'test@example.com',
                applied_corrections,
                failed_corrections,
                'corr-test-123'
            )
            
            # Verify email content
            assert success
            mock_server.send_message.assert_called_once()
            
            # Verify email content contains expected information
            call_args = mock_server.send_message.call_args[0][0]
            email_content = call_args.get_payload()[0].get_payload()
            
            assert 'successfully applied 2 correction(s)' in email_content
            assert 'Updated task task-1' in email_content
            assert 'Deleted task task-2' in email_content
            assert 'Failed to update task task-3' in email_content
            assert 'Error: Task not found' in email_content


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 