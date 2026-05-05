import re
from typing import Any

from pydantic import BaseModel, Field

from common.llm.client import ChatBot
from evals.dataset_generation.data_for_testing.src.constants import (
    ASSESS_COHERENCE_TEMPLATE,
    ASSESS_LEAKAGE_TEMPLATE,
    PROPOSE_ALTERNATIVES_TEMPLATE,
    get_template,
)
from evals.dataset_generation.data_for_testing.src.types import SpanContext


class AlternativeEntry(BaseModel):
    value: str
    text: str


class ValueAlternatives(BaseModel):
    original: str
    alternatives: list[AlternativeEntry]


class AlternativesResponse(BaseModel):
    values: list[ValueAlternatives]


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


def apply_replacements(text: str, replacements: dict[str, str]) -> str:
    for original, alternative in replacements.items():
        text = re.sub(r"\b" + re.escape(original) + r"\b", alternative, text)
    return text


def check_removals(text: str, original_values: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "original_value": v,
            "found_in_rewrite": bool(re.search(r"\b" + re.escape(v) + r"\b", text)),
            "occurrences": len(re.findall(r"\b" + re.escape(v) + r"\b", text)),
        }
        for v in original_values
    ]


async def _propose_alternatives(
    chatbot: ChatBot, entries: list[SpanContext], n: int
) -> dict[str, list[AlternativeEntry]]:
    prompt = get_template(PROPOSE_ALTERNATIVES_TEMPLATE).render(entries=entries, n=n)
    chatbot.clear_history()
    response = await chatbot.structured_chat([{"role": "user", "content": prompt}], AlternativesResponse)
    return {v.original: v.alternatives for v in response.values}


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
    transcript_text: str,
    chatbot: ChatBot,
    num_alternatives: int = 2,
) -> dict[str, Any]:
    span_contexts = extract_span_contexts(reference)
    original_values = [s["text"] for s in span_contexts]
    characteristics = extract_characteristics(reference)
    alternatives_map = await _propose_alternatives(chatbot, span_contexts, num_alternatives)

    rewrites: list[dict[str, Any]] = []
    for i in range(num_alternatives):
        replacements = {
            v: alternatives_map[v][i].text
            for v in original_values
            if v in alternatives_map and i < len(alternatives_map[v])
        }
        rewritten = apply_replacements(transcript_text, replacements)
        checks = check_removals(rewritten, original_values)
        coherence = await _assess_coherence(chatbot, rewritten)

        leakage_checks = []
        for char, value in characteristics:
            result = await _assess_leakage(chatbot, rewritten, char, value)
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
                "replacements": replacements,
                "all_values_removed": not any(c["found_in_rewrite"] for c in checks),
                "coherence": round((coherence.score - 1) / 4, 4),
                "coherence_explanation": coherence.explanation,
                "leakage_checks": leakage_checks,
                "unexpected_edits": unexpected_edits,
                "transcript": rewritten,
            }
        )

    successful = sum(1 for r in rewrites if r["all_values_removed"])
    avg_coherence = round(sum(r["coherence"] for r in rewrites) / len(rewrites), 4) if rewrites else 0.0
    all_leakage_scores = [lc["score"] for r in rewrites for lc in r["leakage_checks"]]
    avg_leakage = round(sum(all_leakage_scores) / len(all_leakage_scores), 4) if all_leakage_scores else 0.0

    return {
        "summary": {
            "num_alternatives": num_alternatives,
            "successful_rewrite_rate": successful / len(rewrites) if rewrites else 0.0,
            "average_coherence": avg_coherence,
            "average_leakage": avg_leakage,
        },
        "rewrites": rewrites,
    }
