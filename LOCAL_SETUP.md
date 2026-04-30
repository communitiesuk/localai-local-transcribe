# Local Setup Guide

Run Minute locally with hardware-accelerated transcription and local Ollama LLM.

## Prerequisites

**System Requirements:**
- Docker Desktop (required for any local setup)
- Python 3.12 (required for any local setup)
- Poetry (required for any local setup)
- FFmpeg
- Ollama

**macOS Installation:**
```bash
brew install ffmpeg poetry
```
Afterwards install Ollama from: https://ollama.com/download/mac


## Prerequisites

**APIM Access (required for transcription):**

Transcription uses Azure Speech-to-Text via APIM. You need access to the APIM gateway before the worker can transcribe audio. Set the following in your `.env` after copying `.env.local`:

```
AZURE_APIM_URL=https://{{host}}.gov.uk/{{product_name}}/
AZURE_APIM_API_VERSION=2024-10-21
AZURE_APIM_ACCESS_TOKEN=placeholder
AZURE_APIM_SUBSCRIPTION_KEY=placeholder
AZURE_APIM_AUTH_METHOD=static_token
```

See the [API Portal](#api-portal) section below for how to obtain your access token.

## Quick Start

```bash
# Install dependencies
poetry install --with worker

# Download Ollama model
ollama pull llama3.2:3b-instruct-q4_K_M

# Configure environment
cp .env.local .env
```

Edit the `.env` file and fill in your APIM credentials (see above).

```bash
# Run worker locally
./run-worker-local.sh
```

### Access the app at http://localhost:3000

**Troubleshooting Ollama:**

If you encounter this error:
```
ollama pull llama3.2:3b-instruct-q4_K_M
Error: ollama server not responding - could not find ollama app
```

You need to launch the Ollama GUI application. Search for 'ollama' in your applications and open it.

## Architecture

- **Docker**: Database, backend, frontend, elasticmq
- **Local Worker**: Runs natively for GPU access (MPS on Apple Silicon)
- **Transcription**: Azure Speech-to-Text
- **LLM**: Ollama (local, runs natively for MPS acceleration)

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
