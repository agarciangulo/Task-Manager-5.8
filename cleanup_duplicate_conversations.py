#!/usr/bin/env python3
"""
Script to clean up duplicate conversations in the Gmail processor.
This will keep only the most recent conversation for each user and remove duplicates.
"""

import json
import os
from datetime import datetime
from collections import defaultdict

# Path to the persistence file
PERSISTENCE_FILE = os.path.join(os.path.dirname(__file__), "pending_conversations.json")
PERSISTENCE_BACKUP_FILE = os.path.join(os.path.dirname(__file__), "pending_conversations.backup.json")

def cleanup_duplicate_conversations():
    """Clean up duplicate conversations, keeping only the most recent one per user."""
    
    print("🧹 Starting cleanup of duplicate conversations...")
    
    # Load current state
    if not os.path.exists(PERSISTENCE_FILE):
        print("❌ No persistence file found")
        return
    
    # Create backup
    import shutil
    shutil.copy2(PERSISTENCE_FILE, PERSISTENCE_BACKUP_FILE)
    print(f"✅ Created backup: {PERSISTENCE_BACKUP_FILE}")
    
    # Load data
    with open(PERSISTENCE_FILE, 'r') as f:
        data = json.load(f)
    
    pending_conversations = data.get('pending_context_conversations', {})
    print(f"📊 Found {len(pending_conversations)} total conversations")
    
    # Group conversations by user email
    user_conversations = defaultdict(list)
    for conv_id, conversation in pending_conversations.items():
        user_email = conversation.get('user_email')
        if user_email:
            user_conversations[user_email].append((conv_id, conversation))
    
    print(f"👥 Found conversations for {len(user_conversations)} users")
    
    # Keep only the most recent conversation per user
    cleaned_conversations = {}
    removed_count = 0
    
    for user_email, conversations in user_conversations.items():
        print(f"\n👤 Processing user: {user_email}")
        print(f"   Found {len(conversations)} conversations")
        
        if len(conversations) == 1:
            # Only one conversation, keep it
            conv_id, conversation = conversations[0]
            cleaned_conversations[conv_id] = conversation
            print(f"   ✅ Kept single conversation: {conv_id}")
        else:
            # Multiple conversations, find the most recent
            most_recent = None
            most_recent_time = None
            
            for conv_id, conversation in conversations:
                created_time = datetime.fromisoformat(conversation['created_at'])
                if most_recent_time is None or created_time > most_recent_time:
                    most_recent = (conv_id, conversation)
                    most_recent_time = created_time
            
            # Keep the most recent
            conv_id, conversation = most_recent
            cleaned_conversations[conv_id] = conversation
            print(f"   ✅ Kept most recent conversation: {conv_id}")
            print(f"   🗑️ Removed {len(conversations) - 1} older conversations")
            removed_count += len(conversations) - 1
    
    # Update the data
    data['pending_context_conversations'] = cleaned_conversations
    data['metadata']['last_save'] = datetime.now().isoformat()
    data['metadata']['cleanup_performed'] = True
    data['metadata']['conversations_removed'] = removed_count
    
    # Save cleaned data
    with open(PERSISTENCE_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"\n✅ Cleanup completed!")
    print(f"   📊 Total conversations before: {len(pending_conversations)}")
    print(f"   📊 Total conversations after: {len(cleaned_conversations)}")
    print(f"   🗑️ Conversations removed: {removed_count}")
    
    # Show remaining conversations
    print(f"\n📋 Remaining conversations:")
    for conv_id, conversation in cleaned_conversations.items():
        user_email = conversation.get('user_email', 'Unknown')
        created_at = conversation.get('created_at', 'Unknown')
        ready_tasks = len(conversation.get('ready_tasks', []))
        context_tasks = len(conversation.get('context_needed_tasks', []))
        print(f"   {conv_id[:8]}... - {user_email} - {ready_tasks} ready, {context_tasks} need context")

if __name__ == "__main__":
    cleanup_duplicate_conversations() 