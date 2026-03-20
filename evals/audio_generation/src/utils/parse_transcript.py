import re
from pathlib import Path
from typing import List
from evals.audio_generation.src.utils.dialogue import DialogueEntry

def parse_transcript(file_path: str | Path) -> List[DialogueEntry]:
    content = Path(file_path).read_text(encoding="utf-8")

    pattern = r"(.*?):\s*\n(.*?)(?=\n.*?:|\Z)"
    matches = re.findall(pattern, content, flags=re.DOTALL)

    entries = []

    for speaker, text in matches:
        entries.append(
            DialogueEntry(
                speaker=speaker.strip(),
                text=text.strip(),
                start_time=0.0,
                end_time=0.0,
            )
        )

    return entries