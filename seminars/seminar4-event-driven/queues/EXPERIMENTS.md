# Experiments Guide

This guide walks you through the experiments for the Event-Driven system seminar.

## Setup

1. Start the system:
```bash
./start.sh
```

2. Install load test dependencies:
```bash
cd load_test
pip install -r requirements.txt
cd ..
```

3. Generate a test image:
```bash
cd test_images
python generate_sample.py
cd ..
```

## Experiment 1: Basic Functionality

### Test single image upload
```bash
cd test_images
curl -X POST "http://localhost:8000/upload" \
  -F "file=@sample.jpg" \
  -F "operations=resize,watermark"
```

Save the `job_id` from the response.

### Check status
```bash
curl "http://localhost:8000/status/{job_id}"
```

### View queue metrics
```bash
curl http://localhost:8000/metrics
```

### Monitor workers
```bash
docker-compose logs -f worker
```

## Experiment 2: Worker Scaling

### Test with 1 worker
```bash
# Scale to 1 worker
./scale_workers.sh 1

# Run load test
cd load_test
python bulk_upload.py --count 50 --concurrency 10
cd ..
```

### Test with 3 workers
```bash
./scale_workers.sh 3

cd load_test
python bulk_upload.py --count 50 --concurrency 10
cd ..
```

### Test with 5 workers
```bash
./scale_workers.sh 5

cd load_test
python bulk_upload.py --count 50 --concurrency 10
cd ..
```

### Compare results
```bash
cd load_test
python analyze_results.py
cd ..
```

**Questions to answer:**
- How does throughput change with more workers?
- What's the optimal number of workers for this workload?
- Where is the bottleneck?

## Experiment 3: Worker Failure (Resilience)

### Start with 3 workers
```bash
./scale_workers.sh 3
```

### Monitor the system
In one terminal:
```bash
docker-compose logs -f worker
```

In another terminal:
```bash
cd monitoring
pip install -r requirements.txt
python queue_monitor.py
```

### Start load test
In a third terminal:
```bash
cd load_test
python bulk_upload.py --count 100 --concurrency 5
```

### Kill a worker during processing
While the load test is running:
```bash
# Find worker container IDs
docker-compose ps worker

# Stop one worker
docker stop <container_id>
```

**Observations:**
- What happens to messages being processed by the stopped worker?
- How do remaining workers handle the load?
- Are any messages lost?

### Restart the worker
```bash
docker-compose up -d --scale worker=3
```

## Experiment 4: Burst Load

### Test system response to burst traffic
```bash
cd load_test
python burst_test.py --burst-size 50 --burst-count 3 --interval 10
cd ..
```

### Monitor queue size during bursts
```bash
# In another terminal
cd monitoring
python queue_monitor.py
```

**Questions:**
- How quickly does the queue drain after each burst?
- What's the maximum queue size reached?
- How does latency vary during bursts?

## Experiment 5: Dead Letter Queue (DLQ)

### Create a corrupted image
```bash
cd test_images
echo "This is not an image" > corrupted.jpg
```

### Upload corrupted file
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@corrupted.jpg" \
  -F "operations=resize"
```

### Check DLQ stats
```bash
curl http://localhost:8000/dlq/stats
```

### View DLQ in RabbitMQ
1. Open http://localhost:15672 (guest/guest)
2. Go to "Queues" tab
3. Look at "dead_letter_queue"

**Observations:**
- Failed messages are moved to DLQ
- Processing pipeline continues for other messages
- No blocking on failed tasks

## Experiment 6: High Concurrency Load

### Push the system to limits
```bash
cd load_test
python bulk_upload.py --count 200 --concurrency 50
```

### Monitor performance
```bash
cd monitoring
python performance_monitor.py
```

### Check if any uploads failed
```bash
python analyze_results.py --pattern "bulk_upload_results_*.json"
```

**Analysis:**
- At what point does the system start to fail?
- What's the failure mode? (timeout, connection refused, etc.)
- How can we improve capacity?

## Experiment 7: Different Operations

### Test different operation combinations
```bash
# Resize only
curl -X POST "http://localhost:8000/upload" \
  -F "file=@test_images/sample.jpg" \
  -F "operations=resize"

# Watermark only
curl -X POST "http://localhost:8000/upload" \
  -F "file=@test_images/sample.jpg" \
  -F "operations=watermark"

# All operations
curl -X POST "http://localhost:8000/upload" \
  -F "file=@test_images/sample.jpg" \
  -F "operations=resize,watermark,filter"
```

### Compare processing times
Check the notification logs for processing times:
```bash
docker-compose logs notification | grep "Processing Time"
```

## Measuring Key Metrics

### Throughput
```bash
# Images processed per second
curl http://localhost:8000/metrics | python -m json.tool
```

### Latency
Check the load test results:
- Mean latency
- P50 (median)
- P95
- P99

### Queue Depth
```bash
# Current queue size
curl http://localhost:8000/metrics | grep -A 5 task_queue
```

### Worker Utilization
```bash
# Active workers
docker-compose ps worker
```

## Results Documentation

After running experiments, document:

1. **Throughput vs Workers**
   - Plot throughput against number of workers

2. **Latency Distribution**
   - Histogram of processing times

3. **Queue Behavior**
   - Queue size over time during burst load

4. **Failure Recovery**
   - Time to recover from worker failure

5. **Resource Usage**
   ```bash
   docker stats
   ```

## Cleanup

```bash
./stop.sh --clean
```
