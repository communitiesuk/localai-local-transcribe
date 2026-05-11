from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, Template, TemplateNotFound, select_autoescape

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "default" / "template_prompts"
_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    undefined=StrictUndefined,
    autoescape=select_autoescape([]),
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_template(template_path: str) -> Template:
    """
    Renders a template

    :param template_path: The template to render.
    :return: The rendered template.
    """

    try:
        return _env.get_template(template_path)

    except TemplateNotFound as e:
        raise TemplateNotFound(f"Template '{template_path}' not found in '{_TEMPLATES_DIR}'.") from e
