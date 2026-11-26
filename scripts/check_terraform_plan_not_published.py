"""Fails if a GitHub Actions workflow could publish a saved Terraform plan.

A saved plan (the file written by `terraform plan -out=...`) contains the whole Terraform state,
including every secret in it, with nothing redacted. This repository is public, so uploading that
file as an artifact, copying it anywhere or printing it with `terraform show -json` leaks the
environment's secrets.

This check reads the workflow files as text and allows a saved plan to be mentioned in exactly two
ways: the command that writes it and the command that turns it into redacted text. Anything else
that mentions it fails.

This check runs before any plans are made so that a workflow that breaks these rules can be stopped
before it gets AWS credentials.
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_DIRECTORY = ".github"
WORKFLOW_SUFFIXES = (".yml", ".yaml")

PLAN_FILE = '"$RUNNER_TEMP/tfplan"'

# The only two commands that may mention a saved plan. Each must be on one line.
ALLOWED_PLAN_COMMAND = re.compile(r'^terraform plan (?:\S.*\s)?-out="\$RUNNER_TEMP/tfplan"(?:\s.*)?$')
ALLOWED_SHOW_COMMAND = re.compile(r'^terraform show -no-color "\$RUNNER_TEMP/tfplan" > tf_plan\.txt$')

MENTIONS_PLAN_FILE = re.compile(r"tfplan", re.IGNORECASE)
MENTIONS_TERRAFORM = re.compile(r"\b(?:terraform|tofu)\b", re.IGNORECASE)
SAVES_A_PLAN = re.compile(r"(?<![\w-])-out(?:=|\s|$)")
SHOWS_AS_JSON = re.compile(r"\bshow\b.*-json\b")
MENTIONS_RUNNER_TEMP = re.compile(r"runner[._]temp", re.IGNORECASE)
CHAINS_ANOTHER_COMMAND = re.compile(r"[;&|<>`]|\$\(")
STEP_PREFIX = re.compile(r"^(?:-\s+)?(?:run:\s*)?")

SAVE_OUTSIDE_TEMP = (
    f"A saved Terraform plan contains secrets. Write it with `terraform plan ... -out={PLAN_FILE}` on a single "
    "line with no other command, so that it stays outside the repository folder."
)
PLAN_FILE_USED_ELSEWHERE = (
    "A saved Terraform plan contains secrets. It may only be written by `terraform plan` and read by "
    f"`terraform show -no-color {PLAN_FILE} > tf_plan.txt`. Never upload, copy or print it."
)
SHOWN_AS_JSON = "`terraform show -json` prints secrets without redacting them. Use `terraform show -no-color`."
RUNNER_TEMP_USED_ELSEWHERE = (
    "This workflow saves a Terraform plan in the runner's temporary directory, so nothing else in it may "
    "use that directory: an upload from there would include the plan."
)


@dataclass(frozen=True)
class Problem:
    path: str
    line_number: int
    message: str


def _command(line: str) -> str:
    return STEP_PREFIX.sub("", line.strip(), count=1).strip()


def _is_allowed(command: str) -> bool:
    if SHOWS_AS_JSON.search(command):
        return False
    if ALLOWED_SHOW_COMMAND.match(command):
        return True
    return bool(
        ALLOWED_PLAN_COMMAND.match(command)
        and not CHAINS_ANOTHER_COMMAND.search(command)
        and len(MENTIONS_PLAN_FILE.findall(command)) == 1
        and len(SAVES_A_PLAN.findall(command)) == 1
    )


def _problem_with(line: str, *, file_uses_terraform: bool, file_saves_a_plan: bool) -> str | None:
    command = _command(line)
    if not command or command.startswith("#"):
        return None
    if SHOWS_AS_JSON.search(command) and (file_uses_terraform or MENTIONS_PLAN_FILE.search(command)):
        return SHOWN_AS_JSON
    if _is_allowed(command):
        return None
    if file_uses_terraform and SAVES_A_PLAN.search(command):
        return SAVE_OUTSIDE_TEMP
    if MENTIONS_PLAN_FILE.search(command):
        return PLAN_FILE_USED_ELSEWHERE
    if file_saves_a_plan and MENTIONS_RUNNER_TEMP.search(command):
        return RUNNER_TEMP_USED_ELSEWHERE
    return None


def find_problems(text: str, path: str) -> list[Problem]:
    lines = text.splitlines()
    file_uses_terraform = bool(MENTIONS_TERRAFORM.search(text))
    file_saves_a_plan = file_uses_terraform and any(SAVES_A_PLAN.search(_command(line)) for line in lines)

    problems = []
    for line_number, line in enumerate(lines, start=1):
        message = _problem_with(line, file_uses_terraform=file_uses_terraform, file_saves_a_plan=file_saves_a_plan)
        if message is not None:
            problems.append(Problem(path=path, line_number=line_number, message=message))
    return problems


def find_problems_in_repository(root: Path) -> list[Problem]:
    problems = []
    for workflow_file in sorted((root / WORKFLOW_DIRECTORY).rglob("*")):
        if workflow_file.is_file() and workflow_file.suffix in WORKFLOW_SUFFIXES:
            relative_path = workflow_file.relative_to(root).as_posix()
            problems.extend(find_problems(workflow_file.read_text(encoding="utf-8"), relative_path))
    return problems


def main() -> int:
    problems = find_problems_in_repository(REPOSITORY_ROOT)
    for problem in problems:
        # The `::error` form makes GitHub show the message against the line in the pull request.
        sys.stdout.write(f"::error file={problem.path},line={problem.line_number}::{problem.message}\n")
    if problems:
        sys.stdout.write(f"{len(problems)} problem(s) found. No Terraform plan will run until they are fixed.\n")
        return 1
    sys.stdout.write("No workflow publishes a saved Terraform plan.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
