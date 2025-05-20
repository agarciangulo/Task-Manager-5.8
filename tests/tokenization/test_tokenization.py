"""
Test suite for tokenization process of sensitive information.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any

from core.security.security_manager import SecurityManager

def load_test_inputs(test_file: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load test inputs from a file.
    
    Args:
        test_file: Path to the test file containing inputs
        
    Returns:
        Dict with 'inputs' key containing list of test cases
    """
    with open(test_file, 'r') as f:
        content = f.read()
    
    # Split content into sections
    sections = content.split('\n\n')
    inputs = []
    
    for section in sections:
        if section.strip():
            # Parse input details
            lines = section.strip().split('\n')
            input_data = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    input_data[key.strip()] = value.strip()
            
            if input_data:
                inputs.append(input_data)
    
    return {"inputs": inputs}

def test_tokenization(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test tokenization of input data.
    
    Args:
        input_data: Input data to tokenize
        
    Returns:
        Dict with tokenization results
    """
    try:
        # Initialize security manager
        security_manager = SecurityManager()
        
        # Test project name tokenization
        project_name = input_data.get('project_name', '')
        tokenized_project = security_manager.tokenize_project(project_name)
        
        # Test task data protection
        task_data = {
            'task': input_data.get('task', ''),
            'category': input_data.get('category', ''),
            'description': input_data.get('description', '')
        }
        protected_task = security_manager.protect_task_data(task_data)
        
        # Test text protection
        text = input_data.get('text', '')
        protected_text = security_manager.protect_text(text)
        
        # Test detokenization
        detokenized_project = security_manager.detokenize_project(tokenized_project)
        unprotected_task = security_manager.unprotect_task_data(protected_task)
        unprotected_text = security_manager.unprotect_text(protected_text)
        
        return {
            "input": input_data,
            "project_tokenization": {
                "original": project_name,
                "tokenized": tokenized_project,
                "detokenized": detokenized_project
            },
            "task_protection": {
                "original": task_data,
                "protected": protected_task,
                "unprotected": unprotected_task
            },
            "text_protection": {
                "original": text,
                "protected": protected_text,
                "unprotected": unprotected_text
            },
            "token_map": security_manager.token_map,
            "explanation": "Successfully tokenized and protected sensitive information"
        }
        
    except Exception as e:
        return {
            "input": input_data,
            "error": str(e),
            "explanation": f"Error during tokenization: {str(e)}"
        }

def run_tokenization_tests(test_file: str = None):
    """
    Run tokenization tests on inputs.
    
    Args:
        test_file: Path to test file (optional)
    """
    if not test_file:
        test_file = "tests/tokenization/sample_inputs/test_case_01_basic_tokenization.txt"
    
    print(f"\nUsing test file: {test_file}")
    
    # Load test inputs
    test_data = load_test_inputs(test_file)
    inputs = test_data.get("inputs", [])
    
    print("\n=== Test Results ===\n")
    
    results = []
    for input_data in inputs:
        print(f"\nTesting input: {input_data.get('project_name', 'No project name')}")
        
        # Test tokenization
        result = test_tokenization(input_data)
        results.append(result)
        
        print("\nTokenization Results:")
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print("\nProject Tokenization:")
            print(f"Original: {result['project_tokenization']['original']}")
            print(f"Tokenized: {result['project_tokenization']['tokenized']}")
            print(f"Detokenized: {result['project_tokenization']['detokenized']}")
            
            print("\nTask Protection:")
            print(f"Original: {result['task_protection']['original']}")
            print(f"Protected: {result['task_protection']['protected']}")
            print(f"Unprotected: {result['task_protection']['unprotected']}")
            
            print("\nText Protection:")
            print(f"Original: {result['text_protection']['original']}")
            print(f"Protected: {result['text_protection']['protected']}")
            print(f"Unprotected: {result['text_protection']['unprotected']}")
            
            print("\nToken Map:")
            for project, token in result['token_map'].items():
                print(f"{project} -> {token}")
        
        print(f"\nExplanation: {result['explanation']}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = "tests/tokenization/results"
    os.makedirs(results_dir, exist_ok=True)
    results_file = os.path.join(results_dir, f"tokenization_results_{timestamp}.json")
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved to: {results_file}")

if __name__ == "__main__":
    import sys
    test_file = sys.argv[1] if len(sys.argv) > 1 else None
    run_tokenization_tests(test_file) 