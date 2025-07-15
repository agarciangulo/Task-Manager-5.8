#!/usr/bin/env python3
"""
Comprehensive import path fixer for AI Team Support.
This script fixes all import paths to use absolute imports from the src package root.
"""
import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix config imports
        content = re.sub(r'from config\.settings import', 'from src.config.settings import', content)
        content = re.sub(r'from config import', 'from src.config.settings import', content)
        
        # Fix core imports
        content = re.sub(r'from core\.', 'from src.core.', content)
        content = re.sub(r'import core\.', 'import src.core.', content)
        
        # Fix plugins imports
        content = re.sub(r'from plugins\.', 'from src.plugins.', content)
        content = re.sub(r'import plugins\.', 'import src.plugins.', content)
        
        # Fix interfaces imports
        content = re.sub(r'from interfaces\.', 'from src.interfaces.', content)
        content = re.sub(r'import interfaces\.', 'import src.interfaces.', content)
        
        # Fix utils imports
        content = re.sub(r'from utils\.', 'from src.utils.', content)
        content = re.sub(r'import utils\.', 'import src.utils.', content)
        
        # Fix api imports
        content = re.sub(r'from api\.', 'from src.api.', content)
        content = re.sub(r'import api\.', 'import src.api.', content)
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed imports in {file_path}")
            return True
        else:
            print(f"ℹ️  No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def fix_plugin_directories_in_file(file_path):
    """Fix plugin directory paths in specific files."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix plugin directory paths
        content = re.sub(r"'plugins/", "'src/plugins/", content)
        content = re.sub(r'"plugins/', '"src/plugins/', content)
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed plugin directories in {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error fixing plugin directories in {file_path}: {e}")
        return False

def main():
    """Main function to fix all imports."""
    print("🔧 Comprehensive Import Path Fixer")
    print("=" * 50)
    
    # Get the project root
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / "src"
    
    if not src_dir.exists():
        print("❌ src/ directory not found!")
        return
    
    print(f"📁 Project root: {project_root}")
    print(f"📁 Source directory: {src_dir}")
    print()
    
    # Find all Python files in src/
    python_files = list(src_dir.rglob("*.py"))
    print(f"📋 Found {len(python_files)} Python files to process")
    print()
    
    fixed_count = 0
    plugin_dir_fixed_count = 0
    
    for file_path in python_files:
        # Fix imports
        if fix_imports_in_file(file_path):
            fixed_count += 1
        
        # Fix plugin directories in specific files
        if "plugins/__init__.py" in str(file_path):
            if fix_plugin_directories_in_file(file_path):
                plugin_dir_fixed_count += 1
    
    print()
    print("📊 Summary:")
    print(f"   Files with import fixes: {fixed_count}")
    print(f"   Files with plugin directory fixes: {plugin_dir_fixed_count}")
    print(f"   Total files processed: {len(python_files)}")
    
    if fixed_count > 0 or plugin_dir_fixed_count > 0:
        print("\n✅ Import path fixes completed!")
        print("💡 You can now run: python -m src.utils.gmail_processor")
    else:
        print("\nℹ️  No import fixes were needed.")

if __name__ == "__main__":
    main() 