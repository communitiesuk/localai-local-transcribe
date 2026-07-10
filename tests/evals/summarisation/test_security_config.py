from __future__ import annotations

import pytest
from pydantic import ValidationError

from evals.summarisation.src.common import AppConfig, load_config

_BASE = """
run:
  eval_type: "{eval_type}"
  input_dir: "evals/summarisation/input/security"
  output_dir: "runs"
  seed: 0
  split: "test"
  prompt_version: "dev"

dataset:
  name: "security"
  config: "default"
  dialogue_field: "dialogue"
  reference_summary_field: "summary"

judge:
  pass_threshold: 4

metrics:
  - accuracy

prompts:
  summarizer_template_name: "General"
  judge_template_path: "evals/summarisation/prompts/judge.j2"
"""


def test_security_eval_type_is_valid(tmp_path):
    config_path = tmp_path / "security.yaml"
    config_path.write_text(_BASE.format(eval_type="security"), encoding="utf-8")

    cfg = load_config(config_path)

    assert isinstance(cfg, AppConfig)
    assert cfg.run.eval_type == "security"
    assert cfg.run.input_dir == "evals/summarisation/input/security"
    assert cfg.prompts.summarizer_template_name == "General"


def test_repo_security_config_loads():
    cfg = load_config("evals/summarisation/configs/security.yaml")
    assert cfg.run.eval_type == "security"


def test_invalid_eval_type_rejected(tmp_path):
    config_path = tmp_path / "bad.yaml"
    config_path.write_text(_BASE.format(eval_type="not_a_mode"), encoding="utf-8")

    with pytest.raises(ValidationError):
        load_config(config_path)
