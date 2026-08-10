import json
import logging
import re

logger = logging.getLogger(__name__)

# Matches a leading "0. " style index the model may copy from the numbered prompt transcript.
_LEADING_ENTRY_INDEX = re.compile(r"^\d+\.\s")


def parse_llm_response(response: str) -> list[str]:
    """Parse LLM response to extract rewritten text strings."""
    try:
        response_clean = response.strip()

        if response_clean.startswith("```"):
            response_clean = _extract_from_code_block(response_clean)

        parsed = json.loads(response_clean)
        if not isinstance(parsed, list):
            msg = f"Expected list of text strings, got {type(parsed)}"
            raise ValueError(msg)

        rewritten_texts: list[str] = []
        for item in parsed:
            if not isinstance(item, str):
                msg = f"Expected string in list, got {type(item)}"
                raise ValueError(msg)
            rewritten_texts.append(item)

        return rewritten_texts

    except json.JSONDecodeError as e:
        logger.error("Failed to parse response. First 500 chars: %s", response[:500])
        msg = f"Failed to parse LLM response as JSON: {e}"
        raise ValueError(msg) from e


def strip_leading_entry_indexes(texts: list[str]) -> list[str]:
    """Remove a leading entry index such as ``0. `` from each rewritten turn.

    The rewrite prompt numbers input turns for clarity. The model sometimes copies that
    prefix into each JSON string. Stripping it before comparing turns keeps modification
    counts limited to real content changes.
    """
    return [_LEADING_ENTRY_INDEX.sub("", text) for text in texts]


def _extract_from_code_block(response: str) -> str:
    """Extract JSON content from markdown code block."""
    lines = response.split("\n")
    json_lines = []
    in_code_block = False

    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            json_lines.append(line)

    return "\n".join(json_lines)
