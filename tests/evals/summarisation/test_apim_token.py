from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from evals.summarisation.src.common.apim_token import TOKEN_VAR, ApimTokenRefresher


@pytest.fixture(autouse=True)
def _clear_token_var(monkeypatch):
    monkeypatch.delenv(TOKEN_VAR, raising=False)


def _write_env(tmp_path: Path, token: str) -> Path:
    env_path = tmp_path / ".env"
    env_path.write_text(f"POSTGRES_HOST=localhost\n{TOKEN_VAR}={token}\n", encoding="utf-8")
    return env_path


def _script(tmp_path: Path) -> Path:
    script = tmp_path / "apim.sh"
    script.write_text("#!/bin/bash\n", encoding="utf-8")
    return script


def _refresher(tmp_path: Path, min_interval_s: float = 0.0) -> ApimTokenRefresher:
    return ApimTokenRefresher(
        script=_script(tmp_path),
        env_path=_write_env(tmp_path, "fresh-token"),
        min_interval_s=min_interval_s,
    )


def test_refresh_runs_script_and_publishes_new_token(tmp_path):
    refresher = _refresher(tmp_path)

    with patch("evals.summarisation.src.common.apim_token.subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stderr="")
        assert refresher.refresh() is True

    # Evals authenticate against the test APIM, so the test login profile is used.
    assert mock_run.call_args.args[0] == [str(tmp_path / "apim.sh"), "--test"]
    assert mock_run.call_args.kwargs["cwd"] == tmp_path
    # An expired az login must fail the script rather than block the run on a login prompt.
    assert mock_run.call_args.kwargs["stdin"] == subprocess.DEVNULL
    assert os.environ[TOKEN_VAR] == "fresh-token"


def test_refresh_skipped_within_min_interval(tmp_path):
    refresher = _refresher(tmp_path, min_interval_s=3600.0)

    with patch("evals.summarisation.src.common.apim_token.subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stderr="")
        assert refresher.refresh() is True
        assert refresher.refresh() is False

    assert mock_run.call_count == 1


def test_failed_refresh_keeps_current_token_and_waits_out_the_interval(tmp_path, monkeypatch):
    """A broken script must not be re-run for every example."""
    monkeypatch.setenv(TOKEN_VAR, "current-token")
    refresher = _refresher(tmp_path, min_interval_s=3600.0)

    with patch("evals.summarisation.src.common.apim_token.subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=1, stderr="Login required")
        assert refresher.refresh() is False
        assert refresher.refresh() is False

    assert mock_run.call_count == 1
    assert os.environ[TOKEN_VAR] == "current-token"


def test_refresh_keeps_current_token_when_script_times_out(tmp_path, monkeypatch):
    monkeypatch.setenv(TOKEN_VAR, "current-token")
    refresher = _refresher(tmp_path)

    with patch(
        "evals.summarisation.src.common.apim_token.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="apim.sh", timeout=1),
    ):
        assert refresher.refresh() is False

    assert os.environ[TOKEN_VAR] == "current-token"


def test_refresh_returns_false_when_script_missing(tmp_path):
    refresher = ApimTokenRefresher(
        script=tmp_path / "absent.sh",
        env_path=_write_env(tmp_path, "fresh-token"),
        min_interval_s=0.0,
    )

    with patch("evals.summarisation.src.common.apim_token.subprocess.run") as mock_run:
        assert refresher.refresh() is False

    mock_run.assert_not_called()
    assert TOKEN_VAR not in os.environ


def test_refresh_returns_false_when_env_has_no_token(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("POSTGRES_HOST=localhost\n", encoding="utf-8")
    refresher = ApimTokenRefresher(script=_script(tmp_path), env_path=env_path, min_interval_s=0.0)

    with patch("evals.summarisation.src.common.apim_token.subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stderr="")
        assert refresher.refresh() is False

    assert TOKEN_VAR not in os.environ
