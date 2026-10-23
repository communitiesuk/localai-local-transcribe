#!/bin/bash

# Function to run database migrations
run_migrations() {
    echo "Running database migrations..."
    alembic upgrade head
    if [ $? -ne 0 ]; then
        echo "Database migration failed!"
        exit 1
    fi
    echo "Database migrations completed successfully"
}

# Function to start the FastAPI application
start_app() {
    echo "Starting FastAPI application..."
    uvicorn backend.main:app --host 0.0.0.0 --port 8080 --no-server-header &
    PID=$!
    wait $PID
}

# rehydrate google account credentials
# written to /tmp (tmpfs-mounted) so this works on a read-only root filesystem
GOOGLE_CREDENTIALS_PATH=/tmp/google-credentials.json
echo "$GOOGLE_APPLICATION_CREDENTIALS_BASE64" | base64 -d > "$GOOGLE_CREDENTIALS_PATH"
chmod 600 "$GOOGLE_CREDENTIALS_PATH"
export GOOGLE_APPLICATION_CREDENTIALS="$GOOGLE_CREDENTIALS_PATH"

# Main execution
run_migrations
start_app