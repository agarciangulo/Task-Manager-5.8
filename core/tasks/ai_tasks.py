"""
Asynchronous AI tasks for Task Manager.
Handles AI operations without blocking the main application.
"""
import traceback
from typing import Dict, List, Any, Optional
from celery import current_task
from celery_config import celery_app
from core.gemini_client import client as gemini_client
from core.openai_client import client as openai_client
from core.ai.insights import get_coaching_insight, get_project_insight
from core.logging_config import get_logger
from config import AI_PROVIDER

logger = get_logger(__name__)

@celery_app.task(bind=True, name='core.tasks.ai_tasks.generate_content_async')
def generate_content_async(self, prompt: str, **kwargs) -> Dict[str, Any]:
    """
    Asynchronously generate content using AI.
    
    Args:
        prompt: The text prompt to send to the AI
        **kwargs: Additional parameters for the API call
        
    Returns:
        Dict with success status and generated content/error
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Preparing AI request...'}
        )
        
        # Select appropriate client
        if AI_PROVIDER == 'gemini':
            client = gemini_client
        elif AI_PROVIDER == 'openai':
            client = openai_client
        else:
            raise ValueError(f"Unsupported AI provider: {AI_PROVIDER}")
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 25, 'total': 100, 'status': 'Generating content...'}
        )
        
        # Generate content
        if AI_PROVIDER == 'gemini':
            response = client.generate_content(prompt, **kwargs)
        else:
            response = client.chat_completions_create(
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            response = response['choices'][0]['message']['content']
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Content generated successfully'}
        )
        
        logger.info(f"Successfully generated content using {AI_PROVIDER}")
        
        return {
            'success': True,
            'content': response,
            'provider': AI_PROVIDER,
            'prompt_length': len(prompt)
        }
        
    except Exception as e:
        logger.error(f"Error generating content with {AI_PROVIDER}: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'provider': AI_PROVIDER,
            'prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt
        }

@celery_app.task(bind=True, name='core.tasks.ai_tasks.create_embeddings_async')
def create_embeddings_async(self, texts: List[str]) -> Dict[str, Any]:
    """
    Asynchronously create embeddings for a list of texts.
    
    Args:
        texts: List of texts to create embeddings for
        
    Returns:
        Dict with success status and embeddings/error
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Preparing embeddings...'}
        )
        
        # Select appropriate client
        if AI_PROVIDER == 'gemini':
            client = gemini_client
        elif AI_PROVIDER == 'openai':
            client = openai_client
        else:
            raise ValueError(f"Unsupported AI provider: {AI_PROVIDER}")
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 25, 'total': 100, 'status': 'Creating embeddings...'}
        )
        
        # Create embeddings
        if AI_PROVIDER == 'gemini':
            embeddings = client.embeddings_create_batch(texts)
        else:
            # For OpenAI, we need to create embeddings one by one
            embeddings = []
            for i, text in enumerate(texts):
                progress = 25 + int((i / len(texts)) * 75)
                self.update_state(
                    state='PROGRESS',
                    meta={'current': progress, 'total': 100, 'status': f'Creating embedding {i+1}/{len(texts)}...'}
                )
                
                embedding = client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=text
                )
                embeddings.append(embedding.data[0].embedding)
        
        logger.info(f"Successfully created {len(embeddings)} embeddings using {AI_PROVIDER}")
        
        return {
            'success': True,
            'embeddings': embeddings,
            'count': len(embeddings),
            'provider': AI_PROVIDER
        }
        
    except Exception as e:
        logger.error(f"Error creating embeddings with {AI_PROVIDER}: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'provider': AI_PROVIDER,
            'text_count': len(texts)
        }

