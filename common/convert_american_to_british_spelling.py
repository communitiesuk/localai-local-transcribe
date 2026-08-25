import logging
import re
from re import Match

from breame.spelling import american_spelling_exists, get_british_spelling  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


def convert_american_to_british_spelling(text: str, strict: bool = False) -> str:
    if not text.strip():
        return text

    try:
        unmapped_count = 0

        def replace_word(match: Match[str]) -> str:
            nonlocal unmapped_count
            # The first group contains any leading punctuation/spaces
            # The second group contains the word
            # The third group contains any trailing punctuation/spaces
            pre, word, post = match.groups()

            # Skip if within code blocks
            if "`" in pre or "`" in post:
                return match.group(0)

            if american_spelling_exists(word.lower()):
                try:
                    british = str(get_british_spelling(word.lower()))
                    # Preserve capitalization
                    if word.isupper():
                        british = british.upper()
                    elif word.istitle():
                        british = british.title()
                    return pre + british + post
                except Exception:
                    unmapped_count += 1
                    if strict:
                        raise
            return match.group(0)

        # Match any word surrounded by non-letter characters
        # Group 1: Leading non-letters (including empty)
        # Group 2: The word itself (only letters)
        # Group 3: Trailing non-letters (including empty)
        pattern = r"([^a-zA-Z]*?)([a-zA-Z]+)([^a-zA-Z]*?)"
        result = re.sub(pattern, replace_word, text)

        if unmapped_count > 0:
            logger.warning("Unmapped spelling conversions: %d", unmapped_count)

        return result

    except Exception:
        logger.exception("Failed to convert text")
        if strict:
            raise
        return text
