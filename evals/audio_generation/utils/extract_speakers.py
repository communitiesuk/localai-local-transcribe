import re


def extract_speakers(transcript: str) -> list[str]:
    # Matches any "Name:" at the start of a line
    speakers = re.findall(r"^([A-Za-z0-9 _-]+):", transcript, flags=re.M)
    return list(dict.fromkeys(speakers))
