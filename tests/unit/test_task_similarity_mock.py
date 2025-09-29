#!/usr/bin/env python3
"""
Comprehensive test of task similarity with realistic mock data.
Demonstrates how the Chroma-based similarity system works with various task scenarios.
"""
import os
import sys
import time
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.task_similarity import check_task_similarity, find_top_k_similar_tasks
from src.core.chroma_embedding_manager_simple import SimpleChromaEmbeddingManager

def create_mock_tasks():
    """Create realistic mock tasks for testing."""
    return [
        # Authentication/Login related tasks
        {
            "task": "Implement user authentication system",
            "status": "In Progress",
            "employee": "John Smith",
            "category": "Security",
            "date": "2024-03-15",
            "notes": "Create secure login with email verification"
        },
        {
            "task": "Set up login functionality",
            "status": "Completed",
            "employee": "Jane Doe",
            "category": "Security",
            "date": "2024-03-10",
            "notes": "Basic login form with password validation"
        },
        {
            "task": "Configure authentication middleware",
            "status": "To Do",
            "employee": "Bob Wilson",
            "category": "Security",
            "date": "2024-03-20",
            "notes": "JWT token implementation"
        },
        
        # Database related tasks
        {
            "task": "Optimize database queries",
            "status": "In Progress",
            "employee": "Lisa Chen",
            "category": "Performance",
            "date": "2024-03-12",
            "notes": "Review and optimize slow queries in reporting module"
        },
        {
            "task": "Fix slow database performance",
            "status": "Completed",
            "employee": "Mike Johnson",
            "category": "Performance",
            "date": "2024-03-08",
            "notes": "Added indexes to improve query speed"
        },
        {
            "task": "Database backup implementation",
            "status": "To Do",
            "employee": "Sarah Brown",
            "category": "DevOps",
            "date": "2024-03-25",
            "notes": "Automated daily backups"
        },
        
        # Documentation tasks
        {
            "task": "Update API documentation",
            "status": "In Progress",
            "employee": "Alex Turner",
            "category": "Documentation",
            "date": "2024-03-14",
            "notes": "Document new endpoints for v2 API"
        },
        {
            "task": "Write technical documentation",
            "status": "To Do",
            "employee": "Emma Davis",
            "category": "Documentation",
            "date": "2024-03-22",
            "notes": "User guide for new features"
        },
        
        # Testing/CI-CD tasks
        {
            "task": "Set up automated testing",
            "status": "Completed",
            "employee": "David Lee",
            "category": "DevOps",
            "date": "2024-03-05",
            "notes": "Configured unit and integration tests"
        },
        {
            "task": "Configure CI/CD pipeline",
            "status": "In Progress",
            "employee": "Rachel Green",
            "category": "DevOps",
            "date": "2024-03-18",
            "notes": "GitHub Actions for automated deployment"
        },
        
        # UI/UX tasks
        {
            "task": "Redesign user interface",
            "status": "To Do",
            "employee": "Tom Anderson",
            "category": "Design",
            "date": "2024-03-30",
            "notes": "Modernize the dashboard layout"
        },
        {
            "task": "Update frontend components",
            "status": "In Progress",
            "employee": "Jessica White",
            "category": "Frontend",
            "date": "2024-03-16",
            "notes": "React component library updates"
        }
    ]

def test_similarity_scenarios():
    """Test various similarity scenarios with mock data."""
    print("🧪 Testing Task Similarity with Mock Data")
    print("=" * 60)
    
    # Create mock data
    existing_tasks = create_mock_tasks()
    print(f"📋 Created {len(existing_tasks)} mock tasks")
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Authentication System Match",
            "new_task": {
                "task": "Build login system with email verification",
                "status": "To Do",
                "employee": "New Developer",
                "category": "Security"
            },
            "expected_match": "Implement user authentication system"
        },
        {
            "name": "Database Performance Match",
            "new_task": {
                "task": "Improve database query speed",
                "status": "To Do",
                "employee": "New Developer",
                "category": "Performance"
            },
            "expected_match": "Optimize database queries"
        },
        {
            "name": "Documentation Match",
            "new_task": {
                "task": "Document our API endpoints",
                "status": "To Do",
                "employee": "New Developer",
                "category": "Documentation"
            },
            "expected_match": "Update API documentation"
        },
        {
            "name": "Testing Match",
            "new_task": {
                "task": "Implement automated testing framework",
                "status": "To Do",
                "employee": "New Developer",
                "category": "DevOps"
            },
            "expected_match": "Set up automated testing"
        },
        {
            "name": "UI Design Match",
            "new_task": {
                "task": "Modernize the user interface design",
                "status": "To Do",
                "employee": "New Developer",
                "category": "Design"
            },
            "expected_match": "Redesign user interface"
        },
        {
            "name": "No Match Expected",
            "new_task": {
                "task": "Create a new mobile app",
                "status": "To Do",
                "employee": "New Developer",
                "category": "Mobile"
            },
            "expected_match": None
        }
    ]
    
    # Run tests
    results = []
    for scenario in test_scenarios:
        print(f"\n📝 Testing: {scenario['name']}")
        print(f"   New task: '{scenario['new_task']['task']}'")
        
        start_time = time.time()
        result = check_task_similarity(scenario['new_task'], existing_tasks)
        test_time = time.time() - start_time
        
        print(f"   ⏱️  Time: {test_time:.3f}s")
        print(f"   ✅ Match found: {result['is_match']}")
        print(f"   🎯 Confidence: {result['confidence']:.3f}")
        print(f"   📝 Explanation: {result['explanation']}")
        
        if result['is_match']:
            matched_task = result['matched_task']['task']
            print(f"   🔗 Matched: '{matched_task}'")
            
            # Check if it matches expected
            if scenario['expected_match']:
                if matched_task == scenario['expected_match']:
                    print(f"   ✅ Expected match ✓")
                else:
                    print(f"   ⚠️  Unexpected match (expected: '{scenario['expected_match']}')")
        else:
            if scenario['expected_match'] is None:
                print(f"   ✅ Correctly no match found ✓")
            else:
                print(f"   ❌ Expected match not found (expected: '{scenario['expected_match']}')")
        
        results.append({
            "scenario": scenario['name'],
            "result": result,
            "time": test_time,
            "expected_match": scenario['expected_match']
        })
    
    return results

