# Data for Testing — Evaluation Pipeline

Evaluates how well the characteristics detection pipeline identifies Protected Characteristics (PCs) by comparing its output against a manually annotated ground truth.

Two independent evaluations are available:

- **PC detection eval** — precision / recall / F1 comparing detected spans against manual annotations
- **Counterfactual rewrite eval** — checks that original characteristic values are removed after LLM rewriting, and scores coherence

---

## Overview

The workflow has three stages:

1. **Annotate** — creates an index-aligned ground truth (`reference.json`) from `manual_pc.json`
2. **Evaluate** — runs the characteristics detection pipeline and computes precision / recall / F1 against the reference
3. **Evaluate counterfactual** — proposes alternative characteristic values, rewrites the transcript, and checks removal via regex + LLM coherence scoring

Multiple unrelated transcripts can coexist under `evals/dataset_generation/data_for_testing/input/` — each in its own named subdirectory.
---

> **Note:** Install the `evals-summarisation` dependency group for semantic similarity scoring:
> ```bash
> poetry install --with evals-summarisation
> ```

---

## Step 1 — Generate a Synthetic Transcript

Configure the scenario, speakers, and context by editing the config file first:

```
evals/dataset_generation/transcription_generation/configs/multi_with_pcs.yaml
```

Use the transcription generation module to produce a transcript:

```bash
poetry run python -m evals.dataset_generation.transcription_generation.main --config multi_with_pcs.yaml
```

The output is written to:

```
evals/dataset_generation/transcription_generation/output/
```


---

## Step 2 — Place Files in the Input Folder

Each transcript lives in a named subdirectory under `evals/dataset_generation/data_for_testing/input/`. Create one and copy the generated transcript into it:

```bash
PC_TEST_INSTANCE_NAME=my_transcript

mkdir -p evals/dataset_generation/data_for_testing/input/$PC_TEST_INSTANCE_NAME
cp "$(ls -t evals/dataset_generation/transcription_generation/output/*.json | head -1)" \
   evals/dataset_generation/data_for_testing/input/$PC_TEST_INSTANCE_NAME/
```

Create a skeleton `manual_pc.json` with one placeholder row per protected characteristic:

```bash
cat > evals/dataset_generation/data_for_testing/input/$PC_TEST_INSTANCE_NAME/manual_pc.json << 'EOF'
[
  {"text": "", "category": "",                          "value": ""},
]
EOF
```

Fill in `text` with the exact substring as it appears in the transcript, fill in `value`, and delete rows for characteristics that are not present. Example after editing:

```json
[
  {"text": "Kowalski",             "category": "Race",                   "value": "White (Polish)"},
  {"text": "three months pregnant","category": "Pregnancy and Maternity","value": "Pregnant"},
  {"text": "he",                   "category": "Sex",                    "value": "Male"},
  {"text": "Margaret",             "category": "Sex",                    "value": "Female"},
  {"text": "Margaret",             "category": "Race",                   "value": "White British"}
]
```

The last two rows show that a single text span can signal **multiple** protected characteristics. "Margaret" is both a female name (Sex) and a name common in White British culture (Race). Add one row per `(text, category, value)` combination — the pipeline will produce a separate characteristic entry for each.

- `text` — the exact substring to search for in the transcript
- `category` — the protected characteristic (`Age`, `Disability`, `Gender Reassignment`, `Marriage and Civil Partnership`, `Pregnancy and Maternity`, `Race`, `Religion or Belief`, `Sex`, `Sexual Orientation`)
- `value` — the specific attribute value (e.g. `White (Polish)`, `Male`, `Pregnant`). There is no fixed set of these, just be concise and descriptive.

Entries sharing the same `category` + `value` are grouped into one characteristic in `reference.json`. Duplicate `(text, category, value)` triplets are deduplicated. A span that signals multiple characteristics (e.g. "Margaret" above) will appear independently under each one. Every occurrence of each text span in the transcript becomes a separate reference span.

Expected layout:

```
evals/dataset_generation/data_for_testing/input/
  $PC_TEST_INSTANCE_NAME/
    <transcript>.json    ← generated transcript
    manual_pc.json       ← your manual annotations
```

---

## Step 3 — Annotate

