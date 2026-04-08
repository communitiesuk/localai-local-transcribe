from __future__ import annotations

from pathlib import Path

from jinja2 import Template


def render_template(path: str | Path, **kwargs: object) -> str:
    """Renders Jinja2 template from file with provided keyword arguments."""
    text = Path(path).read_text(encoding="utf-8")
    template = Template(text)
    return template.render(**kwargs)
