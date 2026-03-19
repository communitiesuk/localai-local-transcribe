from pathlib import Path
from evals.audio_generation.src.settings import AUDIO_GEN_DIR


def get_transcripts(file_name: str) -> str:
    transcript_file = AUDIO_GEN_DIR / "src" / "transcripts" / file_name

    if not transcript_file.is_file():
        raise FileNotFoundError(f"Transcript file not found: {transcript_file}")

    return transcript_file.read_text(encoding="utf-8")
