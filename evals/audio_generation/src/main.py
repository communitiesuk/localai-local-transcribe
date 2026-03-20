import logging
from pathlib import Path

from evals.audio_generation.src.audio_transformation.audio_background import (
    mix_audio_with_background,
    mp3_to_bytes
)

from evals.audio_generation.src.settings import (
    ELEVEN_LABS_API_KEY,
    ELEVEN_LABS_MODEL_ID,
    TRANSCRIPT_FILE,
    OUTPUT_DIR,
    INPUT_DIR
)

from evals.audio_generation.src.tts_adapters.eleven_labs import ElevenLabsAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")



if __name__ == "__main__":

    adapter = ElevenLabsAdapter(ELEVEN_LABS_API_KEY, ELEVEN_LABS_MODEL_ID)
    adapter.generate_audio(TRANSCRIPT_FILE)
    # eleven_text_to_speech(
    #     api_key=ELEVEN_LABS_API_KEY or "",
    #     transcript_file=TRANSCRIPT_FILE,
    #     model_id=ELEVEN_LABS_MODEL_ID,
    # )

    # audio_with_background_fx("eleven_labs_tts_output/two-teens.mp3", "background_sfx/cafe_ambience.mp3" )
