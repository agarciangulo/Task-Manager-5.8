#!/usr/bin/env python3
"""
Test script for hybrid task similarity approach.
Tests the combination of Chroma embeddings + AI analysis.
"""
import os
import sys
import time
import json
from datetime import datetime
from typing import List, Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.task_similarity import (
    check_task_similarity,
    check_task_similarity_mode,
    find_similar_tasks,
    check_task_similarity_ai
)

def load_test_tasks() -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Load test data with existing tasks and new tasks to test."""
    
    # Existing tasks (these would be in your database)
    existing_tasks = [
        {
            "task": "Implement user authentication system",
            "notes": "Create a secure authentication system with email verification and password reset functionality",
            "status": "In Progress",
            "employee": "John Smith",
            "date": "2024-03-15",
            "category": "Security"
        },
        {
            "task": "Set up CI/CD pipeline",
            "notes": "Configure automated testing and deployment pipeline using GitHub Actions",
            "status": "To Do",
            "employee": "Sarah Johnson",
            "date": "2024-03-14",
            "category": "DevOps"
        },
        {
            "task": "Optimize database queries",
            "notes": "Review and optimize slow database queries in the reporting module",
            "status": "In Progress",
            "employee": "Lisa Chen",
            "date": "2024-03-12",
            "category": "Performance"
        },
        {
            "task": "Update API documentation",
            "notes": "Update REST API documentation with new endpoints and examples",
            "status": "To Do",
            "employee": "Mike Wilson",
            "date": "2024-03-10",
            "category": "Documentation"
        },
        {
            "task": "Configure authentication",
            "notes": "Set up OAuth2 authentication for third-party integrations",
            "status": "In Progress",
            "employee": "John Smith",
            "date": "2024-03-08",
            "category": "Security"
        },
        {
            "task": "Create database backup script",
            "notes": "Develop automated backup script for production database",
            "status": "Completed",
            "employee": "Bob Johnson",
            "date": "2024-03-05",
            "category": "DevOps"
        },
        {
            "task": "Write technical documentation",
            "notes": "Create comprehensive technical documentation for the new system",
            "status": "To Do",
            "employee": "Alice Brown",
            "date": "2024-03-03",
            "category": "Documentation"
        },
        {
            "task": "Deploy application to production",
            "notes": "Deploy the latest version to production environment",
            "status": "In Progress",
            "employee": "Sarah Johnson",
            "date": "2024-03-01",
            "category": "DevOps"
        }
    ]
    
    # New tasks to test (these would be user input)
    new_tasks = [
        {
            "task": "need to build a login system with email verification",
            "expected_match": "Implement user authentication system"
        },
        {
            "task": "can someone help set up automated testing?",
            "expected_match": "Set up CI/CD pipeline"
        },
        {
            "task": "database is running slow, need to fix queries",
            "expected_match": "Optimize database queries"
        },
        {
            "task": "document our API endpoints",
            "expected_match": "Update API documentation"
        },
        {
            "task": "refactor the UI components",
            "expected_match": None  # Should not find a match
        },
        {
            "task": "set up OAuth for third party apps",
            "expected_match": "Configure authentication"
        },
        {
            "task": "create backup system for database",
            "expected_match": "Create database backup script"
        },
        {
            "task": "write system documentation",
            "expected_match": "Write technical documentation"
        }
    ]
    
    return existing_tasks, new_tasks

def test_similarity_methods(new_task: Dict[str, Any], existing_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Test all similarity methods for a single task."""
    
    task_text = new_task["task"]
    expected_match = new_task.get("expected_match")
    
    print(f"\n🔍 Testing: '{task_text}'")
    print(f"Expected match: {expected_match}")
    
    results = {
        "new_task": task_text,
        "expected_match": expected_match,
        "embedding_results": None,
        "ai_results": None,
        "hybrid_results": None,
        "default_results": None
    }
    
    # Test embedding-only method
    print("  📝 Testing embedding-only method...")
    start_time = time.time()
    try:
        embedding_result = find_similar_tasks({"task": task_text}, existing_tasks)
        embedding_time = time.time() - start_time
        results["embedding_results"] = {
            "result": embedding_result,
            "time": embedding_time
        }
        print(f"    ✅ Embedding: {embedding_result['is_match']} (confidence: {embedding_result['confidence']:.3f}) in {embedding_time:.3f}s")
    except Exception as e:
        print(f"    ❌ Embedding failed: {e}")
        results["embedding_results"] = {"error": str(e)}
    
    # Test AI-only method
    print("  📝 Testing AI-only method...")
    start_time = time.time()
    try:
        ai_result = check_task_similarity_ai({"task": task_text}, existing_tasks)
        ai_time = time.time() - start_time
        results["ai_results"] = {
            "result": ai_result,
            "time": ai_time
        }
        print(f"    ✅ AI: {ai_result['is_match']} (confidence: {ai_result['confidence']:.3f}) in {ai_time:.3f}s")
    except Exception as e:
        print(f"    ❌ AI failed: {e}")
        results["ai_results"] = {"error": str(e)}
    
    # Test hybrid method
    print("  📝 Testing hybrid method...")
    start_time = time.time()
    try:
        hybrid_result = check_task_similarity_mode({"task": task_text}, existing_tasks, mode='hybrid', top_k=5)
        hybrid_time = time.time() - start_time
        results["hybrid_results"] = {
            "result": hybrid_result,
            "time": hybrid_time
        }
        print(f"    ✅ Hybrid: {hybrid_result['is_match']} (confidence: {hybrid_result['confidence']:.3f}) in {hybrid_time:.3f}s")
    except Exception as e:
        print(f"    ❌ Hybrid failed: {e}")
        results["hybrid_results"] = {"error": str(e)}
    
    # Test default method (should use hybrid now)
    print("  📝 Testing default method...")
    start_time = time.time()
    try:
        default_result = check_task_similarity({"task": task_text}, existing_tasks)
        default_time = time.time() - start_time
        results["default_results"] = {
            "result": default_result,
            "time": default_time
        }
        print(f"    ✅ Default: {default_result['is_match']} (confidence: {default_result['confidence']:.3f}) in {default_time:.3f}s")
    except Exception as e:
        print(f"    ❌ Default failed: {e}")
        results["default_results"] = {"error": str(e)}
    
    # Check accuracy
    if expected_match:
        print("  📊 Accuracy check:")
        for method, data in results.items():
            if method.endswith("_results") and data and "result" in data:
                result = data["result"]
                if result.get("is_match"):
                    matched_task = result.get("matched_task", {}).get("task", "")
                    is_correct = expected_match in matched_task
                    status = "✅ CORRECT" if is_correct else "❌ WRONG"
                    print(f"    {method}: {status} (matched: '{matched_task}')")
                else:
                    print(f"    {method}: ❌ MISSED (should have matched '{expected_match}')")
    
    return results

