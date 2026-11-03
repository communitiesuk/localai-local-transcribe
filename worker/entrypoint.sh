#!/bin/bash

# rehydrate google account credentials
# written to /tmp (tmpfs-mounted) so this works on a read-only root filesystem
GOOGLE_CREDENTIALS_PATH=/tmp/google-credentials.json
echo "$GOOGLE_APPLICATION_CREDENTIALS_BASE64" | base64 -d > "$GOOGLE_CREDENTIALS_PATH"
chmod 600 "$GOOGLE_CREDENTIALS_PATH"
export GOOGLE_APPLICATION_CREDENTIALS="$GOOGLE_CREDENTIALS_PATH"

# Main execution
echo "Starting queue service..."

exec python worker/main.py