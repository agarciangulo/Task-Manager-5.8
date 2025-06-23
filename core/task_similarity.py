"""
Task similarity checking functionality using simplified Chroma-based embeddings and AI.
"""
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import traceback

from config import (
    SIMILARITY_THRESHOLD,
    DEBUG_MODE,
    MIN_TASK_LENGTH,
    USE_AI_MATCHING
)
from core.chroma_embedding_manager_simple import SimpleChromaEmbeddingManager
from core.ai.analyzers import TaskAnalyzer

# Initialize simplified Chroma-based embedding manager
_chroma_manager = SimpleChromaEmbeddingManager()

def debug_print(message):
    """Print debug messages if DEBUG_MODE is True."""
    if DEBUG_MODE:
        print(message)

def find_similar_tasks(new_task: Dict[str, Any], existing_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Find similar tasks using Chroma-based embeddings.
    
    Args:
        new_task: The new task to check
        existing_tasks: List of existing tasks to check against
        
    Returns:
        Dict with similarity results
    """
    if not new_task or not existing_tasks:
        return {
            "is_match": False,
            "confidence": 0.0,
            "explanation": "No tasks to compare"
        }
    
    try:
        debug_print("Using Chroma-based similarity search...")
        
        # Use Chroma manager to find similar tasks
        similar_tasks = _chroma_manager.find_similar_tasks(
            new_task=new_task,
            existing_tasks=existing_tasks,
            top_k=5,
            threshold=SIMILARITY_THRESHOLD
        )
        
        if not similar_tasks:
            return {
                "is_match": False,
                "confidence": 0.0,
                "explanation": "No similar tasks found"
            }
        
        # Get the most similar task
        best_match = similar_tasks[0]
        confidence = best_match["similarity"]
        
        debug_print(f"Found similar task with confidence: {confidence:.3f}")
        
        return {
            "is_match": True,
            "confidence": confidence,
            "matched_task": best_match["task"],
            "explanation": f"Found similar task: '{best_match['task']['task']}' with {confidence:.1%} similarity"
        }
        
    except Exception as e:
        debug_print(f"Error in Chroma similarity search: {e}")
        debug_print(traceback.format_exc())
        return {
            "is_match": False,
            "confidence": 0.0,
            "explanation": f"Error in similarity search: {str(e)}"
        }

def check_task_similarity_ai(new_task: Dict[str, Any], existing_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check task similarity using AI analysis.
    
    Args:
        new_task: The new task to check
        existing_tasks: List of existing tasks to check against
        
    Returns:
        Dict with similarity results
    """
    if not new_task or not existing_tasks:
        return {
            "is_match": False,
            "confidence": 0.0,
            "explanation": "No tasks to compare"
        }
    
    try:
        analyzer = TaskAnalyzer()
        
        # Convert tasks to the format expected by the analyzer
        formatted_existing_tasks = []
        for task in existing_tasks:
            formatted_task = {
                "task": task.get("task", ""),
                "description": task.get("notes", ""),
                "status": task.get("status", ""),
                "employee": task.get("employee", ""),
                "date": task.get("date", ""),
                "category": task.get("category", "")
            }
            formatted_existing_tasks.append(formatted_task)
        
        # Analyze similarity
        result = analyzer.analyze_task_similarity(
            new_task=new_task,
            existing_tasks=formatted_existing_tasks
        )
        
        return result
        
    except Exception as e:
        debug_print(f"Error in AI similarity check: {e}")
        debug_print(traceback.format_exc())
        return {
            "is_match": False,
            "confidence": 0.0,
            "explanation": f"Error in AI analysis: {str(e)}"
        }

def check_task_similarity(new_task: Dict[str, Any], existing_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check if a new task is similar to any existing tasks.
    
    Args:
        new_task: The new task to check
        existing_tasks: List of existing tasks to check against
        
    Returns:
        Dict with similarity results
    """
    if not new_task or not new_task.get("task"):
        return {
            "is_match": False,
            "confidence": 0.0,
            "explanation": "Invalid task"
        }
    
    # Choose method based on configuration
    if USE_AI_MATCHING:
        debug_print("Using AI-based task similarity check")
        return check_task_similarity_ai(new_task, existing_tasks)
    else:
        debug_print("Using Chroma-based task similarity check")
        return find_similar_tasks(new_task, existing_tasks)

def find_top_k_similar_tasks(new_task: Dict[str, Any], existing_tasks: List[Dict[str, Any]], k: int = 5) -> List[Dict[str, Any]]:
    """
    Find the top-k most similar tasks using Chroma-based embeddings.
    Returns a list of dicts with 'task' and 'similarity'.
    """
    if not new_task or not existing_tasks:
        return []
    
    try:
        # Use Chroma manager to find top-k similar tasks
        similar_tasks = _chroma_manager.find_similar_tasks(
            new_task=new_task,
            existing_tasks=existing_tasks,
            top_k=k,
            threshold=0.0  # No threshold for top-k search
        )
        
        # Format results
        results = []
        for item in similar_tasks:
            results.append({
                "task": item["task"],
                "similarity": item["similarity"]
            })
        
        return results
        
    except Exception as e:
        debug_print(f"Error in find_top_k_similar_tasks: {e}")
        debug_print(traceback.format_exc())
        return []

def check_task_similarity_mode(new_task: Dict[str, Any], existing_tasks: List[Dict[str, Any]], mode: str = 'embedding', top_k: int = 5) -> Dict[str, Any]:
    """
    Flexible similarity checker: 'embedding', 'ai', or 'hybrid'.
    - 'embedding': Chroma-based embedding search
    - 'ai': LLM-only (all tasks)
    - 'hybrid': Chroma embeddings for top_k, then LLM for those
    """
    if not new_task or not new_task.get("task"):
        return {
            "is_match": False,
            "confidence": 0.0,
            "explanation": "Invalid task"
        }
    
    if mode == 'embedding':
        return find_similar_tasks(new_task, existing_tasks)
    elif mode == 'ai':
        return check_task_similarity_ai(new_task, existing_tasks)
    elif mode == 'hybrid':
        # 1. Get top_k candidates by Chroma embedding
        top_candidates = find_top_k_similar_tasks(new_task, existing_tasks, k=top_k)
        candidate_tasks = [c['task'] for c in top_candidates]
        # 2. Use LLM to compare only those
        return check_task_similarity_ai(new_task, candidate_tasks)
    else:
        return {
            "is_match": False,
            "confidence": 0.0,
            "explanation": f"Unknown mode: {mode}"
        }

def get_chroma_stats() -> Dict[str, Any]:
    """Get statistics about the Chroma embedding collection."""
    try:
        return _chroma_manager.get_collection_stats()
    except Exception as e:
        debug_print(f"Error getting Chroma stats: {e}")
        return {}

def migrate_old_embeddings(old_embeddings: Dict[str, Any]):
    """Migrate embeddings from old cache to Chroma."""
    try:
        _chroma_manager.migrate_from_old_cache(old_embeddings)
    except Exception as e:
        debug_print(f"Error migrating old embeddings: {e}") 