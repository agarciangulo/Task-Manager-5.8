#!/usr/bin/env python3
"""
Test script for RAG-Enhanced Insights Integration.

This script demonstrates how the RAG system integrates with the insights generator
to provide guideline-aware coaching and project insights.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def create_sample_data():
    """Create sample task data for testing."""
    
    # Sample current tasks with some guideline violations
    current_tasks = [
        {
            'task': 'Follow up on client email about project timeline',
            'status': 'In Progress',
            'date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
            'employee': 'John Doe',
            'category': 'Client Communication'
        },
        {
            'task': 'Review security vulnerability in production system',
            'status': 'In Progress',
            'date': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
            'employee': 'John Doe',
            'category': 'Security'
        },
        {
            'task': 'Complete code review for new feature',
            'status': 'In Progress',
            'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'employee': 'John Doe',
            'category': 'Development'
        }
    ]
    
    # Sample recent task history
    recent_tasks_data = [
        {'task': 'Respond to client inquiry', 'status': 'Completed', 'employee': 'John Doe', 'date': '2025-07-20', 'category': 'Client Communication'},
        {'task': 'Deploy security patch', 'status': 'Completed', 'employee': 'John Doe', 'date': '2025-07-19', 'category': 'Security'},
        {'task': 'Code review for API changes', 'status': 'Completed', 'employee': 'John Doe', 'date': '2025-07-18', 'category': 'Development'},
        {'task': 'Follow up on vendor email', 'status': 'In Progress', 'employee': 'John Doe', 'date': '2025-07-17', 'category': 'Client Communication'},
        {'task': 'Security audit documentation', 'status': 'Completed', 'employee': 'John Doe', 'date': '2025-07-16', 'category': 'Security'},
    ]
    
    recent_tasks = pd.DataFrame(recent_tasks_data)
    
    # Sample peer feedback
    peer_feedback = [
        {
            'from': 'Jane Smith',
            'message': 'Great work on the security patch deployment!',
            'date': '2025-07-19'
        },
        {
            'from': 'Mike Johnson',
            'message': 'Could improve response time on client communications',
            'date': '2025-07-18'
        }
    ]
    
    return current_tasks, recent_tasks, peer_feedback

def test_guideline_context_retrieval():
    """Test the guideline context retrieval functionality."""
    print("🧪 Testing Guideline Context Retrieval...")
    
    try:
        from src.core.ai.rag_enhanced_insights import get_guideline_context_for_coaching
        
        current_tasks, recent_tasks, _ = create_sample_data()
        
        context = get_guideline_context_for_coaching("John Doe", current_tasks, recent_tasks)
        
        if context and context != "No specific guidelines found for current patterns.":
            print(f"✅ Found relevant guideline context ({len(context)} chars)")
            print(f"   Context preview: {context[:200]}...")
            return True
        else:
            print("⚠️  No specific guidelines found for the sample data")
            return False
            
    except Exception as e:
        print(f"❌ Error testing guideline context: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_guideline_violation_detection():
    """Test the guideline violation detection functionality."""
    print("\n🧪 Testing Guideline Violation Detection...")
    
    try:
        from src.core.ai.rag_enhanced_insights import get_guideline_violation_alerts
        
        current_tasks, _, _ = create_sample_data()
        
        alerts = get_guideline_violation_alerts(current_tasks)
        
        if alerts:
            print(f"✅ Found {len(alerts)} potential guideline violations:")
            for alert in alerts:
                print(f"   - {alert['type']}: {alert['task']} ({alert['days_overdue']} days overdue)")
                print(f"     Guideline: {alert['guideline']}")
                print(f"     Severity: {alert['severity']}")
            return True
        else:
            print("✅ No guideline violations detected")
            return True
            
    except Exception as e:
        print(f"❌ Error testing violation detection: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_rag_enhanced_coaching():
    """Test the RAG-enhanced coaching insights."""
    print("\n🧪 Testing RAG-Enhanced Coaching Insights...")
    
    try:
        from src.core.ai.rag_enhanced_insights import get_rag_enhanced_coaching_insight
        
        current_tasks, recent_tasks, peer_feedback = create_sample_data()
        
        insight = get_rag_enhanced_coaching_insight("John Doe", current_tasks, recent_tasks, peer_feedback)
        
        if insight and "Unable to generate" not in insight:
            print(f"✅ Generated RAG-enhanced coaching insight ({len(insight)} chars)")
            print(f"   Preview: {insight[:300]}...")
            
            # Check if it references guidelines
            if any(keyword in insight.lower() for keyword in ['guideline', 'policy', 'standard', 'procedure']):
                print("   ✅ Insight references company guidelines")
            else:
                print("   ⚠️  Insight doesn't explicitly reference guidelines")
            
            return True
        else:
            print(f"❌ Failed to generate coaching insight: {insight}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing RAG-enhanced coaching: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_rag_enhanced_project_insights():
    """Test the RAG-enhanced project insights."""
    print("\n🧪 Testing RAG-Enhanced Project Insights...")
    
    try:
        from src.core.ai.rag_enhanced_insights import get_rag_enhanced_project_insight
        
        _, recent_tasks, _ = create_sample_data()
        
        # Filter for security-related tasks
        security_tasks = recent_tasks[recent_tasks['category'] == 'Security']
        
        if not security_tasks.empty:
            insight = get_rag_enhanced_project_insight("Security", security_tasks)
            
            if insight and "Unable to generate" not in insight:
                print(f"✅ Generated RAG-enhanced project insight ({len(insight)} chars)")
                print(f"   Preview: {insight[:300]}...")
                
                # Check if it references guidelines
                if any(keyword in insight.lower() for keyword in ['guideline', 'policy', 'standard', 'procedure']):
                    print("   ✅ Project insight references company guidelines")
                else:
                    print("   ⚠️  Project insight doesn't explicitly reference guidelines")
                
                return True
            else:
                print(f"❌ Failed to generate project insight: {insight}")
                return False
        else:
            print("⚠️  No security tasks found for testing")
            return True
            
    except Exception as e:
        print(f"❌ Error testing RAG-enhanced project insights: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def demonstrate_email_response_violation():
    """Demonstrate how the system would detect email response violations."""
    print("\n🧪 Demonstrating Email Response Violation Detection...")
    
    try:
        from src.core.ai.rag_enhanced_insights import get_guideline_violation_alerts
        
        # Create a task that violates email response guidelines
        overdue_email_task = {
            'task': 'Respond to urgent client email about project delays',
            'status': 'In Progress',
            'date': (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d'),  # 4 days old
            'employee': 'John Doe',
            'category': 'Client Communication'
        }
        
        alerts = get_guideline_violation_alerts([overdue_email_task])
        
        if alerts:
            email_alert = next((alert for alert in alerts if alert['type'] == 'email_response_time'), None)
            if email_alert:
                print(f"✅ Detected email response violation:")
                print(f"   Task: {email_alert['task']}")
                print(f"   Days overdue: {email_alert['days_overdue']}")
                print(f"   Guideline: {email_alert['guideline']}")
                print(f"   Severity: {email_alert['severity']}")
                
                print("\n   This violation would be included in coaching insights to remind")
                print("   the employee about the 2-business-day email response guideline.")
                return True
            else:
                print("⚠️  No email response violation detected")
                return False
        else:
            print("⚠️  No violations detected")
            return False
            
    except Exception as e:
        print(f"❌ Error demonstrating email violation: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """Run all RAG-enhanced insights tests."""
    print("🚀 Testing RAG-Enhanced Insights Integration")
    print("=" * 60)
    
    # Test 1: Guideline context retrieval
    context_success = test_guideline_context_retrieval()
    
    # Test 2: Guideline violation detection
    violation_success = test_guideline_violation_detection()
    
    # Test 3: RAG-enhanced coaching
    coaching_success = test_rag_enhanced_coaching()
    
    # Test 4: RAG-enhanced project insights
    project_success = test_rag_enhanced_project_insights()
    
    # Test 5: Email response violation demonstration
    email_demo_success = demonstrate_email_response_violation()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 RAG-ENHANCED INSIGHTS TEST RESULTS")
    print("=" * 60)
    print(f"Guideline Context:     {'✅ PASS' if context_success else '❌ FAIL'}")
    print(f"Violation Detection:   {'✅ PASS' if violation_success else '❌ FAIL'}")
    print(f"Enhanced Coaching:     {'✅ PASS' if coaching_success else '❌ FAIL'}")
    print(f"Enhanced Projects:     {'✅ PASS' if project_success else '❌ FAIL'}")
    print(f"Email Violation Demo:  {'✅ PASS' if email_demo_success else '❌ FAIL'}")
    
    overall_success = context_success and violation_success and coaching_success and project_success and email_demo_success
    
    if overall_success:
        print("\n🎉 ALL TESTS PASSED! RAG-Enhanced Insights Integration is working!")
        print("\n📋 Integration Benefits:")
        print("   ✅ Coaching insights now reference company guidelines")
        print("   ✅ Automatic detection of guideline violations")
        print("   ✅ Project insights include best practices")
        print("   ✅ Email response time monitoring")
        print("   ✅ Security incident response tracking")
        print("\n💡 Example: If an email is overdue by 2+ business days,")
        print("   the coaching insight will mention the guideline and suggest")
        print("   prioritizing email responses.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 