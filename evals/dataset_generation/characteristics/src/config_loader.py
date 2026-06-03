import logging
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from evals.dataset_generation.characteristics.src.schema import EvalsConfig
from evals.dataset_generation.shared_constants import ProtectedCharacteristic

logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> EvalsConfig:
    """Loads evaluation config from a YAML file."""
    if not config_path.exists():
        logger.warning("Config file %s not found. Using default parameters.", config_path)
        return EvalsConfig()

    with config_path.open("r", encoding="utf-8") as f:
        raw_yaml = yaml.safe_load(f) or {}
    return EvalsConfig(**raw_yaml)


def _characteristic_context_filename(characteristic: ProtectedCharacteristic) -> str:
    """Return the Jinja2 template filename for a given characteristic."""
    return (
        characteristic.value.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_") + ".jinja2"
    )


def render_prompt_for_characteristic(
    base_template_path: Path,
    characteristic: ProtectedCharacteristic,
    transcript: str,
) -> str:
    """Render a characteristic-specific prompt using Jinja2 template inheritance.

    Each characteristic has its own Jinja2 template (in a characteristics/ subdirectory
    next to the base template) that extends the base template and fills in blocks for
    characteristic_name, characteristic_rules, and characteristic_examples.
    """
    filename = _characteristic_context_filename(characteristic)
    path = base_template_path.resolve()
    env = Environment(
        loader=FileSystemLoader(path.parent),
        autoescape=select_autoescape(),
    )
    template = env.get_template(f"characteristics/{filename}")
    return template.render(transcript=transcript)
