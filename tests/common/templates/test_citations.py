from unittest.mock import AsyncMock, patch

import pytest

from common.database.postgres_models import HallucinationType
from common.templates.citations import (
    CitationResult,
    ClaimCitation,
    ClaimsList,
    add_citations_to_minute,
    cite_claims,
    combine_consecutive_citations,
    extract_claims,
)


def test_combine_consecutive_citations_single():
    result = combine_consecutive_citations("The meeting concluded [1][2][3].")
    assert result == "The meeting concluded [1-3]."


def test_combine_consecutive_citations_gap():
    result = combine_consecutive_citations("Text [1][2][5][6].")
    assert result == "Text [1-2][5-6]."


def test_combine_consecutive_citations_no_citations():
    result = combine_consecutive_citations("No citations here.")
    assert result == "No citations here."


def test_combine_consecutive_citations_single_citation():
    result = combine_consecutive_citations("See reference [3].")
    assert result == "See reference [3]."


def test_combine_consecutive_citations_already_range():
    result = combine_consecutive_citations("Already ranged [1-3].")
    assert result == "Already ranged [1-3]."


@pytest.mark.asyncio
async def test_extract_claims_returns_list_from_structured_chat():
    draft = "<p>The project will cost £500,000 and complete by March 2025.</p>"
    expected_claims = ["The project will cost £500,000", "complete by March 2025"]

    with patch("common.templates.citations.create_default_chatbot") as mock_create:
        mock_chatbot = AsyncMock()
        mock_chatbot.structured_chat = AsyncMock(return_value=ClaimsList(claims=expected_claims))
        mock_create.return_value = mock_chatbot

        result = await extract_claims(draft)

    assert result == expected_claims


@pytest.mark.asyncio
async def test_extract_claims_returns_empty_list_when_no_claims():
    draft = "<p>The meeting took place.</p>"

    with patch("common.templates.citations.create_default_chatbot") as mock_create:
        mock_chatbot = AsyncMock()
        mock_chatbot.structured_chat = AsyncMock(return_value=ClaimsList(claims=[]))
        mock_create.return_value = mock_chatbot

        result = await extract_claims(draft)

    assert result == []


@pytest.mark.asyncio
async def test_cite_claims_returns_citation_result():
    draft = "<p>The budget is £1m. John mentioned the timeline.</p>"
    claims = ["The budget is £1m", "John mentioned the timeline"]
    transcript = []
    expected = CitationResult(
        cited_summary="<p>The budget is £1m[1]. John mentioned the timeline.</p>",
        claim_citations=[
            ClaimCitation(claim="The budget is £1m", citation_indices=[1]),
            ClaimCitation(claim="John mentioned the timeline", citation_indices=[]),
        ],
    )

    with patch("common.templates.citations.create_default_chatbot") as mock_create:
        mock_chatbot = AsyncMock()
        mock_chatbot.structured_chat = AsyncMock(return_value=expected)
        mock_create.return_value = mock_chatbot

        result = await cite_claims(draft, claims, transcript)

    assert result == expected


@pytest.mark.asyncio
async def test_add_citations_to_minute_returns_uncited_claims_as_hallucinations():
    transcript = []
    draft = "<p>The budget is £1m. John mentioned the timeline.</p>"
    cited = "<p>The budget is £1m[1]. John mentioned the timeline.</p>"

    with (
        patch(
            "common.templates.citations.extract_claims",
            new_callable=AsyncMock,
            return_value=["The budget is £1m", "John mentioned the timeline"],
        ),
        patch(
            "common.templates.citations.cite_claims",
            new_callable=AsyncMock,
            return_value=CitationResult(
                cited_summary=cited,
                claim_citations=[
                    ClaimCitation(claim="The budget is £1m", citation_indices=[1]),
                    ClaimCitation(claim="John mentioned the timeline", citation_indices=[]),
                ],
            ),
        ),
    ):
        result_minute, result_total_claims, result_hallucinations = await add_citations_to_minute(
            transcript=transcript, initial_draft=draft
        )

    assert "John mentioned the timeline" in result_minute
    assert result_total_claims == 2
    assert len(result_hallucinations) == 1
    assert result_hallucinations[0].hallucination_type == HallucinationType.FACTUAL_FABRICATION
    assert result_hallucinations[0].hallucination_text == "John mentioned the timeline"


@pytest.mark.asyncio
async def test_add_citations_to_minute_returns_empty_hallucinations_when_all_cited():
    transcript = []
    draft = "<p>The budget is £1m.</p>"
    cited = "<p>The budget is £1m[1].</p>"

    with (
        patch("common.templates.citations.extract_claims", new_callable=AsyncMock, return_value=["The budget is £1m"]),
        patch(
            "common.templates.citations.cite_claims",
            new_callable=AsyncMock,
            return_value=CitationResult(
                cited_summary=cited,
                claim_citations=[
                    ClaimCitation(claim="The budget is £1m", citation_indices=[1]),
                ],
            ),
        ),
    ):
        result_minute, result_total_claims, result_hallucinations = await add_citations_to_minute(
            transcript=transcript, initial_draft=draft
        )

    assert result_minute == cited
    assert result_total_claims == 1
    assert result_hallucinations == []
