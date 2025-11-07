"""
Test script to evaluate OpenAI embeddings on real tasks with freeform text input.
"""
import time
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Tuple

from src.core.embedding_manager import EmbeddingManager

_embedding_manager = EmbeddingManager()

def load_test_tasks() -> Tuple[List[str], List[Dict[str, Any]]]:
    """Load test cases with freeform text input and existing tasks."""
    # Freeform text inputs that a user might type
    test_inputs = [
        "need to schedule a team sync for next week",
        "can someone help me set up our daily standup meeting?",
        "working on the quarterly numbers and performance metrics",
        "have to finish writing up the Q1 results by friday",
        "looking for someone to review my PR for the new feature",
        "documentation needs updating for the API changes",
        "need to organize a meeting with the design team about the new UI",
        "working on performance improvements for the database queries"
    ]
    
    # Existing tasks in the system
    existing_tasks = [
        {
            "task": "Schedule weekly team sync meeting to discuss project progress",
            "description": "Set up a recurring meeting for the team to sync on project status, blockers, and next steps.",
            "status": "To Do",
            "category": "Meetings"
        },
        {
            "task": "Implement daily standup automation in Slack",
            "description": "Create a bot to automate daily standup updates and reminders in our team Slack channel.",
            "status": "In Progress",
            "category": "Process Improvement"
        },
        {
            "task": "Prepare Q1 2024 performance report",
            "description": "Compile and analyze team performance metrics, including velocity, quality metrics, and OKR progress.",
            "status": "In Progress",
            "category": "Reports"
        },
        {
            "task": "Review and merge feature branches",
            "description": "Review pending pull requests for the new features, provide feedback, and merge approved changes.",
            "status": "To Do",
            "category": "Code Review"
        },
        {
            "task": "Update API documentation",
            "description": "Update technical documentation to reflect recent API changes and new endpoints.",
            "status": "To Do",
            "category": "Documentation"
        },
        {
            "task": "UI/UX design review meeting",
            "description": "Meet with design team to review and finalize new UI components and design system updates.",
            "status": "Scheduled",
            "category": "Design"
        },
        {
            "task": "Database performance optimization",
            "description": "Identify and implement optimizations for slow-performing database queries.",
            "status": "In Progress",
            "category": "Engineering"
        }
    ]
    
    return test_inputs, existing_tasks

def test_embedding_quality(test_inputs: List[str], existing_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Test embedding quality by checking if similar tasks are correctly matched."""
    results = []
    
    # Get embeddings for all texts
    # For existing tasks, we'll combine task and description for better matching
    existing_texts = [
        f"{task['task']}. {task['description']}"
        for task in existing_tasks
    ]
    
    test_embeddings = _embedding_manager.get_batch_embeddings(test_inputs)
    existing_embeddings = _embedding_manager.get_batch_embeddings(existing_texts)
    
    # Calculate similarities
    for test_input, test_text in zip(test_inputs, test_inputs):  # Using input as both identifier and text
        test_embedding = test_embeddings[test_text]
        similarities = []
        
        for existing_task, existing_text in zip(existing_tasks, existing_texts):
            existing_embedding = existing_embeddings[existing_text]
            similarity = float(cosine_similarity([test_embedding], [existing_embedding])[0][0])
            similarities.append({
                "task": existing_task,
                "similarity": similarity
            })
        
        # Sort by similarity
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Record results
        result = {
            "input": test_input,
            "matches": [
                {
                    "task": match["task"]["task"],
                    "description": match["task"]["description"],
                    "similarity": match["similarity"]
                }
                for match in similarities[:3]  # Only show top 3 matches
            ]
        }
        results.append(result)
    
    return results

def test_embedding_performance(texts: List[str], num_runs: int = 3) -> Dict[str, float]:
    """Test embedding generation performance."""
    times = []
    
    for _ in range(num_runs):
        start_time = time.time()
        _embedding_manager.get_batch_embeddings(texts)
        end_time = time.time()
        times.append(end_time - start_time)
    
    return {
        "avg_time": sum(times) / len(times),
        "min_time": min(times),
        "max_time": max(times)
    }

def main():
    # Load test data
    test_inputs, existing_tasks = load_test_tasks()
    
    print("🔍 Testing embedding quality with freeform input...")
    print("\n=== Quality Test Results ===")
    
    results = test_embedding_quality(test_inputs, existing_tasks)
    for result in results:
        print(f"\nUser input: {result['input']}")
        print("Top matches:")
        for i, match in enumerate(result["matches"], 1):
            print(f"  {i}. {match['task']}")
            print(f"     Description: {match['description']}")
            print(f"     Similarity: {match['similarity']:.3f}")
    
    print("\n⚡ Testing embedding performance...")
    print("\n=== Performance Test Results ===")
    
    # Test performance with both inputs and full task texts
    all_texts = test_inputs + [
        f"{task['task']}. {task['description']}"
        for task in existing_tasks
    ]
    perf_results = test_embedding_performance(all_texts)
    
    print(f"Average time: {perf_results['avg_time']:.3f}s")
    print(f"Min time: {perf_results['min_time']:.3f}s")
    print(f"Max time: {perf_results['max_time']:.3f}s")

if __name__ == "__main__":
    main() 