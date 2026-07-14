# Claim citation rate thresholds: pass, review, and fail bands

Jira ticket: [AIILG-679](https://mhclgdigital.atlassian.net/browse/AIILG-679)

**All threshold values are placeholders until calibrated.**

## 1. Background

LocalTranscribe produces AI draft minutes from audio transcripts. As part of the hallucination check, the summarisation pipeline extracts the atomic claims a draft makes and then tries to cite each one back to a transcript entry. A claim that cannot be cited is treated as unsupported content. This document defines the claim citation rate, proposes pass, review, and fail bands for it, and records the reasoning behind those bands.

The product and user context for LocalTranscribe is high risk and consequence. A user can adopt a summary into statutory documentation, for example a housing officer drafting a Personal Housing Plan under section 189A of the Housing Act 1996, or a social worker a care needs assessment under the Care Act 2014. Hallucinated or unsupported content that survives human review can therefore enter a statutory record. Because these are decisions about identifiable individuals, the tool also falls within public-sector transparency and data-protection expectations, such as the Algorithmic Transparency Recording Standard for algorithmic tools used in public-sector decisions [9] and the safeguards for automated decisions that significantly affect individuals [10]. This is the same risk basis used for the judge-score thresholds for summary quality metrics in `llm-judge-score-thresholds.md` (AIILG-678), and it is why the bands below are conservative.

The rate is itself produced by two LLM steps (for claim extraction and citation), so its error is not yet known. Following the team's method for choosing thresholds, the numbers here are risk-based defaults and remain placeholders until they are calibrated against human judgements of transcript claim support [1][2].

## 2. Metric definition



### 2.1 Formula

The per-summary claim citation rate is the proportion of extracted claims that were cited:

```
claim citation rate = n_supported / total_claims
```

where `total_claims` is the number of atomic claims extracted from the draft and a claim counts as supported when it was assigned at least one transcript citation index. A claim is unsupported when its citation index list is empty.

The pipeline currently stores the inverse, `hallucination_rate = n_uncited / total_claims`, rounded to three decimal places. The citation rate is `1 - hallucination_rate`. Threshold decisions should be taken from the raw counts `n_supported` and `total_claims`, not from the rounded rate, so that a value sitting on a band boundary is not moved by rounding.

### 2.2 What counts as a claim

Claims are produced by the claim-extraction prompt. It extracts each claim as a single, atomic, self-contained, verifiable statement, and it is deliberately inclusive, in the sense that, when it is unclear whether a statement is a verifiable claim as opposed to a heading, an attendee-list entry, or a purely structural phrase, the extractor counts it as a claim rather than omitting it, which raises the total claim count. It decomposes compound sentences, so an attribution and the content attributed become separate claims. It includes specific facts (figures, amounts, dates, deadlines), named decisions and actions, direct attributions, the underlying content of those attributions, commitments, references to documents or data, and stated positions, concerns, or recommendations. It excludes headings, attendee lists, and purely structural phrases.

### 2.3 What counts as citable

Citations are produced by the citation prompt, which instructs to cite as many claims as possible. Every claim that can be traced to a transcript entry must be cited, and a claim is left uncited only when there is judged to be no supporting evidence at all. Where support is partial, the prompt allows the model to cite the closest matching entries. Because the threshold for citing is configured to be this low, anything left uncited is intended to serve as a strong signal that the content is genuinely unsupported by the transcript.

### 2.4 Direction, aggregation, and the zero-claim case

The bands are defined on the citation rate (higher rate is better). The metric is applied per summary and is intended to support a pass, review, or fail decision about that summary only. 'Example-level' evaluation is more actionable and interpretable for that purpose than a system-level score, which describes how the model performs overall but does not tell you which individual summary needs attention [5]. The existing corpus (all summaries pooled together) micro-average is retained for run-level monitoring but it doesn't serve as the primary gate - a run can look healthy on the micro-average while still hiding a small number of unacceptable summaries.

When `total_claims` is zero the citation rate is undefined (a division of zero by zero). A summary without any claims cannot be evaluated on this metric by design. It must never count as a pass by default and is routed to the review band under the assumption that something has gone wrong. This is encoded as `CITATION_RATE_ZERO_CLAIMS_POLICY` in the shared constants file.

## 3. Proposed thresholds

All values are placeholders pending calibration. The bands are stored in `evals/summarisation/src/constants.py` as `CITATION_RATE_BAND`, with the boundaries expressed as proportions (`0.95` and `0.85`).


| Outcome               | Band (claim citation rate) | Operational reading                                                                                                                         |
| --------------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Pass                  | at or above 95%            | Support is near-complete. The summary still goes through ordinary quality checks, but the hallucination metric does not require escalation. |
| Review                | 85% up to below 95%        | Enough claims are unsupported or uncertain that a person should inspect the summary before it is treated as acceptable.                     |
| Fail                  | below 85%                  | Unsupported claims are plentiful enough that the draft should be treated as unacceptable on this metric.                                    |
| Zero extracted claims | `total_claims == 0`        | Review, never pass by default. Recorded with the specific reason of 'no claims extracted'.                                                  |
| Small denominator     | very low claim counts      | Review is safer, because a single claim can move the rate by a large amount.                                                                |




## 4. Rationale

**Why stricter than the initially proposed 90/80 threshold.** A band is an operating point on a trade-off between two errors. First, a false pass, where a summary carrying unsupported claims is accepted, and second, a false review, where a sound summary is sent for unnecessary checking. A standard approach to setting a metric threshold is to place that operating point according to the relative cost of the two errors and the team's tolerance for each, rather than adopting a round default [1]. Here the two costs are highly asymmetric. A false review costs a reviewer a few minutes. A false pass can let unsupported content enter a statutory record such as a Personal Housing Plan or a care needs assessment, where the harm falls on a vulnerable person [2][7]. 

Downstream human review in this context is imperfect and not a guaranteed failsafe. Human reviewers are subject to automation bias, which is a documented tendency to over-rely on automated output and to miss the errors it introduces. Hence, it is possible for unsupported claims to survive review [8]. Because the automated check cannot rely on reviewers to catch what it passes, it must itself keep unsupported claims out rather than trust a fallible human review to remove them later. A miss is therefore both far costlier than an unnecessary review **and** unlikely to be recovered once made, so the pass bar is configured to make misses rare even at the cost of routing more summaries to review.

Furthermore, a passing summary raises no hallucination flag, so every uncited claim the pass band tolerates is an unsupported claim that proceeds without a targeted second check. As a concrete check at 20 extracted claims, the 95/85 band lets a pass carry at most one uncited claim, puts two to three uncited claims into review, and fails at four or more. A 90/80 band would instead let two uncited claims pass and would not fail a summary until five of its twenty claims were unsupported. Given the cost asymmetry discussed above, accepting up to two unsupported statements per summary with no flag is more risk exposure than this setting justifies, which is why the bar is set at 95/85.

**Why not even more strict (e.g. 98/90).** The rate is an LLM-derived estimate whose sensitivity and specificity in this exact domain and use-case are not yet measured. A very high bar would likely push acceptable summaries into review or fail because of extractor or citer noise rather than genuine problems. The judge-reliability literature argues for leaving room for uncertainty until the evaluator's operating characteristics are known [3][4]. A high pass bar combined with a wide review band reflects both facts at once - tolerate little unsupported content, but do not treat a noisy automated measurement as ground truth.

## 5. Known limitations

The metric measures traceability and claim support rather than full factual faithfulness. Three limitations follow, which is why metrics like `accuracy` and `coverage` are also necessary.

- It is weak on omissions. A fact that wasn't included in the summary never enters the denominator, so silent omissions do not lower the rate [6].
- Partial support still counts as cited, because the prompt allows citing the closest matching entries. A stretched or overbroad claim can therefore score as supported.
- Citation correctness is not the same as citation faithfulness. A claim can be paired with a plausible citation even where the model did not truly rely on that source [3].



## 6. References

1. B. Sarmah et al. "How to Choose a Threshold for an Evaluation Metric for Large Language Models." arXiv:2412.12148, 2024.
2. Ada Lovelace Institute. "Scribe and prejudice? Exploring the use of AI transcription tools in social care." 2026.
3. J. Wallat et al. "Correctness is not Faithfulness in RAG Attributions." arXiv:2412.18004, 2024.
4. R. Lee et al. "How to Correctly Report LLM-as-a-Judge Evaluations." arXiv:2511.21140, 2025.
5. O. Honovich et al. "TRUE: Re-evaluating Factual Consistency Evaluation." arXiv:2204.04991, 2022.
6. S. Min et al. "FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation." arXiv:2305.14251, 2023.
7. Housing Act 1996, section 189A. Care Act 2014, section 9.
8. K. Goddard et al. "Automation bias: a systematic review of frequency, effect mediators, and mitigators." Journal of the American Medical Informatics Association, 19(1), 121-127, 2012.
9. Department for Science, Innovation and Technology and Central Digital and Data Office. "Algorithmic Transparency Recording Standard: mandatory scope and exemptions policy." 2024.
10. Information Commissioner's Office. Guidance on rights related to automated decision-making (UK GDPR Article 22).

