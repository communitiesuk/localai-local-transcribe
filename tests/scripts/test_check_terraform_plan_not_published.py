import pytest

from scripts.check_terraform_plan_not_published import (
    PLAN_FILE_USED_ELSEWHERE,
    REPOSITORY_ROOT,
    RUNNER_TEMP_USED_ELSEWHERE,
    SAVE_OUTSIDE_TEMP,
    SHOWN_AS_JSON,
    find_problems,
    find_problems_in_repository,
)

SAFE_WORKFLOW = """
jobs:
  terraform-plan:
    steps:
      # The tfplan file contains secrets, so it is never uploaded.
      - name: Terraform plan
        run: terraform plan -no-color -input=false -out="$RUNNER_TEMP/tfplan" -lock=false -var="image_tag=abc"

      - name: Terraform show
        run: terraform show -no-color "$RUNNER_TEMP/tfplan" > tf_plan.txt

      - name: Upload readable plan
        uses: actions/upload-artifact@v7
        with:
          name: tf-plan-text-development
          path: terraform/development/tf_plan.txt
"""


def messages(workflow: str) -> list[str]:
    return [problem.message for problem in find_problems(workflow, "workflow.yml")]


def test_the_workflows_in_this_repository_pass():
    assert find_problems_in_repository(REPOSITORY_ROOT) == []


def test_a_workflow_that_saves_and_shows_the_plan_safely_passes():
    assert messages(SAFE_WORKFLOW) == []


def test_the_upload_that_caused_the_leak_is_caught():
    workflow = """
      - name: Terraform plan
        run: terraform plan -no-color -input=false -out=tfplan -lock=false

      - name: Upload plan artifact
        uses: actions/upload-artifact@v7
        with:
          name: tf-plan-development
          path: terraform/development/tfplan
    """

    problems = find_problems(workflow, ".github/workflows/terraform-plan.yml")

    assert [(problem.line_number, problem.message) for problem in problems] == [
        (3, SAVE_OUTSIDE_TEMP),
        (9, PLAN_FILE_USED_ELSEWHERE),
    ]
    assert problems[0].path == ".github/workflows/terraform-plan.yml"


@pytest.mark.parametrize(
    "line",
    [
        "          path: ${{ runner.temp }}/tfplan",
        '        run: aws s3 cp "$RUNNER_TEMP/tfplan" s3://some-bucket/',
        '        run: cat "$RUNNER_TEMP/tfplan"',
        "          path: |\n            tf_plan.txt\n            TFPLAN",
    ],
)
def test_any_other_use_of_the_plan_file_is_caught(line):
    assert PLAN_FILE_USED_ELSEWHERE in messages(SAFE_WORKFLOW + line)


@pytest.mark.parametrize(
    "command",
    [
        "terraform plan -out=tfplan",
        "terraform plan -out plan.bin",
        'terraform plan -out="$GITHUB_WORKSPACE/tfplan"',
        "tofu plan -input=false -out=saved",
    ],
)
def test_a_plan_saved_anywhere_but_the_runner_temp_directory_is_caught(command):
    assert messages(f"        run: {command}") == [SAVE_OUTSIDE_TEMP]


@pytest.mark.parametrize(
    "command",
    [
        'terraform plan -out="$RUNNER_TEMP/tfplan" && cp "$RUNNER_TEMP/tfplan" .',
        'terraform plan -out="$RUNNER_TEMP/tfplan"; curl -T plan.bin https://example.com',
        'terraform plan -out="$RUNNER_TEMP/tfplan" -out=saved',
    ],
)
def test_a_plan_command_that_does_anything_else_on_the_same_line_is_caught(command):
    assert messages(f"        run: {command}") == [SAVE_OUTSIDE_TEMP]


def test_a_plan_command_split_over_several_lines_is_caught():
    workflow = """
        run: |
          terraform plan -input=false \\
            -out="$RUNNER_TEMP/tfplan"
    """

    assert messages(workflow) == [SAVE_OUTSIDE_TEMP]


@pytest.mark.parametrize(
    "command",
    [
        'terraform show -json "$RUNNER_TEMP/tfplan" > plan.json',
        'terraform show -no-color -json "$RUNNER_TEMP/tfplan"',
        "terraform show -json",
    ],
)
def test_showing_a_plan_as_json_is_caught(command):
    assert messages(f"        run: {command}") == [SHOWN_AS_JSON]


@pytest.mark.parametrize(
    "line",
    [
        "          path: ${{ runner.temp }}",
        "          path: ${{ runner.temp }}/",
        '        run: tar -czf out.tgz "$RUNNER_TEMP"',
    ],
)
def test_other_uses_of_the_runner_temp_directory_are_caught_where_a_plan_is_saved(line):
    assert messages(SAFE_WORKFLOW + line) == [RUNNER_TEMP_USED_ELSEWHERE]


def test_the_runner_temp_directory_can_be_used_where_no_plan_is_saved():
    workflow = """
      - name: Terraform plan
        run: terraform plan -input=false -lock=false -detailed-exitcode
      - name: Save a report
        run: echo done > "$RUNNER_TEMP/report.txt"
    """

    assert messages(workflow) == []


def test_other_tools_with_an_out_flag_are_ignored_where_terraform_is_not_used():
    assert messages("        run: openssl req -new -out request.csr") == []


def test_comments_may_mention_the_plan_file():
    assert messages("      # Never upload tfplan, and never use terraform show -json") == []
