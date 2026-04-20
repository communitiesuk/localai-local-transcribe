class ResponseTruncatedError(Exception):
    """Raised when the LLM response was cut off due to reaching the max token limit."""
