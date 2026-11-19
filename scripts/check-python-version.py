import platform
import sys
import tomllib
from pathlib import Path

from packaging.specifiers import SpecifierSet

with Path("pyproject.toml").open("rb") as pyproject:
    required = tomllib.load(pyproject)["project"]["requires-python"]

actual = platform.python_version()
if actual not in SpecifierSet(required):
    sys.exit(f"Python {actual} does not satisfy pyproject.toml requires-python: {required}")
