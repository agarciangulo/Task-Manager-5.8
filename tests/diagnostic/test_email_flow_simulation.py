#!/usr/bin/env python3
"""
Simulate the actual email processing flow to identify where it breaks.
This tests the real path that emails take through the system.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def simulate_email_processing():
    """Simulate processing an email through the actual flow."""
    print("=" * 60)
    print("SIMULATING EMAIL PROCESSING FLOW")
    print("=" * 60)
    
    # Simulate email content
    sample_email_body = """
    Hi,
    
    Here's what I did today:
    - Completed the quarterly report analysis
    - Started working on the new authentication feature
    - Fixed three critical bugs in the user interface
    
    Thanks!
    """
    
    sender_email = os.getenv('GMAIL_ADDRESS', 'test@example.com')
    sender_name = "Test User"
    
    print(f"\n📧 Simulated email from: {sender_email}")
    print(f"📝 Email body:\n{sample_email_body[:100]}...\n")
    
    # Step 1: Check if user exists
    print("STEP 1: User Lookup")
    print("-" * 40)
    try:
        from src.core.services.auth_service import AuthService
        from src.core.security.jwt_utils import JWTManager
        from src.config.settings import NOTION_TOKEN, NOTION_USERS_DB_ID
        
        jwt_manager = JWTManager(secret_key="dummy", algorithm="HS256")
        auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, None)
        user = auth_service.get_user_by_email(sender_email)
        
        if not user:
            print(f"❌ User not found for {sender_email}")
            print("   ACTION: Register the user first")
            return False
        
        print(f"✅ User found: {user.full_name}")
        print(f"   Task Database ID: {user.task_database_id}")
        
        if not user.task_database_id:
            print("❌ User has no task database ID")
            return False
        
    except Exception as e:
        print(f"❌ Error in user lookup: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 2: Extract tasks
    print("\nSTEP 2: Task Extraction")
    print("-" * 40)
    try:
        from src.core.task_extractor import extract_tasks_from_update
        
        print("🔄 Extracting tasks from email body...")
        tasks = extract_tasks_from_update(sample_email_body)
        
        if not tasks:
            print("❌ No tasks extracted!")
            print("   This could be due to:")
            print("   - Gemini API not working")
            print("   - API key issues")
            print("   - Text format not recognized")
            return False
        
        print(f"✅ Extracted {len(tasks)} tasks")
        for i, task in enumerate(tasks, 1):
            print(f"   {i}. {task.get('task', 'N/A')[:50]}")
        
    except Exception as e:
        print(f"❌ Error extracting tasks: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Classify tasks
    print("\nSTEP 3: Task Classification")
    print("-" * 40)
    try:
        from src.utils.gmail_processor_enhanced import classify_tasks_by_context_needs
        
        ready_tasks, context_needed_tasks = classify_tasks_by_context_needs(tasks)
        
        print(f"✅ Classification complete:")
        print(f"   Ready tasks: {len(ready_tasks)}")
        print(f"   Context needed: {len(context_needed_tasks)}")
        
        if len(ready_tasks) == 0 and len(context_needed_tasks) > 0:
            print("⚠️  All tasks need context - they will be queued for verification")
            print("   This means tasks won't appear in Notion until user responds")
        
    except Exception as e:
        print(f"❌ Error classifying tasks: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Test task insertion (if ready tasks exist)
    if ready_tasks:
        print("\nSTEP 4: Task Insertion Test (Dry Run)")
        print("-" * 40)
        try:
            from src.core.notion_service import NotionService
            
            notion_service = NotionService()
            test_task = ready_tasks[0]
            
            # Format task for Notion
            formatted = notion_service._format_task_properties(test_task)
            
            print(f"✅ Task formatted for Notion:")
            for key in ['Task', 'Status', 'Employee', 'Date', 'Category', 'Priority']:
                if key in formatted:
                    print(f"   {key}: ✓")
                else:
                    print(f"   {key}: ✗ MISSING")
            
            # Check for critical fields
            required = ['Task', 'Status', 'Employee', 'Date']
            missing = [f for f in required if f not in formatted]
            
            if missing:
                print(f"\n❌ Missing required fields: {missing}")
                print("   This would cause Notion insertion to fail")
                return False
            else:
                print("\n✅ All required fields present")
                print("   Task insertion should work")
            
        except Exception as e:
            print(f"❌ Error testing task insertion: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("✅ Email processing flow simulation complete")
    
    if ready_tasks:
        print(f"✅ {len(ready_tasks)} tasks would be inserted into Notion")
    if context_needed_tasks:
        print(f"⚠️  {len(context_needed_tasks)} tasks need context verification")
        print("   These will be queued and user will receive a context request email")
    
    return True

if __name__ == "__main__":
    success = simulate_email_processing()
    sys.exit(0 if success else 1)





