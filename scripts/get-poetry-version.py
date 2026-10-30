import re
import sys
import tomllib
from pathlib import Path

with Path("pyproject.toml").open("rb") as pyproject:
    constraint = tomllib.load(pyproject)["tool"]["poetry"]["requires-poetry"]

match = re.fullmatch(r"=([0-9]+(?:\.[0-9]+)*(?:[A-Za-z0-9.+-]*)?)", constraint)
if not match:
    sys.exit(
        "Poetry version must be pinned exactly in pyproject.toml, "
        f'for example requires-poetry = "=2.5.1"; got {constraint!r}'
    )

# print is used here rather than a log since this is a helper script used by
# other scripts so we want the output in stdout
print(match.group(1))  # noqa: T201
