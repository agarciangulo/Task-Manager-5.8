"""
Performance tests for the correction handler functionality.
"""
import pytest
import time
import concurrent.futures
import threading
from datetime import datetime
from unittest.mock import Mock, patch
from typing import List, Dict

from src.core.services.correction_service import CorrectionService
from src.core.agents.correction_agent import CorrectionAgent
from src.core.tasks.correction_tasks import process_correction
from src.core.services.email_router import EmailRouter


class TestCorrectionHandlerPerformance:
    """Performance tests for the correction handler system."""
    
    @pytest.fixture
    def large_task_list(self):
        """Generate a large list of tasks for testing."""
        return [f'task-{i}' for i in range(100)]
    
    @pytest.fixture
    def complex_correction_requests(self):
        """Generate complex correction requests for testing."""
        return [
            "Change task 1 status to completed and task 2 priority to high",
            "Delete task 3 and update task 4 status to in progress",
            "Update task 5 due date to 2024-01-15 and category to 'High Priority'",
            "Change task 6 status to completed, task 7 priority to urgent, and delete task 8",
            "Update task 9 category to 'Work' and task 10 status to 'On Hold'"
        ]
    
    def test_correction_agent_response_time(self, large_task_list):
        """Test AI agent response time with large task lists."""
        agent = CorrectionAgent()
        
        # Test with different request complexities
        test_requests = [
            "Change task 1 status to completed",
            "Update task 50 priority to high and task 75 status to completed",
            "Delete task 25 and change task 99 category to 'Work'"
        ]
        
        for request in test_requests:
            start_time = time.time()
            
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
                
                result = agent.interpret_corrections(request, large_task_list)
                
                end_time = time.time()
                response_time = end_time - start_time
                
                # Should complete within reasonable time (adjust based on your requirements)
                assert response_time < 5.0, f"Response time {response_time}s exceeded 5s limit"
                assert result['corrections'] is not None
    
    def test_correction_service_database_performance(self):
        """Test database operations performance."""
        with patch('src.core.services.correction_service.create_engine') as mock_engine:
            mock_session = Mock()
            mock_engine.return_value = Mock()
            
            service = CorrectionService()
            
            # Test bulk operations
            start_time = time.time()
            
            for i in range(100):
                with patch.object(service, '_get_session') as mock_session:
                    mock_session.return_value.__enter__.return_value = Mock()
                    
                    service.create_correction_log(
                        user_email=f'user{i}@example.com',
                        task_ids=[f'task-{j}' for j in range(10)],
                        email_subject=f'Test Email {i}'
                    )
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should handle 100 operations within reasonable time
            assert total_time < 10.0, f"Bulk operations took {total_time}s, exceeded 10s limit"
    
    def test_email_router_classification_performance(self):
        """Test email router classification performance."""
        router = EmailRouter()
        
        # Generate test emails
        test_emails = []
        for i in range(1000):
            if i % 3 == 0:
                # Correction email
                subject = f"Re: Your Daily Summary [Ref: corr-{uuid.uuid4()}]"
                body = f"Change task {i} status to completed"
            elif i % 3 == 1:
                # Context response email
                subject = f"Re: Task Manager: Need More Details [Context Request: conv-{uuid.uuid4()}]"
                body = f"Here are more details about task {i}"
            else:
                # New task email
                subject = f"Daily Update {i}"
                body = f"Completed task {i} today"
            
            test_emails.append((subject, body))
        
        start_time = time.time()
        
        for subject, body in test_emails:
            email_type, correlation_id = router.classify_email(
                Mock(), subject, body, 'test@example.com'
            )
            assert email_type in ['correction', 'context_response', 'new_task']
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should classify 1000 emails within reasonable time
        assert total_time < 5.0, f"Email classification took {total_time}s, exceeded 5s limit"
    
    def test_concurrent_correction_processing(self, complex_correction_requests):
        """Test concurrent correction processing."""
        with patch('src.core.services.correction_service.CorrectionService') as mock_service_class:
            with patch('src.core.agents.correction_agent.CorrectionAgent') as mock_agent_class:
                with patch('src.core.services.correction_email_service.CorrectionEmailService') as mock_email_class:
                    
                    # Mock services
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
                            }
                        ],
                        'requires_clarification': False,
                        'confidence_score': 0.9
                    }
                    mock_agent_class.return_value = mock_agent
                    
                    mock_email = Mock()
                    mock_email_class.return_value = mock_email
                    
                    # Mock NotionService
                    with patch('src.core.tasks.correction_tasks.NotionService') as mock_notion_class:
                        mock_notion = Mock()
                        mock_notion.update_task.return_value = (True, "Success")
                        mock_notion_class.return_value = mock_notion
                        
                        start_time = time.time()
                        
                        # Process corrections concurrently
                        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                            futures = []
                            for i, request in enumerate(complex_correction_requests):
                                future = executor.submit(
                                    process_correction,
                                    f'corr-test-{i}',
                                    request,
                                    'test@example.com'
                                )
                                futures.append(future)
                            
                            # Wait for all to complete
                            results = [future.result() for future in futures]
                        
                        end_time = time.time()
                        total_time = end_time - start_time
                        
                        # All should complete successfully
                        assert all(result['status'] == 'success' for result in results)
                        assert total_time < 30.0, f"Concurrent processing took {total_time}s, exceeded 30s limit"
    
    def test_memory_usage_under_load(self, large_task_list):
        """Test memory usage under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate heavy load
        agent = CorrectionAgent()
        
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
            
            # Process many requests
            for i in range(1000):
                agent.interpret_corrections(f"Change task {i} status to completed", large_task_list)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (adjust based on your requirements)
        assert memory_increase < 100.0, f"Memory increase {memory_increase}MB exceeded 100MB limit"
    
    def test_database_connection_pooling(self):
        """Test database connection pooling performance."""
        with patch('src.core.services.correction_service.create_engine') as mock_engine:
            mock_engine.return_value = Mock()
            
            service = CorrectionService()
            
            # Simulate multiple concurrent database operations
            def database_operation():
                with patch.object(service, '_get_session') as mock_session:
                    mock_session.return_value.__enter__.return_value = Mock()
                    
                    for i in range(10):
                        service.create_correction_log(
                            user_email=f'user{i}@example.com',
                            task_ids=[f'task-{j}' for j in range(5)],
                            email_subject=f'Test Email {i}'
                        )
            
            start_time = time.time()
            
            # Run multiple database operations concurrently
            threads = []
            for i in range(10):
                thread = threading.Thread(target=database_operation)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should handle concurrent database operations efficiently
            assert total_time < 15.0, f"Concurrent database operations took {total_time}s, exceeded 15s limit"
    
    def test_ai_response_caching(self):
        """Test AI response caching performance."""
        agent = CorrectionAgent()
        
        # Test with repeated requests
        task_ids = ['task-1', 'task-2', 'task-3']
        repeated_request = "Change task 1 status to completed"
        
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
            
            # First request
            start_time = time.time()
            result1 = agent.interpret_corrections(repeated_request, task_ids)
            first_request_time = time.time() - start_time
            
            # Second request (should be faster if caching is implemented)
            start_time = time.time()
            result2 = agent.interpret_corrections(repeated_request, task_ids)
            second_request_time = time.time() - start_time
            
            # Results should be identical
            assert result1['corrections'] == result2['corrections']
            
            # Second request should be faster (if caching is implemented)
            # Note: This test will pass even without caching, but it's good to have
            # for future optimization
            assert second_request_time <= first_request_time
    
    def test_error_recovery_performance(self):
        """Test error recovery performance."""
        with patch('src.core.services.correction_service.CorrectionService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_correction_log.side_effect = Exception("Database error")
            mock_service_class.return_value = mock_service
            
            start_time = time.time()
            
            # Process multiple requests with errors
            for i in range(100):
                result = process_correction(
                    f'corr-test-{i}',
                    'Change task 1 status to completed',
                    'test@example.com'
                )
                assert result['status'] == 'error'
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Error handling should be fast
            assert total_time < 10.0, f"Error handling took {total_time}s, exceeded 10s limit"
    
    def test_email_processing_throughput(self):
        """Test email processing throughput."""
        router = EmailRouter()
        
        # Generate batch of emails
        emails = []
        for i in range(1000):
            if i % 2 == 0:
                subject = f"Re: Your Daily Summary [Ref: corr-{uuid.uuid4()}]"
                body = f"Change task {i} status to completed"
            else:
                subject = f"Daily Update {i}"
                body = f"Completed task {i} today"
            
            emails.append((subject, body))
        
        start_time = time.time()
        
        # Process emails in batches
        batch_size = 100
        for i in range(0, len(emails), batch_size):
            batch = emails[i:i + batch_size]
            
            for subject, body in batch:
                email_type, correlation_id = router.classify_email(
                    Mock(), subject, body, 'test@example.com'
                )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate throughput
        throughput = len(emails) / total_time
        
        # Should process at least 100 emails per second
        assert throughput > 100.0, f"Throughput {throughput} emails/sec below 100 emails/sec threshold"


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 