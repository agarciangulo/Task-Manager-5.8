#!/usr/bin/env python3
"""
Integration test for the hybrid task similarity system.
"""
import os
import sys
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.task_similarity import check_task_similarity
from config.settings import SIMILARITY_MODE, SIMILARITY_TOP_K

def test_integration():
    """Test the integration of the hybrid similarity system."""
    print("🔧 Testing Hybrid Task Similarity Integration")
    print("=" * 50)
    
    # Test configuration
    print(f"📋 Configuration:")
    print(f"   Similarity Mode: {SIMILARITY_MODE}")
    print(f"   Top-K: {SIMILARITY_TOP_K}")
    
    # Sample test data
    existing_tasks = [
        {
            "task": "Implement user authentication system",
            "notes": "Create a secure authentication system with email verification",
            "status": "In Progress",
            "employee": "John Smith",
            "date": "2024-03-15",
            "category": "Security"
        },
        {
            "task": "Set up CI/CD pipeline",
            "notes": "Configure automated testing and deployment pipeline",
            "status": "To Do",
            "employee": "Sarah Johnson",
            "date": "2024-03-14",
            "category": "DevOps"
        }
    ]
    
    new_task = {
        "task": "need to build a login system with email verification"
    }
    
    print(f"\n📝 Test Data:")
    print(f"   New task: '{new_task['task']}'")
    print(f"   Existing tasks: {len(existing_tasks)}")
    
    # Test the similarity check
    print(f"\n🔍 Running similarity check...")
    start_time = time.time()
    
    try:
        result = check_task_similarity(new_task, existing_tasks)
        test_time = time.time() - start_time
        
        print(f"✅ Test completed in {test_time:.3f}s")
        print(f"   Match found: {result['is_match']}")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Explanation: {result['explanation']}")
        
        if result['is_match']:
            matched_task = result['matched_task']
            print(f"   Matched task: '{matched_task['task']}'")
        
        # Verify the result makes sense
        expected_match = "Implement user authentication system"
        if result['is_match']:
            matched_text = result['matched_task']['task']
            if expected_match in matched_text:
                print(f"✅ Integration test PASSED - Correct match found")
                return True
            else:
                print(f"❌ Integration test FAILED - Wrong match found")
                return False
        else:
            print(f"❌ Integration test FAILED - Expected match not found")
            return False
            
    except Exception as e:
        print(f"❌ Integration test FAILED - Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_integration()
    if success:
        print(f"\n🎉 All integration tests passed!")
    else:
        print(f"\n💥 Integration tests failed!")
    sys.exit(0 if success else 1) 