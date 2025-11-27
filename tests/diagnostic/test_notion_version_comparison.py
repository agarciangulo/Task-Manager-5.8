#!/usr/bin/env python3
"""
Compare what works in different notion-client versions.
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_current_version():
    """Test what we have locally (2.3.0)"""
    print("=" * 60)
    print("TESTING: Local version (2.3.0)")
    print("=" * 60)
    
    try:
        from notion_client import Client
        
        token = os.getenv('NOTION_TOKEN')
        db_id = os.getenv('NOTION_USERS_DB_ID')
        
        if not token or not db_id:
            print("Missing env vars")
            return False
        
        client = Client(auth=token)
        
        print(f"\n1. Testing databases.query() (2.3.0 has this)...")
        try:
            response = client.databases.query(database_id=db_id, page_size=1)
            print(f"   ✅ databases.query() works!")
            print(f"   - Results: {len(response.get('results', []))}")
            return True
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_request_method():
    """Test if request() works at all"""
    print("\n" + "=" * 60)
    print("TESTING: request() method")
    print("=" * 60)
    
    try:
        from notion_client import Client
        
        token = os.getenv('NOTION_TOKEN')
        db_id = os.getenv('NOTION_USERS_DB_ID')
        
        client = Client(auth=token)
        
        # Try different endpoints to see what works
        print("\n1. Testing pages.retrieve() (this should work)...")
        try:
            # Get a page ID from the database first
            db_info = client.databases.retrieve(database_id=db_id)
            print(f"   ✅ Database retrieve works")
            
            # Try to get pages from the database
            pages = client.databases.query(database_id=db_id, page_size=1)
            if pages.get('results'):
                page_id = pages['results'][0]['id']
                print(f"   ✅ Got page ID: {page_id[:8]}...")
                
                # Now test request() with a known working endpoint
                print(f"\n2. Testing request() with pages endpoint...")
                page_data = client.request(
                    path=f"pages/{page_id}",
                    method="GET"
                )
                print(f"   ✅ request() works with pages endpoint!")
                return True
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_databases_query_via_request():
    """Test if we can query databases via request()"""
    print("\n" + "=" * 60)
    print("TESTING: databases query via request()")
    print("=" * 60)
    
    try:
        from notion_client import Client
        
        token = os.getenv('NOTION_TOKEN')
        db_id = os.getenv('NOTION_USERS_DB_ID')
        
        client = Client(auth=token)
        
        # Try the exact endpoint
        print(f"\n1. Testing request() with databases/query endpoint...")
        
        # Try without /v1/ (client adds it)
        try:
            response = client.request(
                path=f"databases/{db_id}/query",
                method="POST",
                body={"page_size": 1}
            )
            print(f"   ✅ SUCCESS without /v1/!")
            print(f"   - Results: {len(response.get('results', []))}")
            return True
        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ Failed: {error_msg[:150]}")
            
            # Check error details
            if "Invalid request URL" in error_msg:
                print(f"\n   Analyzing error...")
                # Maybe the issue is the database ID format?
                # Or maybe we need different parameters?
                
                # Try with database_id in body instead of path
                print(f"\n2. Trying with database_id in body...")
                try:
                    response = client.request(
                        path="databases/query",
                        method="POST",
                        body={
                            "database_id": db_id,
                            "page_size": 1
                        }
                    )
                    print(f"   ✅ SUCCESS with database_id in body!")
                    return True
                except Exception as e2:
                    print(f"   ❌ Also failed: {str(e2)[:150]}")
            
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔍 Testing Notion Client Versions\n")
    
    test1 = test_current_version()
    test2 = test_request_method()
    test3 = test_databases_query_via_request()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"databases.query() (2.3.0): {'✅' if test1 else '❌'}")
    print(f"request() with pages: {'✅' if test2 else '❌'}")
    print(f"request() with databases: {'✅' if test3 else '❌'}")
    
    if test3:
        print("\n✅ Found working method! Use this in auth_service.py")
    else:
        print("\n⚠️  request() method isn't working")
        print("   Consider upgrading notion-client to 2.x which has databases.query()")





