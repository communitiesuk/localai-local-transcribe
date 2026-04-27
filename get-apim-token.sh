#!/bin/bash

set -euo pipefail

# Add common macOS paths if they are not already in PATH
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

if ! command -v jq &> /dev/null; then
    echo "Error: jq is not installed.
     Please install jq to continue." >&2
    echo "Install with: brew install jq (macOS) or apt-get install jq (Linux)" >&2
    exit 1
fi

ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE not found. Please create it from .env.example" >&2
    exit 1
fi

# Extract AZURE_APIM_SCOPE from .env (avoiding sourcing to prevent parsing errors)
TOKEN_SCOPE=$(grep "^AZURE_APIM_SCOPE=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'")

if [ -z "$TOKEN_SCOPE" ]; then
    echo "Error: AZURE_APIM_SCOPE not set in $ENV_FILE" >&2
    exit 1
fi

if ! command -v az &> /dev/null; then
    echo "Error: Azure CLI (az) is not installed or not in PATH" >&2
    exit 1
fi

echo "Fetching access token..." >&2
TOKEN_JSON=$(az account get-access-token --scope "$TOKEN_SCOPE" --output json 2>&1) || {
    if echo "$TOKEN_JSON" | grep -q "AADSTS700082\|refresh token has expired\|Please run 'az login'"; then
        echo "Token expired or not logged in. Logging in..." >&2
        az login --scope "$TOKEN_SCOPE" --allow-no-subscriptions
        TOKEN_JSON=$(az account get-access-token --scope "$TOKEN_SCOPE" --output json)
    else
        echo "Error fetching token:" >&2
        echo "$TOKEN_JSON" >&2
        exit 1
    fi
}

ACCESS_TOKEN=$(echo "$TOKEN_JSON" | jq -r '.accessToken')

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
    echo "Error: Failed to retrieve access token" >&2
    exit 1
fi

export APIM_ACCESS_TOKEN="$ACCESS_TOKEN"
echo "Token exported to APIM_ACCESS_TOKEN" >&2

if grep -q "^AZURE_APIM_ACCESS_TOKEN=" "$ENV_FILE"; then
    sed -i '' "s|^AZURE_APIM_ACCESS_TOKEN=.*|AZURE_APIM_ACCESS_TOKEN=$ACCESS_TOKEN|" "$ENV_FILE"
else
    echo "AZURE_APIM_ACCESS_TOKEN=$ACCESS_TOKEN" >> "$ENV_FILE"
fi
echo "Token updated in $ENV_FILE" >&2