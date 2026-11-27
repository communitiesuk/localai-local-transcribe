import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ENV_ASSETS = Path(__file__).parents[2] / "documentation" / "env_assets"


def _load_aws_module() -> ModuleType:
    utils = ModuleType("utils")
    utils.HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR = 0.1
    utils.NUM_SECTIONS = 1
    utils.TRANSCRIPT_WORDS = 1
    utils.WORKING_HOURS_PER_DAY = 8
    utils.combined_impact = lambda _llm, _asr: {"total_co2e_g": 1.0}
    utils._row = lambda _label, _value: None  # noqa: SLF001
    utils._section = lambda _title: None  # noqa: SLF001

    module_path = ENV_ASSETS / "aws.py"
    spec = importlib.util.spec_from_file_location("env_assets_aws", module_path)
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)

    existing_utils = sys.modules.get("utils")
    sys.modules["utils"] = utils
    try:
        spec.loader.exec_module(module)
    finally:
        if existing_utils is None:
            del sys.modules["utils"]
        else:
            sys.modules["utils"] = existing_utils
    return module


aws = _load_aws_module()


def test_calculate_prompts_for_console_values_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    values = iter(["0.017317", "0.064309"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(values))
    monkeypatch.setattr(aws, "last_month_window", lambda: ("start", "end", "April 2026"))
    monkeypatch.setattr(
        aws,
        "fetch_aws_emissions",
        lambda _start, _end: pytest.fail("AWS CLI should not be called by default"),
    )

    result = aws.calculate()

    assert result["source"] == "manual console entry"
    assert result["mbm_g"] == pytest.approx(17_317)
    assert result["lbm_g"] == pytest.approx(64_309)


def test_calculate_uses_aws_cli_only_when_requested(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(aws, "last_month_window", lambda: ("start", "end", "April 2026"))
    monkeypatch.setattr(
        aws,
        "fetch_aws_emissions",
        lambda _start, _end: {
            "EmissionsValues": {
                "TOTAL_MBM_CARBON_EMISSIONS": {"Value": 0.017317},
                "TOTAL_LBM_CARBON_EMISSIONS": {"Value": 0.064309},
            },
            "ModelVersion": "1.0",
        },
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt: pytest.fail("Manual input should not be requested"),
    )

    result = aws.calculate(api_calls=True)

    assert result["source"] == "AWS API via CLI"
    assert result["model_version"] == "1.0"
