import logging
import os

from dotenv import load_dotenv
from evals.audio_generation.audio_transformation.audio_effects import (
    mix_audio_with_effects,
    mp3_to_bytes,
)
from evals.audio_generation.eleven_labs.eleven_labs import eleven_text_to_speech
from evals.audio_generation.transcripts.transcript_utils import get_transcripts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

load_dotenv()

api_key = os.getenv("ELEVEN_LABS_API_KEY")
model_id = "eleven_v3"
transcript_file = "two-teens.txt"
audio_file = "jordan-alex.mp3"
audio_sfx = "noise_on_a_typical_metro.mp3"

if api_key:
    logging.info("Eleven Labs API key found. Using Eleven Labs for audio generation.")
else:
    logging.info("No Eleven Labs API key found. Using a placeholder for audio generation.")



# combine stored transcribed audio and sound-effect files into a single mixed audio track
def mix_audio_with_fx()->None:
    speech_name, audio_bytes = mp3_to_bytes(f"eleven_labs/{audio_file}")
    sfx_name, sfx_bytes = mp3_to_bytes(f"background_sfx/{audio_sfx}") #background sfx generated on the elevenLabs platform & manually added to file
    mix_audio_with_effects(audio_bytes, sfx_bytes, speech_name, sfx_name)


#workflow to utilise eleven text to speech service
def eleven_tts() -> None:
    transcript = get_transcripts(transcript_file)
    eleven_text_to_speech(api_key or "", transcript, transcript_file, model_id)

if __name__ == "__main__":
    eleven_tts()
