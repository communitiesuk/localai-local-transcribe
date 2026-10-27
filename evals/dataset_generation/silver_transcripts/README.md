# Silver transcript generation

Generate draft transcripts and review audio segments for annotation.

Run from config:

```bash
poetry run python -m evals.dataset_generation.silver_transcripts.src.main --config path/to/config.yaml
```

## Azure DevOps (manual)

Use `.azuredevops/pipelines/evals-silver-transcripts.yml` (test only).  
Parameter: `inputPrefix` (default `transcription/`).

It reuses the transcription eval blob input loader, stages selected recordings locally on the agent, runs generation, and always publishes `silver-transcripts-output` (including failed runs). Keep credentials in secret variables/service connections.

## Local end-to-end run from bucket

```bash
poetry run python -m evals.dataset_generation.silver_transcripts.src.local_run --prefix "your/folder/"
```

`--prefix` defaults to `transcription/`.

Output is written under `<work_dir>/drafts/<meeting-id>/` with:
- `audio.mp3`
- `draft.txt`
- `metadata.json`
- `segments/segment_*/` (`audio.mp3`, `audio.txt`, `metadata.json`)

## Smoke test

Place one short recording in `evals/dataset_generation/silver_transcripts/input/smoke/`, then run:

```bash
poetry run python -m evals.dataset_generation.silver_transcripts.src.main --config evals/dataset_generation/silver_transcripts/configs/smoke_test.yaml
```

Writes drafts to `output/smoke/drafts/`.
