from __future__ import annotations

import logging
from typing import TypedDict, cast

from transformers import AutoTokenizer, PreTrainedTokenizer, pipeline
from transformers.pipelines.text_classification import TextClassificationPipeline

from evals.summarisation.src.bias.constants import (
    SENTIMENT_CHUNK_OVERLAP,
    SENTIMENT_CHUNK_SIZE,
    SENTIMENT_MAX_LENGTH,
    SENTIMENT_MODEL_NAME,
)

logger = logging.getLogger(__name__)


class SentimentResult(TypedDict):
    label: str
    score: float


class SentimentAnalyzer:
    """
    Analyzes sentiment of text using a pre-trained transformer model.
    """

    def __init__(self) -> None:
        """Initializes the sentiment analyzer with model and tokenizer."""
        self.sentiment_pipeline: TextClassificationPipeline = pipeline(  # type: ignore[call-overload]
            "sentiment-analysis", model=SENTIMENT_MODEL_NAME, top_k=None
        )
        self.tokenizer: PreTrainedTokenizer = AutoTokenizer.from_pretrained(SENTIMENT_MODEL_NAME)

    def _split_text_by_tokens(self, text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
        """Splits text into overlapping chunks based on token count."""
        tokens = self.tokenizer.encode(text, add_special_tokens=False)
        chunks = []
        start = 0
        while start < len(tokens):
            end = start + chunk_size
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens, skip_special_tokens=True)
            chunks.append(chunk_text)
            start = end - chunk_overlap if end < len(tokens) else end
        return chunks if chunks else [text]

    def compute_sentiment(self, text: str) -> float:
        """Computes average sentiment score for text, ranging from -1 (negative) to 1 (positive)."""
        chunks = self._split_text_by_tokens(text, SENTIMENT_CHUNK_SIZE, SENTIMENT_CHUNK_OVERLAP)

        scores: list[float] = []
        for chunk in chunks:
            chunk_results = self.sentiment_pipeline(chunk, truncation=True, max_length=SENTIMENT_MAX_LENGTH)
            results = cast(list[SentimentResult], chunk_results[0])

            pos_score = 0.0
            neg_score = 0.0

            for result in results:
                if result["label"] == "positive":
                    pos_score = result["score"]
                elif result["label"] == "negative":
                    neg_score = result["score"]

            score = pos_score - neg_score
            scores.append(score)

        return float(sum(scores) / len(scores))
