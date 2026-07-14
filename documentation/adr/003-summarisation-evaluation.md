# ADR-003: Evaluation Strategy for Local Transcribe (Summarisation)

## Status

Accepted

Date of decision: 2026-01-15

## Context and Problem Statement

Local Transcribe produces summaries from meeting transcripts. We need an evaluation approach that is:
* fast enough to run regularly
* informative enough to guide product and model changes
* structured enough to support go/no-go decisions

Traditional lexical metrics and embedding similarity provide limited signal for summary quality in this domain because:

* Important omissions can be missed by surface-form similarity.
* Hallucinations may still look semantically similar.
* The quality criteria (faithfulness, coverage, conciseness, coherence) are multi-dimensional and require judgment.

Hallucination — unsupported claims that do not appear in the transcript — is a particularly high-risk failure mode for this system. While an LLM-as-judge rubric captures faithfulness as one dimension among several, we want stronger, more targeted coverage on this vector than a general-purpose rubric provides.

Therefore, we need a practical, repeatable evaluation strategy, with a preference for LLM-as-judge as the primary method, complemented by a dedicated hallucination check for the summarisation pipeline.

## Considered Options

* LLM-as-judge rubric scoring (selected)
* Dedicated hallucination checks in the summarisation pipeline (selected)
* Heuristic / similarity-based automated evaluation (e.g., embedding similarity)
* Human annotation (spot-checking / gold set)
* Regression evaluation via curated adversarial / edge-case suites

## Decision Outcome

We have selected two complementary options:

1. **LLM-as-judge rubric scoring**, because it provides an automated and scalable way to evaluate multi-dimensional summary quality.
2. **Dedicated hallucination checks in the summarisation pipeline**, added in addition to LLM-as-judge so that we have better coverage on the hallucination vector specifically. Faithfulness is scored by the judge rubric, but a targeted hallucination check gives us a second, more focused signal on unsupported claims.

Note: We will discuss the human annotation approach in a separate ADR, but it won't consitute part of the evals workflow.

## Pros and Cons of the Options

### LLM-as-judge rubric scoring (selected)

This approach uses an LLM to evaluate each candidate summary against the transcript (and optionally a reference summary) according to a rubric. The rubric should include, at minimum:

* Faithfulness (no unsupported claims)
* Coverage (captures key points)
* Conciseness (no unnecessary detail)
* Coherence (readable, logically ordered)

The judge produces per-dimension scores and a rationale. The evaluation should be versioned (judge prompt + model + decoding settings) and stored alongside the pipeline outputs.

* Good, because it can evaluate multi-dimensional quality in a way similarity metrics cannot.
* Good, because it produces rationales that help debugging and prioritization.
* Good, because it can be run frequently and consistently as part of CI or scheduled jobs.
* Bad, because judge models can be biased and inconsistent across model/provider updates.
* Bad, because it introduces additional cost and latency.
* Bad, because it is vulnerable to prompt sensitivity and rubric ambiguity.
* Neutral, because reliability improves with calibration, judge ensembling, and periodic human auditing.

### Dedicated hallucination checks in the summarisation pipeline (selected)

This approach runs a targeted check that verifies claims in the generated summary are supported by the source transcript, flagging unsupported (hallucinated) content. It runs in addition to, not instead of, the LLM-as-judge rubric.

* Good, because it gives focused coverage on the highest-risk failure mode (unsupported claims) rather than treating faithfulness as one dimension among several.
* Good, because it provides a second, independent signal on hallucination, reducing reliance on a single judge rubric.
* Good, because it can be run as part of the pipeline and surfaced alongside judge scores.
* Bad, because it adds cost and latency to the pipeline.
* Bad, because it shares the general LLM-judge weaknesses (prompt sensitivity, potential bias) when implemented with an LLM.
* Neutral, because it overlaps with the judge's faithfulness dimension; the two are intended to be mutually reinforcing rather than redundant.

### Heuristic / similarity-based automated evaluation (e.g., embedding similarity)

This approach uses simple automated metrics such as embedding similarity between candidate and reference summary, ROUGE-like overlap, or other heuristics.

* Good, because it is cheap and fast.
* Good, because it is stable and easy to reproduce.
* Bad, because it misses hallucinations and can reward verbose summaries.
* Bad, because the correct response has a large amount of variation.
* Bad, because it does not directly measure faithfulness/coverage in a reliable way.
* Neutral, because it can be useful as a supplementary signal (e.g., to detect large regressions).

### Human annotation (spot-checking / gold set)

This approach uses human reviewers to score summaries (using the same rubric) on a subset of examples.

* Good, because it provides a high-quality ground truth signal and can identify judge-model failure modes.
* Good, because it can be used to calibrate and validate LLM-as-judge.
* Bad, because it is slow and expensive to scale.
* Bad, because it requires reviewer training, alignment, and QA.
* Neutral, because it can be limited to periodic audits or a small gold set.

### Regression evaluation via curated adversarial / edge-case suites

This approach maintains a curated set of challenging cases (e.g., negation, speaker attribution, numbers, action items, contradictory statements) and ensures the system does not regress.

* Good, because it targets known risk areas and provides strong regression detection.
* Good, because it is actionable: failures map to concrete patterns.
* Bad, because it requires ongoing maintenance as product requirements change.
* Neutral, because it complements LLM-as-judge and human review.

## More Information

* Using new judge model providers (cost, data handling, and security review)
* Introducing any human labeling program for sensitive data(process, privacy, and governance)
