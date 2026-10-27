"""Sample identity helpers for silver transcripts."""

from __future__ import annotations

import re
from uuid import NAMESPACE_URL, uuid5

MAX_SAMPLE_NAME_LENGTH = 60


def build_sample_id(relative_path: str, stem: str) -> str:
    """Build a stable draft identity from the discovered source path."""
    identity = uuid5(NAMESPACE_URL, relative_path).hex[:16]
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", stem)[:MAX_SAMPLE_NAME_LENGTH] or "audio"
    return f"{name}-{identity}"
