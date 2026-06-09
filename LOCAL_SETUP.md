# Local Setup Guide

Run Local Transcribe locally with the worker running natively and services in Docker.

## Prerequisites

**System Requirements:**
- Docker Desktop (required for any local setup)
- Python 3.12 (required for any local setup)
- Poetry (required for any local setup)
- FFmpeg

**macOS Installation:**
```bash
brew install ffmpeg poetry
```

## Quick Start

```bash
# Install dependencies
poetry install --with worker

# Configure environment
cp .env.local .env

# Run worker locally
./run-worker-local.sh
```

### Access the app at http://localhost:3000

## Architecture

- **Docker**: Database, backend, frontend, elasticmq
- **Local Worker**: Runs natively, connects to Azure services for transcription and LLM

## Troubleshooting Docker

The local dev implementation of Minute doesn't impact Docker services except that the worker runs directly on hardware instead of through Docker.

If you encounter Docker issues, the fastest solution is to reset Docker completely:

**⚠️ Warning**: This command will delete all built images, volumes, and database data. Back up any data you want to preserve.

```bash
docker compose down -v
```

## API Portal

To gain & validate access to the platform

-  Install the Azure CLI if needed
-  Login with the command below, when prompted, provide  with your test account credentials
```
az login --scope api://api.azc.test.communities.gov.uk/.default

```
- Get your access token via the command below and set it to the AZURE_APIM_ACCESS_TOKEN key within your env file
```
az account get-access-token

```
- Finally, run the 'test-apim.py' script within root. On success, you should receive the following response 

```
message=ChatCompletionMessage(content="Hello, APIM Test Team! 👋 Hope you're all doing great and having a productive day. Let me know how I can assist you! 🚀" ...)

```
