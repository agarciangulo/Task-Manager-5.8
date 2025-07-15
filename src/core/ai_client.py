"""
Unified AI client that handles API calls to OpenAI or Gemini for AI-based task matching.
"""
import os
import logging
from typing import List, Dict, Any, Optional

from src.config.settings import (
    AI_PROVIDER,
    GEMINI_API_KEY,
    OPENAI_API_KEY,
    CHAT_MODEL,
    DEBUG_MODE
)

logger = logging.getLogger(__name__)

def debug_print(message):
    """Print debug messages if DEBUG_MODE is True."""
    if DEBUG_MODE:
        print(message)

def call_ai_api(prompt: str, **kwargs) -> str:
    """
    Call an AI API (OpenAI or Gemini) to process the prompt.
    
    Args:
        prompt: The text prompt to send to the AI
        **kwargs: Additional parameters for the API call
        
    Returns:
        The AI response as a string
    """
    try:
        if AI_PROVIDER == 'openai':
            return call_openai_api(prompt, **kwargs)
        elif AI_PROVIDER == 'gemini':
            return call_gemini_api(prompt, **kwargs)
        else:
            raise ValueError(f"Unsupported AI provider: {AI_PROVIDER}")
    except Exception as e:
        logger.error(f"Error calling AI API: {str(e)}")
        return f"Error: {str(e)}"

def call_openai_api(prompt: str, **kwargs) -> str:
    """Call OpenAI API to process the prompt."""
    try:
        from src.core.openai_client import client
        
        if not client:
            return "OpenAI client not available"
        
        response = client.chat_completions_create(
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        
        return response['choices'][0]['message']['content']
        
    except ImportError:
        return "OpenAI client not available"
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return f"OpenAI API error: {str(e)}"

def call_gemini_api(prompt: str, **kwargs) -> str:
    """Call Gemini API to process the prompt."""
    try:
        from src.core.gemini_client import client
        
        if not client:
            return "Gemini client not available"
        
        response = client.chat_completions_create(
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        
        return response['choices'][0]['message']['content']
        
    except ImportError:
        return "Gemini client not available"
    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        return f"Gemini API error: {str(e)}"

def get_ai_client():
    """Get the appropriate AI client based on the configured provider."""
    if AI_PROVIDER == 'openai':
        try:
            from src.core.openai_client import client
            return client
        except ImportError:
            return None
    elif AI_PROVIDER == 'gemini':
        try:
            from src.core.gemini_client import client
            return client
        except ImportError:
            return None
    else:
        return None

def get_embedding(text: str) -> List[float]:
    """Get embedding for a text using the configured AI provider."""
    if AI_PROVIDER == 'openai':
        try:
            from src.core.openai_client import get_cached_embedding
            return get_cached_embedding(text)
        except ImportError:
            return [0.0] * 1000
    elif AI_PROVIDER == 'gemini':
        try:
            from src.core.gemini_client import get_cached_embedding
            return get_cached_embedding(text)
        except ImportError:
            return [0.0] * 1000
    else:
        return [0.0] * 1000

def get_batch_embeddings(texts: List[str], force_refresh: bool = False) -> List[List[float]]:
    """Get embeddings for multiple texts using the configured AI provider."""
    if AI_PROVIDER == 'openai':
        try:
            from src.core.openai_client import get_batch_embeddings
            return get_batch_embeddings(texts, force_refresh)
        except ImportError:
            return [[0.0] * 1000] * len(texts)
    elif AI_PROVIDER == 'gemini':
        try:
            from src.core.gemini_client import get_batch_embeddings
            return get_batch_embeddings(texts, force_refresh)
        except ImportError:
            return [[0.0] * 1000] * len(texts)
    else:
        return [[0.0] * 1000] * len(texts)

def get_coaching_insight(person_name: str, tasks: List[str], recent_tasks: List[str], peer_feedback: str) -> str:
    """Get coaching insights using the configured AI provider."""
    if AI_PROVIDER == 'openai':
        try:
            from src.core.openai_client import get_coaching_insight
            return get_coaching_insight(person_name, tasks, recent_tasks, peer_feedback)
        except ImportError:
            return "OpenAI client not available"
    elif AI_PROVIDER == 'gemini':
        try:
            from src.core.gemini_client import get_coaching_insight
            return get_coaching_insight(person_name, tasks, recent_tasks, peer_feedback)
        except ImportError:
            return "Gemini client not available"
    else:
        return f"Unsupported AI provider: {AI_PROVIDER}"

def get_project_insight(selected_category: str, filtered_tasks: List[str]) -> str:
    """Get project insights using the configured AI provider."""
    if AI_PROVIDER == 'openai':
        try:
            from src.core.openai_client import get_project_insight
            return get_project_insight(selected_category, filtered_tasks)
        except ImportError:
            return "OpenAI client not available"
    elif AI_PROVIDER == 'gemini':
        try:
            from src.core.gemini_client import get_project_insight
            return get_project_insight(selected_category, filtered_tasks)
        except ImportError:
            return "Gemini client not available"
    else:
        return f"Unsupported AI provider: {AI_PROVIDER}"