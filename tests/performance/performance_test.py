#!/usr/bin/env python3
"""
Performance testing for AI Team Support API.
Benchmarks endpoint response times and identifies bottlenecks.
"""
import sys
import os
import time
import statistics
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class PerformanceTester:
    """Performance testing class for API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.results = {}
        
    def log(self, message: str):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def get_auth_token(self) -> bool:
        """Get authentication token for testing."""
        try:
            # Register a test user
            register_data = {
                'email': f'perf_test_{int(time.time())}@example.com',
                'password': 'TestPassword123!',
                'full_name': 'Performance Test User'
            }
            
            response = self.session.post(f"{self.base_url}/api/auth/register", 
                                       json=register_data)
            
            if response.status_code == 201:
                # Login to get token
                login_data = {
                    'email': register_data['email'],
                    'password': register_data['password']
                }
                
                response = self.session.post(f"{self.base_url}/api/auth/login", 
                                           json=login_data)
                
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get('data', {}).get('token')
                    self.log("✅ Authentication token obtained")
                    return True
                else:
                    self.log("❌ Login failed")
                    return False
            else:
                self.log("❌ Registration failed")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}")
            return False
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    headers: Dict = None) -> Tuple[int, float]:
        """Make a request and return status code and response time."""
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {}
        
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            else:
                return 0, 0
                
            response_time = time.time() - start_time
            return response.status_code, response_time
            
        except Exception as e:
            self.log(f"❌ Request error for {endpoint}: {str(e)}")
            return 0, 0
    
    def test_endpoint_performance(self, method: str, endpoint: str, 
                                 data: Dict = None, iterations: int = 10) -> Dict:
        """Test performance of a single endpoint."""
        self.log(f"🧪 Testing {method} {endpoint} ({iterations} iterations)")
        
        response_times = []
        success_count = 0
        
        for i in range(iterations):
            status_code, response_time = self.make_request(method, endpoint, data)
            
            if status_code in [200, 201]:
                success_count += 1
                response_times.append(response_time)
            
            # Small delay between requests
            time.sleep(0.1)
        
        if response_times:
            return {
                'endpoint': endpoint,
                'method': method,
                'iterations': iterations,
                'success_count': success_count,
                'success_rate': success_count / iterations,
                'avg_response_time': statistics.mean(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'median_response_time': statistics.median(response_times),
                'std_deviation': statistics.stdev(response_times) if len(response_times) > 1 else 0
            }
        else:
            return {
                'endpoint': endpoint,
                'method': method,
                'iterations': iterations,
                'success_count': 0,
                'success_rate': 0,
                'avg_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0,
                'median_response_time': 0,
                'std_deviation': 0
            }
    
    def test_concurrent_requests(self, endpoint: str, method: str = 'GET', 
                                concurrent_users: int = 10, requests_per_user: int = 5) -> Dict:
        """Test concurrent request performance."""
        self.log(f"🧪 Testing concurrent requests: {concurrent_users} users, {requests_per_user} requests each")
        
        def make_concurrent_request():
            response_times = []
            for _ in range(requests_per_user):
                status_code, response_time = self.make_request(method, endpoint)
                if status_code in [200, 201]:
                    response_times.append(response_time)
                time.sleep(0.1)
            return response_times
        
        all_response_times = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_concurrent_request) for _ in range(concurrent_users)]
            
            for future in as_completed(futures):
                response_times = future.result()
                all_response_times.extend(response_times)
        
        total_time = time.time() - start_time
        total_requests = concurrent_users * requests_per_user
        
        if all_response_times:
            return {
                'endpoint': endpoint,
                'method': method,
                'concurrent_users': concurrent_users,
                'requests_per_user': requests_per_user,
                'total_requests': total_requests,
                'total_time': total_time,
                'requests_per_second': total_requests / total_time,
                'avg_response_time': statistics.mean(all_response_times),
                'min_response_time': min(all_response_times),
                'max_response_time': max(all_response_times),
                'median_response_time': statistics.median(all_response_times),
                'success_count': len(all_response_times),
                'success_rate': len(all_response_times) / total_requests
            }
        else:
            return {
                'endpoint': endpoint,
                'method': method,
                'concurrent_users': concurrent_users,
                'requests_per_user': requests_per_user,
                'total_requests': total_requests,
                'total_time': total_time,
                'requests_per_second': 0,
                'avg_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0,
                'median_response_time': 0,
                'success_count': 0,
                'success_rate': 0
            }
    
    def run_performance_tests(self) -> Dict:
        """Run comprehensive performance tests."""
        self.log("🚀 Starting performance testing...")
        
        # Get authentication token
        if not self.get_auth_token():
            self.log("❌ Failed to get authentication token")
            return {}
        
        # Define test endpoints
        test_endpoints = [
            # Public endpoints
            ('GET', '/api/health'),
            ('GET', '/api/version'),
            
            # Authentication endpoints
            ('GET', '/api/auth/profile'),
            
            # Task endpoints
            ('GET', '/api/tasks/user/tasks'),
            ('GET', '/api/insights/categories'),
            ('GET', '/api/insights/dashboard-data'),
            
            # Processing endpoints (with data)
            ('POST', '/api/tasks/process_update', {
                'text': 'Test performance with this simple update: review quarterly report, call client, schedule meeting'
            }),
            
            # Chat endpoint
            ('POST', '/api/insights/chat', {
                'message': 'What tasks do I have for today?'
            })
        ]
        
        results = {
            'single_request_tests': [],
            'concurrent_tests': [],
            'summary': {}
        }
        
        # Test single request performance
        for test in test_endpoints:
            method, endpoint = test[0], test[1]
            data = test[2] if len(test) > 2 else None
            
            result = self.test_endpoint_performance(method, endpoint, data, iterations=5)
            results['single_request_tests'].append(result)
        
        # Test concurrent performance for key endpoints
        concurrent_endpoints = [
            ('GET', '/api/health'),
            ('GET', '/api/auth/profile'),
            ('GET', '/api/tasks/user/tasks')
        ]
        
        for method, endpoint in concurrent_endpoints:
            result = self.test_concurrent_requests(endpoint, method, concurrent_users=5, requests_per_user=3)
            results['concurrent_tests'].append(result)
        
        # Generate summary
        self.generate_summary(results)
        
        return results
    
    def generate_summary(self, results: Dict):
        """Generate performance summary."""
        self.log("\n📊 Performance Test Summary")
        self.log("=" * 50)
        
        # Single request summary
        self.log("\n🔍 Single Request Performance:")
        for test in results['single_request_tests']:
            status = "✅" if test['success_rate'] >= 0.8 else "⚠️"
            self.log(f"{status} {test['method']} {test['endpoint']}")
            self.log(f"   Avg: {test['avg_response_time']:.3f}s | Success: {test['success_rate']:.1%}")
        
        # Concurrent request summary
        self.log("\n⚡ Concurrent Request Performance:")
        for test in results['concurrent_tests']:
            status = "✅" if test['success_rate'] >= 0.8 else "⚠️"
            self.log(f"{status} {test['method']} {test['endpoint']}")
            self.log(f"   RPS: {test['requests_per_second']:.1f} | Avg: {test['avg_response_time']:.3f}s")
        
        # Identify bottlenecks
        self.identify_bottlenecks(results)
    
    def identify_bottlenecks(self, results: Dict):
        """Identify performance bottlenecks."""
        self.log("\n🔍 Performance Analysis:")
        
        # Find slowest endpoints
        single_tests = results['single_request_tests']
        if single_tests:
            slowest = max(single_tests, key=lambda x: x['avg_response_time'])
            fastest = min(single_tests, key=lambda x: x['avg_response_time'])
            
            self.log(f"🐌 Slowest endpoint: {slowest['method']} {slowest['endpoint']}")
            self.log(f"   Response time: {slowest['avg_response_time']:.3f}s")
            
            self.log(f"⚡ Fastest endpoint: {fastest['method']} {fastest['endpoint']}")
            self.log(f"   Response time: {fastest['avg_response_time']:.3f}s")
        
        # Check success rates
        low_success = [t for t in single_tests if t['success_rate'] < 0.8]
        if low_success:
            self.log("\n⚠️ Endpoints with low success rates:")
            for test in low_success:
                self.log(f"   {test['method']} {test['endpoint']}: {test['success_rate']:.1%}")
        
        # Concurrent performance
        concurrent_tests = results['concurrent_tests']
        if concurrent_tests:
            lowest_rps = min(concurrent_tests, key=lambda x: x['requests_per_second'])
            self.log(f"\n🐌 Lowest throughput: {lowest_rps['method']} {lowest_rps['endpoint']}")
            self.log(f"   Requests/second: {lowest_rps['requests_per_second']:.1f}")

def main():
    """Main performance test runner."""
    print("🧪 AI Team Support Performance Testing")
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
    
    # Run performance tests
    tester = PerformanceTester()
    results = tester.run_performance_tests()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"performance_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filename}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 