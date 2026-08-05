import logging

from common.database.postgres_models import DialogueEntry
from common.llm.client import ChatBot, FastOrBestLLM, create_default_chatbot
from evals.dataset_generation.counterfactual_generation.src.constants import (
    COUNTERFACTUAL_REWRITE_TEMPLATE,
    get_template,
)
from evals.dataset_generation.counterfactual_generation.src.evidence_tracker import verify_evidence_modifications
from evals.dataset_generation.counterfactual_generation.src.models import (
    AxisChange,
    CharacteristicDetection,
    CounterfactualOutput,
    TranscriptInput,
)
from evals.dataset_generation.counterfactual_generation.src.parser import (
    parse_llm_response,
    strip_leading_entry_indexes,
)
from evals.dataset_generation.counterfactual_generation.src.validation import (
    identify_modified_entries,
    validate_evidence_spans,
)

logger = logging.getLogger(__name__)


class CounterfactualRewriter:
    """Counterfactual transcript rewriter."""

    def __init__(
        self, chatbot: ChatBot | None = None, prompt_version: str = "v1.0", model_name: str = "unknown"
    ) -> None:
        """Initialize the counterfactual rewriter."""
        self.chatbot = chatbot or create_default_chatbot(FastOrBestLLM.BEST)
        self.prompt_version = prompt_version
        self.model_name = model_name if chatbot else "default_best_llm"

    async def rewrite_transcript(
        self,
        original_transcript: TranscriptInput,
        characteristic_detection: CharacteristicDetection,
        axis_change: AxisChange,
    ) -> CounterfactualOutput:
        """Rewrite transcript to apply characteristic transformation."""
        logger.info(
            "Starting counterfactual rewrite: %s from %s to %s",
            axis_change.axis,
            axis_change.original_value,
            axis_change.target_value,
        )

        self._validate_axis_compatibility(characteristic_detection, axis_change)
        self._log_evidence_usage(characteristic_detection, len(original_transcript.dialogue_entries))

        original_texts = [entry["text"] for entry in original_transcript.dialogue_entries]
        prompt = self._build_prompt(original_texts, characteristic_detection, axis_change)

        self.chatbot.clear_history()
        messages = [{"role": "user", "content": prompt}]
        response = await self.chatbot.chat(messages=messages)

        rewritten_texts = strip_leading_entry_indexes(parse_llm_response(response))

        if len(rewritten_texts) != len(original_transcript.dialogue_entries):
            expected = len(original_transcript.dialogue_entries)
            got = len(rewritten_texts)
            msg = f"Text count mismatch: expected {expected}, got {got}"
            raise ValueError(msg)

        rewritten_entries = self._reconstruct_entries(original_transcript.dialogue_entries, rewritten_texts)
        modified_indices = identify_modified_entries(original_transcript.dialogue_entries, rewritten_entries)

        if characteristic_detection.evidence_spans:
            verify_evidence_modifications(
                characteristic_detection.evidence_spans,
                modified_indices,
                original_transcript.dialogue_entries,
                rewritten_entries,
            )

        return CounterfactualOutput(
            original_transcript=original_transcript,
            rewritten_transcript=rewritten_entries,
            axis_change=axis_change,
            model_version=self.model_name,
            prompt_version=self.prompt_version,
            evidence_spans_modified=modified_indices,
        )

    def _validate_axis_compatibility(
        self, characteristic_detection: CharacteristicDetection, axis_change: AxisChange
    ) -> None:
        """Validate the axis change refers to the same axis as the characteristic detection.

        The original values are deliberately not compared. A change carries a controlled
        vocabulary value such as "female", used for grouping in the bias evaluation, while a
        detection carries the free text phrase the detector produced such as "Female (name and
        pronoun proxy)". Which detection record a change applies to is settled when the
        detections are loaded, so the two values are not expected to be identical here.
        """
        if axis_change.axis != characteristic_detection.axis:
            msg = (
                f"Axis mismatch: change requests {axis_change.axis} "
                f"but detection found {characteristic_detection.axis}"
            )
            raise ValueError(msg)

    def _log_evidence_usage(self, characteristic_detection: CharacteristicDetection, max_index: int) -> None:
        """Log evidence span usage and validate if present."""
        if characteristic_detection.evidence_spans:
            logger.info(
                "Using %d evidence spans to guide rewriting",
                len(characteristic_detection.evidence_spans),
            )
            validate_evidence_spans(characteristic_detection.evidence_spans, max_index)
        else:
            logger.info("No evidence spans provided, applying uniform transformation")

    def _reconstruct_entries(
        self, original_entries: list[DialogueEntry], rewritten_texts: list[str]
    ) -> list[DialogueEntry]:
        """Deterministically reconstruct DialogueEntry objects with rewritten text."""
        rewritten_entries = []
        for original, new_text in zip(original_entries, rewritten_texts, strict=True):
            rewritten_entry = original.copy()
            rewritten_entry["text"] = new_text
            rewritten_entries.append(rewritten_entry)
        return rewritten_entries

    def _unique_evidence_spans_for_prompt(self, evidence_spans: list) -> list:
        """Keep the first span for each distinct text snippet when building the rewrite prompt.

        Detection often repeats the same phrase across overlapping character ranges. Listing
        every copy in the prompt bloated the evidence checklist and caused the model to return
        the wrong number of dialogue turns on long, densely annotated transcripts.
        """
        seen_snippets: set[str] = set()
        unique_spans = []
        for span in evidence_spans:
            if span.text_snippet in seen_snippets:
                continue
            seen_snippets.add(span.text_snippet)
            unique_spans.append(span)
        return unique_spans

    def _build_prompt(
        self,
        dialogue_texts: list[str],
        characteristic_detection: CharacteristicDetection,
        axis_change: AxisChange,
    ) -> str:
        """Build the prompt for LLM rewriting."""
        template = get_template(COUNTERFACTUAL_REWRITE_TEMPLATE)
        custom_instructions = getattr(axis_change, "instructions", None)

        return template.render(
            dialogue_texts=dialogue_texts,
            axis=axis_change.axis,
            original_value=axis_change.original_value,
            target_value=axis_change.target_value,
            evidence_spans=self._unique_evidence_spans_for_prompt(characteristic_detection.evidence_spans),
            custom_instructions=custom_instructions,
        )
