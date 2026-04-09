import asyncio
import os
import subprocess
import json
import re
import argparse
from pathlib import Path
import httpx
from common.settings import get_settings

# Constants
SCOPE = "api://api.azc.test.communities.gov.uk/.default"
ENV_FILE = ".env"

def refresh_access_token():
    """Extracts a new access token using the Azure CLI."""
    print(f"Refreshing access token for scope: {SCOPE}")
    try:
        cmd = ["az", "account", "get-access-token", "--resource", "api://api.azc.test.communities.gov.uk/", "--output", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        token_data = json.loads(result.stdout)
        return token_data.get("accessToken")
    except subprocess.CalledProcessError as e:
        print(f"Error fetching token: {e.stderr}")
        print("Note: You may need to run `az login --scope " + SCOPE + "` first.")
        return None
    except Exception as e:
        print(f"Unexpected error fetching token: {e}")
        return None

def update_env_file(key, value):
    """Updates or adds a key in the .env file."""
    if not os.path.exists(ENV_FILE):
        print(f"Creating {ENV_FILE}...")
        with open(ENV_FILE, "w") as f:
            f.write(f"{key}={value}\n")
        return

    with open(ENV_FILE, "r") as f:
        lines = f.readlines()

    updated = False
    new_lines = []
    pattern = re.compile(rf"^{key}=.*")

    for line in lines:
        if pattern.match(line):
            new_lines.append(f"{key}={value}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] += "\n"
        new_lines.append(f"{key}={value}\n")

    with open(ENV_FILE, "w") as f:
        f.writelines(new_lines)
    
    print(f"Updated {key} in {ENV_FILE}")

async def test_chat_completion(settings, model: str):
    print("\n--- Testing Chat Completion via APIM ---")
    if not all([settings.AZURE_APIM_URL, settings.AZURE_APIM_ACCESS_TOKEN, settings.AZURE_APIM_SUBSCRIPTION_KEY]):
        print("Skipping Chat Completion: APIM settings missing.")
        return

    # Construct URL. We'll use model in the URL path.
    url = f"{settings.AZURE_APIM_URL}{model}/chat/completions"
    params = {"api-version": settings.AZURE_APIM_API_VERSION or "2024-10-21"}
    
    headers = {
        "Authorization": f"Bearer {settings.AZURE_APIM_ACCESS_TOKEN}",
        "Ocp-Apim-Subscription-Key": settings.AZURE_APIM_SUBSCRIPTION_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [
            {"role": "user", "content": "Hello, please response with a single word acknowledging this test connection."}
        ],
        "max_tokens": 10
    }

    async with httpx.AsyncClient() as client:
        try:
            print(f"Calling URL: {url}")
            response = await client.post(url, headers=headers, json=payload, params=params, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            print("Success!")
            print(f"Response: {result['choices'][0]['message']['content']}")
        except Exception as e:
            print(f"Chat Completion failed: {e}")
            if hasattr(e, 'response') and e.response: # type: ignore
                print(f"Status Code: {e.response.status_code}") # type: ignore
                print(f"Response Text: {e.response.text}") # type: ignore

import mimetypes

async def test_transcription(settings, audio_file_path: str, model: str):
    print(f"\n--- Testing Audio Transcription via APIM/Azure ---")

    if not os.path.exists(audio_file_path):
        print(f"Skipping Transcription: Audio file not found at {audio_file_path}")
        return

    # Guess mime type
    mime_type, _ = mimetypes.guess_type(audio_file_path)
    mime_type = mime_type or "application/octet-stream"

    # Check if we should use APIM or direct Azure
    if settings.AZURE_SPEECH_REGION == "not_needed_for_local" and settings.AZURE_APIM_URL:
        # Use OpenAI-style transcription endpoint via APIM
        # User specified: azure_apim_url/ with /audio/transcriptions
        url = f"{settings.AZURE_APIM_URL}audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {settings.AZURE_APIM_ACCESS_TOKEN}",
            "Ocp-Apim-Subscription-Key": settings.AZURE_APIM_SUBSCRIPTION_KEY,
        }
        params = {"api-version": settings.AZURE_APIM_API_VERSION or "2024-10-21"}

        print(f"Transcribing via APIM (OpenAI-style) using file {audio_file_path} ({mime_type})")
        
        # Use multipart/form-data. Key should be 'file' for OpenAI style.
        with open(audio_file_path, "rb") as f:
            audio_content = f.read()

        files = {
            "file": (os.path.basename(audio_file_path), audio_content, mime_type),
        }

        # Some OpenAI endpoints also want the 'model' in form data
        data = {"model": model}

        async with httpx.AsyncClient() as client:
            try:
                print(f"Calling URL: {url}")
                response = await client.post(url, headers=headers, files=files, data=data, params=params, timeout=120.0)
                response.raise_for_status()
                result = response.json()
                print("Success!")
                
                transcript = result.get('text', '(No text field in response)')
                print(f"Transcript preview: {transcript[:100]}...")
                
                # Output to file
                output_file = f"{os.path.splitext(audio_file_path)[0]}.txt"
                with open(output_file, "w") as f_out:
                    f_out.write(transcript)
                print(f"Full transcription saved to: {output_file}")

            except Exception as e:
                print(f"Transcription via APIM failed: {e}")
                if hasattr(e, 'response') and e.response: # type: ignore
                    print(f"Status Code: {e.response.status_code}") # type: ignore
                    print(f"Response Text: {e.response.text}") # type: ignore

    else:
        # Classic direct Azure Speech STT
        url = f"https://{settings.AZURE_SPEECH_REGION}.api.cognitive.microsoft.com/speechtotext/transcriptions:transcribe"
        headers = {
            "Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY,
        }
        params = {"api-version": "2024-11-15"}

        if not all([settings.AZURE_SPEECH_KEY, settings.AZURE_SPEECH_REGION]):
            print("Skipping Transcription: Azure Speech settings missing.")
            return

        print(f"Transcribing via Direct Azure Speech API using file {audio_file_path}")
        
        with open(audio_file_path, "rb") as f:
            audio_content = f.read()

        files = {
            "audio": (os.path.basename(audio_file_path), audio_content),
            "definition": (
                None,
                '{"locales":["en-GB"],"diarization":{"enabled":true},"profanityFilterMode":"None"}',
            ),
        }

        async with httpx.AsyncClient() as client:
            try:
                print(f"Calling URL: {url}")
                response = await client.post(url, headers=headers, files=files, params=params, timeout=120.0)
                response.raise_for_status()
                result = response.json()
                print("Success!")
                
                phrases = result.get("phrases", [])
                if phrases:
                    transcript = " ".join([p.get('text', '') for p in phrases])
                    print(f"Transcript preview: {transcript[:100]}...")
                    
                    # Output to file
                    output_file = f"{os.path.splitext(audio_file_path)[0]}.txt"
                    with open(output_file, "w") as f_out:
                        f_out.write(transcript)
                    print(f"Full transcription saved to: {output_file}")
                else:
                    print("No phrases returned, but call succeeded.")
            except Exception as e:
                print(f"Direct Azure Transcription failed: {e}")
                if hasattr(e, 'response') and e.response: # type: ignore
                    print(f"Status Code: {e.response.status_code}") # type: ignore
                    print(f"Response Text: {e.response.text}") # type: ignore

async def main():
    parser = argparse.ArgumentParser(description="Test APIM responses for Chat and Transcription.")
    parser.add_argument("--refresh", action="store_true", help="Refresh the access token using the Azure CLI")
    parser.add_argument("--audio", type=str, default="./bored.mp3", help="Path to audio file for transcription test")
    parser.add_argument("--model", type=str, default="gpt-4o", help="Model name for APIM (e.g. gpt-4o)")
    
    args = parser.parse_args()

    # Initial settings load
    from common.settings import get_settings
    settings = get_settings()

    if args.refresh or not settings.AZURE_APIM_ACCESS_TOKEN:
        new_token = refresh_access_token()
        if new_token:
            update_env_file("AZURE_APIM_ACCESS_TOKEN", new_token)
            # Reload settings
            os.environ["AZURE_APIM_ACCESS_TOKEN"] = new_token
            settings = get_settings()
        elif not settings.AZURE_APIM_ACCESS_TOKEN:
            print("Warning: No access token found and failed to refresh one automatically.")

    await test_chat_completion(settings, args.model)
    await test_transcription(settings, args.audio, args.model)

if __name__ == "__main__":
    asyncio.run(main())
