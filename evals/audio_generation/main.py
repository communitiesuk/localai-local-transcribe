import logging
from pathlib import Path

from evals.audio_generation.audio_transformation.audio_background import (
    mix_audio_with_background,
    mp3_to_bytes,
)
from evals.audio_generation.eleven_labs.config.settings import (
    ELEVEN_LABS_API_KEY,
    ELEVEN_LABS_MODEL_ID,
    TRANSCRIPT_FILE,
)
from evals.audio_generation.eleven_labs.eleven_labs import eleven_text_to_speech

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def audio_with_background_fx(
    audio_dir: Path,
    audio_file: Path,
    audio_sfx: Path,
) -> None:
    """
    Combines stored audio dialogue and sound-effect files
    into a single mixed audio track.
    """
    speech_name, audio_bytes = mp3_to_bytes(audio_dir / audio_file)
    sfx_name, sfx_bytes = mp3_to_bytes(Path("background_sfx") / audio_sfx)
    mix_audio_with_background(audio_bytes, sfx_bytes, speech_name, sfx_name)


if __name__ == "__main__":
    eleven_text_to_speech(
        api_key=ELEVEN_LABS_API_KEY or "",
        transcript_file=TRANSCRIPT_FILE,
        model_id=ELEVEN_LABS_MODEL_ID,
    )
