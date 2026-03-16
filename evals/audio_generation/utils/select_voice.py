default_voices = [
    "qimfC2HPDJhhTmdOzs2z",  # Eastern European man
    "hhDdiMwM9dWfw6qEFzju",  # Young Mancunian
]

voice_map = {
    "social_care_worker": "snf0TZa0mc0w5XBI",
    "storyteller": "AZnzlk1XvdvUeBnXmlld",
}

# _Prompt used to generate the audio for the social care worker speaker_
# A social care worker from the South East of England.
# Formal but not overly so, works with vulnerable people (homelessness, job security, children)
# Should be confident, assuring & sound natural

PYTHONHASHSEED = 0


def get_voice_for_speaker(speaker: str, fallback_pool: list[str] = default_voices) -> str:
    # if speaker in voice_map:
    #     return voice_map[speaker]

    # assign a fallback voice
    return fallback_pool[hash(speaker) % len(default_voices)]
