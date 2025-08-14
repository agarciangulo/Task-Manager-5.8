"""
Integration tests for the correction handler functionality.
"""
import pytest
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

from src.core.models.correction_models import TaskCorrectionLog, TaskCorrection, Base
from src.core.services.correction_service import CorrectionService
from src.core.agents.correction_agent import CorrectionAgent
from src.core.services.correction_email_service import CorrectionEmailService
from src.core.tasks.correction_tasks import process_correction, cleanup_old_correction_logs
from src.core.services.email_router import EmailRouter


class TestCorrectionHandlerIntegration:
    """Integration tests for the correction handler system."""
    
    @pytest.fixture
    def mock_database(self):
        """Mock database setup."""
        with patch('src.core.services.correction_service.create_engine') as mock_engine:
            mock_session = Mock()
            mock_engine.return_value = Mock()
            yield mock_session
    
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
            },
            {
                'id': 'task-3',
                'task': 'Schedule team meeting',
                'status': 'Completed',
                'category': 'Meetings',
                'priority': 'Low'
            }
        ]
    
    @pytest.fixture
    def sample_correction_log(self):
        """Sample correction log for testing."""
        return {
            'id': str(uuid.uuid4()),
            'correlation_id': 'corr-test-123',
            'user_email': 'test@example.com',
            'task_ids': ['task-1', 'task-2', 'task-3'],
            'email_subject': 'Test Summary',
            'status': 'pending',
            'created_at': datetime.now()
        }
    
    def test_correction_service_creation(self, mock_database):
        """Test correction service initialization."""
        service = CorrectionService()
        assert service is not None
        assert hasattr(service, 'create_correction_log')
        assert hasattr(service, 'get_correction_log')
        assert hasattr(service, 'update_correction_log_status')
    
    def test_correction_log_creation(self, mock_database):
        """Test creating a correction log."""
        with patch('src.core.services.correction_service.CorrectionService._get_session') as mock_session:
            mock_session.return_value.__enter__.return_value = Mock()
            
            service = CorrectionService()
            correlation_id = service.create_correction_log(
                user_email='test@example.com',
                task_ids=['task-1', 'task-2'],
                email_subject='Test Email'
            )
            
            assert correlation_id.startswith('corr-')
            assert len(correlation_id) > 20
    
    def test_correction_agent_interpretation(self):
        """Test AI interpretation of correction requests."""
        agent = CorrectionAgent()
        
        # Test simple update request
        reply_text = "Change task 1 status to completed"
        task_ids = ['task-1', 'task-2', 'task-3']
        
        with patch.object(agent.ai_client, 'generate_content') as mock_response:
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
            
            result = agent.interpret_corrections(reply_text, task_ids)
            
            assert result['corrections'] is not None
            assert len(result['corrections']) == 1
            assert result['corrections'][0]['task_id'] == 'task-1'
            assert result['corrections'][0]['correction_type'] == 'update'
            assert result['corrections'][0]['updates']['status'] == 'Completed'
    
    def test_correction_agent_complex_request(self):
        """Test complex correction request interpretation."""
        agent = CorrectionAgent()
        
        # Test multiple corrections
        reply_text = "Change task 1 status to completed and delete task 2"
        task_ids = ['task-1', 'task-2', 'task-3']
        
        with patch.object(agent.ai_client, 'generate_response') as mock_response:
            mock_response.return_value = '''
            {
                "corrections": [
                    {
                        "task_index": 1,
                        "type": "update",
                        "changes": {"status": "Completed"}
                    },
                    {
                        "task_index": 2,
                        "type": "delete",
                        "changes": {}
                    }
                ]
            }
            '''
            
            result = agent.interpret_corrections(reply_text, task_ids)
            
            assert len(result['corrections']) == 2
            assert result['corrections'][0]['correction_type'] == 'update'
            assert result['corrections'][1]['correction_type'] == 'delete'
    
    def test_correction_agent_validation(self):
        """Test correction validation."""
        agent = CorrectionAgent()
        
        # Test invalid task index
        invalid_correction = {
            'task_index': 5,  # Out of range
            'type': 'update',
            'changes': {'status': 'Completed'}
        }
        
        task_ids = ['task-1', 'task-2', 'task-3']
        assert not agent._validate_correction(invalid_correction, task_ids)
        
        # Test valid correction
        valid_correction = {
            'task_index': 1,
            'type': 'update',
            'changes': {'status': 'Completed'}
        }
        assert agent._validate_correction(valid_correction, task_ids)
    
    def test_email_router_classification(self):
        """Test email classification by router."""
        router = EmailRouter()
        
        # Test correction email
        subject = "Re: Your Daily Summary [Ref: corr-123e4567-e89b-12d3-a456-426614174000]"
        body = "Change task 1 status to completed"
        
        email_type, correlation_id = router.classify_email(
            Mock(), subject, body, 'test@example.com'
        )
        
        assert email_type == 'correction'
        assert correlation_id == 'corr-123e4567-e89b-12d3-a456-426614174000'
    
    def test_email_router_context_response(self):
        """Test context response email classification."""
        router = EmailRouter()
        
        # Test context response email
        subject = "Re: Task Manager: Need More Details [Context Request: conv-123e4567-e89b-12d3-a456-426614174000]"
        body = "Here are more details about the tasks"
        
        email_type, conversation_id = router.classify_email(
            Mock(), subject, body, 'test@example.com'
        )
        
        assert email_type == 'context_response'
        assert conversation_id == 'conv-123e4567-e89b-12d3-a456-426614174000'
    
    def test_email_service_confirmation(self):
        """Test correction confirmation email service."""
        with patch('src.core.services.correction_email_service.smtplib.SMTP_SSL') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            email_service = CorrectionEmailService()
            
            applied_corrections = [
                {
                    'task_id': 'task-1',
                    'correction_type': 'update',
                    'updates': {'status': 'Completed'}
                }
            ]
            
            failed_corrections = []
            
            success = email_service.send_correction_confirmation(
                'test@example.com',
                applied_corrections,
                failed_corrections,
                'corr-test-123'
            )
            
            assert success
            mock_server.login.assert_called_once()
            mock_server.send_message.assert_called_once()
    
    def test_correction_task_processing(self, sample_correction_log):
        """Test the complete correction task processing."""
        with patch('src.core.services.correction_service.CorrectionService') as mock_service_class:
            with patch('src.core.agents.correction_agent.CorrectionAgent') as mock_agent_class:
                with patch('src.core.services.correction_email_service.CorrectionEmailService') as mock_email_class:
                    
                    # Mock services
                    mock_service = Mock()
                    mock_service.get_correction_log.return_value = sample_correction_log
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
                    
                    # Mock NotionService
                    with patch('src.core.notion_service.NotionService') as mock_notion_class:
                        mock_notion = Mock()
                        mock_notion.update_task.return_value = (True, "Success")
                        mock_notion_class.return_value = mock_notion
                        
                        # Test the task
                        result = process_correction(
                            'corr-test-123',
                            'Change task 1 status to completed',
                            'test@example.com'
                        )
                        
                        assert result['status'] == 'success'
                        assert result['applied_corrections'] == 1
                        assert result['failed_corrections'] == 0
    
    def test_correction_task_security_violation(self, sample_correction_log):
        """Test security validation in correction processing."""
        with patch('src.core.services.correction_service.CorrectionService') as mock_service_class:
            with patch('src.core.services.correction_email_service.CorrectionEmailService') as mock_email_class:
                
                mock_service = Mock()
                mock_service.get_correction_log.return_value = sample_correction_log
                mock_service_class.return_value = mock_service
                
                mock_email = Mock()
                mock_email_class.return_value = mock_email
                
                # Test with wrong sender email
                result = process_correction(
                    'corr-test-123',
                    'Change task 1 status to completed',
                    'wrong@example.com'  # Different from sample_correction_log['user_email']
                )
                
                assert result['status'] == 'security_violation'
                mock_service.update_correction_log_status.assert_called_with(
                    'corr-test-123', 'failed', pytest.approx(any(str))
                )
    
    def test_correction_task_clarification_needed(self, sample_correction_log):
        """Test when clarification is needed."""
        with patch('src.core.services.correction_service.CorrectionService') as mock_service_class:
            with patch('src.core.agents.correction_agent.CorrectionAgent') as mock_agent_class:
                with patch('src.core.services.correction_email_service.CorrectionEmailService') as mock_email_class:
                    
                    mock_service = Mock()
                    mock_service.get_correction_log.return_value = sample_correction_log
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
                    
                    result = process_correction(
                        'corr-test-123',
                        'Please fix the tasks',  # Ambiguous request
                        'test@example.com'
                    )
                    
                    assert result['status'] == 'clarification_requested'
                    mock_service.update_correction_log_status.assert_called_with(
                        'corr-test-123', 'clarification_requested'
                    )
    
    def test_cleanup_old_logs(self):
        """Test cleanup of old correction logs."""
        with patch('src.core.services.correction_service.CorrectionService') as mock_service_class:
            mock_service = Mock()
            mock_service.cleanup_old_logs.return_value = 5
            mock_service_class.return_value = mock_service
            
            result = cleanup_old_correction_logs()
            
            assert result['status'] == 'success'
            assert result['deleted_count'] == 5
            mock_service.cleanup_old_logs.assert_called_with(days_old=30)
    
    def test_complex_correction_scenarios(self):
        """Test complex correction scenarios."""
        agent = CorrectionAgent()
        
        test_scenarios = [
            {
                'request': 'Update task 1 priority to high and due date to 2024-01-15',
                'expected_updates': {'priority': 'High', 'due_date': '2024-01-15'}
            },
            {
                'request': 'Delete task 2 and change task 3 status to completed',
                'expected_types': ['delete', 'update']
            },
            {
                'request': 'Change task 1 category to "High Priority" and status to "In Progress"',
                'expected_updates': {'category': 'High Priority', 'status': 'In Progress'}
            }
        ]
        
        task_ids = ['task-1', 'task-2', 'task-3']
        
        for scenario in test_scenarios:
            with patch.object(agent.ai_client, 'generate_response') as mock_response:
                # Mock appropriate response based on scenario
                if 'expected_updates' in scenario:
                    mock_response.return_value = f'''
                    {{
                        "corrections": [
                            {{
                                "task_index": 1,
                                "type": "update",
                                "changes": {json.dumps(scenario['expected_updates'])}
                            }}
                        ]
                    }}
                    '''
                else:
                    mock_response.return_value = '''
                    {
                        "corrections": [
                            {
                                "task_index": 2,
                                "type": "delete",
                                "changes": {}
                            },
                            {
                                "task_index": 3,
                                "type": "update",
                                "changes": {"status": "Completed"}
                            }
                        ]
                    }
                    '''
                
                result = agent.interpret_corrections(scenario['request'], task_ids)
                
                assert result['corrections'] is not None
                assert len(result['corrections']) > 0
                assert not result['requires_clarification']
    
    def test_error_handling(self):
        """Test error handling in correction processing."""
        # Test database connection error
        with patch('src.core.services.correction_service.CorrectionService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_correction_log.side_effect = Exception("Database connection failed")
            mock_service_class.return_value = mock_service
            
            result = process_correction(
                'corr-test-123',
                'Change task 1 status to completed',
                'test@example.com'
            )
            
            assert result['status'] == 'error'
            assert 'Database connection failed' in result['error']
    
    def test_retry_logic(self):
        """Test retry logic for transient failures."""
        with patch('src.core.services.correction_service.CorrectionService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_correction_log.side_effect = Exception("Transient error")
            mock_service_class.return_value = mock_service
            
            # Mock the retry mechanism
            with patch('src.core.tasks.correction_tasks.process_correction.retry') as mock_retry:
                mock_retry.side_effect = Exception("Retry called")
                
                with pytest.raises(Exception, match="Retry called"):
                    process_correction(
                        'corr-test-123',
                        'Change task 1 status to completed',
                        'test@example.com'
                    )
    
    def test_email_content_generation(self):
        """Test email content generation for different scenarios."""
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
        
        content = email_service._build_confirmation_content(applied_corrections, failed_corrections)
        
        assert 'successfully applied 2 correction(s)' in content
        assert 'Updated task task-1' in content
        assert 'Deleted task task-2' in content
        assert 'Failed to update task task-3' in content
        assert 'Error: Task not found' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 