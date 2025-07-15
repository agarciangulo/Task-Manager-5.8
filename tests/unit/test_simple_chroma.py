#!/usr/bin/env python3
"""
Test script for simplified Chroma integration without sentence-transformers.
"""
import os
import sys
import time
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.chroma_embedding_manager_simple import SimpleChromaEmbeddingManager
from core.task_similarity import check_task_similarity, get_chroma_stats

def test_simple_chroma():
    """Test the simplified Chroma integration."""
    print("🧪 Testing Simplified Chroma Integration")
    print("=" * 60)
    
    try:
        # Initialize simplified Chroma manager
        print("📝 Initializing SimpleChromaEmbeddingManager...")
        chroma_manager = SimpleChromaEmbeddingManager()
        
        # Get collection stats
        stats = chroma_manager.get_collection_stats()
        print(f"✅ Chroma initialized successfully")
        print(f"   Collection: {stats.get('collection_name', 'Unknown')}")
        print(f"   Total embeddings: {stats.get('total_embeddings', 0)}")
        print(f"   Embedding dimension: {stats.get('embedding_dimension', 0)}")
        print(f"   Embedding function: {stats.get('embedding_function', 'Unknown')}")
        
        # Test embedding generation
        print("\n📝 Testing embedding generation...")
        test_texts = [
            "Implement user authentication system",
            "Set up login functionality",
            "Create database backup script",
            "Optimize database queries",
            "Fix slow database performance"
        ]
        
        start_time = time.time()
        embeddings = chroma_manager.get_batch_embeddings(test_texts)
        generation_time = time.time() - start_time
        
        print(f"✅ Generated {len(embeddings)} embeddings in {generation_time:.3f}s")
        
        # Test similarity search
        print("\n📝 Testing similarity search...")
        query = "Implement user authentication system"
        candidates = [
            "Set up login functionality",
            "Create database backup script",
            "Optimize database queries"
        ]
        
        start_time = time.time()
        similar_texts = chroma_manager.find_similar(
            query_text=query,
            texts=candidates,
            top_k=3,
            threshold=0.7
        )
        search_time = time.time() - start_time
        
        print(f"✅ Similarity search completed in {search_time:.3f}s")
        print(f"   Found {len(similar_texts)} similar texts:")
        for result in similar_texts:
            print(f"   - '{result['text']}' (similarity: {result['similarity']:.3f})")
        
        # Test task similarity integration
        print("\n📝 Testing task similarity integration...")
        new_task = {
            "task": "Implement user authentication system",
            "status": "In Progress",
            "employee": "John Doe",
            "category": "Security"
        }
        
        existing_tasks = [
            {
                "task": "Set up login functionality",
                "status": "Completed",
                "employee": "Jane Smith",
                "category": "Security"
            },
            {
                "task": "Create database backup script",
                "status": "In Progress",
                "employee": "Bob Johnson",
                "category": "DevOps"
            }
        ]
        
        start_time = time.time()
        result = check_task_similarity(new_task, existing_tasks)
        integration_time = time.time() - start_time
        
        print(f"✅ Task similarity check completed in {integration_time:.3f}s")
        print(f"   Is match: {result['is_match']}")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Explanation: {result['explanation']}")
        
        # Test Chroma stats
        print("\n📝 Testing Chroma statistics...")
        stats = get_chroma_stats()
        print("✅ Chroma statistics retrieved:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        print("\n🎉 All tests passed! Simplified Chroma integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_chroma()
    sys.exit(0 if success else 1) 