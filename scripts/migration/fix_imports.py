#!/usr/bin/env python3
"""
Fix import paths after file organization.
Removes 'src.' prefix from imports since we're now running from within src directory.
"""
import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix imports that start with 'src.'
        original_content = content
        content = re.sub(r'from src\.', 'from ', content)
        content = re.sub(r'import src\.', 'import ', content)
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed imports in: {file_path}")
            return True
        else:
            print(f"⏭️  No changes needed: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {str(e)}")
        return False

def find_python_files(directory):
    """Find all Python files in directory and subdirectories."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def main():
    """Main function to fix imports."""
    print("🔧 Fixing import paths after file organization...")
    
    # Get the src directory
    src_dir = Path(__file__).parent.parent.parent / 'src'
    
    if not src_dir.exists():
        print("❌ src directory not found!")
        return False
    
    # Find all Python files
    python_files = find_python_files(src_dir)
    print(f"📁 Found {len(python_files)} Python files to process")
    
    # Process each file
    fixed_count = 0
    for file_path in python_files:
        if fix_imports_in_file(file_path):
            fixed_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   Total files processed: {len(python_files)}")
    print(f"   Files with import fixes: {fixed_count}")
    print(f"   Files unchanged: {len(python_files) - fixed_count}")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 