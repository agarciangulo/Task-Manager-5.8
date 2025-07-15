#!/usr/bin/env python3
"""
Test script for migrated endpoints in AI Team Support.
Tests all the new modular blueprints and their endpoints.
"""
import sys
import os
import requests
import json
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_flask_app_startup():
    """Test that the Flask app can start without errors."""
    print("🧪 Testing Flask app startup...")
    try:
        from src.api.app_auth import app
        print("✅ Flask app imports successfully")
        return True
    except Exception as e:
        print(f"❌ Flask app import failed: {e}")
        return False

def test_blueprint_registration():
    """Test that all blueprints are properly registered."""
    print("\n🧪 Testing blueprint registration...")
    try:
        from src.api.app_auth import app
        
        # Check if blueprints are registered
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        expected_blueprints = ['auth', 'tasks', 'insights', 'misc']
        
        for bp_name in expected_blueprints:
            if bp_name in blueprint_names:
                print(f"✅ Blueprint '{bp_name}' registered")
            else:
                print(f"❌ Blueprint '{bp_name}' not found")
                return False
        
        print("✅ All blueprints registered successfully")
        return True
    except Exception as e:
        print(f"❌ Blueprint registration test failed: {e}")
        return False

def test_endpoint_routes():
    """Test that all expected routes are available."""
    print("\n🧪 Testing endpoint routes...")
    try:
        from src.api.app_auth import app
        
        # Expected routes by blueprint
        expected_routes = {
            'auth': [
                '/api/auth/register',
                '/api/auth/login', 
                '/api/auth/refresh',
                '/api/auth/profile'
            ],
            'tasks': [
                '/api/tasks/process_update',
                '/api/tasks/user/tasks',
                '/api/tasks/user/tasks/by-category',
                '/api/tasks/user/stale-tasks',
                '/api/tasks/user/task-database'
            ],
            'insights': [
                '/api/insights/user/insights',
                '/api/insights/chat',
                '/api/insights/dashboard-data',
                '/api/insights/categories'
            ],
            'misc': [
                '/api/health',
                '/api/version',
                '/api/users',
                '/api/test_auth'
            ]
        }
        
        # Get all registered routes
        all_routes = []
        for rule in app.url_map.iter_rules():
            all_routes.append(rule.rule)
        
        # Check each expected route
        missing_routes = []
        for blueprint, routes in expected_routes.items():
            for route in routes:
                if route in all_routes:
                    print(f"✅ Route '{route}' found")
                else:
                    print(f"❌ Route '{route}' missing")
                    missing_routes.append(route)
        
        if missing_routes:
            print(f"❌ Missing routes: {missing_routes}")
            return False
        
        print("✅ All expected routes found")
        return True
    except Exception as e:
        print(f"❌ Route testing failed: {e}")
        return False

def test_request_models():
    """Test that request models can be instantiated and validated."""
    print("\n🧪 Testing request models...")
    try:
        from src.api.models.request_models import (
            LoginRequest, RegisterRequest, ProcessUpdateRequest, 
            CreateTaskRequest, GetStaleTasksRequest
        )
        
        # Test LoginRequest
        login_req = LoginRequest(email="test@example.com", password="password123")
        errors = login_req.validate()
        if not errors:
            print("✅ LoginRequest validation works")
        else:
            print(f"❌ LoginRequest validation failed: {errors}")
            return False
        
        # Test RegisterRequest
        register_req = RegisterRequest(
            email="test@example.com", 
            password="password123", 
            full_name="Test User"
        )
        errors = register_req.validate()
        if not errors:
            print("✅ RegisterRequest validation works")
        else:
            print(f"❌ RegisterRequest validation failed: {errors}")
            return False
        
        # Test ProcessUpdateRequest
        process_req = ProcessUpdateRequest(text="This is a test update")
        errors = process_req.validate()
        if not errors:
            print("✅ ProcessUpdateRequest validation works")
        else:
            print(f"❌ ProcessUpdateRequest validation failed: {errors}")
            return False
        
        print("✅ All request models working correctly")
        return True
    except Exception as e:
        print(f"❌ Request model testing failed: {e}")
        return False

def test_response_models():
    """Test that response models can be created."""
    print("\n🧪 Testing response models...")
    try:
        from src.api.models.response_models import (
            create_success_response, create_error_response
        )
        
        # Test success response
        success_resp = create_success_response(
            data={"test": "data"}, 
            message="Test successful"
        )
        if success_resp.get("success") and success_resp.get("message"):
            print("✅ Success response creation works")
        else:
            print("❌ Success response creation failed")
            return False
        
        # Test error response
        error_resp = create_error_response(
            message="Test error", 
            error_code="TEST_ERROR"
        )
        if not error_resp.get("success") and error_resp.get("message"):
            print("✅ Error response creation works")
        else:
            print("❌ Error response creation failed")
            return False
        
        print("✅ All response models working correctly")
        return True
    except Exception as e:
        print(f"❌ Response model testing failed: {e}")
        return False

def test_service_container():
    """Test that service container can provide services."""
    print("\n🧪 Testing service container...")
    try:
        from src.core.container.service_container import (
            get_task_service, get_insight_service
        )
        
        # Test task service
        task_service = get_task_service()
        if task_service:
            print("✅ Task service available")
        else:
            print("❌ Task service not available")
            return False
        
        # Test insight service
        insight_service = get_insight_service()
        if insight_service:
            print("✅ Insight service available")
        else:
            print("❌ Insight service not available")
            return False
        
        print("✅ All services available through container")
        return True
    except Exception as e:
        print(f"❌ Service container testing failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting migrated endpoints test suite...")
    print(f"📅 Test run at: {datetime.now()}")
    
    tests = [
        test_flask_app_startup,
        test_blueprint_registration,
        test_endpoint_routes,
        test_request_models,
        test_response_models,
        test_service_container
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test '{test.__name__}' failed")
        except Exception as e:
            print(f"❌ Test '{test.__name__}' crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Migrated endpoints are ready.")
        return True
    else:
        print("⚠️ Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 