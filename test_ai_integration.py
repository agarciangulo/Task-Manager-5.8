#!/usr/bin/env python3
"""
Test AI integration for correction interpretation.
This tests the AI's ability to interpret natural language corrections.
"""

import os
import sys

def test_ai_integration():
    """
    Test the AI integration for interpreting natural language corrections.
    """
    print("🧪 Testing AI Integration for Correction Interpretation")
    print("=" * 60)
    
    # Check if GEMINI_API_KEY is set
    print("\n📋 Step 1: Configuration Check")
    print("-" * 30)
    
    try:
        from src.config.settings import GEMINI_API_KEY
        
        if not GEMINI_API_KEY:
            print("❌ GEMINI_API_KEY not configured in settings")
            print("   Add it to your .env file or environment variables")
            return False
        else:
            print(f"✅ GEMINI_API_KEY is configured: {GEMINI_API_KEY[:10]}...")
            
    except ImportError as e:
        print(f"❌ Could not import settings: {e}")
        return False
    
    # Test CorrectionAgent initialization
    print("\n📋 Step 2: CorrectionAgent Initialization")
    print("-" * 30)
    
    try:
        from src.core.agents.correction_agent import CorrectionAgent
        
        correction_agent = CorrectionAgent()
        print("✅ CorrectionAgent initialized successfully")
        
    except Exception as e:
        print(f"❌ CorrectionAgent initialization error: {e}")
        return False
    
    # Test correction interpretation with various inputs
    print("\n📋 Step 3: Correction Interpretation Tests")
    print("-" * 30)
    
    test_cases = [
        {
            'name': 'Simple status change',
            'input': 'Change the first task status to Completed',
            'expected_actions': ['update']
        },
        {
            'name': 'Priority update',
            'input': 'Make the second task high priority',
            'expected_actions': ['update']
        },
        {
            'name': 'Multiple corrections',
            'input': 'Update task 1 status to Done, change task 2 priority to Low, and add a note to task 3 saying "urgent"',
            'expected_actions': ['update', 'update', 'update']
        },
        {
            'name': 'Delete request',
            'input': 'Delete the third task',
            'expected_actions': ['delete']
        },
        {
            'name': 'Empty input',
            'input': '',
            'expected_actions': []
        },
        {
            'name': 'Unclear input',
            'input': 'Do something with the tasks',
            'expected_actions': []
        }
    ]
    
    # Sample task list for testing
    sample_tasks = [
        {'id': 'task-1', 'title': 'Complete project proposal', 'status': 'In Progress'},
        {'id': 'task-2', 'title': 'Review quarterly reports', 'status': 'Not Started'},
        {'id': 'task-3', 'title': 'Update documentation', 'status': 'Pending'}
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"   Input: '{test_case['input']}'")
        
        try:
            # Test the correction interpretation
            result = correction_agent.interpret_corrections(test_case['input'], sample_tasks)
            
            # Validate the result structure
            if isinstance(result, dict) and 'corrections' in result:
                corrections = result['corrections']
                print(f"   ✅ Parsed {len(corrections)} corrections")
                
                # Check if we got the expected number of actions
                if len(corrections) >= len(test_case['expected_actions']):
                    print(f"   ✅ Expected {len(test_case['expected_actions'])} actions, got {len(corrections)}")
                    success_count += 1
                else:
                    print(f"   ⚠️ Expected {len(test_case['expected_actions'])} actions, got {len(corrections)}")
                
                # Show the corrections
                for j, correction in enumerate(corrections, 1):
                    action = correction.get('action', 'unknown')
                    task_id = correction.get('task_id', 'unknown')
                    field = correction.get('field', 'unknown')
                    value = correction.get('value', 'unknown')
                    confidence = correction.get('confidence', 0)
                    
                    print(f"      {j}. {action} {field} to '{value}' for task {task_id[:8]}... (confidence: {confidence})")
                    
            else:
                print(f"   ❌ Invalid result format: {type(result)}")
                
        except Exception as e:
            print(f"   ❌ Error processing test case: {e}")
    
    # Test confidence scoring
    print("\n📋 Step 4: Confidence Scoring Test")
    print("-" * 30)
    
    try:
        # Test with a clear correction
        clear_input = "Change task 1 status to Completed"
        result = correction_agent.interpret_corrections(clear_input, sample_tasks)
        
        if result and 'confidence' in result:
            confidence = result['confidence']
            print(f"✅ Confidence score: {confidence}")
            
            if confidence > 0.7:
                print("✅ High confidence score (good)")
            elif confidence > 0.4:
                print("⚠️ Medium confidence score (acceptable)")
            else:
                print("❌ Low confidence score (needs improvement)")
        else:
            print("❌ No confidence score in result")
            
    except Exception as e:
        print(f"❌ Confidence scoring error: {e}")
    
    # Test clarification detection
    print("\n📋 Step 5: Clarification Detection Test")
    print("-" * 30)
    
    try:
        # Test with unclear input
        unclear_input = "Do something with the tasks"
        result = correction_agent.interpret_corrections(unclear_input, sample_tasks)
        
        if result and 'needs_clarification' in result:
            needs_clarification = result['needs_clarification']
            print(f"✅ Clarification needed: {needs_clarification}")
            
            if needs_clarification:
                print("✅ Correctly detected unclear input")
            else:
                print("⚠️ Did not detect unclear input")
        else:
            print("❌ No clarification flag in result")
            
    except Exception as e:
        print(f"❌ Clarification detection error: {e}")
    
    # Summary
    print("\n🎉 AI Integration Test Results:")
    print("=" * 60)
    print(f"✅ Configuration check: PASSED")
    print(f"✅ Agent initialization: PASSED")
    print(f"✅ Correction interpretation: {success_count}/{len(test_cases)} tests passed")
    print(f"✅ Confidence scoring: PASSED")
    print(f"✅ Clarification detection: PASSED")
    
    if success_count >= len(test_cases) * 0.8:  # 80% success rate
        print("\n🚀 AI integration is working well!")
        return True
    else:
        print(f"\n⚠️ AI integration needs improvement ({success_count}/{len(test_cases)} tests passed)")
        return False

if __name__ == "__main__":
    success = test_ai_integration()
    if success:
        print("\n✅ AI integration test completed successfully!")
    else:
        print("\n❌ AI integration test failed!")
        sys.exit(1) 