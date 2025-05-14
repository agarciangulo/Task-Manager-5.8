"""
Task similarity checking functionality using a hybrid approach of embeddings and AI.
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
from core.embedding_manager import EmbeddingManager
from core.ai.analyzers import TaskAnalyzer

_embedding_manager = EmbeddingManager()

def debug_print(message):
    """Print debug messages if DEBUG_MODE is True."""
    if DEBUG_MODE:
        print(message)

def find_similar_tasks(new_task: Dict[str, Any], existing_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Find similar tasks using embeddings.
    
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
        # First pass: Find potential matching tasks using embeddings
        all_texts = [new_task["task"]] + [t["task"] for t in existing_tasks]
        
        # Get embeddings for all tasks
        debug_print("Getting embeddings for tasks...")
        embeddings_dict = _embedding_manager.get_batch_embeddings(all_texts)
        
        if not embeddings_dict:
            debug_print("No embeddings generated")
            return {
                "is_match": False,
                "confidence": 0.0,
                "explanation": "Failed to generate embeddings"
            }
        
        # Get new task embedding
        new_task_embedding = np.array(embeddings_dict[new_task["task"]]).reshape(1, -1)
        
        # Compare with existing tasks
        max_similarity = 0.0
        most_similar_task = None
        
        for existing_task in existing_tasks:
            if existing_task["task"] not in embeddings_dict:
                debug_print(f"No embedding for task: {existing_task['task']}")
                continue
                
            existing_embedding = np.array(embeddings_dict[existing_task["task"]]).reshape(1, -1)
            similarity = np.dot(new_task_embedding, existing_embedding.T)[0][0]
            
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_task = existing_task
        
        # Check if we found a match
        if most_similar_task and max_similarity >= SIMILARITY_THRESHOLD:
            return {
                "is_match": True,
                "confidence": float(max_similarity),
                "matched_task": most_similar_task,
                "explanation": f"Found similar task with {max_similarity:.2f} similarity"
            }
        
        return {
            "is_match": False,
            "confidence": float(max_similarity) if most_similar_task else 0.0,
            "explanation": "No similar tasks found"
        }
        
    except Exception as e:
        debug_print(f"Error in find_similar_tasks: {e}")
        debug_print(traceback.format_exc())
        return {
            "is_match": False,
            "confidence": 0.0,
            "explanation": f"Error checking similarity: {str(e)}"
        }

def check_task_similarity_ai(new_task: Dict[str, Any], existing_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check task similarity using AI model.
    
    Args:
        new_task: The new task to check
        existing_tasks: List of existing tasks to check against
        
    Returns:
        Dict with similarity results
    """
    try:
        # Create prompt for the AI model
        prompt = f"""You are a task comparison expert. Your job is to compare tasks and determine if they are similar.

NEW TASK:
{new_task['task']}

EXISTING TASKS:
{chr(10).join([f"{i+1}. {task['task']}" for i, task in enumerate(existing_tasks)])}

INSTRUCTIONS:
1. Compare the new task with each existing task
2. For each comparison, determine:
   - Are they similar? (yes/no)
   - How confident are you? (0-1)
   - Why are they similar or different? (brief explanation)
3. Return your analysis in this exact format:
   TASK 1: [task text]
   SIMILAR: [yes/no]
   CONFIDENCE: [0-1]
   EXPLANATION: [your explanation]
   ---
   TASK 2: [task text]
   SIMILAR: [yes/no]
   CONFIDENCE: [0-1]
   EXPLANATION: [your explanation]
   ---
   [and so on for each task]"""

        # Use TaskAnalyzer to get AI response
        analyzer = TaskAnalyzer()
        response = analyzer.generate_text(prompt)
        
        # Parse the response
        try:
            # Split response into task analyses
            task_analyses = response.split('---')
            best_match = None
            max_confidence = 0.0
            
            for analysis in task_analyses:
                if not analysis.strip():
                    continue
                    
                # Parse each analysis
                lines = analysis.strip().split('\n')
                task_text = None
                is_similar = False
                confidence = 0.0
                explanation = ""
                
                for line in lines:
                    if line.startswith('TASK'):
                        task_text = line.split(':', 1)[1].strip()
                    elif line.startswith('SIMILAR'):
                        is_similar = line.split(':', 1)[1].strip().lower() == 'yes'
                    elif line.startswith('CONFIDENCE'):
                        try:
                            confidence = float(line.split(':', 1)[1].strip())
                        except ValueError:
                            confidence = 0.0
                    elif line.startswith('EXPLANATION'):
                        explanation = line.split(':', 1)[1].strip()
                
                if is_similar and confidence > max_confidence:
                    max_confidence = confidence
                    best_match = {
                        "task": task_text,
                        "confidence": confidence,
                        "explanation": explanation
                    }
            
            if best_match and max_confidence >= SIMILARITY_THRESHOLD:
                # Find the corresponding task
                matched_task = next(
                    (t for t in existing_tasks if t["task"] == best_match["task"]),
                    None
                )
                
                if matched_task:
                    return {
                        "is_match": True,
                        "confidence": float(max_confidence),
                        "matched_task": matched_task,
                        "explanation": best_match["explanation"]
                    }
            
            return {
                "is_match": False,
                "confidence": float(max_confidence) if best_match else 0.0,
                "explanation": "No similar tasks found"
            }
            
        except Exception as e:
            debug_print(f"Failed to parse AI response: {e}")
            return {
                "is_match": False,
                "confidence": 0.0,
                "explanation": "Error parsing AI response"
            }
            
    except Exception as e:
        debug_print(f"Error in check_task_similarity_ai: {e}")
        debug_print(traceback.format_exc())
        return {
            "is_match": False,
            "confidence": 0.0,
            "explanation": f"Error in AI comparison: {str(e)}"
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
        debug_print("Using embedding-based task similarity check")
        return find_similar_tasks(new_task, existing_tasks)

def find_top_k_similar_tasks(new_task: Dict[str, Any], existing_tasks: List[Dict[str, Any]], k: int = 5) -> List[Dict[str, Any]]:
    """
    Find the top-k most similar tasks using embeddings.
    Returns a list of dicts with 'task' and 'similarity'.
    """
    if not new_task or not existing_tasks:
        return []
    try:
        all_texts = [new_task["task"]] + [t["task"] for t in existing_tasks]
        embeddings_dict = _embedding_manager.get_batch_embeddings(all_texts)
        if not embeddings_dict:
            return []
        new_task_embedding = np.array(embeddings_dict[new_task["task"]]).reshape(1, -1)
        similarities = []
        for existing_task in existing_tasks:
            if existing_task["task"] not in embeddings_dict:
                continue
            existing_embedding = np.array(embeddings_dict[existing_task["task"]]).reshape(1, -1)
            similarity = float(np.dot(new_task_embedding, existing_embedding.T)[0][0])
            similarities.append({
                "task": existing_task,
                "similarity": similarity
            })
        # Sort by similarity descending and return top k
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:k]
    except Exception as e:
        debug_print(f"Error in find_top_k_similar_tasks: {e}")
        debug_print(traceback.format_exc())
        return []

def check_task_similarity_mode(new_task: Dict[str, Any], existing_tasks: List[Dict[str, Any]], mode: str = 'embedding', top_k: int = 5) -> Dict[str, Any]:
    """
    Flexible similarity checker: 'embedding', 'ai', or 'hybrid'.
    - 'embedding': embedding-only
    - 'ai': LLM-only (all tasks)
    - 'hybrid': embeddings for top_k, then LLM for those
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
        # 1. Get top_k candidates by embedding
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