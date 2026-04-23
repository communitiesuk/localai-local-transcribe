from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
COUNTERFACTUAL_REWRITE_TEMPLATE = "counterfactual_rewrite.j2"


def get_template(template_name: str) -> Template:
    env = Environment(loader=FileSystemLoader(PROMPTS_DIR), autoescape=True)
    return env.get_template(template_name)
