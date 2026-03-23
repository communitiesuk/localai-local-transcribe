import logging

from evals.audio_generation.src.audio_with_background import audio_with_background_fx
from evals.audio_generation.src.eleven_text_to_speech import generate_eleven_tts_audio
from evals.audio_generation.src.settings import (
    ELEVEN_LABS_API_KEY,
    ELEVEN_LABS_MODEL_ID,
    TRANSCRIPT_FILE,
)
from evals.audio_generation.src.tts_adapters.eleven_labs import ElevenLabsAdapter
from evals.audio_generation.src.utils.parsing_utils import parse_args

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def main() -> None:
    if not ELEVEN_LABS_API_KEY:
        error_message = "ELEVEN_LABS_API_KEY is missing. Please set it within your .env file."
        raise ValueError(error_message)

    adapter = ElevenLabsAdapter(ELEVEN_LABS_API_KEY, ELEVEN_LABS_MODEL_ID)

    args = parse_args()

    if args.command == "tts":
        generate_eleven_tts_audio(
            adapter=adapter,
            transcript_file=args.transcript or TRANSCRIPT_FILE,
        )

    elif args.command == "mix":
        audio_with_background_fx(
            transcript_file=args.audio,
            sfx_file=args.background,
        )


if __name__ == "__main__":
    main()
