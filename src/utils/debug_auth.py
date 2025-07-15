#!/usr/bin/env python3
"""
Debug script for authentication system.
"""

import requests
import json
from datetime import datetime

def test_registration():
    """Test registration with detailed error reporting."""
    print("🔍 Testing registration endpoint...")
    
    url = "http://localhost:5001/api/register"
    data = {
        "user_id": f"debug_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "password": "testpassword123",
        "full_name": "Debug User",
        "role": "user"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            return True
        else:
            print("❌ Registration failed!")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def test_login():
    """Test login endpoint."""
    print("\n🔍 Testing login endpoint...")
    
    url = "http://localhost:5001/api/login"
    data = {
        "user_id": "test_user",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            return True
        else:
            print("❌ Login failed!")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def test_server_info():
    """Test basic server connectivity."""
    print("🔍 Testing server connectivity...")
    
    try:
        response = requests.get("http://localhost:5001/")
        print(f"Server Status: {response.status_code}")
        print("✅ Server is responding!")
        return True
    except Exception as e:
        print(f"❌ Server error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🐛 Authentication System Debug")
    print("=" * 40)
    
    # Test server connectivity
    if not test_server_info():
        print("❌ Cannot connect to server!")
        exit(1)
    
    # Test registration
    test_registration()
    
    # Test login
    test_login() 