# Evals flow

Short map of the current offline eval system. Runnable details live in [`../evals/README.md`](../evals/README.md).

Related eval docs:

- [`../evals/README.md`](../evals/README.md): commands, configs and outputs for summarisation, transcription, dataset generation and audio generation evals.
- [`../evals/dataset_generation/data_for_testing/README.md`](../evals/dataset_generation/data_for_testing/README.md): creating annotated test data.
- [`../evals/dataset_generation/counterfactual_generation/bias_july_counterfactuals_for_eval/README.md`](../evals/dataset_generation/counterfactual_generation/bias_july_counterfactuals_for_eval/README.md): bias counterfactual dataset notes.

## Flow

```mermaid
flowchart TD
  RD[Real dialogue / diarised transcript + template]
  SD[Synthetic dialogue / diarised transcript + template]
  PI[Prompt-injection scenarios + template]
  I1[Audio + reference transcript]
  CF[Counterfactual transcript pairs]

  G1[Synthetic transcript generation]
  G2[Characteristic detection]
  G3[Counterfactual rewrite]
  S[Standard summarisation eval*]
  J[LLM rubric judges]
  H[Hallucination / citation check]
  P[Prompt-injection eval]
  B[Counterfactual bias eval*]
  RS[Regard + sentiment scoring]
  BT[4/5 + SPC thresholds]
  T[Transcription eval*]

  SR[Summarisation results + summary JSON]
  HR[Hallucination / citation results]
  PR[Prompt-injection results]
  BR[Counterfactual bias results]
  TR[Transcription results]

  G1 --> SD
  SD --> G2
  RD --> G2
  G2 --> G3
  G3 --> CF

  RD --> S
  SD --> S
  S --> J --> SR
  S --> H --> HR

  PI --> P --> PR
  CF --> B --> RS --> BT --> BR
  I1 --> T --> TR

  classDef input fill:#e8f3ff,stroke:#1f77b4,color:#111;
  classDef process fill:#fff4cc,stroke:#b7791f,color:#111;
  classDef output fill:#e7f6e7,stroke:#2f855a,color:#111;
  class RD,SD,PI,I1,CF input;
  class G1,G2,G3,S,J,H,P,B,RS,BT,T process;
  class SR,HR,PR,BR,TR output;
```

There are three broad input types: real or synthetic dialogue/diarised transcripts with a summary template for summarisation quality, counterfactual transcript pairs for bias checks, and audio with reference transcripts for transcription quality. Standard summarisation, prompt-injection, counterfactual bias and transcription produce separate result outputs; standard summarisation can also emit hallucination/citation outputs when that check is enabled.

## What each eval measures

| Area | Purpose | Primary metrics | Output |
|---|---|---|---|
| **Standard summarisation*** | Main regression check for summary quality on dialogue plus optional reference summary. | LLM-judge `accuracy`, `coverage`, `readability`, optionally `numerical_accuracy`, `template_fit`, `action_clarity`, `professional_tone`, `auditability`; `overall` score. | `results.jsonl`, `summary.json`, optional `hallucination_inputs.json` |
| Transcription* | Checks speech-to-text and speaker attribution against AMI references. | `wer`, `wder`, `speaker_count_accuracy`, `processing_speed_ratio`. | Per-sample rows and run summary in `evals/transcription/output/` |
| Counterfactual bias* | Checks whether summaries change when protected characteristics are rewritten. | Judge-score deltas, sentiment delta, optional Regard negative-score delta; aggregate deltas by characteristic/axis. | `evals/summarisation/output/bias/<run_id>/` |
| Bias thresholds | Turns bias measurements into pass/fail signals. | SPC checks and 4/5-rule checks. | Attached to bias `results.jsonl` |
| Hallucination / citation | Checks whether summary claims are supported by transcript citations. | `hallucination_rate`, `citation_outcome`, supported vs unsupported claim counts. | Hallucination report + citation outcome rollup |
| Security / prompt injection | Checks whether transcript or template injections change summariser behaviour. | `harmlessness`, `summarisation_adherence`, `refusal_robustness`. | `evals/summarisation/output/security/<run_id>/` |

`*` Regular evaluation pipeline planned on `feat/evals-pipeline`.

## Standard summarisation eval

This is the main regression check for summary quality: generate a summary for each dialogue, then score it against selected judge dimensions. It is config-driven (`evals/summarisation/configs/smoke-test.yaml` by default) so the selected dataset split and aggregate metrics are recorded in `summary.json`.

Judges are rubric prompts run as separate single-dimension LLM calls. Each judge sees the transcript, candidate summary and one target dimension, returns a 1-5 score plus rationale, and the eval stores the score normalised to 0-1. Citation quality (`auditability`) is skipped when the selected summary template cannot produce citations.

## Threshold work

Current threshold docs:

- [LLM judge score thresholds](eval_thresholds/llm-judge-score-thresholds.md): provisional pass/review/fail bands for judge dimensions.
- [Claim citation rate thresholds](eval_thresholds/claim-citation-rate-thresholds.md): provisional `pass >= 0.95`, `review >= 0.85`, otherwise fail.
- [Transcription metric drift thresholds](eval_thresholds/transcription-metric-drift-thresholds.md): AMI-proxy drift gates for WER, WDER, speaker-count accuracy and processing speed.
- [ADR-024 bias thresholding](adr/024-bias-thresholding.md): bias uses the 4/5 rule as the floor and SPC as the drift/regression signal.

## Data

Datasets should cover varied speaker counts, meeting types, audio quality, accents and protected-characteristic axes. Ideal records have human reference transcripts and summaries; minimum viable records can use approved AI-generated transcripts/summaries.

Eval inputs and sensitive outputs should remain in controlled storage. Aggregate metric reports that contain no sensitive content can be published.
