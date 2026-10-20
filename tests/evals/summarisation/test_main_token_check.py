"""The summarisation run fetches one AI Gateway token before it reads any data.

A missing pipeline value is not empty. .env.example uses a placeholder, and Azure DevOps
leaves an unmapped variable as the literal $(NAME). Both must fail at this fetch, before
the dataset is staged.

Exercises: evals.summarisation.src.main._require_ai_gateway_token.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar
from unittest.mock import patch

import pytest
import yaml
from typer.testing import CliRunner

from common.azure_apim_auth import get_azure_client_secret_token_provider
from evals.summarisation.src.main import _require_ai_gateway_token, app

runner = CliRunner()

# Kept before the autouse fixture replaces the module attribute.
_real_require_ai_gateway_token = _require_ai_gateway_token


def _write_config(tmp_path: Path) -> Path:
    cfg = {
        "run": {"eval_type": "standard", "output_dir": str(tmp_path / "output"), "limit": 1},
        "dataset": {"name": "synthetic", "dialogue_field": "dialogue", "reference_summary_field": "summary"},
        "judge": {"pass_threshold": 4},
        "prompts": {"judge_template_path": "evals/summarisation/prompts/judge.j2"},
    }
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return path


class _RejectingCredential:
    """Records the secret it was given and refuses the token request."""

    def __init__(self, _tenant_id: str, _client_id: str, client_secret: str) -> None:
        """Keep the secret so the failure can name the value that was supplied."""
        self.client_secret = client_secret

    def get_token(self, _scope: str) -> str:
        """Fail the sign-in. The secret is non-empty, which is the case under test."""
        message = f"sign-in failed for {self.client_secret}"
        raise RuntimeError(message)


class _AcceptingCredential:
    """Returns a token without contacting Azure."""

    events: ClassVar[list[str]] = []

    def __init__(self, _tenant_id: str, _client_id: str, _client_secret: str) -> None:
        """Accept the three values the real credential is constructed with."""

    def get_token(self, _scope: str) -> SimpleNamespace:
        """Return a token object with the shape the provider stores."""
        self.events.append("token")
        return SimpleNamespace(token="fetched-token")


@pytest.fixture
def client_secret_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Point the run at client-secret auth with the four values the pipeline supplies."""
    monkeypatch.setattr("evals.summarisation.src.main._require_ai_gateway_token", _real_require_ai_gateway_token)
    monkeypatch.setenv("AZURE_APIM_AUTH_METHOD", "client_secret")
    monkeypatch.setenv("AZURE_APIM_TENANT_ID", "tenant")
    monkeypatch.setenv("AZURE_APIM_CLIENT_ID", "client")
    monkeypatch.setenv("AZURE_APIM_SCOPE", "api://example/.default")
    get_azure_client_secret_token_provider.cache_clear()
    yield
    get_azure_client_secret_token_provider.cache_clear()


@pytest.mark.usefixtures("client_secret_env")
@pytest.mark.parametrize("client_secret", ["$(AZURE_APIM_CLIENT_SECRET)", "not_needed_for_static_token"])
def test_bad_client_secret_stops_the_run_before_the_dataset_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, client_secret: str
) -> None:
    monkeypatch.setenv("AZURE_APIM_CLIENT_SECRET", client_secret)
    monkeypatch.setattr("common.azure_apim_auth.ClientSecretCredential", _RejectingCredential)

    with patch("evals.summarisation.src.main.run_standard_eval") as run_eval:
        result = runner.invoke(app, ["--config", str(_write_config(tmp_path))])

    assert result.exit_code != 0
    assert isinstance(result.exception, RuntimeError)
    assert client_secret in str(result.exception)
    run_eval.assert_not_called()


@pytest.mark.usefixtures("client_secret_env")
def test_token_is_fetched_before_the_dataset_is_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AZURE_APIM_CLIENT_SECRET", "secret")
    _AcceptingCredential.events = []
    monkeypatch.setattr("common.azure_apim_auth.ClientSecretCredential", _AcceptingCredential)

    def _run_eval(*_args: object, **_kwargs: object) -> list[object]:
        _AcceptingCredential.events.append("eval")
        return []

    with patch("evals.summarisation.src.main.run_standard_eval", side_effect=_run_eval):
        result = runner.invoke(app, ["--config", str(_write_config(tmp_path))])

    assert result.exit_code == 0, result.output
    assert _AcceptingCredential.events == ["token", "eval"]
