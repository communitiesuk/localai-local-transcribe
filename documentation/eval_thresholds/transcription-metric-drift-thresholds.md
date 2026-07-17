# Transcription metric drift thresholds. Pass, review, fail, and absolute floors

Jira ticket. [AIILG-680](https://mhclgdigital.atlassian.net/browse/AIILG-680)

**All threshold values are placeholders based on a proxy dataset. They must be recalculated on real council meeting audio with human-annotated ground truth before they can be trusted.**

Constants live in [`evals/transcription/src/constants.py`](../../evals/transcription/src/constants.py).

Enforcement lives in [`evals/transcription/src/drift.py`](../../evals/transcription/src/drift.py) and is switched on by setting `check_drift_thresholds: true` in the baseline transcription eval config.

---

## 1. Background

LocalTranscribe turns meeting audio into a transcript, and then turns that transcript into draft minutes.

This document covers **offline drift gates** for three transcription metrics. "Offline" here means these checks run as a separate evaluation step against a fixed, known test set of recordings, rather than "live" inside the production transcription service on real user audio. The checks compare each new evaluation run to a stored baseline and decide whether quality has drifted.

The three metrics are.

- corpus word error rate (WER)
- speaker-count accuracy
- processing speed ratio

Each is defined in full in section 2.

Judge scores and hallucination / claim-citation drift are out of scope here. Those are documented separately in [`llm-judge-score-thresholds.md`](./llm-judge-score-thresholds.md) and [`claim-citation-rate-thresholds.md`](./claim-citation-rate-thresholds.md).

### 1.1 Why gate transcription quality at all

The product context is high risk and high consequence. A user can adopt AI-generated content from LocalTranscribe into statutory documentation, for example a Personal Housing Plan under section 189A of the Housing Act 1996, or a care needs assessment under the Care Act 2014 [8]. A transcription error that survives human review can therefore feed into a statutory record.

The gates below are two-tier.

1. **Tier 1 (relative).** Compare the candidate (latest) run to a committed baseline. Send the run to review, or fail it, when the relative change is large enough.
2. **Tier 2 (absolute floor).** Fail the run when the absolute value is past a fixed "disaster line", even if the change relative to the baseline looks small.

### 1.2 The baseline dataset and transcription service

There is **no real council audio in the current calibration**. The numbers were produced from a stand-in (a proxy) called the **baseline transcription eval config** ([`evals/transcription/configs/larger_cloud_test.yaml`](../../evals/transcription/configs/larger_cloud_test.yaml)).

That config runs 10 full audio recordings from the **AMI Meeting Corpus**, a publicly available research dataset of 100 hours of hand-transcribed meeting recordings created for meeting-analysis research [1]. The recordings and reference transcripts are pulled from the `edinburghcstr/ami` dataset on Hugging Face [2], and the transcription eval auto-downloads them (see the transcription section of [`evals/README.md`](../../evals/README.md)). AMI is a reasonable proxy because it is real multi-speaker meeting speech, but it is not local-government audio, so treat every number here as provisional.

The transcription service under test is the **Azure AI Speech fast transcription API** (the synchronous `speechtotext/transcriptions:transcribe` endpoint), called at REST API version `2024-11-15` [7]. The request is configured for locale `en-GB`, with speaker diarisation enabled and the profanity filter turned off. In the code this adapter is registered as `azure_stt_synchronous`.

---

## 2. Metric definitions

### 2.1 Corpus WER

Word error rate compares the machine transcript (the "hypothesis") against the human reference transcript (the "ground truth"). The two are aligned word by word using minimum-edit-distance alignment, which produces four counts per meeting [3][4].

- **hits**. Reference words the machine transcribed correctly.
- **substitutions**. Reference words the machine replaced with a different word.
- **deletions**. Reference words the machine missed entirely.
- **insertions**. Extra words the machine added that were never spoken.

From those counts, two per-meeting totals are derived.

- **reference words** = hits + substitutions + deletions (the length of the human transcript).
- **errors** = substitutions + deletions + insertions (the three ways the machine can be wrong).

**Corpus WER** (the value the gate acts on) pools these totals across all meetings before dividing.

```
corpus WER = sum(errors across meetings) / sum(reference words across meetings)
```

This is the standard, aggregate definition of WER used by the National Institute of Standards and Technology (NIST) scoring toolkit and in automatic speech recognition (ASR) evaluation generally, where corpus WER is the total error count divided by the total reference-word count across the whole test set [3][4].

Importantly, corpus WER is **not** the plain average of each meeting's individual WER. In a plain average, a 2-minute meeting and a 90-minute meeting would count equally, so one short, difficult meeting could change the reported mean WER by a large amount even though it contributes relatively few words to the test set. Pooling instead weights each meeting by its number of reference words, so longer meetings contribute proportionally more. This is why corpus WER is the standard way to report overall transcript quality and is less sensitive to short recordings [3][4].

Higher corpus WER is worse. The change relative to the baseline is.

```
relative increase = (candidate corpus WER - baseline corpus WER) / baseline corpus WER
```

### 2.2 Speaker-count accuracy

For each meeting, the eval records whether the number of speakers the machine detected matches the number of speakers in the ground truth. This is stored as 1.0 when the count is correct and 0.0 when it is not.

The value the gate acts on is the **number of meetings with a correct speaker count**, out of the total number of meetings in the eval set (`n_meetings`). Higher is better.

We express the bands as whole counts (for example 7 out of 10), not as a fine-grained percentage. This is because.

- With 10 meetings, each meeting is worth exactly one tenth of the score, which is 10 percentage points.
- The only accuracy values that can ever occur are therefore 0%, 10%, 20%, and so on up to 100%. Nothing can land between, for example, 70% and 80%.
- A threshold written as a precise-looking percentage such as 75% would be misleading, because no run can ever score 75%. It would always collapse back to the nearest whole count.
- A single meeting flipping from correct to incorrect moves the score by a full 10 points, so the metric is inherently coarse. Reporting it as a whole count out of 10 is both exact and easier to read.

`n_meetings` must equal `num_samples` in the baseline transcription eval config. If a run's meeting count differs, drift checking raises an error rather than applying, for example, "7 out of 10" bands to a set of a different size, which would silently change what pass, review, and fail mean.

### 2.3 Processing speed ratio

```
processing speed ratio = processing time (seconds) / audio duration (seconds)
```

A higher ratio means the transcription took longer relative to the length of the audio. A ratio of 1.0 means processing took as long as the recording itself (as slow as real time). The value the gate acts on is the run-level summary ratio.

The change relative to the baseline uses the same formula as for WER.

---

## 3. What bootstrapping is and why we use it

The WER review band is set with a technique called the **bootstrap**. This section explains what that is.

### 3.1 The problem it solves

We only have 10 meetings in the baseline set. If we had happened to pick 10 slightly different meetings, the corpus WER would come out a little different, purely by chance of which meetings were included. Before we can say "a new run has drifted", we need to know how much the baseline number itself could wobble simply from that sampling. The review band should sit just outside that natural wobble, so ordinary sampling variation is not mistaken for a real regression [6].

### 3.2 How the bootstrap estimates that fluctuation

The bootstrap estimates the uncertainty of a statistic by resampling the data we already have, with replacement, many times over [4][5]. Specifically, for corpus WER.

1. Start with the 10 real meetings and their error and reference-word counts.
2. Draw a new set of 10 meetings by picking from those 10 at random, with replacement, so some meetings appear more than once and others not at all. This is one "resample".
3. Recompute corpus WER on that resample.
4. Repeat many times (the artefact uses 10,000 resamples) to build up a distribution of plausible corpus WER values.
5. Read a high percentile of that distribution (for example the 95th percentile) to see how far up the corpus WER realistically drifts from sampling alone. That distance sets the review band.

### 3.3 Why "meeting-block" bootstrap

We resample **whole meetings**, not individual words. This is what "meeting-block" means. The meeting is the unit that gets drawn each time, keeping all of its words together.

The reason is that errors within a single meeting are not independent of each other. One noisy recording, one strong accent, or one difficult acoustic setting makes many nearby words wrong together. Resampling individual words would ignore that correlation and understate the true uncertainty. Resampling whole meetings preserves it, which is the established approach for WER confidence estimation in speech recognition, where error events are known not to occur independently [4].

This bootstrap is used only during calibration, to choose the width of the review band. It is not run again when the live gate compares a candidate run to the committed constants (see section 5).

---

## 4. Proposed thresholds

Source of truth for these values. `WER_DRIFT_THRESHOLDS`, `SPEAKER_COUNT_DRIFT_THRESHOLDS`, and `PROCESSING_SPEED_DRIFT_THRESHOLDS` in [`evals/transcription/src/constants.py`](../../evals/transcription/src/constants.py).

The flag `DRIFT_THRESHOLDS_ARE_AMI_PROXY_PLACEHOLDERS` is `True` while these remain proxy values.

The overall approach to picking the bands follows the team's threshold-setting method used in the other threshold documents. Start from the tolerance for each kind of mistake, then choose the number, rather than adopting a round default [6].

### 4.1 Corpus WER

| Outcome | Rule                                                                      | Current proxy value                   |
| ------- | ------------------------------------------------------------------------- | ------------------------------------- |
| Pass    | relative increase is below the review band                                | below +10% versus baseline (0.289275) |
| Review  | relative increase is at or above the review band, and below the fail band | at or above +10%                      |
| Fail    | relative increase is at or above the fail band                            | at or above +25%                      |
| Floor   | absolute corpus WER is at or above the floor                              | at or above 0.50                      |

Baseline corpus WER **0.289275** comes from the committed bootstrap artefact built from the baseline eval results.

Review **+10%** follows the 95th-percentile relative increase from the meeting-block bootstrap (section 3). In other words, it is just outside the natural sampling fluctuation of the 10-meeting aggregate. Azure was deterministic across repeated runs for WER, so this band is about which meetings are sampled rather than run-to-run randomness.

Fail **+25%** is placed clearly above that sampling band, so a failure reflects a genuine change rather than chance.

Absolute floor **0.50** is a loose disaster line for this proxy only. It is not a product-readiness bar for real meetings.

### 4.2 Speaker-count accuracy

| Outcome | Rule                                 | Current proxy value (out of 10) |
| ------- | ------------------------------------ | ------------------------------- |
| Pass    | correct count above the review count | 7, 8, 9, or 10 correct          |
| Review  | exactly the review count             | 6 correct                       |
| Fail    | at or below the fail count           | 5 or fewer correct              |
| Floor   | at or below the floor count          | 4 or fewer correct              |

The baseline on the proxy set was **7 out of 10** correct. These counts must be recomputed together with any change to the number of meetings (see section 6.3).

### 4.3 Processing speed ratio

| Outcome    | Rule                                                                      | Current proxy value                                     |
| ---------- | ------------------------------------------------------------------------- | ------------------------------------------------------- |
| Pass       | relative increase is below the review band                                | below +10% versus baseline (0.0441)                     |
| Review     | relative increase is at or above the review band, and below the fail band | at or above +10%                                        |
| Fail       | relative increase is at or above the fail band                            | at or above +25%                                        |
| Floor      | absolute ratio is at or above the absolute floor                          | at or above 0.10                                        |
| Hard floor | absolute ratio is at or above 1.0                                         | at or above 1.0 (as slow as, or slower than, real time) |

Baseline **0.0441** is the mean processing speed ratio across three repeated Azure runs on the baseline config.

The relative bands match the WER shape, but they are set conservatively rather than derived from a measured variance. The baseline rests on only three repeated runs, and three observations are too few to estimate the run-to-run variance of cloud processing time with any precision. The bands are therefore deliberately wide.

---

## 5. How the eval enforces these gates

1. Run the transcription evaluate step with a config that sets `check_drift_thresholds: true`. This is enabled on `larger_cloud_test.yaml`. It is left off on the smoketest config so that a 2-meeting smoke run cannot accidentally trigger the speaker-count size guard described in section 2.2.
2. After results are saved, `apply_drift_thresholds` classifies each metric as pass, review, fail, or floor.
3. The overall outcome is the **most severe** of the individual metric outcomes, ordered pass, then review, then fail, then floor.
4. The process exit code is.
  - **0** for pass or review.
  - **1** for fail or floor.
5. When the overall outcome is not a pass (that is review, fail, or floor), the eval writes `evals/transcription/output/drift_review_{timestamp}.json` with the per-metric detail so a person can inspect it.

The live comparison is always **the observed metric versus the committed constants**. The bootstrap is only used beforehand, during calibration, to set the width of the WER review band.

---

## 6. Recomputation instructions

Use this section whenever the meeting set, the transcription service, or the accepted baseline changes. Update the constants and the artefacts in the same change. Do not, for example, leave speaker-count bands sized for 10 meetings while `num_samples` says something else.

### 6.1 Refresh the proxy baseline (current setup)

**1.** Run the baseline transcription eval config.

```bash
poetry run python evals/transcription/src/evaluate.py --config larger_cloud_test.yaml
```

You can repeat this a few times if you want a more stable speed baseline. WER and speaker count were deterministic for Azure on AMI in the calibration runs whereas processing speed wasn't.

**2.** Rebuild the WER bootstrap artefact from a saved results file.

```bash
poetry run python -m evals.transcription.src.baseline.compute_wer_bootstrap \
    evals/transcription/output/evaluation_results_YYYYMMDD_HHMMSS.json
```

The default output path is `evals/transcription/baseline/wer_bootstrap_ami_proxy.json`.

**3.** Copy the values from the artefact into `WER_DRIFT_THRESHOLDS`.

- `baseline_corpus_wer` becomes `WER_DRIFT_THRESHOLDS.baseline_corpus_wer`.
- the bootstrap relative increase at the 95th percentile (or the percentile the team agrees) becomes `review_relative_increase`.
- set `fail_relative_increase` clearly above that sampling band (the current choice is 0.25).

**4.** Count the meetings with `speaker_count_accuracy == 1.0` on the accepted run and update `SPEAKER_COUNT_DRIFT_THRESHOLDS` (the `n_meetings`, baseline, review, fail, and floor counts).

**5.** Average the run-level `processing_speed_ratio` across the accepted repeats and set `PROCESSING_SPEED_DRIFT_THRESHOLDS.baseline_ratio`. Adjust the relative bands and floors deliberately. Do not treat three eval runs as a precise performance guarantee and consider upping the repeats for a better sense of fluctuation.

**6.** Keep `DRIFT_THRESHOLDS_ARE_AMI_PROXY_PLACEHOLDERS = True` until real council data replaces AMI.

**7.** Run the unit tests.

```bash
poetry run pytest tests/evals/transcription/test_drift.py tests/evals/transcription/test_wer_bootstrap.py -q
```

### 6.2 Move to a real council golden set (rolling baseline)

A "golden set" is a fixed, trusted set of recordings with human-verified transcripts that the baseline is measured against.

1. First the team must agree on a set of real meeting recordings and their human-annotated transcripts (the ground truth, i.e. our version of the AMI set).
2. Point the transcription eval at that set, using a new or updated config. Keep `num_samples` and the speaker-count `n_meetings` equal.
3. Run the pipeline and compute corpus WER, speaker-count correct meetings, and processing speed as defined in section 2.
4. Commit the new baselines and bands in `constants.py`. Rename or replace the bootstrap artefact so its filename reflects real data rather than `ami_proxy`.
5. Delete the `DRIFT_THRESHOLDS_ARE_AMI_PROXY_PLACEHOLDERS` flag once the team agrees the real data numbers are the operating baseline. Update this document to reflect any changes in the calibration process.
6. On each agreed refresh (on a schedule, or at a release). Re-run on the **same** meeting set, compare to the current constants as in section 5, and, if the run is accepted, replace the committed baseline with the new figures and re-check the review band width with the bootstrap. This periodic refresh is what makes the baseline a "rolling" one.

### 6.3 Changing the number of meetings

The speaker-count bands are absolute counts out of `n_meetings`. If you move from 10 to a different number of meetings.

1. Update `num_samples` in the baseline transcription eval config and `SPEAKER_COUNT_DRIFT_THRESHOLDS.n_meetings` together.
2. Recompute the baseline correct count and the review, fail, and floor counts for the new size.
3. Recompute the corpus WER baseline and its bootstrap bands on the new set.
4. Do not reuse "7 out of 10"-style numbers on a different denominator.

---

## 7. Known limitations and further work

### Proxy data only

AMI is not council audio. The absolute floors are disaster lines for this proxy, rather than readiness criteria for real meetings this product is intended for.

### Static constants at evaluate time

A "rolling baseline", in the ticket's sense, means refreshing the committed baseline when the data or an accepted run changes. It does not mean recomputing the baseline inside every candidate run.

### The bootstrap used for calibration is unpaired

Candidate and baseline runs both use the **same** meetings and the same ground-truth set. The live gate already compares two corpus WER numbers computed on that shared set. What is unpaired is the bootstrap itself. It is run on **one** results file (the baseline) to estimate how much that aggregate can wobble if the mix of those meetings is redrawn. It does **not** also bootstrap the **difference** between candidate and baseline by redrawing the same meeting IDs in pairs. So we have a same-meetings point comparison plus a fixed percentage band. We do not have a sampling distribution for "candidate minus baseline on matched meetings."

### Paired bootstrap (suggested further work)

A paired bootstrap would take baseline and candidate results for the same meeting IDs, resample those IDs together, and each time compute candidate corpus WER minus baseline corpus WER. That would estimate uncertainty in the **delta** on the shared set, which can support tighter calibration or human review of small WER changes. Turning that into a live gate would need its own decisions about how to map that difference distribution to review and fail, and is not required for the current constants-based gate.

### Speed bands are coarse

Cloud latency varies between runs, so treat the relative speed gates as rough early warnings rather than precise performance targets.

### Speaker count is coarse

As explained in section 2.2, one meeting moves a 10-meeting set by 10 percentage points, so the whole-count bands are intentional.

---

## 8. References

### External literature

1. Carletta, J., et al. (2006). "The AMI Meeting Corpus. A Pre-announcement." In S. Renals and S. Bengio (eds), Machine Learning for Multimodal Interaction (MLMI 2005). Lecture Notes in Computer Science, vol. 3869, pp. 28-39. Springer. [https://doi.org/10.1007/11677482_3](https://doi.org/10.1007/11677482_3)
2. AMI Meeting Corpus on Hugging Face. `edinburghcstr/ami`. [https://huggingface.co/datasets/edinburghcstr/ami](https://huggingface.co/datasets/edinburghcstr/ami)
3. National Institute of Standards and Technology. Speech Recognition Scoring Toolkit (SCTK / sclite). [https://github.com/usnistgov/SCTK](https://github.com/usnistgov/SCTK)
4. Bisani, M., and Ney, H. (2004). "Bootstrap Estimates for Confidence Intervals in ASR Performance Evaluation." Proc. IEEE International Conference on Acoustics, Speech, and Signal Processing (ICASSP), Montreal, vol. 1, pp. 409-412.
5. Efron, B., and Tibshirani, R. (1993). An Introduction to the Bootstrap. Chapman and Hall.
6. Sarmah, B., et al. (2024). "How to Choose a Threshold for an Evaluation Metric for Large Language Models." arXiv:2412.12148.
7. Microsoft. "Use the fast transcription API." Azure AI Speech documentation, REST API version 2024-11-15. [https://learn.microsoft.com/en-us/azure/ai-services/speech-service/fast-transcription-create](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/fast-transcription-create)
8. Housing Act 1996, section 189A. Care Act 2014, section 9.

### Repository references

1. Constants and placeholder flag. [`evals/transcription/src/constants.py`](../../evals/transcription/src/constants.py)
2. Drift classification and exit behaviour. [`evals/transcription/src/drift.py`](../../evals/transcription/src/drift.py)
3. WER bootstrap helpers and artefact builder. [`evals/transcription/src/baseline/`](../../evals/transcription/src/baseline/)
4. Committed bootstrap artefact. [`evals/transcription/baseline/wer_bootstrap_ami_proxy.json`](../../evals/transcription/baseline/wer_bootstrap_ami_proxy.json)
5. Baseline transcription eval config. [`evals/transcription/configs/larger_cloud_test.yaml`](../../evals/transcription/configs/larger_cloud_test.yaml)
6. Related summarisation threshold documents. [`llm-judge-score-thresholds.md`](./llm-judge-score-thresholds.md) (AIILG-678), [`claim-citation-rate-thresholds.md`](./claim-citation-rate-thresholds.md) (AIILG-679)
