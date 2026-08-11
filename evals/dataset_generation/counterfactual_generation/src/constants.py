from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template

from evals.dataset_generation.shared_constants import ProtectedCharacteristic

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
# Entry templates live under prompts/counterfactual_rewrite/<axis_slug>.j2 and extend base.j2.
COUNTERFACTUAL_REWRITE_TEMPLATE_DIR = "counterfactual_rewrite"


def counterfactual_rewrite_template_name(axis: ProtectedCharacteristic | str) -> str:
    """Return the axis-specific rewrite template path under the prompts directory.

    Each protected characteristic has its own Jinja file that extends the shared base prompt, so
    reviewers edit one axis without scrolling through rules for the other eight.
    """
    axis_value = axis.value if isinstance(axis, ProtectedCharacteristic) else str(axis)
    slug = axis_value.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
    return f"{COUNTERFACTUAL_REWRITE_TEMPLATE_DIR}/{slug}.j2"


def get_template(template_name: str) -> Template:
    """Load a Jinja template from the counterfactual generation prompts directory."""
    env = Environment(loader=FileSystemLoader(PROMPTS_DIR), autoescape=True)
    return env.get_template(template_name)