@celery_app.task(bind=True, name='core.tasks.ai_tasks.batch_api_requests_async')
def batch_api_requests_async(self, prompts: List[str], **kwargs) -> Dict[str, Any]:
    """
    Asynchronously process multiple prompts in batch.
    
    Args:
        prompts: List of prompt strings
        **kwargs: Additional parameters for the API calls
        
    Returns:
        Dict with success status and results/error
    """
    try:
        # Select appropriate client
        if AI_PROVIDER == 'gemini':
            client = gemini_client
        elif AI_PROVIDER == 'openai':
            client = openai_client
        else:
            raise ValueError(f"Unsupported AI provider: {AI_PROVIDER}")
        
        results = []
        
        for i, prompt in enumerate(prompts):
            # Update progress
            progress = int((i / len(prompts)) * 100)
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': progress,
                    'total': 100,
                    'status': f'Processing prompt {i+1}/{len(prompts)}...'
                }
            )
            
            try:
                if AI_PROVIDER == 'gemini':
                    response = client.generate_content(prompt, **kwargs)
                else:
                    response = client.chat_completions_create(
                        messages=[{"role": "user", "content": prompt}],
                        **kwargs
                    )
                    response = response['choices'][0]['message']['content']
                
                results.append({
                    'prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt,
                    'success': True,
                    'response': response
                })
                
            except Exception as e:
                results.append({
                    'prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt,
                    'success': False,
                    'error': str(e)
                })
        
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        logger.info(f"Batch API requests completed: {successful} successful, {failed} failed")
        
        return {
            'success': True,
            'results': results,
            'summary': {
                'total': len(prompts),
                'successful': successful,
                'failed': failed
            },
            'provider': AI_PROVIDER
        }
        
    except Exception as e:
        logger.error(f"Error in batch API requests with {AI_PROVIDER}: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'provider': AI_PROVIDER,
            'prompt_count': len(prompts)
        }

@celery_app.task(bind=True, name='core.tasks.ai_tasks.generate_coaching_insight_async')
def generate_coaching_insight_async(self, person_name: str, tasks: List[Dict], 
                                  recent_tasks: List[Dict], peer_feedback: List[Dict]) -> Dict[str, Any]:
    """
    Asynchronously generate coaching insights.
    
    Args:
        person_name: Name of the person
        tasks: List of current tasks
        recent_tasks: List of recent tasks
        peer_feedback: List of peer feedback
        
    Returns:
        Dict with success status and insights/error
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Analyzing tasks...'}
        )
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'Generating insights...'}
        )
        
        insights = get_coaching_insight(person_name, tasks, recent_tasks, peer_feedback)
        
        logger.info(f"Successfully generated coaching insights for {person_name}")
        
        return {
            'success': True,
            'insights': insights,
            'person_name': person_name,
            'task_count': len(tasks),
            'recent_task_count': len(recent_tasks),
            'feedback_count': len(peer_feedback)
        }
        
    except Exception as e:
        logger.error(f"Error generating coaching insights for {person_name}: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'person_name': person_name,
            'task_count': len(tasks)
        }

@celery_app.task(bind=True, name='core.tasks.ai_tasks.generate_project_insight_async')
def generate_project_insight_async(self, selected_category: str, filtered_tasks: List[Dict]) -> Dict[str, Any]:
    """
    Asynchronously generate project insights.
    
    Args:
        selected_category: The project category
        filtered_tasks: List of tasks for the project
        
    Returns:
        Dict with success status and insights/error
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Analyzing project...'}
        )
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'Generating project insights...'}
        )
        
        insights = get_project_insight(selected_category, filtered_tasks)
        
        logger.info(f"Successfully generated project insights for {selected_category}")
        
        return {
            'success': True,
            'insights': insights,
            'category': selected_category,
            'task_count': len(filtered_tasks)
        }
        
    except Exception as e:
        logger.error(f"Error generating project insights for {selected_category}: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'category': selected_category,
            'task_count': len(filtered_tasks)
        }

@celery_app.task(bind=True, name='core.tasks.ai_tasks.extract_tasks_async')
def extract_tasks_async(self, update_text: str) -> Dict[str, Any]:
    """
    Asynchronously extract tasks from update text.
    
    Args:
        update_text: Text containing task updates
        
    Returns:
        Dict with success status and extracted tasks/error
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Analyzing text...'}
        )
        
        from core.task_extractor import extract_tasks_from_update
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'Extracting tasks...'}
        )
        
        tasks = extract_tasks_from_update(update_text)
        
        logger.info(f"Successfully extracted {len(tasks)} tasks from text")
        
        return {
            'success': True,
            'tasks': tasks,
            'count': len(tasks),
            'text_length': len(update_text)
        }
        
    except Exception as e:
        logger.error(f"Error extracting tasks from text: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'text_length': len(update_text)
        } 