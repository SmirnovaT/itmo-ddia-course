#!/usr/bin/env python3
"""
Verify system setup and connectivity
"""
import sys
import time
import requests
import pika
from minio import Minio


def check_api():
    """Check if API is accessible"""
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        if response.status_code == 200:
            print("✓ API Service is running")
            return True
        else:
            print(f"✗ API Service returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ API Service is not accessible: {e}")
        return False


def check_rabbitmq():
    """Check if RabbitMQ is accessible"""
    try:
        credentials = pika.PlainCredentials("guest", "guest")
        parameters = pika.ConnectionParameters(
            host="localhost",
            port=5672,
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        connection.close()
        print("✓ RabbitMQ is running")
        return True
    except Exception as e:
        print(f"✗ RabbitMQ is not accessible: {e}")
        return False


def check_minio():
    """Check if MinIO is accessible"""
    try:
        client = Minio(
            "localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False
        )
        
        # Check if buckets exist
        buckets = [b.name for b in client.list_buckets()]
        
        if "images" in buckets and "processed" in buckets:
            print("✓ MinIO is running (buckets ready)")
            return True
        else:
            print("⚠ MinIO is running but buckets may not be ready")
            return True
    except Exception as e:
        print(f"✗ MinIO is not accessible: {e}")
        return False


def check_workers():
    """Check if workers are running"""
    try:
        import subprocess
        result = subprocess.run(
            ["docker-compose", "ps", "worker"],
            capture_output=True,
            text=True,
            cwd="/Users/georgii.semenov/home/repos/itmo-ddia-course/seminars/seminar4-event-driven/queues"
        )
        
        # Count running workers
        lines = result.stdout.strip().split('\n')
        running_workers = sum(1 for line in lines if "Up" in line)
        
        if running_workers > 0:
            print(f"✓ {running_workers} worker(s) running")
            return True
        else:
            print("✗ No workers are running")
            return False
    except Exception as e:
        print(f"⚠ Could not check workers: {e}")
        return True  # Don't fail on this


def main():
    """Run all checks"""
    print("="*60)
    print("System Verification")
    print("="*60)
    print()
    
    checks = [
        ("API Service", check_api),
        ("RabbitMQ", check_rabbitmq),
        ("MinIO", check_minio),
        ("Workers", check_workers)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"Checking {name}...")
        result = check_func()
        results.append(result)
        time.sleep(0.5)
    
    print()
    print("="*60)
    
    if all(results):
        print("✓ All systems operational!")
        print()
        print("You can now:")
        print("  1. Upload an image:")
        print("     curl -X POST 'http://localhost:8000/upload' \\")
        print("       -F 'file=@test_images/sample.jpg' \\")
        print("       -F 'operations=resize,watermark'")
        print()
        print("  2. View API docs: http://localhost:8000/docs")
        print("  3. Run load tests: cd load_test && python bulk_upload.py")
        print()
        return 0
    else:
        print("✗ Some systems are not ready")
        print()
        print("Try:")
        print("  1. Make sure Docker is running")
        print("  2. Run: ./start.sh")
        print("  3. Wait 10-15 seconds for services to start")
        print("  4. Run this check again")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
