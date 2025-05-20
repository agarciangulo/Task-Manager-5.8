"""
Test script to evaluate task similarity functionality using different methods.
"""
import json
from typing import List, Dict, Any
from datetime import datetime
import ast
import os
import sys

from core.task_similarity import check_task_similarity_ai

def load_test_tasks(test_file: str = None) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Load test cases with existing tasks and new tasks to test."""
    if test_file is None:
        test_file = os.path.join(os.path.dirname(__file__), "sample_inputs", "test_case_01_basic_similarity.txt")
    
    with open(test_file, 'r') as f:
        content = f.read()
        
    # Extract the Python dictionary definitions
    existing_tasks_str = content.split("existing_tasks = ")[1].split("## NEW TASKS TO TEST:")[0].strip()
    new_tasks_str = content.split("new_tasks = ")[1].strip()
    
    # Convert string representations
    existing_tasks = ast.literal_eval(existing_tasks_str)
    new_tasks = ast.literal_eval(new_tasks_str)
    
    return existing_tasks, new_tasks

def test_similarity_methods(new_task: Dict[str, Any], existing_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Test AI similarity method for a single task."""
    results = {
        "new_task": new_task["task"],
        "ai_results": check_task_similarity_ai(new_task, existing_tasks)
    }
    return results

def run_similarity_tests(test_file: str = None):
    """Run similarity tests for all new tasks against existing tasks."""
    # Load test data
    existing_tasks, new_tasks = load_test_tasks(test_file)
    
    print(f"\n🔍 Testing task similarity with AI method...")
    if test_file:
        print(f"Using test file: {test_file}")
    print("\n=== Test Results ===")
    
    all_results = []
    for new_task in new_tasks:
        print(f"\nTesting new task: {new_task['task']}")
        results = test_similarity_methods(new_task, existing_tasks)
        all_results.append(results)
        
        # Print results for this task
        print("\nAI Results:")
        print(f"Match found: {results['ai_results']['is_match']}")
        if results['ai_results']['is_match']:
            print(f"Matched task: {results['ai_results']['matched_task']['task']}")
            print(f"Confidence: {results['ai_results']['confidence']:.3f}")
            print(f"Explanation: {results['ai_results']['explanation']}")
        else:
            print(f"Confidence: {results['ai_results']['confidence']:.3f}")
            print(f"Explanation: {results['ai_results']['explanation']}")
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(os.path.dirname(__file__), "results", f"task_similarity_results_{timestamp}.json")
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n✅ Results saved to: {results_file}")

if __name__ == "__main__":
    test_file = sys.argv[1] if len(sys.argv) > 1 else None
    run_similarity_tests(test_file) 