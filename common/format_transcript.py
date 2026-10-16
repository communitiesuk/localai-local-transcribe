from common.database.postgres_models import DialogueEntry


def _format_recording_offset(seconds: float) -> str:
    rounded_seconds = round(seconds)
    minutes, seconds = divmod(rounded_seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours:
        return f"+{hours}h{minutes}m{seconds}s"
    if minutes:
        return f"+{minutes}m{seconds}s"
    return f"+{seconds}s"


def _speaker_offset_and_text(entry: DialogueEntry) -> str:
    start_time = entry.get("start_time")
    if not isinstance(start_time, int | float):
        return f"{entry['speaker']}: {entry['text']}"
    return f"{entry['speaker']} (recording offset {_format_recording_offset(float(start_time))}): {entry['text']}"


def transcript_as_speaker_and_utterance(transcript: list[DialogueEntry]) -> str:
    return "\n".join([f"{item['speaker']}: {item['text']}" for item in transcript])


def transcript_as_index_speaker_and_utterance(
    transcript: list[DialogueEntry],
    *,
    include_recording_offsets: bool = False,
) -> str:
    if include_recording_offsets:
        return "\n".join(f"[{i}] {_speaker_offset_and_text(entry)}" for i, entry in enumerate(transcript))
    return "\n".join(f"[{i}] {entry['speaker']}: {entry['text']}" for i, entry in enumerate(transcript))
