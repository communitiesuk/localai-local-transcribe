import asyncio
import httpx
from common.settings import get_settings

async def ping_endpoint(name, url, headers=None, params=None):
    print(f"Pinging {name}: {url}")
    async with httpx.AsyncClient() as client:
        try:
            # We use GET for a simple ping, or HEAD if supported
            response = await client.get(url, headers=headers, params=params, timeout=10.0)
            print(f"  Status Code: {response.status_code}")
            print(f"  Reason: {response.reason_phrase}")
            return response.status_code
        except Exception as e:
            print(f"  Connection failed: {e}")
            return None

async def main():
    settings = get_settings()
    
    if not settings.AZURE_APIM_URL:
        print("Error: AZURE_APIM_URL not found in settings.")
        return

    # 1. Ping the base APIM URL
    await ping_endpoint("Base APIM URL", settings.AZURE_APIM_URL)

    # 2. Ping Chat Endpoint (requires model)
    model = "gpt-4o"
    chat_url = f"{settings.AZURE_APIM_URL}{model}/chat/completions"
    headers = {
        "Ocp-Apim-Subscription-Key": settings.AZURE_APIM_SUBSCRIPTION_KEY,
    }
    params = {"api-version": settings.AZURE_APIM_API_VERSION or "2024-10-21"}
    
    print("\n--- Endpoint Connectivity Check ---")
    await ping_endpoint("Chat Endpoint", chat_url, headers=headers, params=params)

    # 3. Ping Transcription Endpoint
    transcription_url = f"{settings.AZURE_APIM_URL}audio/transcriptions"
    await ping_endpoint("Transcription Endpoint", transcription_url, headers=headers, params=params)

if __name__ == "__main__":
    asyncio.run(main())
