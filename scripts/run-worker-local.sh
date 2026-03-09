#!/bin/bash

set -e

cleanup() {
    echo ""
    echo "Shutting down worker..."
    if [ ! -z "$OLLAMA_PID" ]; then
        kill $OLLAMA_PID 2>/dev/null || true
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "Starting Minute Worker with MPS Acceleration"
echo ""

if [ ! -f .env ]; then
    echo "Creating .env from .env.local..."
    cp .env.local .env
    echo "IMPORTANT: Edit .env and set WHISPLY_HF_TOKEN"
    echo "Get token from: https://huggingface.co/settings/tokens"
    echo ""
    read -p "Press Enter after adding your HuggingFace token to .env..."
fi

echo "Checks:"
echo -n "[1/6] MPS availability... "
MPS_AVAILABLE=$(poetry run python -c "import torch; print(torch.backends.mps.is_available())" 2>/dev/null || echo "false")
if [ "$MPS_AVAILABLE" = "True" ]; then
    echo "✓"
else
    echo "✗ (will use CPU)"
fi

echo -n "[2/6] Ollama installed... "
if ! command -v ollama &> /dev/null; then
    echo "✗"
    echo "ERROR: Install Ollama: brew install ollama"
    exit 1
fi
echo "✓"

echo -n "[3/6] Ollama service... "
if ! pgrep -x "ollama" > /dev/null; then
    ollama serve > /tmp/ollama.log 2>&1 &
    OLLAMA_PID=$!
    sleep 3
fi
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✗"
    echo "ERROR: Ollama not responding. Check /tmp/ollama.log"
    exit 1
fi
echo "✓"

echo -n "[4/6] Ollama models... "
FAST_MODEL=$(grep "FAST_LLM_MODEL_NAME" .env 2>/dev/null | cut -d'=' -f2 || echo "llama3.2:3b-instruct-q4_K_M")
BEST_MODEL=$(grep "BEST_LLM_MODEL_NAME" .env 2>/dev/null | cut -d'=' -f2 || echo "llama3.2:3b-instruct-q4_K_M")
for MODEL in "$FAST_MODEL" "$BEST_MODEL"; do
    if [ -n "$MODEL" ] && ! ollama list | grep -q "$MODEL"; then
        echo "✗"
        echo "ERROR: Model '$MODEL' not found. Run: ollama pull $MODEL"
        exit 1
    fi
done
echo "✓"

echo -n "[5/6] Starting Docker services... "
docker compose stop worker 2>/dev/null || true
docker compose up -d db localstack backend frontend > /dev/null 2>&1
echo "✓"

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
    
    echo "✗"
    echo "ERROR: $service_name failed. Check: docker compose logs $log_service"
    exit 1
}

echo -n "[6/6] Waiting for services... "
wait_for_service "Database" "docker compose ps db | grep -q 'healthy'" "db"
wait_for_service "Backend" "curl -s http://localhost:8080/healthcheck" "backend"
wait_for_service "Frontend" "curl -s http://localhost:3000" "frontend"
echo "✓"

echo ""
echo "Rest of the App is Ready:"
echo "  Application: http://localhost:3000"
echo ""
echo "Starting worker (Ctrl+C to stop)..."
echo ""

exec poetry run python worker/main.py
