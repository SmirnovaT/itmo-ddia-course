# Getting Started with Event-Driven Image Processing

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for load testing and monitoring)
- 4GB+ available RAM
- 2GB+ available disk space

## Installation Steps

### 1. Navigate to the project directory
```bash
cd /Users/georgii.semenov/home/repos/itmo-ddia-course/seminars/seminar4-event-driven/queues
```

### 2. Start the system
```bash
./start.sh
```

This will:
- Start RabbitMQ (message queue)
- Start MinIO (S3-compatible storage)
- Start API service
- Start 2 worker instances
- Start notification service
- Create necessary buckets and queues

### 3. Wait for services to initialize (10-15 seconds)
Watch the logs:
```bash
docker-compose logs -f
```

Press Ctrl+C when you see messages like:
- "Worker 1 waiting for messages..."
- "Notification Service waiting for notifications..."

### 4. Verify the system is ready
```bash
# Install verification dependencies
pip install -r requirements.txt

# Run verification
python verify_setup.py
```

You should see all checks passing with ✓ marks.

## First Steps

### Access the web interfaces

Open in your browser:
1. **API Documentation**: http://localhost:8000/docs
   - Interactive API testing
   - See all endpoints

2. **RabbitMQ Management**: http://localhost:15672
   - Username: `guest`
   - Password: `guest`
   - Monitor queues and messages

3. **MinIO Console**: http://localhost:9001
   - Username: `minioadmin`
   - Password: `minioadmin`
   - View stored images

### Upload your first image

#### Option 1: Use the provided test image
```bash
# Generate a test image
cd test_images
python generate_sample.py
cd ..

# Upload it
curl -X POST "http://localhost:8000/upload" \
  -F "file=@test_images/sample.jpg" \
  -F "operations=resize,watermark"
```

#### Option 2: Use your own image
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@/path/to/your/image.jpg" \
  -F "operations=resize,watermark,filter"
```

You'll get a response like:
```json
{
  "job_id": "abc123...",
  "status": "queued",
  "operations": ["resize", "watermark"],
  "message": "Image uploaded and queued for processing"
}
```

### Check processing status

```bash
# Replace JOB_ID with the actual ID from above
curl "http://localhost:8000/status/JOB_ID"
```

### View logs

Watch the processing in real-time:
```bash
# All logs
docker-compose logs -f

# Just workers
docker-compose logs -f worker

# Just notifications
docker-compose logs -f notification
```

## Running Experiments

### Experiment 1: Basic Load Test
```bash
# Install load test dependencies
cd load_test
pip install -r requirements.txt

# Run a simple load test (50 images)
python bulk_upload.py --count 50 --concurrency 10

# View results
python analyze_results.py
```

### Experiment 2: Scale Workers
```bash
# Scale to 5 workers
./scale_workers.sh 5

# Check status
docker-compose ps worker

# Run another load test
cd load_test
python bulk_upload.py --count 100 --concurrency 20
```

### Experiment 3: Monitor the System
```bash
# In one terminal: start monitoring
cd monitoring
pip install -r requirements.txt
python queue_monitor.py

# In another terminal: generate load
cd load_test
python bulk_upload.py --count 100
```

## Viewing Results

### Check metrics
```bash
curl http://localhost:8000/metrics | python -m json.tool
```

### View processed images in MinIO
1. Go to http://localhost:9001
2. Login with `minioadmin` / `minioadmin`
3. Browse to "processed" bucket
4. Download processed images

### Check Dead Letter Queue
```bash
# Check DLQ stats
curl http://localhost:8000/dlq/stats

# Or view in RabbitMQ Management UI
# Go to Queues tab → dead_letter_queue
```

## Common Issues

### Services won't start
```bash
# Check Docker is running
docker ps

# If not, start Docker Desktop

# Clean start
docker-compose down -v
./start.sh
```

### API returns "Connection refused"
```bash
# Wait a bit longer (services take 10-15 seconds to start)
sleep 10

# Check if API is running
docker-compose logs api

# Restart API if needed
docker-compose restart api
```

### Workers not processing
```bash
# Check worker logs
docker-compose logs worker

# Restart workers
docker-compose restart worker

# Or scale up
./scale_workers.sh 3
```

### Out of memory
```bash
# Stop services
./stop.sh

# Increase Docker memory limit in Docker Desktop settings
# Recommended: 4GB minimum

# Restart
./start.sh
```

## Stopping the System

### Normal stop (keeps data)
```bash
./stop.sh
```

### Complete cleanup (removes all data)
```bash
./stop.sh --clean
```

## Next Steps

Once you're comfortable with the basics:

1. **Read the experiments guide**: `EXPERIMENTS.md`
2. **Review the architecture**: `PROJECT_STRUCTURE.md`
3. **Run comprehensive tests**: See `load_test/` directory
4. **Customize operations**: Modify `worker/processors/`
5. **Add monitoring**: Integrate Prometheus/Grafana

## Learning Objectives

By the end of this seminar, you should understand:

- ✓ How event-driven architectures work
- ✓ Message queue patterns (producer/consumer)
- ✓ Horizontal scaling strategies
- ✓ Fault tolerance mechanisms (DLQ)
- ✓ Performance testing and optimization
- ✓ Monitoring distributed systems

## Need Help?

- Check the logs: `docker-compose logs`
- Run verification: `python verify_setup.py`
- Review documentation in the `*.md` files
- Check RabbitMQ Management UI for queue status
- Use the API docs at http://localhost:8000/docs

## Resources

- [README.md](README.md) - Full documentation
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command cheat sheet
- [EXPERIMENTS.md](EXPERIMENTS.md) - Detailed experiments
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Architecture details

Good luck with your experiments! 🚀