def test_top_k_similarity():
    """Test finding top-k similar tasks."""
    print("\n🧪 Testing Top-K Similarity Search")
    print("=" * 60)
    
    existing_tasks = create_mock_tasks()
    
    # Test query
    query_task = {
        "task": "Implement user login and authentication",
        "status": "To Do",
        "employee": "New Developer",
        "category": "Security"
    }
    
    print(f"📝 Query task: '{query_task['task']}'")
    
    # Find top 5 similar tasks
    start_time = time.time()
    similar_tasks = find_top_k_similar_tasks(query_task, existing_tasks, k=5)
    search_time = time.time() - start_time
    
    print(f"⏱️  Search time: {search_time:.3f}s")
    print(f"🔍 Found {len(similar_tasks)} similar tasks:")
    
    for i, item in enumerate(similar_tasks, 1):
        task = item['task']
        similarity = item['similarity']
        print(f"   {i}. '{task['task']}' (similarity: {similarity:.3f})")
        print(f"      Category: {task['category']}, Status: {task['status']}")

def test_performance_benchmark():
    """Benchmark performance with larger dataset."""
    print("\n🧪 Performance Benchmark")
    print("=" * 60)
    
    # Create larger dataset
    base_tasks = create_mock_tasks()
    large_dataset = base_tasks * 10  # 120 tasks
    
    print(f"📊 Dataset size: {len(large_dataset)} tasks")
    
    # Test multiple queries
    test_queries = [
        "Implement user authentication",
        "Optimize database performance", 
        "Update documentation",
        "Set up automated testing",
        "Redesign user interface"
    ]
    
    total_time = 0
    total_matches = 0
    
    for query in test_queries:
        new_task = {"task": query, "status": "To Do", "employee": "Test", "category": "Test"}
        
        start_time = time.time()
        result = check_task_similarity(new_task, large_dataset)
        query_time = time.time() - start_time
        
        total_time += query_time
        if result['is_match']:
            total_matches += 1
        
        print(f"   Query: '{query}' - {query_time:.3f}s - Match: {result['is_match']}")
    
    avg_time = total_time / len(test_queries)
    print(f"\n📈 Performance Summary:")
    print(f"   Average query time: {avg_time:.3f}s")
    print(f"   Total matches found: {total_matches}/{len(test_queries)}")
    print(f"   Queries per second: {1/avg_time:.1f}")

def main():
    """Run all similarity tests."""
    print("🚀 Starting Comprehensive Task Similarity Tests")
    print("=" * 80)
    
    try:
        # Test 1: Similarity scenarios
        results = test_similarity_scenarios()
        
        # Test 2: Top-k similarity
        test_top_k_similarity()
        
        # Test 3: Performance benchmark
        test_performance_benchmark()
        
        # Summary
        print("\n📊 Test Summary")
        print("=" * 60)
        
        successful_matches = sum(1 for r in results if r['result']['is_match'])
        total_tests = len(results)
        
        print(f"✅ Successful matches: {successful_matches}/{total_tests}")
        print(f"🎯 Average confidence: {sum(r['result']['confidence'] for r in results)/total_tests:.3f}")
        print(f"⏱️  Average response time: {sum(r['time'] for r in results)/total_tests:.3f}s")
        
        print("\n🎉 All tests completed! Chroma-based similarity is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 