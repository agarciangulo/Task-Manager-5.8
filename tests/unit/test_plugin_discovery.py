#!/usr/bin/env python3
"""
Test script to verify plugin discovery is working correctly.
"""
import os
import sys
import traceback

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_plugin_directories_exist():
    """Test that plugin directories exist in the correct locations."""
    try:
        plugin_dirs = [
            'src/plugins/guidelines',
            'src/plugins/feedback',
            'src/plugins/integrations',
            'src/plugins/security'
        ]
        
        print("📁 Checking plugin directories...")
        for plugin_dir in plugin_dirs:
            if os.path.exists(plugin_dir):
                print(f"✅ {plugin_dir} exists")
            else:
                print(f"❌ {plugin_dir} does not exist")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking plugin directories: {e}")
        return False

def test_plugin_files_exist():
    """Test that plugin files exist in the directories."""
    try:
        expected_plugins = {
            'src/plugins/guidelines': ['consultant_guidelines.py'],
            'src/plugins/feedback': ['peer_feedback.py'],
            'src/plugins/security': ['project_protection.py'],
            'src/plugins/integrations': []  # May be empty
        }
        
        print("\n📄 Checking plugin files...")
        for plugin_dir, expected_files in expected_plugins.items():
            if os.path.exists(plugin_dir):
                actual_files = [f for f in os.listdir(plugin_dir) if f.endswith('.py') and not f.startswith('__')]
                print(f"📁 {plugin_dir}:")
                for expected_file in expected_files:
                    if expected_file in actual_files:
                        print(f"   ✅ {expected_file}")
                    else:
                        print(f"   ❌ {expected_file} (missing)")
                        return False
                for actual_file in actual_files:
                    if actual_file not in expected_files:
                        print(f"   ℹ️  {actual_file} (additional)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking plugin files: {e}")
        return False

def test_plugin_manager_discovery():
    """Test that the plugin manager can discover plugins."""
    try:
        from src.plugins.plugin_manager_instance import plugin_manager
        print("\n🔍 Testing plugin manager discovery...")
        
        # Test discovery with correct paths
        plugin_directories = [
            'src/plugins/guidelines',
            'src/plugins/feedback',
            'src/plugins/integrations',
            'src/plugins/security'
        ]
        
        plugin_manager.discover_plugins(plugin_directories)
        
        print(f"📋 Discovered {len(plugin_manager.plugin_classes)} plugin classes:")
        for plugin_name in plugin_manager.plugin_classes:
            print(f"   - {plugin_name}")
        
        # Check for expected plugins
        expected_plugins = [
            'ConsultantGuidelinesPlugin',
            'PeerFeedbackPlugin', 
            'ProjectProtectionPlugin'
        ]
        
        missing_plugins = []
        for expected_plugin in expected_plugins:
            if expected_plugin in plugin_manager.plugin_classes:
                print(f"✅ {expected_plugin} discovered")
            else:
                print(f"❌ {expected_plugin} not discovered")
                missing_plugins.append(expected_plugin)
        
        if missing_plugins:
            print(f"⚠️ Missing plugins: {missing_plugins}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing plugin manager discovery: {e}")
        print(traceback.format_exc())
        return False

def test_plugin_registration():
    """Test that plugins can be registered."""
    try:
        from src.plugins.plugin_manager_instance import plugin_manager
        print("\n📝 Testing plugin registration...")
        
        # Discover plugins first
        plugin_directories = [
            'src/plugins/guidelines',
            'src/plugins/feedback',
            'src/plugins/integrations',
            'src/plugins/security'
        ]
        plugin_manager.discover_plugins(plugin_directories)
        
        # Register plugins
        registered_count = 0
        for plugin_name in plugin_manager.plugin_classes:
            try:
                plugin_manager.register_plugin_by_name(plugin_name)
                print(f"✅ Registered {plugin_name}")
                registered_count += 1
            except Exception as e:
                print(f"❌ Failed to register {plugin_name}: {e}")
        
        print(f"📊 Successfully registered {registered_count} plugins")
        
        return registered_count > 0
        
    except Exception as e:
        print(f"❌ Error testing plugin registration: {e}")
        print(traceback.format_exc())
        return False

def test_gmail_processor_plugin_loading():
    """Test that gmail processor loads plugins correctly."""
    try:
        print("\n📧 Testing gmail processor plugin loading...")
        
        # Import the gmail processor (this will trigger plugin loading)
        import src.utils.gmail_processor_enhanced
        print("✅ Gmail processor imported successfully")
        
        # Check if plugins were loaded
        from src.plugins.plugin_manager_instance import plugin_manager
        if hasattr(plugin_manager, 'registered_plugins') and plugin_manager.registered_plugins:
            print(f"✅ {len(plugin_manager.registered_plugins)} plugins loaded by gmail processor")
            for plugin_name, plugin_instance in plugin_manager.registered_plugins.items():
                print(f"   - {plugin_name}: {type(plugin_instance).__name__}")
            return True
        else:
            print("⚠️ No plugins loaded by gmail processor")
            return False
        
    except Exception as e:
        print(f"❌ Error testing gmail processor plugin loading: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🧪 Testing Plugin Discovery...")
    print("=" * 50)
    
    tests = [
        ("Plugin Directories", test_plugin_directories_exist),
        ("Plugin Files", test_plugin_files_exist),
        ("Plugin Manager Discovery", test_plugin_manager_discovery),
        ("Plugin Registration", test_plugin_registration),
        ("Gmail Processor Loading", test_gmail_processor_plugin_loading),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        result = test_func()
        results.append((test_name, result))
        print(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All plugin discovery tests passed!")
    else:
        print("\n⚠️ Some plugin discovery tests failed. Please check the errors above.")
        sys.exit(1) 