import asyncio
import os
import argparse
import httpx
from common.settings import get_settings

async def test_apim_chat(prompt: str, model_override: str = None):
    settings = get_settings()
    
    # Use override if provided, otherwise use setting from .env
    model = model_override or settings.BEST_LLM_MODEL_NAME
    
    print(f"\n--- Testing Chat Completion via APIM ---")
    print(f"Model: {model}")
    print(f"Prompt: {prompt}")

    if not all([settings.AZURE_APIM_URL, settings.AZURE_APIM_ACCESS_TOKEN, settings.AZURE_APIM_SUBSCRIPTION_KEY]):
        print("Error: Missing APIM settings in .env.")
        return

    # Construct URL. Based on common/llm/adapters/azure_apim.py logic
    url = f"{settings.AZURE_APIM_URL}{model}/chat/completions"
    params = {"api-version": settings.AZURE_APIM_API_VERSION or "2024-10-21"}
    
    headers = {
        "Authorization": f"Bearer {settings.AZURE_APIM_ACCESS_TOKEN}",
        "Ocp-Apim-Subscription-Key": settings.AZURE_APIM_SUBSCRIPTION_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500
    }

    async with httpx.AsyncClient() as client:
        try:
            print(f"Calling URL: {url}")
            response = await client.post(url, headers=headers, json=payload, params=params, timeout=60.0)
            
            if response.status_code == 404:
                print("\nError 404: Resource Not Found.")
                print(f"It's likely that the model name '{model}' is not recognized by APIM.")
                print("Try passing a different model name with --model (e.g., --model gpt-4o)")
                return

            response.raise_for_status()
            result = response.json()
            print("\nSuccess!")
            print("-" * 20)
            print(result['choices'][0]['message']['content'])
            print("-" * 20)
        except Exception as e:
            print(f"\nChat Completion failed: {e}")
            if hasattr(e, 'response') and e.response: # type: ignore
                print(f"Status Code: {e.response.status_code}") # type: ignore
                print(f"Response Text: {e.response.text}") # type: ignore

async def main():
    parser = argparse.ArgumentParser(description="Run a simple chat prompt against APIM.")
    parser.add_argument("prompt", type=str, nargs="?", default="tell me the various parts of an avocado pear", help="The text prompt to send")
    parser.add_argument("--model", type=str, help="Override the model name (e.g. gpt-4o)")
    
    args = parser.parse_args()

    await test_apim_chat(args.prompt, args.model)

if __name__ == "__main__":
    asyncio.run(main())
