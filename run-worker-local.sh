#!/bin/bash

set -e

cleanup() {
    echo ""
    echo "Shutting down worker..."
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "Starting Local Transcribe Worker"
echo ""

if [ ! -f .env ]; then
    echo "Creating .env from .env.local..."
    cp .env.local .env
    echo ""
fi

echo "Checks:"
echo "[1/2] Docker Desktop:"
echo -n "  Checking Docker... "
if ! docker info > /dev/null 2>&1; then
    echo "✗ (not running)"
    echo "  Starting Docker Desktop..."
    open -a Docker
    echo -n "  Waiting for Docker... "
    max_wait=60
    waited=0
    while ! docker info > /dev/null 2>&1 && [ $waited -lt $max_wait ]; do
        sleep 2
        waited=$((waited + 2))
    done
    if ! docker info > /dev/null 2>&1; then
        echo "✗"
        echo "  ERROR: Docker failed to start. Please start Docker Desktop manually."
        exit 1
    fi
    echo "✓"
else
    echo "✓"
fi

wait_for_service() {
    local service_name=$1
    local check_command=$2
    local log_service=$3
    local max_retries=30
    local retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        if eval "$check_command" > /dev/null 2>&1; then
            return 0
        fi
        retry_count=$((retry_count + 1))
        sleep 2
    done

    echo ""
    echo "  ERROR: $service_name failed. Check: docker compose logs $log_service"
    exit 1
}

echo ""
echo "[2/2] Service Health Checks:"

# Start db and elasticmq first — backend depends on queues existing
echo -n "  Starting db and elasticmq... "
docker compose stop worker 2>/dev/null || true
docker compose up -d db elasticmq > /dev/null 2>&1
echo "✓"

echo -n "  Database... "
wait_for_service "Database" \
    "docker compose ps db | grep -q 'healthy'" \
    "db"
echo "✓"

echo -n "  ElasticMQ... "
wait_for_service "ElasticMQ" \
    "curl --silent --fail http://localhost:9324/?Action=ListQueues" \
    "elasticmq"
echo "✓"

#Start backend and frontend
echo -n "  Starting backend and frontend... "
docker compose up -d backend frontend > /dev/null 2>&1
echo "✓"

echo -n "  Backend... "
wait_for_service "Backend" \
    "curl -s http://localhost:8080/healthcheck" \
    "backend"
echo "✓"

echo -n "  Frontend... "
wait_for_service "Frontend" \
    "curl -s http://localhost:3000" \
    "frontend"
echo "✓"

echo ""
echo "App is Ready:"
echo "  Application: http://localhost:3000"
echo ""
echo "Starting worker (Ctrl+C to stop)..."
echo ""

exec poetry run python worker/main.py
