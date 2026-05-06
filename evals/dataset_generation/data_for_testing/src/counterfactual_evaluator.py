import re
from typing import Any

from pydantic import BaseModel, Field

from common.llm.client import ChatBot
from evals.dataset_generation.counterfactual_generation.src.constants import (
    COUNTERFACTUAL_REWRITE_TEMPLATE,
)
from evals.dataset_generation.counterfactual_generation.src.constants import (
    get_template as get_rewrite_template,
)
from evals.dataset_generation.counterfactual_generation.src.parser import parse_llm_response
from evals.dataset_generation.data_for_testing.src.constants import (
    ASSESS_COHERENCE_TEMPLATE,
    ASSESS_LEAKAGE_TEMPLATE,
    PROPOSE_ALTERNATIVES_TEMPLATE,
    get_template,
)
from evals.dataset_generation.data_for_testing.src.types import SpanContext


class AxisTransformation(BaseModel):
    axis: str
    original_value: str
    target_value: str


class AxesResponse(BaseModel):
    axes: list[AxisTransformation]


class CoherenceResponse(BaseModel):
    score: int = Field(ge=1, le=5)
    explanation: str


class LeakageResponse(BaseModel):
    reasoning: str
    score: int = Field(ge=1, le=5)
    explanation: str


def extract_span_contexts(reference: dict) -> list[SpanContext]:
    seen: set[str] = set()
    result: list[SpanContext] = []
    for item in reference.get("detected_characteristics", []):
        cat = item.get("characteristic", "")
        val = item.get("attribute_value", "")
        for span in item.get("evidence_spans", []):
            text = span.get("text", "")
            if text and text not in seen:
                seen.add(text)
                result.append({"text": text, "value": val, "category": cat})
    return result


def extract_characteristics(reference: dict) -> list[tuple[str, str]]:
    return list(
        {
            (item["characteristic"], item["attribute_value"])
            for item in reference.get("detected_characteristics", [])
            if item.get("characteristic") and item.get("attribute_value")
        }
    )


def check_removals(text: str, original_values: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "original_value": v,
            "found_in_rewrite": bool(re.search(r"\b" + re.escape(v) + r"\b", text)),
            "occurrences": len(re.findall(r"\b" + re.escape(v) + r"\b", text)),
        }
        for v in original_values
    ]


async def _propose_axes(chatbot: ChatBot, entries: list[SpanContext], n: int) -> list[AxisTransformation]:
    prompt = get_template(PROPOSE_ALTERNATIVES_TEMPLATE).render(entries=entries, n=n)
    chatbot.clear_history()
    response = await chatbot.structured_chat([{"role": "user", "content": prompt}], AxesResponse)
    return response.axes


async def _rewrite_transcript(
    chatbot: ChatBot,
    dialogue_texts: list[str],
    axis_transform: AxisTransformation,
    evidence_spans: list[SpanContext],
) -> list[str]:
    axis_spans = [s for s in evidence_spans if s["category"].lower() == axis_transform.axis.lower()]
    prompt = get_rewrite_template(COUNTERFACTUAL_REWRITE_TEMPLATE).render(
        dialogue_texts=dialogue_texts,
        axis=axis_transform.axis,
        original_value=axis_transform.original_value,
        target_value=axis_transform.target_value,
        evidence_spans=axis_spans,
    )
    chatbot.clear_history()
    response = await chatbot.chat(messages=[{"role": "user", "content": prompt}])
    return parse_llm_response(response)


async def _assess_coherence(chatbot: ChatBot, transcript: str) -> CoherenceResponse:
    prompt = get_template(ASSESS_COHERENCE_TEMPLATE).render(transcript=transcript)
    chatbot.clear_history()
    return await chatbot.structured_chat([{"role": "user", "content": prompt}], CoherenceResponse)


async def _assess_leakage(chatbot: ChatBot, transcript: str, characteristic: str, value: str) -> LeakageResponse:
    prompt = get_template(ASSESS_LEAKAGE_TEMPLATE).render(
        transcript=transcript, characteristic=characteristic, value=value
    )
    chatbot.clear_history()
    return await chatbot.structured_chat([{"role": "user", "content": prompt}], LeakageResponse)


async def evaluate_counterfactual(
    reference: dict,
    dialogue_entries: list[dict],
    chatbot: ChatBot,
    num_alternatives: int = 2,
) -> dict[str, Any]:
    span_contexts = extract_span_contexts(reference)
    characteristics = extract_characteristics(reference)
    dialogue_texts = [entry["text"] for entry in dialogue_entries]

    proposed_axes = await _propose_axes(chatbot, span_contexts, num_alternatives)

    rewrites: list[dict[str, Any]] = []
    for i, axis_transform in enumerate(proposed_axes):
        axis_spans = [s for s in span_contexts if s["category"].lower() == axis_transform.axis.lower()]
        original_values = [s["text"] for s in axis_spans]

        rewritten_texts = await _rewrite_transcript(chatbot, dialogue_texts, axis_transform, span_contexts)

        rewritten_transcript = "\n".join(
            f"{entry.get('speaker', str(j + 1))}: {text}"
            for j, (entry, text) in enumerate(zip(dialogue_entries, rewritten_texts, strict=False))
        )

        checks = check_removals(rewritten_transcript, original_values)
        coherence = await _assess_coherence(chatbot, rewritten_transcript)

        leakage_checks = []
        for char, value in characteristics:
            result = await _assess_leakage(chatbot, rewritten_transcript, char, value)
            leakage_checks.append(
                {
                    "characteristic": char,
                    "value": value,
                    "score": round((result.score - 1) / 4, 4),
                    "explanation": result.explanation,
                    "reasoning": result.reasoning,
                }
            )

        unexpected_edits = [
            {"original": c["original_value"], "occurrences_remaining": c["occurrences"]}
            for c in checks
            if c["found_in_rewrite"]
        ]

        rewrites.append(
            {
                "alternative_index": i,
                "axis_change": {
                    "axis": axis_transform.axis,
                    "original_value": axis_transform.original_value,
                    "target_value": axis_transform.target_value,
                },
                "all_values_removed": not any(c["found_in_rewrite"] for c in checks),
                "coherence": round((coherence.score - 1) / 4, 4),
                "coherence_explanation": coherence.explanation,
                "leakage_checks": leakage_checks,
                "unexpected_edits": unexpected_edits,
                "transcript": rewritten_transcript,
            }
        )

    successful = sum(1 for r in rewrites if r["all_values_removed"])
    avg_coherence = round(sum(r["coherence"] for r in rewrites) / len(rewrites), 4) if rewrites else 0.0
    all_leakage_scores = [lc["score"] for r in rewrites for lc in r["leakage_checks"]]
    avg_leakage = round(sum(all_leakage_scores) / len(all_leakage_scores), 4) if all_leakage_scores else 0.0

    return {
        "summary": {
            "num_rewrites": len(rewrites),
            "successful_rewrite_rate": successful / len(rewrites) if rewrites else 0.0,
            "average_coherence": avg_coherence,
            "average_leakage": avg_leakage,
        },
        "rewrites": rewrites,
    }
