import logging
import re
import typing
from pathlib import Path

from elevenlabs.client import ElevenLabs

from evals.audio_generation.transcripts.transcript_util import get_transcripts
from evals.audio_generation.utils.parsing_utils import build_pattern, extract_speakers, save_audio
from evals.audio_generation.utils.select_voice import get_voice_for_speaker

logger = logging.getLogger(__name__)


def eleven_text_to_speech(api_key: str, transcript_file: str, model_id: str) -> None:
    """
    Convert transcript to speech using Eleven Labs TTS.
    Parameters:
        api_key: Eleven Labs API key
        transcript_file: Path to the transcript text file
        model_id: Voice/model to use for TTS
    """

    if not api_key:
        logger.warning("No Eleven Labs API key provided. Audio generation will be skipped.")
        return

    transcript_content = get_transcripts(transcript_file)
    transcript_path = Path(transcript_file)

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

    output_file = Path(transcript_path).stem + ".mp3"

    eleven_labs_dir = Path(__file__).parent.resolve()
    target_dir = eleven_labs_dir / "output"

    saved_path = save_audio(full_audio, output_file, target_dir=target_dir)
    logger.info("Audio saved to %s", saved_path)
