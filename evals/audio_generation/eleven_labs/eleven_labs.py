import logging
import re
import typing
from pathlib import Path

from elevenlabs.client import ElevenLabs

from evals.audio_generation.utils.build_pattern import build_pattern
from evals.audio_generation.utils.extract_speakers import extract_speakers
from evals.audio_generation.utils.save_audio import save_audio
from evals.audio_generation.utils.select_voice import get_voice_for_speaker

logger = logging.getLogger(__name__)


def eleven_text_to_speech(api_key: str, transcript_content: str, transcript_file: str, model_id: str) -> None:
    """
    Converts text to speech using the Eleven Labs API.
    """
    if not api_key:
        logger.warning("No Eleven Labs API key provided. Audio generation will be skipped.")
        return

    client = ElevenLabs(api_key=api_key)

    speakers = extract_speakers(transcript_content)
    regex_pattern = build_pattern(speakers)
    dialogue_entries = re.findall(regex_pattern, transcript_content, flags=re.DOTALL)

    audio_segments = []
    for speaker, text, _ in dialogue_entries:
        voice_id = get_voice_for_speaker(speaker)

        audio: typing.Iterator[bytes] = client.text_to_speech.convert(
            text=text.strip(),
            voice_id=voice_id,
            model_id=model_id,
        )
        audio_bytes = b"".join(audio)
        audio_segments.append(audio_bytes)

    full_audio = b"".join(audio_segments)

    output_file = Path(transcript_file).stem + ".mp3"

    eleven_labs_dir = Path(__file__).parent.resolve()
    target_dir = eleven_labs_dir / "generated_audio_files"

    saved_path = save_audio(full_audio, output_file, target_dir=target_dir)
    logger.info("Audio saved to %s", saved_path)
