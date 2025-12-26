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


def get_queue_stats():
    """Get statistics for all queues"""
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        queues = ["image_processing", "notifications", "dead_letter_queue"]
        stats = {}
        
        for queue_name in queues:
            try:
                result = channel.queue_declare(queue=queue_name, passive=True)
                stats[queue_name] = {
                    "messages": result.method.message_count,
                    "consumers": result.method.consumer_count
                }
            except Exception as e:
                stats[queue_name] = {"error": str(e)}
        
        connection.close()
        return stats
        
    except Exception as e:
        return {"error": str(e)}


def print_stats(stats):
    """Pretty print queue statistics"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("\n" + "="*70)
    print(f"Queue Monitor - {timestamp}")
    print("="*70)
    
    if "error" in stats:
        print(f"ERROR: {stats['error']}")
        return
    
    for queue_name, queue_stats in stats.items():
        if "error" in queue_stats:
            print(f"\n{queue_name}: ERROR - {queue_stats['error']}")
        else:
            messages = queue_stats["messages"]
            consumers = queue_stats["consumers"]
            status = "✓" if messages == 0 else "⚠" if messages < 100 else "✗"
            
            print(f"\n{queue_name}:")
            print(f"  Status: {status}")
            print(f"  Messages: {messages}")
            print(f"  Consumers: {consumers}")
            
            if messages > 0 and consumers == 0:
                print("  WARNING: No consumers processing messages!")
    
    print("\n" + "="*70 + "\n")


def main():
    """Main monitoring loop"""
    print("Queue Monitor - Starting...")
    print(f"Monitoring RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            stats = get_queue_stats()
            print_stats(stats)
            time.sleep(5)  # Update every 5 seconds
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
