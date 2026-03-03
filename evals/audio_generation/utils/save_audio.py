from pathlib import Path


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
        # audio_generation dir's root
        audio_gen_root = Path(__file__).parent.parent.resolve()
        target_dir = audio_gen_root / "generated_audio_files"

    target_dir.mkdir(parents=True, exist_ok=True)

    # Full path to output file
    path = target_dir / output_file
    if path.suffix == "":
        path = path.with_suffix(".mp3")

    path.write_bytes(full_audio)
    return str(path)
