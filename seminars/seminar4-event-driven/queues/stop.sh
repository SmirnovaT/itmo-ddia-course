#!/bin/bash
# Stop all services and clean up

echo "Stopping all services..."
docker-compose down

if [ "$1" == "--clean" ]; then
    echo "Removing volumes..."
    docker-compose down -v
    echo "All data cleared."
fi

echo "Services stopped."
