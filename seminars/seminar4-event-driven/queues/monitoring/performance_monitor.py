import time
import statistics
from datetime import datetime
from collections import defaultdict

import pika


class PerformanceMonitor:
    """Monitor performance metrics of the system"""
    
    def __init__(self, rabbitmq_host="localhost", rabbitmq_port=5672):
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_port = rabbitmq_port
        self.metrics_history = defaultdict(list)
        
    def get_queue_metrics(self):
        """Get current queue metrics"""
        try:
            credentials = pika.PlainCredentials("guest", "guest")
            parameters = pika.ConnectionParameters(
                host=self.rabbitmq_host,
                port=self.rabbitmq_port,
                credentials=credentials
            )
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            result = channel.queue_declare(queue="image_processing", passive=True)
            queue_size = result.method.message_count
            
            connection.close()
            return queue_size
            
        except Exception as e:
            print(f"Error getting metrics: {e}")
            return None
    
    def record_metric(self, metric_name, value):
        """Record a metric value"""
        self.metrics_history[metric_name].append({
            "timestamp": datetime.now(),
            "value": value
        })
    
    def calculate_stats(self, metric_name, window_size=10):
        """Calculate statistics for a metric"""
        if metric_name not in self.metrics_history:
            return None
        
        values = [m["value"] for m in self.metrics_history[metric_name][-window_size:]]
        
        if not values:
            return None
        
        return {
            "current": values[-1],
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0
        }
    
    def print_summary(self):
        """Print performance summary"""
        print("\n" + "="*70)
        print(f"Performance Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        for metric_name in self.metrics_history:
            stats = self.calculate_stats(metric_name)
            if stats:
                print(f"\n{metric_name}:")
                print(f"  Current: {stats['current']:.2f}")
                print(f"  Mean: {stats['mean']:.2f}")
                print(f"  Median: {stats['median']:.2f}")
                print(f"  Min: {stats['min']:.2f}")
                print(f"  Max: {stats['max']:.2f}")
                print(f"  StdDev: {stats['stdev']:.2f}")
        
        print("\n" + "="*70 + "\n")
    
    def monitor(self, interval=5):
        """Start monitoring loop"""
        print("Performance Monitor - Starting...")
        print(f"Monitoring interval: {interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                queue_size = self.get_queue_metrics()
                
                if queue_size is not None:
                    self.record_metric("queue_size", queue_size)
                    
                    if len(self.metrics_history["queue_size"]) % 12 == 0:  # Every minute
                        self.print_summary()
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\nFinal Summary:")
            self.print_summary()
            print("Monitoring stopped.")


if __name__ == "__main__":
    monitor = PerformanceMonitor()
    monitor.monitor()
