# Evaluation Pipeline

This pipeline evaluates how well automatically detected Protected Characteristics (PCs) align with manually identified ones.

---

## 🔹 Overview

The workflow is split into **two stages**:

1. **Pipeline (1/2)** → Generate transcript + extract PCs + prepare files  
2. **Pipeline (2/2)** → Compare manual PCs vs model output and compute metrics  

---

> [!NOTE]
> #### poetry install --with evals-summarisation
> This module optionally uses of the sentence-transformers dependency

## 1️⃣ Configure Transcript Generation

Edit the config file:

> `evals/dataset_generation/transcription_generation/configs/multi_with_pcs.yaml`


Define your desired:
- Theme / scenario  
- Speakers  
- Context  

---

## 2️⃣ Run Pipeline (1/2)

```bash
poetry run python evals/dataset_generation/data_for_testing/src/run.py
```


## Outputs

- Generated transcript → processed automatically

- Extracted characteristics →
> `evals/characteristics/output/`
> `evals/dataset_generation/data_for_testing/transcripts/`

- Auto-created manual file →
> `evals/dataset_generation/data_for_testing/transcripts/manual/`

- Manifest →
> `evals/dataset_generation/data_for_testing/transcripts/manifest.json`


## ✍️ 3️⃣ Add Manual PCs

Open the auto-created file in:

> `evals/dataset_generation/data_for_testing/transcripts/manual/`

Populate the list with manually identified PC-related text spans, e.g.:

```python
my_manual_pcs = [
    "Biola",
    "three months pregnant",
    "expecting a baby",
    "he",
    "my partner",
]
```
Include duplicates if they appear multiple times — the evaluation supports this.


## 4️⃣ Run Pipeline (2/2)

After adding manual PCs:

Import the list and add it as the first arg of the  `evaluate_manual_vs_hypothesis` funtion within main (manual_list param), then run

```bash
poetry run python evals/dataset_generation/data_for_testing/src/main.py
```

## Outputs

Results are written to:
> `evals/dataset_generation/data_for_testing/output/`

They include:

#### Per-item diagnostics
```json
{
  "manual_text": "...",
  "best_match": "...",
  "score": 0.82,
  "label": "TP | FN"
}
```
#### False positives
```json
{
  "hypothesis_text": "...",
  "best_match": "...",
  "score": 0.41,
  "label": "FP"
}
```

#### Summary metrics

```json
{
  "average_similarity": "...",
  "coverage@threshold": "...",
  "precision": "...",
  "recall": "...",
  "f1_score": "...",
}
```

## 🔁 Iteration Workflow

You can refine your manual PCs:

1. Update the manual list
2. Re-run Pipeline (2/2) only

No need to regenerate transcripts.


## 🧠 Notes

- Matching using **fuzzy similarity** resolves such as:
  - `"he said"` ≈ `"he said that"`

- Matching is **bidirectional**:
  - Manual → Hypothesis (recall-like)
  - Hypothesis → Manual (precision-like)

- **Threshold is configurable**:
  - Default is `0.6`
  - Controls what qualifies as a match (TP vs FN/FP)
  - Lower → more lenient matching  
  - Higher → stricter matching  

- **Similarity function is configurable**:
  - You can swap out the `text_similarity` param for different strategies, or choose to create one to suit your needs
  - Functions on file:
    - semantic_similarity (default, requires installing evals-summarisation's group-dev-dependencies )
    - default_similarity
    - containment_similarity (useful for substrings)
  - This directly impacts scoring behaviour and evaluation sensitivity

- Manifest ensures:
  - Always uses latest pipeline output  
