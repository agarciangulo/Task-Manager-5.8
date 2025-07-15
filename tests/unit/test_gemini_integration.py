#!/usr/bin/env python3
"""
Test script to verify Gemini integration is working correctly.
"""
import os
import sys
from datetime import datetime

def test_gemini_integration():
    """Test the Gemini integration through the main application."""
    print("\n=== Testing Gemini Integration ===")
    try:
        # Test configuration
        from config.settings import GEMINI_API_KEY, AI_PROVIDER, CHAT_MODEL
        
        if not GEMINI_API_KEY:
            print("❌ GEMINI_API_KEY not set")
            return False
            
        if AI_PROVIDER != 'gemini':
            print(f"❌ AI_PROVIDER is set to '{AI_PROVIDER}', expected 'gemini'")
            return False
            
        print(f"✅ Configuration: AI_PROVIDER={AI_PROVIDER}, MODEL={CHAT_MODEL}")
        
        # Test Gemini client
        from core.gemini_client import client
        
        if not client:
            print("❌ Gemini client not available")
            return False
            
        print("✅ Gemini client initialized successfully")
        
        # Test a simple API call
        test_prompt = "Hello! Please respond with 'Gemini is working correctly' if you can see this message."
        
        response_text = client.generate_content(
            test_prompt,
            temperature=0.1
        )
        
        print(f"✅ Gemini response: {response_text}")
        
        if "Gemini is working correctly" in response_text:
            print("✅ Gemini integration test passed!")
            return True
        else:
            print("❌ Unexpected response from Gemini")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Gemini integration: {e}")
        return False

def test_gemini_client_directly():
    """Test the Gemini client directly."""
    print("\n=== Testing Gemini Client Directly ===")
    try:
        from core.gemini_client import client
        
        if not client:
            print("❌ Gemini client not available")
            return False
            
        test_prompt = "Hello! Please respond with 'Gemini is working correctly' if you can see this message."
        
        response_text = client.generate_content(
            test_prompt,
            temperature=0.1
        )
        
        print(f"✅ Gemini response: {response_text}")
        
        if "Gemini is working correctly" in response_text:
            print("✅ Gemini client test passed!")
            return True
        else:
            print("❌ Unexpected response from Gemini")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Gemini client: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Gemini Integration Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    
    gemini_success = test_gemini_integration()
    gemini_client_success = test_gemini_client_directly()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"Gemini Integration: {'✅ PASS' if gemini_success else '❌ FAIL'}")
    print(f"Gemini Client Directly: {'✅ PASS' if gemini_client_success else '❌ FAIL'}")
    
    if gemini_success and gemini_client_success:
        print("\n🎉 All tests passed! Gemini integration is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the configuration and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 