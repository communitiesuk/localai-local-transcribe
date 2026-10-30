from pathlib import Path
from typing import Any, cast

from jinja2 import Environment, FileSystemLoader, StrictUndefined, Template, TemplateNotFound, select_autoescape

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "default" / "template_prompts"
_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    undefined=StrictUndefined,
    autoescape=select_autoescape([]),
    # Autoescape is disabled as we are generating plain text prompts, not HTML/XML.
    # This prevents characters like <, > used within tags from being unnecessarily escaped.
    # This can be revised later if HTML or XML rendering is introduced.
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
        error_msg = f"Template '{template_path}' not found in '{_TEMPLATES_DIR}'."
        raise TemplateNotFound(error_msg) from e


def call_macro(template: Template, macro: str, **kwargs: Any) -> str:
    """
    Calls a macro from a Jinja2 template with the provided keyword arguments.
    :param template: The Jinja2 template containing the macro.
    :param macro: The name of the macro to call.
    :param kwargs: The keyword arguments to pass to the macro.
    :return: The result of the macro call as a string.
    """

    return cast(str, getattr(template.module, macro)(**kwargs))
