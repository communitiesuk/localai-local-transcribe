"""Pydantic schema for `feature_flags.json`.

This enforces the subset of AWS AppConfig's `AWS.AppConfig.FeatureFlags` format this repo
relies on, plus internal consistency rules (e.g. `flags`/`values` key symmetry) that AWS's
own `ValidateConfiguration` call doesn't check. Validating locally lets malformed content fail
fast, before a new hosted configuration version is ever created in AppConfig.

The model validates tightly on standard flags but is lax on multivariants: `attributes`
(flag-side) and any custom keys under `values` pass through unvalidated via `extra="allow"`,
since approximating AWS's own constraint schema (`pattern`/`enum`/`type` rules) risks drifting
out of sync with it. `validate_new_version` (AWS's own `ValidateConfiguration`) remains the
authoritative check for that content.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator


class FlagDefinition(BaseModel):
    """A single entry under `flags`. `extra="allow"` permits multivariant `attributes`."""

    model_config = ConfigDict(extra="allow")

    name: str
    description: str | None = None


class FlagValue(BaseModel):
    """A single entry under `values`. `extra="allow"` permits multivariant custom attributes."""

    model_config = ConfigDict(extra="allow")

    enabled: bool


class FeatureFlagsFile(BaseModel):
    flags: dict[str, FlagDefinition]
    values: dict[str, FlagValue]
    version: Literal["1"]

    @model_validator(mode="after")
    def check_flags_and_values_match(self) -> FeatureFlagsFile:
        flag_keys = set(self.flags)
        value_keys = set(self.values)

        problems = []
        if missing_values := flag_keys - value_keys:
            problems.append(f"flags missing a matching 'values' entry: {sorted(missing_values)}")
        if missing_flags := value_keys - flag_keys:
            problems.append(f"values missing a matching 'flags' entry: {sorted(missing_flags)}")
        for key, flag in self.flags.items():
            if flag.name != key:
                problems.append(f"flags['{key}'].name ({flag.name!r}) must match its key ({key!r})")

        if problems:
            raise ValueError("; ".join(problems))
        return self
