from collections.abc import Iterable

from common.database.postgres_models import DialogueEntry


def transcript_as_speaker_and_utterance(transcript: list[DialogueEntry]) -> str:
    return "\n".join([f"{item['speaker']}: {item['text']}" for item in transcript])


def format_indexed_transcript(entries: Iterable[tuple[int, str, str]]) -> str:
    """Format (index, speaker, text) tuples as a numbered transcript string.

    This is the single source of truth for the [n] speaker: text format used
    in prompts and evals.
    """
    return "\n".join(f"[{index}] {speaker}: {text}" for index, speaker, text in entries)


def transcript_as_index_speaker_and_utterance(transcript: list[DialogueEntry]) -> str:
    return format_indexed_transcript(
        (i, entry["speaker"], entry["text"]) for i, entry in enumerate(transcript, start=1)
    )
