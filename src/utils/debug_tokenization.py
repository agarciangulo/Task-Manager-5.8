#!/usr/bin/env python3
"""
Debug script to test tokenization system step by step.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import PRESERVE_TOKENS_IN_UI
from src.plugins.plugin_manager_instance import plugin_manager
from src.core.security.security_manager import SecurityManager

# Discover and initialize plugins
PLUGIN_DIRECTORIES = [
    'plugins/guidelines',
    'plugins/feedback',
    'plugins/integrations',
    'plugins/security'
]
plugin_manager.discover_plugins(PLUGIN_DIRECTORIES)
# Register all discovered plugins
for plugin_name in plugin_manager.plugin_classes:
    plugin_manager.register_plugin_by_name(plugin_name)

def test_tokenization_system():
    """Test the tokenization system step by step."""
    print("🔍 DEBUGGING TOKENIZATION SYSTEM")
    print("=" * 50)
    
    # 1. Check config
    print(f"1. PRESERVE_TOKENS_IN_UI: {PRESERVE_TOKENS_IN_UI}")
    print(f"   Type: {type(PRESERVE_TOKENS_IN_UI)}")
    
    # 2. Check plugin manager
    print(f"\n2. Plugin Manager Status:")
    print(f"   Available plugins: {list(plugin_manager.plugins.keys())}")
    
    # 3. Check ProjectProtectionPlugin
    protection_plugin = plugin_manager.get_plugin('ProjectProtectionPlugin')
    print(f"\n3. ProjectProtectionPlugin:")
    print(f"   Found: {protection_plugin is not None}")
    if protection_plugin:
        print(f"   Enabled: {protection_plugin.enabled}")
        print(f"   Config: {protection_plugin.config}")
        print(f"   Security Manager: {protection_plugin.security_manager}")
        print(f"   Token Map: {protection_plugin.security_manager.token_map}")
        print(f"   Preserve Tokens: {protection_plugin.security_manager.preserve_tokens_in_ui}")
    else:
        print("   ❌ Plugin not found!")
    
    # 4. Test tokenization directly
    print(f"\n4. Direct Tokenization Test:")
    if protection_plugin and protection_plugin.enabled:
        test_categories = ['Attornato', 'Training', 'Education', 'General']
        for category in test_categories:
            token = protection_plugin.security_manager.tokenize_project(category)
            print(f"   '{category}' -> '{token}'")
        
        print(f"   Final Token Map: {protection_plugin.security_manager.token_map}")
    else:
        print("   ❌ Cannot test - plugin not available or disabled")
    
    # 5. Test task protection
    print(f"\n5. Task Protection Test:")
    if protection_plugin and protection_plugin.enabled:
        test_task = {
            'task': 'Work on Attornato project',
            'category': 'Attornato',
            'status': 'In Progress',
            'employee': 'Test User'
        }
        
        print(f"   Original task: {test_task}")
        protected_task = protection_plugin.protect_task(test_task)
        print(f"   Protected task: {protected_task}")
        
        # Test unprotection
        unprotected_task = protection_plugin.unprotect_task(protected_task)
        print(f"   Unprotected task: {unprotected_task}")
    else:
        print("   ❌ Cannot test - plugin not available or disabled")
    
    # 6. Check if token file exists
    print(f"\n6. Token File Check:")
    token_file = 'security_tokens.json'
    if os.path.exists(token_file):
        print(f"   ✅ Token file exists: {token_file}")
        with open(token_file, 'r') as f:
            content = f.read()
            print(f"   Content: {content}")
    else:
        print(f"   ❌ Token file not found: {token_file}")

if __name__ == "__main__":
    test_tokenization_system() 