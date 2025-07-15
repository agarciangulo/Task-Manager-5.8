#!/usr/bin/env python3
"""
Comprehensive API endpoint testing for AI Team Support.
Tests all migrated endpoints with proper authentication and validation.
"""
import sys
import os
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class APITester:
    """Comprehensive API testing class."""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_user = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    headers: Optional[Dict] = None, expected_status: int = 200) -> Dict[str, Any]:
        """Make an HTTP request and validate response."""
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {}
        
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response_data = response.json() if response.content else {}
            
            if response.status_code == expected_status:
                self.log(f"✅ {method} {endpoint} - Status: {response.status_code}")
                return response_data
            else:
                self.log(f"❌ {method} {endpoint} - Expected: {expected_status}, Got: {response.status_code}")
                self.log(f"Response: {response_data}")
                return response_data
                
        except Exception as e:
            self.log(f"❌ {method} {endpoint} - Error: {str(e)}", "ERROR")
            return {}
    
    def test_health_endpoint(self) -> bool:
        """Test the health check endpoint."""
        self.log("🧪 Testing health endpoint...")
        response = self.make_request('GET', '/api/health')
        return response.get('success', False)
    
    def test_version_endpoint(self) -> bool:
        """Test the version endpoint."""
        self.log("🧪 Testing version endpoint...")
        response = self.make_request('GET', '/api/version')
        return response.get('success', False) and 'version' in response.get('data', {})
    
    def test_register_endpoint(self) -> bool:
        """Test user registration."""
        self.log("🧪 Testing user registration...")
        
        test_data = {
            'email': f'test_{int(time.time())}@example.com',
            'password': 'TestPassword123!',
            'full_name': 'Test User',
            'company': 'Test Company'
        }
        
        response = self.make_request('POST', '/api/auth/register', data=test_data, expected_status=201)
        
        if response.get('success'):
            self.test_user = response.get('data', {}).get('user', {})
            self.log(f"✅ User registered: {self.test_user.get('email')}")
            return True
        else:
            self.log(f"❌ Registration failed: {response.get('message')}")
            return False
    
    def test_login_endpoint(self) -> bool:
        """Test user login."""
        self.log("🧪 Testing user login...")
        
        if not self.test_user:
            self.log("❌ No test user available for login test")
            return False
        
        login_data = {
            'email': self.test_user.get('email'),
            'password': 'TestPassword123!'
        }
        
        response = self.make_request('POST', '/api/auth/login', data=login_data)
        
        if response.get('success'):
            self.auth_token = response.get('data', {}).get('token')
            self.log("✅ Login successful, token obtained")
            return True
        else:
            self.log(f"❌ Login failed: {response.get('message')}")
            return False
    
    def test_profile_endpoint(self) -> bool:
        """Test profile retrieval."""
        self.log("🧪 Testing profile endpoint...")
        
        if not self.auth_token:
            self.log("❌ No auth token available for profile test")
            return False
        
        response = self.make_request('GET', '/api/auth/profile')
        return response.get('success', False)
    
    def test_process_update_endpoint(self) -> bool:
        """Test text processing endpoint."""
        self.log("🧪 Testing process update endpoint...")
        
        if not self.auth_token:
            self.log("❌ No auth token available for process update test")
            return False
        
        test_text = """
        Today's updates:
        - Need to review the quarterly report by Friday
        - Call with client about project timeline
        - Schedule team meeting for next week
        - Follow up on pending invoices
        """
        
        response = self.make_request('POST', '/api/tasks/process_update', 
                                   data={'text': test_text})
        
        if response.get('success'):
            processed_tasks = response.get('data', {}).get('processed_tasks', [])
            self.log(f"✅ Processed {len(processed_tasks)} tasks")
            return True
        else:
            self.log(f"❌ Process update failed: {response.get('message')}")
            return False
    
    def test_get_user_tasks(self) -> bool:
        """Test getting user tasks."""
        self.log("🧪 Testing get user tasks...")
        
        if not self.auth_token:
            self.log("❌ No auth token available for tasks test")
            return False
        
        response = self.make_request('GET', '/api/tasks/user/tasks')
        return response.get('success', False)
    
    def test_create_task(self) -> bool:
        """Test creating a new task."""
        self.log("🧪 Testing create task...")
        
        if not self.auth_token:
            self.log("❌ No auth token available for create task test")
            return False
        
        task_data = {
            'task': 'Test task created via API',
            'status': 'Not Started',
            'priority': 'Medium',
            'category': 'Testing',
            'description': 'This is a test task created during API testing'
        }
        
        response = self.make_request('POST', '/api/tasks/user/tasks', 
                                   data=task_data, expected_status=201)
        return response.get('success', False)
    
    def test_get_categories(self) -> bool:
        """Test getting categories."""
        self.log("🧪 Testing get categories...")
        
        if not self.auth_token:
            self.log("❌ No auth token available for categories test")
            return False
        
        response = self.make_request('GET', '/api/insights/categories')
        return response.get('success', False)
    
    def test_get_dashboard_data(self) -> bool:
        """Test getting dashboard data."""
        self.log("🧪 Testing get dashboard data...")
        
        if not self.auth_token:
            self.log("❌ No auth token available for dashboard test")
            return False
        
        response = self.make_request('GET', '/api/insights/dashboard-data')
        return response.get('success', False)
    
    def test_chat_endpoint(self) -> bool:
        """Test chat endpoint."""
        self.log("🧪 Testing chat endpoint...")
        
        if not self.auth_token:
            self.log("❌ No auth token available for chat test")
            return False
        
        chat_data = {
            'message': 'What tasks do I have for today?'
        }
        
        response = self.make_request('POST', '/api/insights/chat', data=chat_data)
        return response.get('success', False)
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all API tests and return results."""
        self.log("🚀 Starting comprehensive API endpoint testing...")
        
        tests = [
            ('Health Check', self.test_health_endpoint),
            ('Version Check', self.test_version_endpoint),
            ('User Registration', self.test_register_endpoint),
            ('User Login', self.test_login_endpoint),
            ('Profile Retrieval', self.test_profile_endpoint),
            ('Process Update', self.test_process_update_endpoint),
            ('Get User Tasks', self.test_get_user_tasks),
            ('Create Task', self.test_create_task),
            ('Get Categories', self.test_get_categories),
            ('Dashboard Data', self.test_get_dashboard_data),
            ('Chat Endpoint', self.test_chat_endpoint),
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                self.log(f"\n📋 Running: {test_name}")
                result = test_func()
                results[test_name] = result
                if result:
                    passed += 1
                else:
                    self.log(f"❌ {test_name} failed")
            except Exception as e:
                self.log(f"❌ {test_name} crashed: {str(e)}", "ERROR")
                results[test_name] = False
        
        self.log(f"\n📊 Test Results: {passed}/{total} tests passed")
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status}: {test_name}")
        
        return results

def main():
    """Main test runner."""
    print("🧪 AI Team Support API Endpoint Testing")
    print("=" * 50)
    
    # Check if Flask app is running
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Flask app is running on localhost:5000")
        else:
            print("⚠️ Flask app responded but with unexpected status")
    except requests.exceptions.ConnectionError:
        print("❌ Flask app is not running on localhost:5000")
        print("Please start the Flask app first:")
        print("  cd src && python -m flask --app api.app_auth run")
        return False
    
    # Run tests
    tester = APITester()
    results = tester.run_all_tests()
    
    # Summary
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n🎯 Final Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All API endpoints are working correctly!")
        return True
    else:
        print("⚠️ Some endpoints need attention. Check the logs above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 