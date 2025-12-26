import json
import os
import sys
import time
import traceback
from io import BytesIO
from datetime import datetime

import pika
from minio import Minio
from minio.error import S3Error

from processors.resize import resize_image
from processors.watermark import add_watermark
from processors.filter import apply_filter


# Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

WORKER_ID = os.getenv("WORKER_ID", "1")

TASK_QUEUE = "image_processing"
NOTIFICATION_QUEUE = "notifications"
UPLOAD_BUCKET = "images"
PROCESSED_BUCKET = "processed"


# MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)


def process_image(image_data: bytes, operations: list) -> bytes:
    """
    Process image with specified operations
    
    Args:
        image_data: Original image bytes
        operations: List of operations to apply
        
    Returns:
        Processed image bytes
    """
    result = image_data
    
    for operation in operations:
        print(f"[Worker {WORKER_ID}] Applying operation: {operation}")
        
        if operation == "resize":
            result = resize_image(result)
        elif operation == "watermark":
            result = add_watermark(result)
        elif operation == "filter":
            result = apply_filter(result, filter_type="blur")
        else:
            print(f"[Worker {WORKER_ID}] Unknown operation: {operation}")
    
    return result


def callback(ch, method, properties, body):
    """
    Process message from queue
    """
    try:
        # Parse message
        message = json.loads(body)
        job_id = message["job_id"]
        file_name = message["file_name"]
        operations = message["operations"]
        bucket = message.get("bucket", UPLOAD_BUCKET)
        
        print(f"\n[Worker {WORKER_ID}] Processing job {job_id}")
        print(f"[Worker {WORKER_ID}] File: {file_name}")
        print(f"[Worker {WORKER_ID}] Operations: {operations}")
        
        start_time = time.time()
        
        # Download image from MinIO
        print(f"[Worker {WORKER_ID}] Downloading from MinIO...")
        response = minio_client.get_object(bucket, file_name)
        image_data = response.read()
        response.close()
        response.release_conn()
        
        # Process image
        print(f"[Worker {WORKER_ID}] Processing image...")
        processed_data = process_image(image_data, operations)
        
        # Upload processed image
        processed_file_name = f"processed_{file_name}"
        print(f"[Worker {WORKER_ID}] Uploading processed image...")
        
        minio_client.put_object(
            PROCESSED_BUCKET,
            processed_file_name,
            BytesIO(processed_data),
            length=len(processed_data),
            content_type="image/jpeg"
        )
        
        processing_time = time.time() - start_time
        
        # Send notification
        notification = {
            "job_id": job_id,
            "status": "completed",
            "processed_file": processed_file_name,
            "processing_time": processing_time,
            "worker_id": WORKER_ID,
            "timestamp": datetime.now().isoformat()
        }
        
        ch.basic_publish(
            exchange='',
            routing_key=NOTIFICATION_QUEUE,
            body=json.dumps(notification),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )
        
        print(f"[Worker {WORKER_ID}] Job {job_id} completed in {processing_time:.2f}s")
        
        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f"[Worker {WORKER_ID}] Error processing message: {e}")
        traceback.print_exc()
        
        # Reject and requeue (will go to DLQ after retries)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    """
    Main worker loop
    """
    print(f"[Worker {WORKER_ID}] Starting...")
    print(f"[Worker {WORKER_ID}] RabbitMQ: {RABBITMQ_HOST}:{RABBITMQ_PORT}")
    print(f"[Worker {WORKER_ID}] MinIO: {MINIO_ENDPOINT}")
    
    # Wait for services to be ready
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Test RabbitMQ connection
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            # Declare queue
            channel.queue_declare(queue=TASK_QUEUE, durable=True)
            channel.queue_declare(queue=NOTIFICATION_QUEUE, durable=True)
            
            # Set QoS - process one message at a time
            channel.basic_qos(prefetch_count=1)
            
            # Start consuming
            print(f"[Worker {WORKER_ID}] Waiting for messages...")
            channel.basic_consume(queue=TASK_QUEUE, on_message_callback=callback)
            
            channel.start_consuming()
            
        except KeyboardInterrupt:
            print(f"\n[Worker {WORKER_ID}] Shutting down...")
            sys.exit(0)
            
        except Exception as e:
            retry_count += 1
            print(f"[Worker {WORKER_ID}] Connection error (attempt {retry_count}/{max_retries}): {e}")
            time.sleep(2)
    
    print(f"[Worker {WORKER_ID}] Failed to connect after {max_retries} attempts")
    sys.exit(1)


if __name__ == "__main__":
    main()
