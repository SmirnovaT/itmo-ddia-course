# Project Structure Summary

## Complete File Listing

```
queues/
├── README.md                       # Main documentation
├── QUICK_REFERENCE.md             # Quick command reference
├── EXPERIMENTS.md                 # Detailed experiment guide
├── docker-compose.yml             # Docker orchestration
├── requirements.txt               # Python dependencies for verification
├── verify_setup.py                # System verification script
├── .gitignore                     # Git ignore rules
│
├── start.sh                       # Quick start script
├── stop.sh                        # Stop services script
├── scale_workers.sh               # Scale workers dynamically
│
├── api/                           # API Service (FastAPI)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                    # Main API application
│   └── config.py                  # Configuration settings
│
├── worker/                        # Worker Service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── worker.py                  # Main worker application
│   └── processors/
│       ├── __init__.py
│       ├── resize.py              # Image resizing
│       ├── watermark.py           # Watermark addition
│       └── filter.py              # Image filters
│
├── notification/                  # Notification Service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── notifier.py                # Notification handler
│
├── monitoring/                    # Monitoring Tools
│   ├── requirements.txt
│   ├── queue_monitor.py           # Queue size monitoring
│   └── performance_monitor.py     # Performance metrics
│
├── load_test/                     # Load Testing Scripts
│   ├── requirements.txt
│   ├── bulk_upload.py             # Bulk upload test
│   ├── burst_test.py              # Burst load test
│   └── analyze_results.py         # Results analysis
│
└── test_images/                   # Test Images
    ├── README.md
    └── generate_sample.py         # Generate test images
```

## Key Components

### 1. API Service (api/)
- **Language**: Python with FastAPI
- **Purpose**: Accept image uploads, publish to RabbitMQ
- **Features**:
  - REST API for image upload
  - Job status tracking
  - Metrics endpoint
  - Dead Letter Queue stats
  - OpenAPI documentation

### 2. Worker Service (worker/)
- **Language**: Python
- **Purpose**: Process images from queue
- **Operations**:
  - Resize: Scale images to standard size
  - Watermark: Add text watermark
  - Filter: Apply image filters
- **Features**:
  - Concurrent processing
  - Automatic retries
  - Dead Letter Queue for failures
  - Horizontal scaling

### 3. Notification Service (notification/)
- **Language**: Python
- **Purpose**: Handle completion notifications
- **Features**:
  - Log completion events
  - Track processing metrics
  - Can be extended for email/webhooks

### 4. Infrastructure (docker-compose.yml)
- **RabbitMQ**: Message queue with management UI
- **MinIO**: S3-compatible object storage
- **Networking**: Isolated Docker network
- **Volumes**: Persistent data storage

### 5. Monitoring Tools (monitoring/)
- Queue size and depth tracking
- Performance metrics collection
- Real-time monitoring dashboard
- Historical data analysis

### 6. Load Testing (load_test/)
- Bulk upload testing
- Burst load simulation
- Results analysis and comparison
- Performance profiling

## Usage Flow

1. **Upload**: Client → API → MinIO (store) + RabbitMQ (queue)
2. **Process**: Worker → RabbitMQ (consume) → Process → MinIO (save)
3. **Notify**: Worker → RabbitMQ (notification queue) → Notification Service
4. **Monitor**: All stages emit metrics for monitoring

## Scalability Features

- **Horizontal Scaling**: Multiple worker instances
- **Load Balancing**: RabbitMQ distributes tasks
- **Async Processing**: Non-blocking operations
- **Fault Tolerance**: DLQ for failed messages
- **Resource Isolation**: Docker containers

## Educational Value

This demo illustrates:
- ✓ Event-driven architecture patterns
- ✓ Message queue (RabbitMQ) usage
- ✓ Producer-consumer pattern
- ✓ Horizontal scaling
- ✓ Fault tolerance (DLQ)
- ✓ Monitoring and observability
- ✓ Load testing methodology
- ✓ Performance optimization

## Time Allocation (90 minutes)

1. **Setup (15 min)**: Start services, verify connectivity
2. **Demo (15 min)**: Upload images, show processing flow
3. **Experiments (45 min)**:
   - Worker scaling
   - Failure recovery
   - Load testing
4. **Analysis (15 min)**: Review metrics, discuss results

## Success Criteria

Students should be able to:
- ✓ Start and configure the system
- ✓ Upload and process images
- ✓ Scale workers dynamically
- ✓ Monitor queue metrics
- ✓ Conduct load tests
- ✓ Analyze performance data
- ✓ Understand trade-offs in event-driven systems

## Extension Ideas

- Add more image operations
- Implement priority queues
- Add authentication
- Create web dashboard
- Implement webhooks
- Add distributed tracing
- Integrate with Prometheus/Grafana
