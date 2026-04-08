from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from evals.summarisation.src.bias.sentiment_analyzer import SentimentAnalyzer


@pytest.fixture
def mock_sentiment_pipeline():
    with (
        patch("evals.summarisation.src.bias.sentiment_analyzer.pipeline") as mock_pipeline,
        patch("evals.summarisation.src.bias.sentiment_analyzer.AutoTokenizer") as mock_tokenizer_class,
    ):
        mock_tokenizer = MagicMock()
        mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
        mock_tokenizer.decode.return_value = "test text"
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer

        mock_pipe = MagicMock()
        mock_pipeline.return_value = mock_pipe

        yield mock_pipe, mock_tokenizer


def test_sentiment_analyzer_initialization(mock_sentiment_pipeline):
    mock_pipe, mock_tokenizer = mock_sentiment_pipeline

    analyzer = SentimentAnalyzer()

    assert analyzer.sentiment_pipeline == mock_pipe
    assert analyzer.tokenizer == mock_tokenizer


def test_compute_sentiment_positive(mock_sentiment_pipeline):
    mock_pipe, mock_tokenizer = mock_sentiment_pipeline

    mock_pipe.return_value = [
        [
            {"label": "positive", "score": 0.9},
            {"label": "negative", "score": 0.1},
        ]
    ]

    analyzer = SentimentAnalyzer()
    result = analyzer.compute_sentiment("This is great!")

    assert result == 0.8
    assert mock_pipe.called


def test_compute_sentiment_negative(mock_sentiment_pipeline):
    mock_pipe, mock_tokenizer = mock_sentiment_pipeline

    mock_pipe.return_value = [
        [
            {"label": "positive", "score": 0.2},
            {"label": "negative", "score": 0.8},
        ]
    ]

    analyzer = SentimentAnalyzer()
    result = analyzer.compute_sentiment("This is terrible!")

    assert result == pytest.approx(-0.6)


def test_compute_sentiment_neutral(mock_sentiment_pipeline):
    mock_pipe, mock_tokenizer = mock_sentiment_pipeline

    mock_pipe.return_value = [
        [
            {"label": "positive", "score": 0.5},
            {"label": "negative", "score": 0.5},
        ]
    ]

    analyzer = SentimentAnalyzer()
    result = analyzer.compute_sentiment("This is okay.")

    assert result == 0.0


def test_split_text_by_tokens_single_chunk(mock_sentiment_pipeline):
    mock_pipe, mock_tokenizer = mock_sentiment_pipeline

    mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
    mock_tokenizer.decode.return_value = "short text"

    analyzer = SentimentAnalyzer()
    chunks = analyzer._split_text_by_tokens("short text", chunk_size=100, chunk_overlap=20)  # noqa: SLF001

    assert len(chunks) == 1
    assert chunks[0] == "short text"


def test_split_text_by_tokens_multiple_chunks(mock_sentiment_pipeline):
    mock_pipe, mock_tokenizer = mock_sentiment_pipeline

    long_token_list = list(range(250))
    mock_tokenizer.encode.return_value = long_token_list

    call_count = 0

    def decode_side_effect(tokens, skip_special_tokens=True):  # noqa: ARG001
        nonlocal call_count
        call_count += 1
        return f"chunk_{call_count}"

    mock_tokenizer.decode.side_effect = decode_side_effect

    analyzer = SentimentAnalyzer()
    chunks = analyzer._split_text_by_tokens("long text", chunk_size=100, chunk_overlap=20)  # noqa: SLF001

    assert len(chunks) > 1


def test_compute_sentiment_multiple_chunks(mock_sentiment_pipeline):
    mock_pipe, mock_tokenizer = mock_sentiment_pipeline

    long_token_list = list(range(250))
    mock_tokenizer.encode.return_value = long_token_list
    mock_tokenizer.decode.return_value = "chunk text"

    mock_pipe.return_value = [
        [
            {"label": "positive", "score": 0.8},
            {"label": "negative", "score": 0.2},
        ]
    ]

    analyzer = SentimentAnalyzer()
    result = analyzer.compute_sentiment("very long text that will be chunked")

    assert isinstance(result, float)
    assert -1.0 <= result <= 1.0


def test_split_text_by_tokens_empty_text(mock_sentiment_pipeline):
    mock_pipe, mock_tokenizer = mock_sentiment_pipeline

    mock_tokenizer.encode.return_value = []

    analyzer = SentimentAnalyzer()
    chunks = analyzer._split_text_by_tokens("", chunk_size=100, chunk_overlap=20)  # noqa: SLF001

    assert len(chunks) == 1
    assert chunks[0] == ""
