from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

ASSESS_COHERENCE_TEMPLATE = "assess_coherence.j2"
ASSESS_CONCEALMENT_TEMPLATE = "assess_concealment.j2"


def get_template(template_name: str) -> Template:
    env = Environment(loader=FileSystemLoader(PROMPTS_DIR), autoescape=True)
    return env.get_template(template_name)
