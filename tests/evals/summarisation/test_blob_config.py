from __future__ import annotations

from evals.summarisation.src.common import AppConfig, BlobStorageConfig, load_config

_MINIMAL = {
    "run": {"output_dir": "runs"},
    "dataset": {"name": "knkarthick/dialogsum"},
    "judge": {"pass_threshold": 4},
    "prompts": {"judge_template_path": "prompts/judge.j2"},
}


def test_blob_disabled_by_default():
    cfg = AppConfig.model_validate(_MINIMAL)
    assert cfg.blob.enabled is False
    assert cfg.blob.output_prefix == "summarisation"


def test_dataset_defaults_to_huggingface():
    cfg = AppConfig.model_validate(_MINIMAL)
    assert cfg.dataset.source == "huggingface"
    assert cfg.dataset.blob_path is None


def test_blob_config_parsed_from_yaml(tmp_path):
    config_path = tmp_path / "cfg.yaml"
    config_path.write_text(
        """
run:
  eval_type: standard
  output_dir: out
dataset:
  name: synthetic
  source: blob
  blob_path: summarisation/standard/dialogues.jsonl
judge:
  pass_threshold: 4
prompts:
  judge_template_path: prompts/judge.j2
blob:
  enabled: true
  account_url: https://example.blob.core.windows.net
  output_prefix: summ-out
""",
        encoding="utf-8",
    )

    cfg = load_config(config_path)

    assert cfg.blob.enabled is True
    assert cfg.blob.account_url == "https://example.blob.core.windows.net"
    assert cfg.dataset.source == "blob"
    assert cfg.dataset.blob_path == "summarisation/standard/dialogues.jsonl"


def test_blob_storage_config_standalone_defaults():
    cfg = BlobStorageConfig()
    assert cfg.enabled is False
    assert cfg.account_url is None
