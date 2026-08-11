import secrets
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

_TEMPLATES_DIR = Path(__file__).parent / "prompt_templates"
_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    undefined=StrictUndefined,
    autoescape=select_autoescape([]),
    keep_trailing_newline=True,
)


def generate_marker_hash() -> str:
    """Generate the canary marker used to distinguish real boundaries from injected ones."""
    return secrets.token_hex(4)


def wrap_with_canary(label: str, content: str, marker_hash: str | None = None) -> str:
    if marker_hash is None:
        marker_hash = generate_marker_hash()
    return _env.get_template("canary_wrapper.j2").render(
        label=label,
        marker_hash=marker_hash,
        content=content,
    ).rstrip()
