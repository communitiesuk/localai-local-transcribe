import re


def extract_speakers(transcript: str) -> list[str]:
    """
    Matches any "Name:" at the start of a line and returns a list of unique speaker names
    """
    speakers = re.findall(r"^([A-Za-z0-9 _-]+):", transcript, flags=re.MULTILINE)
    return list(dict.fromkeys(speakers))
