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
    ASSESS_CONCEALMENT_TEMPLATE,
    get_template,
)
from evals.dataset_generation.data_for_testing.src.types import CharacteristicKey, SpanContext, SpanKey


class AxisTransformation(BaseModel):
    axis: str
    original_value: str
    target_value: str
    instructions: str | None = None


class CoherenceResponse(BaseModel):
    score: int = Field(ge=1, le=5)
    explanation: str


class ConcealmentResponse(BaseModel):
    reasoning: str
    score: int = Field(ge=1, le=4)
    explanation: str


def extract_span_contexts(reference: dict) -> list[SpanContext]:
    seen: set[SpanKey] = set()
    result: list[SpanContext] = []
    for item in reference.get("detected_characteristics", []):
        cat = item.get("characteristic", "")
        val = item.get("attribute_value", "")
        for span in item.get("evidence_spans", []):
            text = span.get("text", "")
            key = (text, cat, val)
            if text and key not in seen:
                seen.add(key)
                result.append({"text": text, "value": val, "category": cat})
    return result


def extract_characteristics(reference: dict) -> list[CharacteristicKey]:
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


async def _assess_concealment(
    chatbot: ChatBot, transcript: str, characteristic: str, value: str
) -> ConcealmentResponse:
    prompt = get_template(ASSESS_CONCEALMENT_TEMPLATE).render(
        transcript=transcript, characteristic=characteristic, value=value
    )
    chatbot.clear_history()
    return await chatbot.structured_chat([{"role": "user", "content": prompt}], ConcealmentResponse)


async def evaluate_counterfactual(
    reference: dict,
    dialogue_entries: list[dict],
    chatbot: ChatBot,
    axes: list[AxisTransformation],
    num_rewrites: int = 2,
) -> dict[str, Any]:
    span_contexts = extract_span_contexts(reference)
    characteristics = extract_characteristics(reference)
    dialogue_texts = [entry["text"] for entry in dialogue_entries]

    axis_results: list[dict[str, Any]] = []

    for axis_transform in axes:
        axis_spans = [s for s in span_contexts if s["category"].lower() == axis_transform.axis.lower()]
        original_values = [s["text"] for s in axis_spans]

        rewrites: list[dict[str, Any]] = []
        for i in range(num_rewrites):
            rewritten_texts = await _rewrite_transcript(chatbot, dialogue_texts, axis_transform, span_contexts)

            if len(rewritten_texts) != len(dialogue_entries):
                msg = f"LLM returned {len(rewritten_texts)} lines but dialogue has {len(dialogue_entries)}"
                raise ValueError(msg)
            rewritten_transcript = "\n".join(
                f"{entry.get('speaker', str(j + 1))}: {text}"
                for j, (entry, text) in enumerate(zip(dialogue_entries, rewritten_texts, strict=True))
            )

            checks = check_removals(rewritten_transcript, original_values)
            coherence = await _assess_coherence(chatbot, rewritten_transcript)

            axis_characteristics = [
                (char, value) for char, value in characteristics if char.lower() == axis_transform.axis.lower()
            ]
            concealment_checks = []
            for char, value in axis_characteristics:
                result = await _assess_concealment(chatbot, rewritten_transcript, char, value)
                concealment_checks.append(
                    {
                        "characteristic": char,
                        "value": value,
                        "score": round((result.score - 1) / 3, 4),
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
                    "rewrite_index": i,
                    "all_values_removed": not any(c["found_in_rewrite"] for c in checks),
                    "coherence": round((coherence.score - 1) / 4, 4),
                    "coherence_explanation": coherence.explanation,
                    "concealment_checks": concealment_checks,
                    "unexpected_edits": unexpected_edits,
                    "transcript": rewritten_transcript,
                }
            )

        successful_rewrite_rate = sum(1 for r in rewrites if r["all_values_removed"]) / len(rewrites)
        avg_coherence = round(sum(r["coherence"] for r in rewrites) / len(rewrites), 4)
        all_concealment_scores = [lc["score"] for r in rewrites for lc in r["concealment_checks"]]
        avg_concealment = (
            round(sum(all_concealment_scores) / len(all_concealment_scores), 4) if all_concealment_scores else 0.0
        )

        axis_results.append(
            {
                "axis_change": {
                    "axis": axis_transform.axis,
                    "original_value": axis_transform.original_value,
                    "target_value": axis_transform.target_value,
                },
                "successful_rewrite_rate": successful_rewrite_rate,
                "average_coherence": avg_coherence,
                "average_concealment": avg_concealment,
                "rewrites": rewrites,
            }
        )

    if axis_results:
        successful_axis_rate = sum(1 for a in axis_results if a["successful_rewrite_rate"] == 1.0) / len(axis_results)
        avg_coherence = round(sum(a["average_coherence"] for a in axis_results) / len(axis_results), 4)
        all_concealment = [a["average_concealment"] for a in axis_results]
        avg_concealment = round(sum(all_concealment) / len(all_concealment), 4)
    else:
        successful_axis_rate = 0.0
        avg_coherence = 0.0
        avg_concealment = 0.0

    return {
        "summary": {
            "num_axes": len(axis_results),
            "num_rewrites_per_axis": num_rewrites,
            "successful_axis_rate": successful_axis_rate,
            "average_coherence": avg_coherence,
            "average_concealment": avg_concealment,
        },
        "axes": axis_results,
    }
