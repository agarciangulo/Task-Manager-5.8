#!/usr/bin/env python3
"""
Comprehensive test script for Chroma integration.
Tests similarity matching, performance, and migration from old system.
"""
import os
import sys
import time
import json
from datetime import datetime
from typing import List, Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.chroma_embedding_manager import ChromaEmbeddingManager
from src.core.task_similarity import check_task_similarity, get_chroma_stats
from src.core.embedding_manager import EmbeddingManager

def test_chroma_initialization():
    """Test Chroma initialization and basic functionality."""
    print("🧪 Testing Chroma Initialization")
    print("=" * 50)
    
    try:
        # Initialize Chroma manager
        chroma_manager = ChromaEmbeddingManager()
        
        # Get collection stats
        stats = chroma_manager.get_collection_stats()
        print(f"✅ Chroma initialized successfully")
        print(f"   Collection: {stats.get('collection_name', 'Unknown')}")
        print(f"   Total embeddings: {stats.get('total_embeddings', 0)}")
        print(f"   Embedding dimension: {stats.get('embedding_dimension', 0)}")
        print(f"   Model: {stats.get('model_name', 'Unknown')}")
        
        return chroma_manager
        
    except Exception as e:
        print(f"❌ Chroma initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_embedding_generation(chroma_manager):
    """Test embedding generation and storage."""
    print("\n🧪 Testing Embedding Generation")
    print("=" * 50)
    
    test_texts = [
        "Implement user authentication system",
        "Set up login functionality",
        "Create database backup script",
        "Optimize database queries",
        "Fix slow database performance",
        "Update API documentation",
        "Write technical documentation",
        "Configure CI/CD pipeline",
        "Set up automated testing",
        "Deploy application to production"
    ]
    
    try:
        # Test single embedding
        print("📝 Testing single embedding generation...")
        start_time = time.time()
        embedding = chroma_manager.get_embedding(test_texts[0])
        single_time = time.time() - start_time
        
        if embedding is not None:
            print(f"✅ Single embedding generated in {single_time:.3f}s")
            print(f"   Dimension: {len(embedding)}")
        else:
            print("❌ Single embedding generation failed")
            return False
        
        # Test batch embeddings
        print("\n📝 Testing batch embedding generation...")
        start_time = time.time()
        embeddings = chroma_manager.get_batch_embeddings(test_texts)
        batch_time = time.time() - start_time
        
        if embeddings:
            print(f"✅ Batch embeddings generated in {batch_time:.3f}s")
            print(f"   Generated: {len(embeddings)} embeddings")
            print(f"   Average time per embedding: {batch_time/len(embeddings):.3f}s")
        else:
            print("❌ Batch embedding generation failed")
            return False
        
        # Test caching (should be faster on second run)
        print("\n📝 Testing embedding caching...")
        start_time = time.time()
        cached_embeddings = chroma_manager.get_batch_embeddings(test_texts)
        cache_time = time.time() - start_time
        
        print(f"✅ Cached embeddings retrieved in {cache_time:.3f}s")
        print(f"   Speed improvement: {batch_time/cache_time:.1f}x faster")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_similarity_search(chroma_manager):
    """Test similarity search functionality."""
    print("\n🧪 Testing Similarity Search")
    print("=" * 50)
    
    # Test tasks with known similarities
    test_cases = [
        {
            "query": "Implement user authentication system",
            "candidates": [
                "Set up login functionality",
                "Create user login system",
                "Configure authentication",
                "Update API documentation",
                "Fix database performance"
            ],
            "expected_similar": ["Set up login functionality", "Create user login system", "Configure authentication"]
        },
        {
            "query": "Optimize database queries",
            "candidates": [
                "Fix slow database performance",
                "Improve query performance",
                "Update API documentation",
                "Set up automated testing",
                "Deploy application to production"
            ],
            "expected_similar": ["Fix slow database performance", "Improve query performance"]
        }
    ]
    
    try:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 Test case {i}: '{test_case['query']}'")
            
            # Find similar texts
            similar_texts = chroma_manager.find_similar(
                query_text=test_case["query"],
                texts=test_case["candidates"],
                top_k=3,
                threshold=0.7
            )
            
            if similar_texts:
                print(f"✅ Found {len(similar_texts)} similar texts:")
                for result in similar_texts:
                    print(f"   - '{result['text']}' (similarity: {result['similarity']:.3f})")
                    
                    # Check if this was expected
                    if result['text'] in test_case['expected_similar']:
                        print(f"     ✅ Expected match")
                    else:
                        print(f"     ⚠️  Unexpected match")
            else:
                print("❌ No similar texts found")
        
        return True
        
    except Exception as e:
        print(f"❌ Similarity search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_task_similarity_integration():
    """Test the integrated task similarity system."""
    print("\n🧪 Testing Task Similarity Integration")
    print("=" * 50)
    
    # Test tasks
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
        },
        {
            "task": "Update API documentation",
            "status": "To Do",
            "employee": "Alice Brown",
            "category": "Documentation"
        },
        {
            "task": "Configure authentication",
            "status": "In Progress",
            "employee": "Charlie Wilson",
            "category": "Security"
        }
    ]
    
    try:
        print("📝 Testing task similarity check...")
        start_time = time.time()
        
        result = check_task_similarity(new_task, existing_tasks)
        
        similarity_time = time.time() - start_time
        
        print(f"✅ Task similarity check completed in {similarity_time:.3f}s")
        print(f"   Is match: {result['is_match']}")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Explanation: {result['explanation']}")
        
        if result['is_match']:
            matched_task = result['matched_task']
            print(f"   Matched task: '{matched_task['task']}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Task similarity integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_comparison():
    """Compare performance between old and new systems."""
    print("\n🧪 Testing Performance Comparison")
    print("=" * 50)
    
    # Generate test data
    test_texts = [f"Test task {i} for performance comparison" for i in range(100)]
    
    try:
        # Test old system (if available)
        print("📝 Testing old embedding system...")
        try:
            old_manager = EmbeddingManager()
            start_time = time.time()
            old_embeddings = old_manager.get_batch_embeddings(test_texts[:10])  # Limit for old system
            old_time = time.time() - start_time
            print(f"   Old system: {old_time:.3f}s for {len(old_embeddings)} embeddings")
        except Exception as e:
            print(f"   Old system not available: {e}")
            old_time = None
        
        # Test new Chroma system
        print("📝 Testing new Chroma system...")
        chroma_manager = ChromaEmbeddingManager()
        start_time = time.time()
        chroma_embeddings = chroma_manager.get_batch_embeddings(test_texts)
        chroma_time = time.time() - start_time
        print(f"   Chroma system: {chroma_time:.3f}s for {len(chroma_embeddings)} embeddings")
        
        if old_time:
            speedup = old_time / chroma_time
            print(f"   Performance improvement: {speedup:.1f}x faster")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance comparison test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_migration_from_old_cache():
    """Test migration from old cache to Chroma."""
    print("\n🧪 Testing Migration from Old Cache")
    print("=" * 50)
    
    # Create sample old cache data
    old_cache = {
        "Implement user authentication": {
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5] * 20,  # 100-dim vector
            "last_accessed": time.time()
        },
        "Set up login functionality": {
            "embedding": [0.2, 0.3, 0.4, 0.5, 0.6] * 20,
            "last_accessed": time.time()
        }
    }
    
    try:
        chroma_manager = ChromaEmbeddingManager()
        
        # Get initial stats
        initial_stats = chroma_manager.get_collection_stats()
        initial_count = initial_stats.get('total_embeddings', 0)
        
        print(f"📝 Initial embeddings: {initial_count}")
        
        # Migrate old cache
        print("📝 Migrating old cache...")
        chroma_manager.migrate_from_old_cache(old_cache)
        
        # Get final stats
        final_stats = chroma_manager.get_collection_stats()
        final_count = final_stats.get('total_embeddings', 0)
        
        print(f"📝 Final embeddings: {final_count}")
        print(f"📝 Migrated: {final_count - initial_count} embeddings")
        
        if final_count > initial_count:
            print("✅ Migration successful")
            return True
        else:
            print("❌ Migration failed - no new embeddings added")
            return False
        
    except Exception as e:
        print(f"❌ Migration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chroma_stats():
    """Test Chroma statistics and monitoring."""
    print("\n🧪 Testing Chroma Statistics")
    print("=" * 50)
    
    try:
        stats = get_chroma_stats()
        
        if stats:
            print("✅ Chroma statistics retrieved:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
        else:
            print("❌ Failed to retrieve Chroma statistics")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Chroma statistics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Chroma integration tests."""
    print("🚀 Starting Chroma Integration Tests")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Initialization
    chroma_manager = test_chroma_initialization()
    test_results.append(("Initialization", chroma_manager is not None))
    
    if chroma_manager:
        # Test 2: Embedding generation
        test_results.append(("Embedding Generation", test_embedding_generation(chroma_manager)))
        
        # Test 3: Similarity search
        test_results.append(("Similarity Search", test_similarity_search(chroma_manager)))
        
        # Test 4: Task similarity integration
        test_results.append(("Task Similarity Integration", test_task_similarity_integration()))
        
        # Test 5: Performance comparison
        test_results.append(("Performance Comparison", test_performance_comparison()))
        
        # Test 6: Migration
        test_results.append(("Migration from Old Cache", test_migration_from_old_cache()))
        
        # Test 7: Statistics
        test_results.append(("Chroma Statistics", test_chroma_stats()))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Chroma integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 