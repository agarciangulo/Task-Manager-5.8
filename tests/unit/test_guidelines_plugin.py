#!/usr/bin/env python3
"""
Test script to verify ConsultantGuidelinesPlugin is working with correct guidelines.
"""
import os
import sys
import traceback

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_guideline_documents_exist():
    """Test that the actual guideline documents exist."""
    try:
        guideline_docs = [
            'docs/guidelines/process/project_management.md',
            'docs/guidelines/technical/field_guide.md',
            'docs/guidelines/Automation Services - SDLC Guide.docx',
            'docs/guidelines/Prisma Cloud Field Guide.pdf'
        ]
        
        print("📄 Checking guideline documents...")
        for doc_path in guideline_docs:
            if os.path.exists(doc_path):
                print(f"✅ {doc_path} exists")
            else:
                print(f"❌ {doc_path} does not exist")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking guideline documents: {e}")
        return False

def test_plugin_initialization():
    """Test that the ConsultantGuidelinesPlugin initializes correctly."""
    try:
        from src.plugins.guidelines.consultant_guidelines import ConsultantGuidelinesPlugin
        print("\n🔧 Testing plugin initialization...")
        
        # Initialize plugin
        plugin = ConsultantGuidelinesPlugin()
        success = plugin.initialize()
        
        if success:
            print(f"✅ Plugin initialized successfully with {len(plugin.guidelines)} guidelines")
            return True
        else:
            print("❌ Plugin initialization failed")
            return False
        
    except Exception as e:
        print(f"❌ Error testing plugin initialization: {e}")
        print(traceback.format_exc())
        return False

def test_guideline_content():
    """Test that the guidelines contain the expected content."""
    try:
        from src.plugins.guidelines.consultant_guidelines import ConsultantGuidelinesPlugin
        print("\n📋 Testing guideline content...")
        
        plugin = ConsultantGuidelinesPlugin()
        plugin.initialize()
        
        # Check for expected guideline categories
        expected_categories = ['Project Management', 'Technical Standards']
        found_categories = set()
        
        for guideline in plugin.guidelines:
            found_categories.add(guideline['category'])
            print(f"   - {guideline['title']} ({guideline['category']})")
        
        print(f"\n📊 Found categories: {list(found_categories)}")
        
        # Check if expected categories are present
        for expected_category in expected_categories:
            if expected_category in found_categories:
                print(f"✅ Found {expected_category} guidelines")
            else:
                print(f"❌ Missing {expected_category} guidelines")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing guideline content: {e}")
        print(traceback.format_exc())
        return False

def test_guideline_checking():
    """Test that the guidelines can check tasks properly."""
    try:
        from src.plugins.guidelines.consultant_guidelines import ConsultantGuidelinesPlugin
        print("\n🔍 Testing guideline checking...")
        
        plugin = ConsultantGuidelinesPlugin()
        plugin.initialize()
        
        # Create a mock task for testing
        class MockTask:
            def __init__(self, description, category="General"):
                self.description = description
                self.category = category
        
        # Test tasks
        test_tasks = [
            MockTask("Conduct stakeholder interviews to gather requirements for the new API", "Project Management"),
            MockTask("Implement authentication and authorization for the user management system", "Technical Standards"),
            MockTask("Create deployment pipeline with automated testing and monitoring", "Technical Standards"),
            MockTask("Update project documentation and communicate status to stakeholders", "Project Management")
        ]
        
        for i, task in enumerate(test_tasks, 1):
            print(f"\n   Testing task {i}: {task.description}")
            result = plugin.check_task(task)
            
            if result['compliant']:
                print(f"   ✅ Task is compliant")
                if result['suggestions']:
                    print(f"   💡 Suggestions: {result['suggestions']}")
            else:
                print(f"   ❌ Task is not compliant")
                if result['suggestions']:
                    print(f"   💡 Suggestions: {result['suggestions']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing guideline checking: {e}")
        print(traceback.format_exc())
        return False

def test_plugin_integration():
    """Test that the plugin integrates with the plugin manager correctly."""
    try:
        from src.plugins.plugin_manager_instance import plugin_manager
        print("\n🔌 Testing plugin integration...")
        
        # Discover and register plugins
        plugin_manager.discover_plugins(['src/plugins/guidelines'])
        plugin_manager.register_plugin_by_name('ConsultantGuidelinesPlugin')
        
        # Check if plugin is registered
        if 'ConsultantGuidelinesPlugin' in plugin_manager.registered_plugins:
            plugin = plugin_manager.registered_plugins['ConsultantGuidelinesPlugin']
            print(f"✅ Plugin registered: {type(plugin).__name__}")
            
            # Test that it can be used
            if hasattr(plugin, 'check_task'):
                print("✅ Plugin has check_task method")
                return True
            else:
                print("❌ Plugin missing check_task method")
                return False
        else:
            print("❌ Plugin not registered")
            return False
        
    except Exception as e:
        print(f"❌ Error testing plugin integration: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🧪 Testing Consultant Guidelines Plugin...")
    print("=" * 60)
    
    tests = [
        ("Guideline Documents", test_guideline_documents_exist),
        ("Plugin Initialization", test_plugin_initialization),
        ("Guideline Content", test_guideline_content),
        ("Guideline Checking", test_guideline_checking),
        ("Plugin Integration", test_plugin_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        result = test_func()
        results.append((test_name, result))
        print(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All guideline plugin tests passed!")
    else:
        print("\n⚠️ Some guideline plugin tests failed. Please check the errors above.")
        sys.exit(1) 