import re
from pathlib import Path

from evals.audio_generation.src.settings import OUTPUT_DIR
from evals.audio_generation.src.tts_adapters.base import TTSAdapter
from evals.audio_generation.src.utils.audio_duration import get_audio_duration
from evals.audio_generation.src.utils.dialogue import DialogueEntry
from evals.audio_generation.src.utils.parsing_utils import (
    build_pattern,
    extract_speakers,
    get_transcripts,
    make_timestamp,
    save_audio,
)
from evals.audio_generation.src.utils.select_voice import get_voice_for_speaker
from evals.audio_generation.src.utils.write_dialogue import write_dialogue


def generate_eleven_tts_audio(
    adapter: TTSAdapter,
    transcript_file: str,
) -> str:
    """
    Full pipeline: transcript → audio file + structured dialogue output
    Returns saved file path
    """
    transcript_content = get_transcripts(transcript_file)
    transcript_path = Path(transcript_file)

    speakers = extract_speakers(transcript_content)
    regex_pattern = build_pattern(speakers)
    dialogue_entries = re.findall(regex_pattern, transcript_content, flags=re.DOTALL)

    audio_segments = []
    dialogue_output: list[DialogueEntry] = []

    current_time = 0.0

    for speaker, text, _ in dialogue_entries:
        voice_id = get_voice_for_speaker(speaker)

        audio_bytes = adapter.text_to_speech(text, voice_id)

        duration = get_audio_duration(audio_bytes)

        start_time = current_time
        end_time = current_time + duration

        dialogue_output.append(
            DialogueEntry(
                speaker=speaker,
                text=text.strip(),
                start_time=start_time,
                end_time=end_time,
            )
        )

        audio_segments.append(audio_bytes)
        current_time = end_time

    full_audio = b"".join(audio_segments)

    output_file = f"{transcript_path.stem}_{make_timestamp()}.mp3"
    target_dir = OUTPUT_DIR / "eleven_labs_tts"

    audio_path = save_audio(full_audio, output_file, target_dir=target_dir)

    write_dialogue(dialogue_output, OUTPUT_DIR / "transcripts" / f"{transcript_path.stem}_{make_timestamp()}.json")

    return audio_path
