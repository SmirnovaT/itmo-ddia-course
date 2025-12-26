#!/bin/bash
# Scale workers dynamically

if [ -z "$1" ]; then
    echo "Usage: ./scale_workers.sh <number_of_workers>"
    echo "Example: ./scale_workers.sh 5"
    exit 1
fi

NUM_WORKERS=$1

echo "Scaling workers to $NUM_WORKERS instances..."
docker-compose up -d --scale worker=$NUM_WORKERS

echo ""
echo "Current worker instances:"
docker-compose ps worker

echo ""
echo "Monitor workers with:"
echo "  docker-compose logs -f worker"
