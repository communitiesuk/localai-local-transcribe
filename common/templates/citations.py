import re

from pydantic import BaseModel

from common.canaries import strip_boundary_metadata
from common.database.postgres_models import DialogueEntry
from common.llm.client import FastOrBestLLM, create_default_chatbot
from common.prompts import get_cite_claims_prompt, get_extract_claims_prompt
from common.types import LLMHallucination


class ClaimsList(BaseModel):
    claims: list[str]


class ClaimCitation(BaseModel):
    claim: str
    citation_indices: list[int]


class CitationResult(BaseModel):
    cited_summary: str
    claim_citations: list[ClaimCitation]


async def extract_claims(draft: str) -> list[str]:
    chatbot = create_default_chatbot(FastOrBestLLM.BEST)
    result = await chatbot.structured_chat(
        messages=get_extract_claims_prompt(draft),
        response_format=ClaimsList,
    )
    return result.claims


async def cite_claims(
    draft: str,
    claims: list[str],
    transcript: list[DialogueEntry],
) -> CitationResult:
    chatbot = create_default_chatbot(FastOrBestLLM.BEST)
    result = await chatbot.structured_chat(
        messages=get_cite_claims_prompt(draft, claims, transcript),
        response_format=CitationResult,
    )
    result.cited_summary = strip_boundary_metadata(result.cited_summary)
    return result


async def add_citations_to_minute(
    transcript: list[DialogueEntry],
    initial_draft: str,
) -> tuple[str, int, list[LLMHallucination]]:
    claims = await extract_claims(initial_draft)
    total_claims = len(claims)
    citation_result = await cite_claims(initial_draft, claims, transcript)

    minute = combine_consecutive_citations(strip_boundary_metadata(citation_result.cited_summary))

    uncited_hallucinations = [
        LLMHallucination(
            hallucination_text=cc.claim,
            hallucination_reason="Could not find supporting evidence in the transcript",
        )
        for cc in citation_result.claim_citations
        if not cc.citation_indices
    ]

    return minute or "", total_claims, uncited_hallucinations


MAX_CITATION_DISTANCE = 2

cluster_pattern = re.compile(r"(\[\d+\])+")
citation_pattern = re.compile(r"\d+")


def combine_consecutive_citations(minute: str) -> str:
    matches = cluster_pattern.finditer(minute)
    for match in matches:
        citation_cluster = match.group()
        numbers = [int(n.group()) for n in citation_pattern.finditer(citation_cluster)]
        numbers.sort()
        groups: list[list[int]] = []
        for number in numbers:
            if len(groups) == 0 or abs(groups[-1][-1] - number) > MAX_CITATION_DISTANCE:
                groups.append([number])
            else:
                groups[-1].append(number)

        out = ""
        for citation_group in groups:
            if len(citation_group) == 1:
                out += f"[{citation_group[0]}]"
            else:
                out += f"[{citation_group[0]}-{citation_group[-1]}]"
        minute = minute.replace(citation_cluster, out)
    return minute
