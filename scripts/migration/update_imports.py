#!/usr/bin/env python3
"""
Script to update all import statements from the old structure to the new src-based structure.
"""
import os
import re
import glob

def update_imports_in_file(file_path):
    """Update imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update import patterns
        replacements = [
            # Core imports
            (r'from core\.', 'from src.core.'),
            (r'import core\.', 'import src.core.'),
            
            # Config imports
            (r'from config import', 'from src.config.settings import'),
            (r'from config\.', 'from src.config.'),
            
            # Plugin imports
            (r'from plugins import', 'from src.plugins import'),
            (r'from plugins\.', 'from src.plugins.'),
            
            # Plugin manager instance
            (r'from plugin_manager_instance import', 'from src.plugins.plugin_manager_instance import'),
            
            # Specific file imports that might be missed
            (r'from core\.notion_service import', 'from src.core.notion_service import'),
            (r'from core\.task_extractor import', 'from src.core.task_extractor import'),
            (r'from core\.task_processor import', 'from src.core.task_processor import'),
            (r'from core\.services\.', 'from src.core.services.'),
            (r'from core\.security\.', 'from src.core.security.'),
            (r'from core\.ai\.', 'from src.core.ai.'),
            (r'from core\.agents\.', 'from src.core.agents.'),
            (r'from core\.models\.', 'from src.core.models.'),
            (r'from core\.adapters\.', 'from src.core.adapters.'),
            (r'from core\.chat\.', 'from src.core.chat.'),
            (r'from core\.logging_config import', 'from src.core.logging_config import'),
            (r'from core\.exceptions import', 'from src.core.exceptions import'),
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated: {file_path}")
            return True
        else:
            print(f"⏭️  No changes: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    """Update imports in all Python files in the src directory."""
    print("🔄 Updating imports in all Python files...")
    
    # Find all Python files in src directory
    python_files = []
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files to update")
    
    updated_count = 0
    for file_path in python_files:
        if update_imports_in_file(file_path):
            updated_count += 1
    
    print(f"\n✅ Updated {updated_count} files out of {len(python_files)} total files")

if __name__ == "__main__":
    main() 