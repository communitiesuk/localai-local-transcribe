# Data for Testing — Evaluation Pipeline

Evaluates how well the characteristics detection pipeline identifies Protected Characteristics (PCs) by comparing its output against a manually annotated ground truth.

---

## Overview

The workflow has two stages:

1. **Annotate** — runs characteristics detection on the transcript and creates an index-aligned annotated ground truth file from `manual_pc.json`
2. **Evaluate** — compares the manual list against the characteristics detection output and computes precision / recall / F1

Multiple unrelated transcripts can coexist under `input/` — each in its own named subdirectory. The annotate step picks the most recently modified one.

---

> **Note:** Install the `evals-summarisation` dependency group for semantic similarity scoring:
> ```bash
> poetry install --with evals-summarisation
> ```

---

## Step 1 — Generate a Synthetic Transcript

Use the transcription generation module to produce a transcript:

```bash
poetry run python -m evals.dataset_generation.transcription_generation.main --config multi_with_pcs.yaml
```

The output is written to:

```
evals/dataset_generation/transcription_generation/output/
```

Configure the scenario, speakers, and context by editing the config file first:

```
evals/dataset_generation/transcription_generation/configs/multi_with_pcs.yaml
```

---

## Step 2 — Place Files in the Input Folder

Each transcript lives in a named subdirectory under `input/`. Create one and copy the generated transcript into it:

```bash
PC_TEST_INSTANCE_NAME=my_transcript

mkdir -p evals/dataset_generation/data_for_testing/input/$PC_TEST_INSTANCE_NAME
cp "$(ls -t evals/dataset_generation/transcription_generation/output/*.json | head -1)" \
   evals/dataset_generation/data_for_testing/input/$PC_TEST_INSTANCE_NAME/
```

Create `manual_pc.json` in the same subdirectory with a JSON array of text spans you have manually identified as PC-related:

```bash
echo '[]' > evals/dataset_generation/data_for_testing/input/$PC_TEST_INSTANCE_NAME/manual_pc.json
# Then open and edit it — for example:
#   code evals/dataset_generation/data_for_testing/input/$PC_TEST_INSTANCE_NAME/manual_pc.json
```

```json
["Biola", "three months pregnant", "expecting a baby", "he", "my partner"]
```

Each unique text span listed here will be searched across the full transcript — every position where it appears becomes a separate reference span in the evaluation. No need to list the same text multiple times.

Each subdirectory should contain exactly **two files**:

```
input/
  $PC_TEST_INSTANCE_NAME/
    <transcript>.json    ← generated transcript
    manual_pc.json       ← your manual annotations
```

---

## Step 3 — Annotate

```bash
poetry run python evals/dataset_generation/data_for_testing/src/annotate.py $PC_TEST_INSTANCE_NAME
```

This step:

- Reads `manual_pc.json` and finds each text span in the transcript, recording start/end character indices aligned to those produced by the characteristics detection pipeline
- Writes `annotated_<transcript_name>.json` to `transcripts/` (ground truth in characteristics format)
- Runs the characteristics detection pipeline on the transcript
- Copies the characteristics output to `transcripts/`
- Writes `transcripts/manifest.json` linking all files

Outputs:

```
transcripts/
  annotated_$PC_TEST_INSTANCE_NAME.json        ← manual annotations with aligned span indices
  $PC_TEST_INSTANCE_NAME.json                  ← characteristics detection model output
  manifest.json                ← links all paths for the evaluate step
```

---

## Step 4 — Evaluate

```bash
poetry run python evals/dataset_generation/data_for_testing/src/evaluate.py $PC_TEST_INSTANCE_NAME
```

This compares `manual_pc.json` against the characteristics detection output and writes results to:

```
evals/dataset_generation/data_for_testing/output/evaluation_<timestamp>.json
```

### Per-item diagnostics

```json
{ "manual_text": "...", "best_match": "...", "score": 0.82, "label": "TP | FN" }
{ "hypothesis_text": "...", "best_match": "...", "score": 0.41, "label": "FP" }
```

### Summary metrics

```json
{ "precision": 0.85, "recall": 0.78, "f1_score": 0.81, "true_positive": 7, "false_negative": 2, "false_positive": 1 }
```

---

## Iteration

To refine results without re-running characteristics detection:

1. Edit `input/$PC_TEST_INSTANCE_NAME/manual_pc.json`
2. Re-run annotate: `poetry run python ... annotate.py $PC_TEST_INSTANCE_NAME`
3. Re-run evaluate: `poetry run python ... evaluate.py $PC_TEST_INSTANCE_NAME`

---

## Notes

- **Index alignment** — both `annotated_$PC_TEST_INSTANCE_NAME.json` and the characteristics detection output use the same transcript string representation (`"Speaker: text\n..."`) and the same `re.escape` / `re.finditer` pattern, so span indices are directly comparable
- **Similarity function** — configurable in `evaluate.py`; options: `semantic_similarity` (default, requires `evals-summarisation`), `default_similarity`, `containment_similarity`
- **Threshold** — default `0.6`; lower is more lenient, higher is stricter
- **Matching** — bidirectional: manual→hypothesis (recall) and hypothesis→manual (precision)
