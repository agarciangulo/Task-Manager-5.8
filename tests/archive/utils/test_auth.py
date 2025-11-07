#!/usr/bin/env python3
"""
Test script for the authentication system.
This script tests the registration, login, and token validation functionality.
"""

import os
import sys
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5001"
TEST_USER_ID = "test_user_" + datetime.now().strftime("%Y%m%d_%H%M%S")
TEST_PASSWORD = "testpassword123"
TEST_FULL_NAME = "Test User"

def print_status(message, status="INFO"):
    """Print a formatted status message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {status}: {message}")

def test_register():
    """Test user registration."""
    print_status("Testing user registration...")
    
    url = f"{BASE_URL}/api/register"
    data = {
        "user_id": TEST_USER_ID,
        "password": TEST_PASSWORD,
        "full_name": TEST_FULL_NAME,
        "role": "user"
    }
    
    try:
        response = requests.post(url, json=data)
        print_status(f"Registration response status: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print_status(f"User registered successfully: {result['user']['user_id']}")
            return True
        else:
            print_status(f"Registration failed: {response.text}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Registration error: {str(e)}", "ERROR")
        return False

def test_login():
    """Test user login."""
    print_status("Testing user login...")
    
    url = f"{BASE_URL}/api/login"
    data = {
        "user_id": TEST_USER_ID,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(url, json=data)
        print_status(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_status(f"Login successful: {result['user']['user_id']}")
            return result['token']
        else:
            print_status(f"Login failed: {response.text}", "ERROR")
            return None
            
    except Exception as e:
        print_status(f"Login error: {str(e)}", "ERROR")
        return None

def test_protected_endpoint(token):
    """Test accessing a protected endpoint."""
    print_status("Testing protected endpoint access...")
    
    url = f"{BASE_URL}/api/profile"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print_status(f"Protected endpoint response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_status(f"Profile retrieved successfully: {result['user']['user_id']}")
            return True
        else:
            print_status(f"Protected endpoint access failed: {response.text}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Protected endpoint error: {str(e)}", "ERROR")
        return False

def test_invalid_token():
    """Test accessing protected endpoint with invalid token."""
    print_status("Testing invalid token access...")
    
    url = f"{BASE_URL}/api/profile"
    headers = {
        "Authorization": "Bearer invalid_token_here"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print_status(f"Invalid token response status: {response.status_code}")
        
        if response.status_code == 401:
            print_status("Invalid token correctly rejected")
            return True
        else:
            print_status(f"Invalid token not properly rejected: {response.text}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Invalid token test error: {str(e)}", "ERROR")
        return False

def test_no_token():
    """Test accessing protected endpoint without token."""
    print_status("Testing no token access...")
    
    url = f"{BASE_URL}/api/profile"
    
    try:
        response = requests.get(url)
        print_status(f"No token response status: {response.status_code}")
        
        if response.status_code == 401:
            print_status("No token correctly rejected")
            return True
        else:
            print_status(f"No token not properly rejected: {response.text}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"No token test error: {str(e)}", "ERROR")
        return False

def test_token_refresh(token):
    """Test token refresh functionality."""
    print_status("Testing token refresh...")
    
    url = f"{BASE_URL}/api/refresh"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.post(url, headers=headers)
        print_status(f"Token refresh response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_status("Token refreshed successfully")
            return result['token']
        else:
            print_status(f"Token refresh failed: {response.text}", "ERROR")
            return None
            
    except Exception as e:
        print_status(f"Token refresh error: {str(e)}", "ERROR")
        return None

def test_dashboard_access(token):
    """Test dashboard data access."""
    print_status("Testing dashboard data access...")
    
    url = f"{BASE_URL}/api/dashboard_data"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print_status(f"Dashboard access response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_status(f"Dashboard data retrieved successfully")
            return True
        else:
            print_status(f"Dashboard access failed: {response.text}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Dashboard access error: {str(e)}", "ERROR")
        return False

def main():
    """Run all authentication tests."""
    print_status("Starting authentication system tests...")
    print_status(f"Test user ID: {TEST_USER_ID}")
    print_status(f"Base URL: {BASE_URL}")
    print("=" * 60)
    
    # Test 1: Registration
    if not test_register():
        print_status("Registration test failed. Exiting.", "ERROR")
        return False
    
    print("-" * 40)
    
    # Test 2: Login
    token = test_login()
    if not token:
        print_status("Login test failed. Exiting.", "ERROR")
        return False
    
    print("-" * 40)
    
    # Test 3: Protected endpoint access
    if not test_protected_endpoint(token):
        print_status("Protected endpoint test failed.", "ERROR")
        return False
    
    print("-" * 40)
    
    # Test 4: Token refresh
    new_token = test_token_refresh(token)
    if not new_token:
        print_status("Token refresh test failed.", "ERROR")
        return False
    
    print("-" * 40)
    
    # Test 5: Dashboard access with new token
    if not test_dashboard_access(new_token):
        print_status("Dashboard access test failed.", "ERROR")
        return False
    
    print("-" * 40)
    
    # Test 6: Invalid token
    if not test_invalid_token():
        print_status("Invalid token test failed.", "ERROR")
        return False
    
    print("-" * 40)
    
    # Test 7: No token
    if not test_no_token():
        print_status("No token test failed.", "ERROR")
        return False
    
    print("=" * 60)
    print_status("All authentication tests completed successfully!", "SUCCESS")
    return True

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print_status("Server is not responding properly. Make sure app_auth.py is running.", "ERROR")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print_status("Cannot connect to server. Make sure app_auth.py is running on localhost:5000", "ERROR")
        sys.exit(1)
    
    # Run tests
    success = main()
    
    if success:
        print_status("Authentication system is working correctly!", "SUCCESS")
        sys.exit(0)
    else:
        print_status("Authentication system tests failed!", "ERROR")
        sys.exit(1) 