def run_hybrid_tests():
    """Run comprehensive tests for the hybrid similarity approach."""
    print("🚀 Starting Hybrid Task Similarity Tests")
    print("=" * 60)
    
    # Load test data
    existing_tasks, new_tasks = load_test_tasks()
    
    print(f"📊 Test Setup:")
    print(f"  - Existing tasks: {len(existing_tasks)}")
    print(f"  - New tasks to test: {len(new_tasks)}")
    print(f"  - Expected matches: {sum(1 for t in new_tasks if t.get('expected_match'))}")
    
    # Run tests
    all_results = []
    total_tests = len(new_tasks)
    successful_tests = 0
    
    for i, new_task in enumerate(new_tasks, 1):
        print(f"\n{'='*50}")
        print(f"Test {i}/{total_tests}")
        
        try:
            results = test_similarity_methods(new_task, existing_tasks)
            all_results.append(results)
            successful_tests += 1
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")
            all_results.append({
                "new_task": new_task["task"],
                "error": str(e)
            })
    
    # Generate summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    print(f"✅ Successful tests: {successful_tests}/{total_tests}")
    
    # Calculate accuracy for each method
    methods = ["embedding_results", "ai_results", "hybrid_results", "default_results"]
    
    for method in methods:
        correct_matches = 0
        total_expected = 0
        avg_time = 0
        successful_method_tests = 0
        
        for result in all_results:
            if method in result and result[method] and "result" in result[method]:
                method_result = result[method]["result"]
                expected_match = result.get("expected_match")
                
                if expected_match:
                    total_expected += 1
                    if method_result.get("is_match"):
                        matched_task = method_result.get("matched_task", {}).get("task", "")
                        if expected_match in matched_task:
                            correct_matches += 1
                
                if "time" in result[method]:
                    avg_time += result[method]["time"]
                    successful_method_tests += 1
        
        accuracy = (correct_matches / total_expected * 100) if total_expected > 0 else 0
        avg_time = avg_time / successful_method_tests if successful_method_tests > 0 else 0
        
        print(f"\n{method.replace('_', ' ').title()}:")
        print(f"  Accuracy: {accuracy:.1f}% ({correct_matches}/{total_expected})")
        print(f"  Average time: {avg_time:.3f}s")
        print(f"  Successful tests: {successful_method_tests}/{total_tests}")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"hybrid_similarity_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    return all_results

if __name__ == "__main__":
    run_hybrid_tests() 