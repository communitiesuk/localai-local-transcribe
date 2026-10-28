import re
import unicodedata
from pathlib import Path
from typing import Protocol
from urllib.parse import quote

_UNSAFE_FILENAME_CHARS = re.compile(r'[\x00-\x1f\x7f"\\/]')
_FALLBACK_FILENAME = "download"


def build_content_disposition(filename: str) -> str:
    """Build an RFC 6266 attachment header.

    S3 rejects header values it cannot represent in ISO-8859-1, so non-ASCII
    characters are carried by `filename*` and stripped from the plain fallback (`filename`)
    """
    cleaned = _UNSAFE_FILENAME_CHARS.sub("", filename).strip() or _FALLBACK_FILENAME
    ascii_filename = unicodedata.normalize("NFKD", cleaned).encode("ascii", "ignore").decode().strip()
    ascii_filename = re.sub(r"\s+", " ", ascii_filename) or _FALLBACK_FILENAME
    return f"attachment; filename=\"{ascii_filename}\"; filename*=UTF-8''{quote(cleaned, safe='')}"


class StorageService(Protocol):
    name: str

    @classmethod
    async def upload(cls, key: str, path: Path) -> None: ...

    @classmethod
    async def download(cls, key: str, path: Path) -> None: ...

    @classmethod
    async def generate_presigned_url_put_object(cls, key: str, expiry_seconds: int) -> str: ...

    @classmethod
    async def generate_presigned_url_get_object(cls, key: str, filename: str, expiry_seconds: int) -> str: ...

    @classmethod
    async def check_object_exists(cls, key: str) -> bool: ...

    @classmethod
    async def delete(cls, key: str) -> None: ...
