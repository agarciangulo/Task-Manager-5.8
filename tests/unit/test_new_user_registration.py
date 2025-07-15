#!/usr/bin/env python3
"""
Test script to register a new user and verify automatic task database creation.
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://127.0.0.1:5001"

def test_new_user_registration():
    """Test registering a new user and check if task database is created automatically."""
    print("🧪 Testing New User Registration with Automatic Task Database Creation")
    print("=" * 70)
    
    # Generate unique email for this test
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_email = f"test_user_{timestamp}@example.com"
    test_password = "testpassword123"
    test_name = f"Test User {timestamp}"
    
    print(f"📧 Test email: {test_email}")
    print(f"👤 Test name: {test_name}")
    
    # Step 1: Register new user
    print(f"\n1. Registering new user...")
    user_data = {
        "email": test_email,
        "password": test_password,
        "full_name": test_name,
        "role": "user"
    }
    
    response = requests.post(f"{BASE_URL}/api/register", json=user_data)
    if response.status_code == 201:
        print("✅ User registered successfully")
        user_info = response.json().get("user", {})
        print(f"   User ID: {user_info.get('user_id')}")
        print(f"   Task Database ID: {user_info.get('task_database_id', 'None')}")
    else:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return False
    
    # Step 2: Login to get token
    print(f"\n2. Logging in...")
    login_data = {
        "email": test_email,
        "password": test_password
    }
    
    response = requests.post(f"{BASE_URL}/api/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return False
    
    token = response.json().get("token")
    if not token:
        print("❌ No token received")
        return False
    
    print("✅ Login successful")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Step 3: Get user profile to check task database
    print(f"\n3. Getting user profile...")
    response = requests.get(f"{BASE_URL}/api/profile", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get profile: {response.status_code} - {response.text}")
        return False
    
    profile = response.json().get("user", {})
    task_database_id = profile.get("task_database_id")
    
    if task_database_id:
        print(f"✅ User has task database: {task_database_id}")
        print("🎉 Automatic task database creation is working!")
        return True
    else:
        print("❌ User doesn't have task database")
        print("❌ Automatic task database creation is NOT working")
        return False

if __name__ == "__main__":
    test_new_user_registration() 