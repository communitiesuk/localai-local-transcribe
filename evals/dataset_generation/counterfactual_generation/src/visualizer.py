import difflib
import logging
from pathlib import Path

from jinja2 import Template

from evals.dataset_generation.counterfactual_generation.src.models import (
    CounterfactualOutput,
)

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
REPORT_TEMPLATE_PATH = TEMPLATE_DIR / "report.html"


def generate_modification_report(
    counterfactual_output: CounterfactualOutput,
    output_path: Path,
) -> None:
    """Generate HTML visualization comparing original vs rewritten transcripts."""
    html = _build_html_report(counterfactual_output)
    output_path.write_text(html)
    logger.info("Modification report saved to: %s", output_path)


def _compute_text_diff(original: str, rewritten: str) -> tuple[str, str]:
    """Compute word-level diff highlighting between two texts."""
    if original == rewritten:
        return original, rewritten

    matcher = difflib.SequenceMatcher(None, original, rewritten)
    original_html = []
    rewritten_html = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        original_chunk = original[i1:i2]
        rewritten_chunk = rewritten[j1:j2]

        if tag == "equal":
            original_html.append(original_chunk)
            rewritten_html.append(rewritten_chunk)
        elif tag == "replace":
            original_html.append(f'<mark class="removed">{original_chunk}</mark>')
            rewritten_html.append(f'<mark class="added">{rewritten_chunk}</mark>')
        elif tag == "delete":
            original_html.append(f'<mark class="removed">{original_chunk}</mark>')
        elif tag == "insert":
            rewritten_html.append(f'<mark class="added">{rewritten_chunk}</mark>')

    return "".join(original_html), "".join(rewritten_html)


def _build_html_report(counterfactual_output: CounterfactualOutput) -> str:
    """Build HTML report with collapsible diff view."""
    dialogue_entries = []
    modified_count = 0

    for idx, (original, rewritten) in enumerate(
        zip(
            counterfactual_output.original_transcript.dialogue_entries,
            counterfactual_output.rewritten_transcript,
            strict=True,
        )
    ):
        original_text = original.get("text", "")
        rewritten_text = rewritten.get("text", "")
        is_modified = original_text != rewritten_text

        if is_modified:
            modified_count += 1
            original_html, rewritten_html = _compute_text_diff(original_text, rewritten_text)
        else:
            original_html = original_text
            rewritten_html = rewritten_text

        dialogue_entries.append(
            {
                "idx": idx,
                "speaker": original.get("speaker", "Unknown"),
                "original_text": original_html,
                "rewritten_text": rewritten_html,
                "is_modified": is_modified,
            }
        )

    template_content = REPORT_TEMPLATE_PATH.read_text()
    template = Template(template_content, autoescape=True)
    return template.render(
        axis_change=counterfactual_output.axis_change,
        total_entries=len(counterfactual_output.original_transcript.dialogue_entries),
        modified_count=modified_count,
        dialogue_entries=dialogue_entries,
    )
