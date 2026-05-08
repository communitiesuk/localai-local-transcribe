from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape, TemplateNotFound, Template
from pathlib import Path


_TEMPLATES_DIR = (
    Path(__file__).resolve().parent.parent
    / "default"
    / "template_prompts"
)
_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    undefined=StrictUndefined,
    autoescape=select_autoescape([]),
    keep_trailing_newline=True,
)


def render_template(template_path: str) -> Template:
    """
    Renders a template with the given context.

    :param template_path: The template to render.
    :param context: The context to use for rendering the template.
    :return: The rendered template.
    """

    try:
        return _env.get_template(template_path)

    except TemplateNotFound as e:
        raise TemplateNotFound(
            f"Template '{template_path}' not found in '{_TEMPLATES_DIR}'."
        ) from e

