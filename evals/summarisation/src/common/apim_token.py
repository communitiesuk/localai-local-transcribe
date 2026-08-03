from __future__ import annotations

import logging
import os
import subprocess
import threading
import time
from collections.abc import Sequence
from pathlib import Path

import dotenv

from common.settings import DOT_ENV_PATH

logger = logging.getLogger(__name__)

TOKEN_VAR = "AZURE_APIM_ACCESS_TOKEN"  # noqa: S105 - the variable's name, not a token
REPO_ROOT = Path(__file__).resolve().parents[4]
APIM_SCRIPT = REPO_ROOT / "apim.sh"
ENV_PATH = REPO_ROOT / DOT_ENV_PATH
SCRIPT_TIMEOUT_S = 120.0
# Well inside the ~1h token lifetime, so a burst of examples finishing together costs one az call.
DEFAULT_MIN_INTERVAL_S = 300.0
# Evals run against the test APIM, which is the az-mhclg-test login profile.
DEFAULT_SCRIPT_ARGS: tuple[str, ...] = ("--test",)


class ApimTokenRefresher:
    """Re-runs ``./apim.sh`` during a run so a static APIM token cannot expire part-way through.

    Every LLM call builds its token provider from a freshly constructed ``Settings``, so a token
    written to ``.env`` and ``os.environ`` is picked up by the next call.
    """

    def __init__(
        self,
        *,
        script: Path = APIM_SCRIPT,
        script_args: Sequence[str] = DEFAULT_SCRIPT_ARGS,
        env_path: Path = ENV_PATH,
        min_interval_s: float = DEFAULT_MIN_INTERVAL_S,
    ) -> None:
        self._script = script
        self._script_args = list(script_args)
        self._env_path = env_path
        self._min_interval_s = min_interval_s
        self._lock = threading.Lock()
        self._last_refresh_s: float | None = None

    def refresh(self) -> bool:
        """Refreshes the token unless one was fetched under ``min_interval_s`` ago. Never raises."""
        with self._lock:
            now = time.monotonic()
            if self._last_refresh_s is not None and now - self._last_refresh_s < self._min_interval_s:
                return False
            refreshed = self._fetch_token()
            # Stamped on failure too, so a broken script is retried on the interval, not per example.
            self._last_refresh_s = time.monotonic()
            return refreshed

    def _fetch_token(self) -> bool:
        if not self._script.exists():
            logger.warning("APIM token refresh skipped: %s not found", self._script)
            return False

        try:
            result = subprocess.run(  # noqa: S603
                [str(self._script), *self._script_args],
                cwd=self._script.parent,
                capture_output=True,
                text=True,
                # Closed so an expired az login fails the script instead of blocking on a prompt.
                stdin=subprocess.DEVNULL,
                timeout=SCRIPT_TIMEOUT_S,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            logger.warning("APIM token refresh failed, keeping the current token: %s", exc)
            return False

        if result.returncode != 0:
            logger.warning(
                "APIM token refresh failed (exit %s), keeping the current token: %s",
                result.returncode,
                result.stderr.strip(),
            )
            return False

        return self._publish_token()

    def _publish_token(self) -> bool:
        token = dotenv.dotenv_values(self._env_path).get(TOKEN_VAR)
        if not token:
            logger.warning("APIM token refresh ran but %s is not set in %s", TOKEN_VAR, self._env_path)
            return False

        # os.environ takes precedence over the dotenv file in Settings, so it has to be updated too.
        os.environ[TOKEN_VAR] = token
        logger.info("APIM access token refreshed")
        return True
