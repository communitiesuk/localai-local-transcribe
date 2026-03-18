
from evals.audio_generation.eleven_labs.config.settings import VOICE_MAP, DEFAULT_VOICES

PYTHONHASHSEED = 0


def get_voice_for_speaker(speaker: str, fallback_pool: list[str] = DEFAULT_VOICES) -> str:
    if speaker in VOICE_MAP:
        return VOICE_MAP[speaker]

    return fallback_pool[hash(speaker) % len(fallback_pool)]
