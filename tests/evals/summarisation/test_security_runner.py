from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import pytest

from evals.summarisation.src.common import load_config
from evals.summarisation.src.security import runner as runner_module
from evals.summarisation.src.security.runner import build_run_summary, run_security_eval


def _scenario(level):
    return {
        "scenario_id": f"demo__{level}",
        "base_transcript": "demo",
        "injection_level": level,
        "intended_solicitation": f"{level} injection note",
        "dialogue_entries": [
            {"speaker": "1", "text": "We approved the Q3 budget.", "start_time": 0.0, "end_time": 1.0},
            {"speaker": "2", "text": "Some instruction.", "start_time": 1.0, "end_time": 2.0},
        ],
    }


@pytest.fixture
def input_dir(tmp_path):
    d = tmp_path / "scenarios"
    d.mkdir()
    for name, level in (("a_benign", "benign"), ("b_borderline", "borderline"), ("c_malicious", "malicious")):
        (d / f"{name}.json").write_text(json.dumps(_scenario(level)), encoding="utf-8")
    return d


@pytest.fixture
def patched_pipeline(monkeypatch):
    """Mock the production summariser and the LLM judge so the runner makes no live calls."""

    async def fake_generate_summary(_dialogue_entries, _template_name=None):
        return SimpleNamespace(
            text="The team approved the Q3 budget and will reconvene in September.",
            total_claims=0,
            hallucinations=[],
        )

    async def fake_judge(*, dimensions, **_kwargs):
        return {"dimensions": {d: {"score": 5, "rationale": f"rationale for {d}"} for d in dimensions}}

    monkeypatch.setattr(runner_module, "generate_summary", fake_generate_summary)
    monkeypatch.setattr(runner_module, "call_llm_judge_parallel", fake_judge)


@pytest.fixture
def cfg(tmp_path, input_dir):
    cfg = load_config("evals/summarisation/configs/security.yaml")
    cfg.run.input_dir = str(input_dir)
    cfg.run.output_dir = str(tmp_path / "out")
    return cfg


@pytest.mark.usefixtures("patched_pipeline")
def test_run_security_eval_writes_artifacts(cfg, input_dir):
    from pathlib import Path

    run_id, results_path = asyncio.run(run_security_eval(cfg, input_dir, Path(cfg.run.output_dir)))

    run_dir = Path(cfg.run.output_dir) / run_id
    assert results_path.exists()
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "report.md").exists()

    records = [json.loads(line) for line in results_path.read_text().splitlines() if line.strip()]
    assert len(records) == 3

    # every record carries a summary and all three security dimensions
    for r in records:
        assert r["summary_text"]
        assert set(r["metrics"]) == {
            "rubric_harmfulness",
            "rubric_summarisation_adherence",
            "rubric_refusal_robustness",
        }
        assert r["metrics"]["rubric_harmfulness"]["score"] == 5


@pytest.mark.usefixtures("patched_pipeline")
def test_build_run_summary_aggregates(cfg, input_dir):
    from pathlib import Path

    run_id, _results_path = asyncio.run(run_security_eval(cfg, input_dir, Path(cfg.run.output_dir)))

    summary = json.loads((Path(cfg.run.output_dir) / run_id / "summary.json").read_text())
    assert summary["n_scenarios"] == 3
    assert set(summary["by_level"]) == {"benign", "borderline", "malicious"}
    assert summary["dimension_means"]["rubric_harmfulness"] == 5.0


def test_build_run_summary_empty():
    summary = build_run_summary("run-x", [])
    assert summary.n_scenarios == 0
    assert summary.by_level == {}
    assert summary.dimension_means == {}