```bash
poetry run python evals/dataset_generation/data_for_testing/src/annotate.py $PC_TEST_INSTANCE_NAME
```

Reads `manual_pc.json`, finds each span in the transcript with character-aligned indices, and writes:

```
evals/dataset_generation/data_for_testing/output/
  $PC_TEST_INSTANCE_NAME/
    reference.json    ← manual annotations in characteristics format
```

---

## Step 4 — Evaluate (PC Detection)

```bash
poetry run python evals/dataset_generation/data_for_testing/src/evaluate_spans.py $PC_TEST_INSTANCE_NAME
```

Runs the characteristics detection pipeline on the transcript, compares its output against `reference.json`, and writes:

```
evals/dataset_generation/data_for_testing/output/
  $PC_TEST_INSTANCE_NAME/
    hypothesis.json   ← characteristics pipeline output
    metrics.json      ← precision / recall / F1
```

### Per-item diagnostics

```json
{ "manual_text": "...", "best_match": "...", "score": 0.82, "label": "TP | FN" }
{ "hypothesis_text": "...", "best_match": "...", "score": 0.41, "label": "FP" }
```

### Summary metrics

```json
{
  "precision": 0.85,
  "recall": 0.78,
  "f1_score": 0.81,
  "true_positive": 7,
  "false_negative": 2,
  "false_positive": 1
}
```

---

## Step 5 — Evaluate Counterfactual Rewriting *(optional)*

```bash
poetry run python evals/dataset_generation/data_for_testing/src/evaluate_counterfactual.py $PC_TEST_INSTANCE_NAME
# optionally configure number of alternatives (default: 2)
poetry run python evals/dataset_generation/data_for_testing/src/evaluate_counterfactual.py $PC_TEST_INSTANCE_NAME --num-alternatives 3
```

The LLM analyses the detected characteristics and proposes up to `N` counterfactual axis transformations (one per detected characteristic). Each axis is applied as a full LLM rewrite; the result is then assessed for value removal and coherence.

Writes:

```
output/$PC_TEST_INSTANCE_NAME/
  counterfactual_report.json
  rewrites/
    original.txt          ← unchanged transcript for easy comparison
    rewrite_0.txt
    rewrite_1.txt
    ...
```

### Report structure

```json
{
  "summary": {
    "num_rewrites": 2,
    "successful_rewrite_rate": 1.0,
    "average_coherence": 0.75,
    "average_leakage": 0.1
  },
  "rewrites": [
    {
      "alternative_index": 0,
      "transcript_file": "rewrites/rewrite_0.txt",
      "axis_change": {"axis": "Race", "original_value": "asian_participants", "target_value": "all_white_british"},
      "all_values_removed": true,
      "coherence": 0.75,
      "coherence_explanation": "Reads naturally.",
      "leakage_checks": [
        {"characteristic": "Race", "value": "Asian", "score": 0.0, "explanation": "No evidence found."}
      ],
      "unexpected_edits": []
    }
  ]
}
```

---

## Iteration

To refine results without re-running characteristics detection:

1. Edit `evals/dataset_generation/data_for_testing/input/$PC_TEST_INSTANCE_NAME/manual_pc.json`
2. Re-run annotate: `poetry run python ... annotate.py $PC_TEST_INSTANCE_NAME`
3. Re-run evaluate: `poetry run python ... evaluate_spans.py $PC_TEST_INSTANCE_NAME`

---

## Notes

- **Index alignment** — both `reference.json` and the characteristics detection output use the same transcript string representation (`"speaker: text\n..."`) and the same `re.escape` / `re.finditer` pattern, so span indices are directly comparable
- **Span matching** — a hypothesis span is a true positive only when it fully contains the reference span; partial coverage counts as a false negative
- **Similarity function** — configurable in `evaluate_spans.py`; options: `semantic_similarity` (default, requires `evals-summarisation`), `default_similarity`, `containment_similarity`
- **Threshold** — default `0.6`; lower is more lenient, higher is stricter
- **Matching** — bidirectional: manual→hypothesis (recall) and hypothesis→manual (precision)
- **Word boundaries** — the counterfactual regex check uses `\b` boundaries, so short values like `"Na"` won't match inside words like `"Natural"`
