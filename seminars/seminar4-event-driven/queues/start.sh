#!/bin/bash
# Quick start script for the demo

set -e

echo "=========================================="
echo "Event-Driven Image Processing System"
echo "=========================================="
echo ""

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

echo "1. Starting services..."
docker-compose up -d

echo ""
echo "2. Waiting for services to be ready..."
sleep 10

echo ""
echo "3. Checking service status..."
docker-compose ps

echo ""
echo "=========================================="
echo "Services are ready!"
echo "=========================================="
echo ""
echo "Access points:"
echo "  - API Service: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - RabbitMQ Management: http://localhost:15672 (guest/guest)"
echo "  - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
echo ""
echo "Quick test:"
echo "  cd test_images"
echo "  python generate_sample.py"
echo "  curl -X POST \"http://localhost:8000/upload\" \\"
echo "    -F \"file=@sample.jpg\" \\"
echo "    -F \"operations=resize,watermark\""
echo ""
echo "View logs:"
echo "  docker-compose logs -f"
echo ""
echo "Stop services:"
echo "  docker-compose down"
echo ""
