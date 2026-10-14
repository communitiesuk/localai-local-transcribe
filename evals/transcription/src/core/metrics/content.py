"""Content WER using the shared conservative filler-word list."""

import jiwer

from evals.transcription.src.core.metrics.transforms import normalise_text

# Conservative non-lexical vocalisations. Meaningful responses such as "yeah",
# "okay", "right", and "oh" deliberately remain part of the score.
DEFAULT_IGNORED_WORDS = frozenset(
    {
        "ah",
        "eh",
        "er",
        "erm",
        "hm",
        "hmm",
        "mhm",
        "mm",
        "mmhmm",
        "uh",
        "uhh",
        "um",
        "umm",
    }
)


def normalise_content(text: str, ignored_words: frozenset[str] = DEFAULT_IGNORED_WORDS) -> str:
    """
    Apply the standard WER normalisation and remove agreed non-lexical words.
    """
    normalised_text = normalise_text(text)
    return " ".join(word for word in normalised_text.split() if word not in ignored_words)


def compute_content_wer_metrics(
    reference: str, hypothesis: str, ignored_words: frozenset[str] = DEFAULT_IGNORED_WORDS
) -> dict[str, int | float | None]:
    """
    Return WER and edit counts after content normalisation.

    A reference made up entirely of ignored words leaves no content to score against, so
    the rate is undefined and reported as None. The edit counts are still exact, and
    corpus-level scores sum them, so spurious hypothesis words are never lost.
    """
    reference_content = normalise_content(reference, ignored_words)
    hypothesis_content = normalise_content(hypothesis, ignored_words)
    if not reference_content:
        insertions = len(hypothesis_content.split())
        return {
            "content_wer": None,
            "hits": 0,
            "substitutions": 0,
            "deletions": 0,
            "insertions": insertions,
            "reference_words": 0,
            "hypothesis_words": insertions,
        }
    result = jiwer.process_words(reference_content, hypothesis_content)
    return {
        "content_wer": float(result.wer),
        "hits": int(result.hits),
        "substitutions": int(result.substitutions),
        "deletions": int(result.deletions),
        "insertions": int(result.insertions),
        "reference_words": int(result.hits + result.substitutions + result.deletions),
        "hypothesis_words": int(result.hits + result.substitutions + result.insertions),
    }
