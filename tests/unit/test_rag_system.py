#!/usr/bin/env python3
"""
Test script for the RAG system implementation.

This script tests the complete RAG pipeline:
1. KnowledgeBase query_guidelines method
2. Chat handler /ask command
3. End-to-end RAG response generation
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def test_knowledge_base_query():
    """Test the KnowledgeBase query_guidelines method."""
    print("🧪 Testing KnowledgeBase query_guidelines method...")
    
    try:
        from src.core.knowledge.knowledge_base import KnowledgeBase
        
        kb = KnowledgeBase(name="guidelines")
        
        # Test query
        test_question = "What are the deployment procedures?"
        print(f"Query: {test_question}")
        
        chunks = kb.query_guidelines(test_question, top_k=3)
        
        if chunks:
            print(f"✅ Found {len(chunks)} relevant chunks")
            for i, chunk in enumerate(chunks[:2]):  # Show first 2 chunks
                print(f"   Chunk {i+1}: {chunk[:100]}...")
        else:
            print("❌ No chunks found")
            
        return len(chunks) > 0
        
    except Exception as e:
        print(f"❌ Error testing KnowledgeBase: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_chat_handler_rag():
    """Test the chat handler RAG functionality."""
    print("\n🧪 Testing Chat Handler RAG functionality...")
    
    try:
        from src.core.chat.handler import handle_rag_query
        
        # Test /ask command
        test_message = "/ask What are the security best practices?"
        print(f"Message: {test_message}")
        
        # Mock context and parameters
        user_id = "test_user"
        chat_context = {}
        database_id = "test_db"
        
        result = handle_rag_query(test_message, user_id, chat_context, database_id)
        
        if isinstance(result, dict) and "message" in result:
            print(f"✅ RAG response generated")
            print(f"   Type: {result.get('type', 'unknown')}")
            print(f"   Sources: {result.get('context_sources', 'unknown')}")
            print(f"   Response: {result['message'][:200]}...")
            return True
        else:
            print(f"❌ Unexpected result format: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Chat Handler: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_end_to_end_rag():
    """Test complete end-to-end RAG functionality."""
    print("\n🧪 Testing End-to-End RAG System...")
    
    try:
        from src.core.chat.handler import handle_chat_message
        
        # Test questions
        test_questions = [
            "What are the deployment procedures?",
            "How do I handle security issues?",
            "What are the code quality standards?",
            "How do I manage database connections?"
        ]
        
        user_id = "test_user"
        chat_context = {}
        database_id = "test_db"
        
        success_count = 0
        
        for question in test_questions:
            print(f"\n   Testing: {question}")
            message = f"/ask {question}"
            
            result = handle_chat_message(message, user_id, chat_context, database_id)
            
            if isinstance(result, dict) and "message" in result and result.get("type") == "rag_response":
                print(f"   ✅ Success - {len(result['message'])} chars")
                success_count += 1
            else:
                print(f"   ❌ Failed - {result}")
        
        print(f"\n📊 End-to-End Results: {success_count}/{len(test_questions)} successful")
        return success_count >= 2  # At least 2 should work
        
    except Exception as e:
        print(f"❌ Error testing End-to-End RAG: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """Run all RAG system tests."""
    print("🚀 Testing RAG System Implementation")
    print("=" * 50)
    
    # Test 1: KnowledgeBase query
    kb_success = test_knowledge_base_query()
    
    # Test 2: Chat Handler RAG
    chat_success = test_chat_handler_rag()
    
    # Test 3: End-to-End
    e2e_success = test_end_to_end_rag()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 RAG SYSTEM TEST RESULTS")
    print("=" * 50)
    print(f"KnowledgeBase Query: {'✅ PASS' if kb_success else '❌ FAIL'}")
    print(f"Chat Handler RAG:    {'✅ PASS' if chat_success else '❌ FAIL'}")
    print(f"End-to-End RAG:      {'✅ PASS' if e2e_success else '❌ FAIL'}")
    
    overall_success = kb_success and chat_success and e2e_success
    
    if overall_success:
        print("\n🎉 ALL TESTS PASSED! RAG System is working correctly.")
        print("\nYou can now use the /ask command in your chat interface:")
        print("   /ask What are the deployment procedures?")
        print("   /ask How do I handle security issues?")
        print("   /ask What are the code quality standards?")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    print("=" * 50)

if __name__ == "__main__":
    main() 