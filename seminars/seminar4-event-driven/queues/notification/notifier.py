import json
import os
import sys
import time
from datetime import datetime

import pika


# Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

NOTIFICATION_QUEUE = "notifications"


def callback(ch, method, properties, body):
    """
    Process notification message
    """
    try:
        notification = json.loads(body)
        
        job_id = notification.get("job_id")
        status = notification.get("status")
        processed_file = notification.get("processed_file")
        processing_time = notification.get("processing_time", 0)
        worker_id = notification.get("worker_id", "unknown")
        
        print(f"\n{'='*60}")
        print(f"[Notification Service] Job Completed!")
        print(f"{'='*60}")
        print(f"Job ID: {job_id}")
        print(f"Status: {status}")
        print(f"Processed File: {processed_file}")
        print(f"Processing Time: {processing_time:.2f}s")
        print(f"Worker: {worker_id}")
        print(f"Timestamp: {notification.get('timestamp')}")
        print(f"{'='*60}\n")
        
        # In a real system, this would:
        # - Send email notification
        # - Update database
        # - Trigger webhook
        # - Push notification to mobile app
        # etc.
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f"[Notification Service] Error processing notification: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    """
    Main notification service loop
    """
    print("[Notification Service] Starting...")
    print(f"[Notification Service] RabbitMQ: {RABBITMQ_HOST}:{RABBITMQ_PORT}")
    
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
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
            channel.queue_declare(queue=NOTIFICATION_QUEUE, durable=True)
            
            # Set QoS
            channel.basic_qos(prefetch_count=1)
            
            # Start consuming
            print("[Notification Service] Waiting for notifications...")
            channel.basic_consume(queue=NOTIFICATION_QUEUE, on_message_callback=callback)
            
            channel.start_consuming()
            
        except KeyboardInterrupt:
            print("\n[Notification Service] Shutting down...")
            sys.exit(0)
            
        except Exception as e:
            retry_count += 1
            print(f"[Notification Service] Connection error (attempt {retry_count}/{max_retries}): {e}")
            time.sleep(2)
    
    print(f"[Notification Service] Failed to connect after {max_retries} attempts")
    sys.exit(1)


if __name__ == "__main__":
    main()
