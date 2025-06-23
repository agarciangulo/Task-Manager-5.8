#!/usr/bin/env python3
"""
Startup script for the asynchronous task processing system.
Initializes Celery workers, Redis, and the main application.
"""
import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

def check_redis_connection():
    """Check if Redis is running and accessible."""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def start_redis():
    """Start Redis server if not running."""
    if check_redis_connection():
        print("Redis is already running")
        return True
    
    print("Starting Redis server...")
    try:
        # Try to start Redis using docker-compose
        subprocess.run([
            "docker-compose", "up", "-d", "redis"
        ], check=True, capture_output=True)
        
        # Wait for Redis to be ready
        for i in range(30):
            if check_redis_connection():
                print("✅ Redis started successfully")
                return True
            time.sleep(1)
        
        print("❌ Redis failed to start within 30 seconds")
        return False
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Redis: {e}")
        return False

def start_celery_worker():
    """Start Celery worker process."""
    print("Starting Celery worker...")
    try:
        worker_process = subprocess.Popen([
            sys.executable, "-m", "celery", "-A", "celery_config", 
            "worker", "--loglevel=info", "--concurrency=4"
        ])
        print(f"✅ Celery worker started with PID: {worker_process.pid}")
        return worker_process
    except Exception as e:
        print(f"❌ Failed to start Celery worker: {e}")
        return None

def start_celery_beat():
    """Start Celery beat scheduler."""
    print("Starting Celery beat scheduler...")
    try:
        beat_process = subprocess.Popen([
            sys.executable, "-m", "celery", "-A", "celery_config", 
            "beat", "--loglevel=info"
        ])
        print(f"✅ Celery beat started with PID: {beat_process.pid}")
        return beat_process
    except Exception as e:
        print(f"❌ Failed to start Celery beat: {e}")
        return None

def start_flower():
    """Start Flower monitoring interface."""
    print("Starting Flower monitoring...")
    try:
        flower_process = subprocess.Popen([
            sys.executable, "-m", "celery", "-A", "celery_config", 
            "flower", "--port=5555"
        ])
        print(f"✅ Flower started with PID: {flower_process.pid}")
        return flower_process
    except Exception as e:
        print(f"❌ Failed to start Flower: {e}")
        return None

def start_flask_app():
    """Start the Flask application."""
    print("Starting Flask application...")
    try:
        flask_process = subprocess.Popen([
            sys.executable, "app_flask.py"
        ])
        print(f"✅ Flask app started with PID: {flask_process.pid}")
        return flask_process
    except Exception as e:
        print(f"❌ Failed to start Flask app: {e}")
        return None

def cleanup_processes(processes):
    """Clean up running processes."""
    print("\n🛑 Shutting down processes...")
    for name, process in processes.items():
        if process and process.poll() is None:
            print(f"Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            print(f"✅ {name} stopped")

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    cleanup_processes(running_processes)
    sys.exit(0)

def test_async_system():
    """Test the async system by queuing a simple task."""
    print("\n🧪 Testing async system...")
    try:
        from celery_config import celery_app
        from core.tasks.ai_tasks import generate_content_async
        
        # Queue a simple test task
        result = generate_content_async.delay("Hello, this is a test message!", temperature=0.7)
        print(f"✅ Test task queued with ID: {result.id}")
        
        # Wait for result
        print("Waiting for task completion...")
        task_result = result.get(timeout=30)
        
        if task_result['success']:
            print("✅ Test task completed successfully")
            print(f"Response: {task_result['content'][:100]}...")
        else:
            print(f"❌ Test task failed: {task_result['error']}")
            
    except Exception as e:
        print(f"❌ Async system test failed: {e}")

def main():
    """Main startup function."""
    global running_processes
    running_processes = {}
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Starting Task Manager Async System")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("celery_config.py").exists():
        print("❌ celery_config.py not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Start Redis
    if not start_redis():
        print("❌ Failed to start Redis. Exiting.")
        sys.exit(1)
    
    # Start Celery worker
    worker_process = start_celery_worker()
    if worker_process:
        running_processes['celery_worker'] = worker_process
    
    # Start Celery beat
    beat_process = start_celery_beat()
    if beat_process:
        running_processes['celery_beat'] = beat_process
    
    # Start Flower (optional)
    flower_process = start_flower()
    if flower_process:
        running_processes['flower'] = flower_process
    
    # Start Flask app
    flask_process = start_flask_app()
    if flask_process:
        running_processes['flask_app'] = flask_process
    
    # Wait a moment for everything to start
    time.sleep(5)
    
    # Test the async system
    test_async_system()
    
    print("\n🎉 Async system started successfully!")
    print("\n📋 Services running:")
    print(f"  - Flask App: http://localhost:5001")
    print(f"  - Flower Monitoring: http://localhost:5555")
    print(f"  - Redis: localhost:6379")
    print(f"  - Celery Worker: {running_processes.get('celery_worker', 'Not running')}")
    print(f"  - Celery Beat: {running_processes.get('celery_beat', 'Not running')}")
    
    print("\n⏹️  Press Ctrl+C to stop all services")
    
    try:
        # Keep the main process running
        while True:
            time.sleep(1)
            
            # Check if any processes have died
            for name, process in running_processes.items():
                if process and process.poll() is not None:
                    print(f"⚠️  {name} process has stopped unexpectedly")
                    
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    finally:
        cleanup_processes(running_processes)
        print("✅ All services stopped")

if __name__ == "__main__":
    main() 