import io
from pathlib import Path

from pydub import AudioSegment

from evals.audio_generation.eleven_labs.config.settings import BACKGROUND_VOLUME_OFFSET


def mix_audio_with_background(
    speech_audio: bytes, effects_audio: bytes, speech_name: str, sfx_name: str
) -> AudioSegment:
    """
    Mixes the speech audio with the background sound effects audio using pydub.
    """
    audio_dir = Path(__file__).parent / "output"
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Load the speech and effects audio into AudioSegment objects
    dialogue = AudioSegment.from_mp3(io.BytesIO(speech_audio))
    background = AudioSegment.from_mp3(io.BytesIO(effects_audio))

    background = background + BACKGROUND_VOLUME_OFFSET

    # Loop background to match or exceed dialogue length
    if len(background) < len(dialogue):
        loops_needed = (len(dialogue) // len(background)) + 1
        background = background * loops_needed

        background = background[: len(dialogue)]

    final = background.overlay(dialogue)
    output_path = audio_dir / f"{speech_name}_mixed{sfx_name}.mp3"
    final.export(output_path, format="mp3")

    return final


def mp3_to_bytes(mp3_path: str | Path) -> tuple[str, bytes]:
    """
    Reads an MP3 file and returns its name and content as bytes.
    """
    audio_gen_root = Path(__file__).parent.parent.resolve()
    path = (audio_gen_root / mp3_path).resolve()

    if not path.exists():
        msg = f"MP3 file not found: {path}"
        raise FileNotFoundError(msg)

    file_name = path.stem

    return file_name.split("_", 1)[0], path.read_bytes()
