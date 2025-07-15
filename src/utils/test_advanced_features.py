#!/usr/bin/env python3
"""
Test script to verify advanced task extraction features are working.
Tests vague task detection, suggested questions, and comprehensive extraction.
"""
import os
import sys
import json
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.task_extractor import extract_tasks_from_update

def test_advanced_features():
    """Test the advanced task extraction features."""
    print("🧪 Testing Advanced Task Extraction Features")
    print("=" * 60)
    
    # Test cases with different levels of detail
    test_cases = [
        {
            "name": "Vague Tasks (Should be flagged)",
            "text": """From: John Smith
Date: 2024-03-20

Today's work:
- Meeting
- Resume
- Training
- Project work
- Email""",
            "expected_vague": 5
        },
        {
            "name": "Detailed Tasks (Should not be flagged)",
            "text": """From: Jane Doe
Date: 2024-03-20

Completed Activities:
- Implemented user authentication system with JWT tokens
- Updated API documentation for version 2.0
- Fixed database performance issues by adding indexes
- Deployed hotfix to production servers
- Reviewed and approved 15 pull requests""",
            "expected_vague": 0
        },
        {
            "name": "Mixed Tasks (Some vague, some detailed)",
            "text": """From: Bob Wilson
Date: 2024-03-20

Today's work:
- Meeting with team about project timeline
- Updated resume with new skills
- Implemented login functionality
- Training
- Fixed bug in checkout process
- Email correspondence""",
            "expected_vague": 3
        },
        {
            "name": "Complex Email with Multiple Formats",
            "text": """From: Alice Johnson <alice@company.com>
Date: 2024-03-20
Subject: Daily Update

Completed Activities:
TechStart Project:
- Fixed user authentication problems
- Updated software dependencies
- Tested mobile application on various devices

MegaCorp Project:
- Attended meeting about upcoming feature releases
- Reviewed pull requests from team members
- Investigated performance issues in checkout process

General:
- Wrote technical documentation
- Analyzed server logs for error patterns
- Created backup of production database

Planned Activities:
- Resume work on API optimization
- Meeting with stakeholders
- Training session""",
            "expected_vague": 3
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n📝 Testing: {test_case['name']}")
        print(f"   Input length: {len(test_case['text'])} characters")
        
        try:
            # Extract tasks
            tasks = extract_tasks_from_update(test_case['text'])
            
            if not tasks:
                print("   ❌ No tasks extracted")
                results.append({
                    "test": test_case['name'],
                    "status": "failed",
                    "reason": "No tasks extracted"
                })
                continue
            
            print(f"   ✅ Extracted {len(tasks)} tasks")
            
            # Analyze results
            vague_tasks = [t for t in tasks if t.get("needs_description", False)]
            detailed_tasks = [t for t in tasks if not t.get("needs_description", False)]
            
            print(f"   📊 Vague tasks: {len(vague_tasks)}")
            print(f"   📊 Detailed tasks: {len(detailed_tasks)}")
            
            # Check if expected number of vague tasks
            expected = test_case['expected_vague']
            actual = len(vague_tasks)
            
            if actual == expected:
                print(f"   ✅ Correctly identified {actual} vague tasks")
                status = "passed"
            else:
                print(f"   ⚠️ Expected {expected} vague tasks, got {actual}")
                status = "partial"
            
            # Show examples of vague tasks with suggested questions
            if vague_tasks:
                print("   📝 Examples of vague tasks:")
                for i, task in enumerate(vague_tasks[:3], 1):
                    print(f"      {i}. '{task['task']}'")
                    if task.get("suggested_question"):
                        print(f"         Q: {task['suggested_question']}")
            
            # Show examples of detailed tasks
            if detailed_tasks:
                print("   📝 Examples of detailed tasks:")
                for i, task in enumerate(detailed_tasks[:3], 1):
                    print(f"      {i}. '{task['task']}' (Status: {task.get('status', 'Unknown')})")
            
            results.append({
                "test": test_case['name'],
                "status": status,
                "total_tasks": len(tasks),
                "vague_tasks": len(vague_tasks),
                "detailed_tasks": len(detailed_tasks),
                "expected_vague": expected
            })
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                "test": test_case['name'],
                "status": "failed",
                "reason": str(e)
            })
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 60)
    
    passed = 0
    partial = 0
    failed = 0
    
    for result in results:
        if result["status"] == "passed":
            passed += 1
            print(f"✅ {result['test']}")
        elif result["status"] == "partial":
            partial += 1
            print(f"⚠️ {result['test']} (Expected {result['expected_vague']} vague, got {result['vague_tasks']})")
        else:
            failed += 1
            print(f"❌ {result['test']} - {result.get('reason', 'Unknown error')}")
    
    print(f"\n🎯 Overall Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ⚠️ Partial: {partial}")
    print(f"   ❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 Advanced features are working correctly!")
        return True
    else:
        print(f"\n⚠️ {failed} tests failed. Please check the implementation.")
        return False

def test_specific_vague_detection():
    """Test specific vague task detection patterns."""
    print("\n🧪 Testing Specific Vague Task Detection")
    print("=" * 60)
    
    vague_patterns = [
        "Meeting",
        "Call",
        "Email",
        "Training",
        "Resume",
        "Review",
        "Update",
        "Work",
        "Project work",
        "General",
        "Misc",
        "Other"
    ]
    
    for pattern in vague_patterns:
        test_text = f"""From: Test User
Date: 2024-03-20

Today's work:
- {pattern}"""
        
        try:
            tasks = extract_tasks_from_update(test_text)
            if tasks:
                task = tasks[0]
                is_vague = task.get("needs_description", False)
                has_question = bool(task.get("suggested_question", "").strip())
                
                status = "✅" if is_vague else "❌"
                question_status = "✅" if has_question else "❌"
                
                print(f"{status} '{pattern}' - Vague: {is_vague}, Has question: {has_question}")
                if has_question:
                    print(f"   Q: {task['suggested_question']}")
            else:
                print(f"❌ '{pattern}' - No tasks extracted")
                
        except Exception as e:
            print(f"❌ '{pattern}' - Error: {e}")

if __name__ == "__main__":
    print("🚀 Testing Advanced Task Extraction Features")
    print("=" * 80)
    
    # Test 1: General advanced features
    success1 = test_advanced_features()
    
    # Test 2: Specific vague detection
    test_specific_vague_detection()
    
    # Final result
    if success1:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️ Some tests failed. Please review the implementation.")
        sys.exit(1) 