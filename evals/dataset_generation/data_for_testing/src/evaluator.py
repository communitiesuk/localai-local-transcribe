from difflib import SequenceMatcher
from typing import Callable, List, Dict, Any
from statistics import mean
from evals.dataset_generation.data_for_testing.src.types import ManualResult
from sentence_transformers import SentenceTransformer
import numpy as np

TextSimilarityFn = Callable[[str, str], float]

model = SentenceTransformer("all-MiniLM-L6-v2")  

def semantic_similarity(a: str, b: str) -> float:
    emb = model.encode([a, b], normalize_embeddings=True)
    return float(np.dot(emb[0], emb[1]))

def default_similarity(a: str, b: str) -> float:
    """A default similarity function that uses case-insensitive sequence matching."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    

def containment_similarity(a: str, b: str) -> float:
    """A simple similarity function that checks for containment and falls back to fuzzy matching."""
    a = a.lower()
    b = b.lower()

    if a in b or b in a:
        return 1.0

    from rapidfuzz import fuzz
    return fuzz.partial_ratio(a, b) / 100



def evaluate_manual_vs_hypothesis(
    manual_list: list[str],
    auto_pcs: dict,
    text_similarity: TextSimilarityFn = default_similarity,
    threshold: float = 0.6,
)->  dict[str, Any]:
    """Evaluates the hypothesis against the manual list using a specified text similarity function and threshold.
    Returns detailed results and summary metrics.
    """

    detected = auto_pcs.get("detected_characteristics", [])
    if not isinstance(detected, list):
        raise ValueError("Expected 'detected_characteristics' to be a list")

    hypothesis_texts = [
        span["text"]
        for item in detected
        for span in item.get("evidence_spans", [])
    ]

    manual_results: list[ManualResult] = []
    hypothesis_results = []

    true_positive = 0
    false_negative = 0

    used_hyp_indices = set()

    # manual → hypothesis
    # -----------------------------
    for manual in manual_list:
        best_score = 0.0
        best_match = None
        best_idx =None

        for i, hyp in enumerate(hypothesis_texts):
            if i in used_hyp_indices:
                continue

            score = text_similarity(manual, hyp)
            if score > best_score:
                best_score = score
                best_match = hyp
                best_idx = i

        is_tp = best_score >= threshold

        if is_tp:
            true_positive += 1
            used_hyp_indices.add(best_idx)
        else:
            false_negative += 1

        manual_results.append({
            "manual_text": manual,
            "best_match": best_match,
            "score": best_score,
            "label": "TP" if is_tp else "FN",
        })

    # hypothesis → manual
    # -----------------------------
    false_positive = 0
    tp_from_hypothesis = 0

    for hyp in hypothesis_texts:
        best_score = 0.0
        best_match = None

        for manual in manual_list:
            score = text_similarity(hyp, manual)
            if score > best_score:
                best_score = score
                best_match = manual

        is_tp = best_score >= threshold

        if is_tp:
            tp_from_hypothesis += 1
        else:
            false_positive += 1

        hypothesis_results.append({
            "hypothesis_text": hyp,
            "best_match": best_match,
            "score": best_score,
            "label": "TP" if is_tp else "FP",
        })

    # METRICS
    # -----------------------------
    precision = (
        tp_from_hypothesis / (tp_from_hypothesis + false_positive)
        if (tp_from_hypothesis + false_positive) > 0 else 0.0
    )

    recall = (
        true_positive / (true_positive + false_negative)
        if (true_positive + false_negative) > 0 else 0.0
    )

    f1_score = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0 else 0.0
    )

    avg_similarity = mean(r["score"] for r in manual_results) if manual_results else 0.0

    summary = {
        "average_similarity": avg_similarity,
        "coverage@threshold": recall,
        "true_positive": true_positive,
        "false_negative": false_negative,
        "false_positive": false_positive,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
    }

    return {
        "manual_to_hypothesis": manual_results,
        "hypothesis_to_manual": hypothesis_results,
        "summary": summary,
    }


