"""
Test suite for verifying if tasks need additional context or information.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any

from core.task_extractor import extract_tasks_from_update

def load_test_tasks(test_file: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load test tasks from a file.
    
    Args:
        test_file: Path to the test file containing tasks
        
    Returns:
        Dict with 'tasks' key containing list of tasks
    """
    with open(test_file, 'r') as f:
        content = f.read()
    
    # Split content into sections
    sections = content.split('\n\n')
    tasks = []
    
    for section in sections:
        if section.strip():
            # Parse task details
            lines = section.strip().split('\n')
            task = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    task[key.strip()] = value.strip()
            
            if task:
                tasks.append(task)
    
    return {"tasks": tasks}

def test_context_verification(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test if a task needs more context/information.
    
    Args:
        task: Task to verify
        
    Returns:
        Dict with verification results
    """
    try:
        # Convert task to text format for extraction
        task_text = f"Task: {task.get('task', '')}\n"
        if task.get('description'):
            task_text += f"Description: {task['description']}\n"
        if task.get('employee'):
            task_text += f"Employee: {task['employee']}\n"
        if task.get('date'):
            task_text += f"Date: {task['date']}\n"
        if task.get('category'):
            task_text += f"Category: {task['category']}\n"
        if task.get('status'):
            task_text += f"Status: {task['status']}\n"
        
        # Extract tasks using the existing functionality
        extracted_tasks = extract_tasks_from_update(task_text)
        
        if not extracted_tasks:
            return {
                "task": task,
                "error": "No tasks extracted",
                "needs_context": False,
                "missing_fields": [],
                "suggestions": [],
                "confidence": 0.0,
                "explanation": "Failed to extract task"
            }
        
        # Get the first extracted task (since we only input one)
        extracted_task = extracted_tasks[0]
        
        return {
            "task": task,
            "needs_context": extracted_task.get("needs_description", False),
            "missing_fields": ["description"] if extracted_task.get("needs_description") else [],
            "suggestions": [extracted_task.get("suggested_question", "")] if extracted_task.get("needs_description") else [],
            "confidence": 1.0 if not extracted_task.get("needs_description") else 0.0,
            "explanation": "Task needs more context" if extracted_task.get("needs_description") else "Task has sufficient context"
        }
        
    except Exception as e:
        return {
            "task": task,
            "error": str(e),
            "needs_context": False,
            "missing_fields": [],
            "suggestions": [],
            "confidence": 0.0,
            "explanation": f"Error during verification: {str(e)}"
        }

def run_context_verification_tests(test_file: str = None):
    """
    Run context verification tests on tasks.
    
    Args:
        test_file: Path to test file (optional)
    """
    if not test_file:
        test_file = "tests/task_context_verification/sample_inputs/test_case_01_basic_context.txt"
    
    print(f"\nUsing test file: {test_file}")
    
    # Load test tasks
    test_data = load_test_tasks(test_file)
    tasks = test_data.get("tasks", [])
    
    print("\n=== Test Results ===\n")
    
    results = []
    for task in tasks:
        print(f"\nTesting task: {task.get('task', 'No task description')}")
        
        # Test context verification
        result = test_context_verification(task)
        results.append(result)
        
        print("\nContext Verification Results:")
        print(f"Needs more context: {result['needs_context']}")
        if result['needs_context']:
            print(f"Missing fields: {', '.join(result['missing_fields'])}")
            print(f"Suggestions: {', '.join(result['suggestions'])}")
        print(f"Confidence: {result['confidence']}")
        print(f"Explanation: {result['explanation']}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = "tests/task_context_verification/results"
    os.makedirs(results_dir, exist_ok=True)
    results_file = os.path.join(results_dir, f"context_verification_results_{timestamp}.json")
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved to: {results_file}")

if __name__ == "__main__":
    import sys
    test_file = sys.argv[1] if len(sys.argv) > 1 else None
    run_context_verification_tests(test_file) 