'''Constants for summarisation evaluation.

MAX_TOKENS: Maximum number of tokens the LLM should generate for a summary.
TEMPERATURE: Sampling temperature for the LLM generation.
'''

# Default token limit for generated summaries. Adjust as needed.
MAX_TOKENS: int = 1024

# Temperature setting (1.0 uses the default model temperature).
TEMPERATURE: float = 1.0

__all__ = ["MAX_TOKENS", "TEMPERATURE"]
