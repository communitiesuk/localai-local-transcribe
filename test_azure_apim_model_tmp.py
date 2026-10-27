import asyncio
import sys

from evals.summarisation.src.common.adapter_factory import build_azure_apim_adapter


async def main():
    adapter = build_azure_apim_adapter()
    reply = await adapter.chat([{"role": "user", "content": "Reply with exactly one word: pong"}])
    print(f"{sys.argv[1] if len(sys.argv) > 1 else '?'}: {reply!r}")


asyncio.run(main())
