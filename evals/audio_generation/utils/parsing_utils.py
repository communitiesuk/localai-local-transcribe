import re
from pathlib import Path


def extract_speakers(transcript: str) -> list[str]:
    """
    Matches any "Name:" at the start of a line and returns a list of unique speaker names
    """
    speakers = re.findall(r"^([A-Za-z0-9 _-]+):", transcript, flags=re.MULTILINE)
    return list(dict.fromkeys(speakers))



def save_audio(
    full_audio: bytes,
    output_file: str | Path,
    target_dir: Path | None = None,
) -> str:
    """
    Saves audio bytes to a file.

    By default, saves to `audio_generation/generated_audio_files` directory.
    The caller can override this by passing `target_dir`.

    Returns the absolute path to the saved file as a string.
    """

    if target_dir is None:
        audio_gen_root = Path(__file__).parent.parent.resolve()
        target_dir = audio_gen_root / "generated_audio_files"

    target_dir.mkdir(parents=True, exist_ok=True)

    # Full path to output file
    path = target_dir / output_file
    if path.suffix == "":
        path = path.with_suffix(".mp3")

    path.write_bytes(full_audio)
    return str(path)




def build_pattern(speakers: list[str]) -> str:
    escaped = [re.escape(s) for s in speakers]
    group = "|".join(escaped)
    return rf"({group}):\s*(.+?)(?=({group}):|$)"
