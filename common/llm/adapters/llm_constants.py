TEMPERATURE = 1
MAX_COMPLETION_TOKENS = 16384

# Internal tool name used to force Anthropic's tool-use mechanism for structured output.
# This never varies between schemas or leaves the adapter, so a fixed name is sufficient.
STRUCTURED_OUTPUT_TOOL_NAME = "extract_structured_output"
