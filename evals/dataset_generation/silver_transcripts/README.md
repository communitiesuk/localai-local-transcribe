# Silver transcript generation

Generate Azure transcripts and audio segments for human annotation. Listen to each segment and correct its transcript to create a silver reference.

The pipeline reads directories from a YAML config, defaulting to `configs/smoke_test.yaml`. Paths resolve relative to the config file. Set `input_dir` to your source audio directory and optionally set `work_dir`; its default is `output/` under this directory.

```bash
poetry run python -m evals.dataset_generation.silver_transcripts.src.main --config path/to/config.yaml
```

## Azure DevOps manual pipeline

Use `.azuredevops/pipelines/evals-silver-transcripts.yml` for manual runs in test.

Run-time parameters:

- `inputPrefix` (optional): folder/prefix inside the uploads container (`AZURE_UPLOADS_CONTAINER_NAME`), default `transcription/`.

The pipeline downloads recordings from the same uploads container used by transcription (`AZURE_UPLOADS_CONTAINER_NAME`) into a local agent directory via the shared Python Azure Blob storage components, writes a run-specific silver config with that local `input_dir`, runs the generator with test Azure credentials, and always publishes the `silver-transcripts-output` pipeline artifact (including failed runs). It sets `segment_duration_seconds: null` so each recording is kept as one full segment.

Keep credentials in secret pipeline variables or a variable group/service connection. The pipeline expects these variables at run time (secrets where applicable): `AZURE_BLOB_CONNECTION_STRING`, `STORAGE_SERVICE_NAME`, `AZURE_UPLOADS_CONTAINER_NAME`, `AZURE_TRANSCRIPTION_CONTAINER_NAME`, `AZURE_APIM_URL`, `AZURE_APIM_API_VERSION`, `AZURE_APIM_SUBSCRIPTION_KEY`, `AZURE_APIM_AUTH_METHOD`, and either `AZURE_APIM_ACCESS_TOKEN` or the client-secret set (`AZURE_APIM_TENANT_ID`, `AZURE_APIM_CLIENT_ID`, `AZURE_APIM_CLIENT_SECRET`, `AZURE_APIM_SCOPE`).

## Local end-to-end run from bucket

If you have credentials locally, you can run the same flow without Azure DevOps:

```bash
poetry run python -m evals.dataset_generation.silver_transcripts.src.local_run --prefix "your/folder/"
```

If omitted, `--prefix` defaults to `transcription/`.

Required environment variables are the same storage/transcription ones used above (for short files, batch-specific settings are only needed if a recording exceeds the synchronous limit).

Generation uses Azure credentials and ffmpeg. Every source is converted to mono MP3 at 192 kbps using the same helper as transcription evaluation. Sources up to two hours use synchronous Azure transcription. Sources over two hours and up to four hours use the existing Azure batch adapter: the MP3 is uploaded to the configured storage service, submitted for asynchronous transcription, then deleted after a result is retrieved. Polling allows at least 30 minutes and scales to twice the recording duration. If a submitted job does not complete, its uploaded audio is retained so the running job can still access it. This requires S3 or Azure Blob storage so Azure can fetch the uploaded audio; `STORAGE_SERVICE_NAME=local` is not supported for batch transcription. Recordings over four hours fail with a recorded error. Supported extensions are `.wav`, `.flac`, `.ogg`, `.mp3`, `.m4a` and `.aac`, discovered recursively. Keep the work directory outside the input directory.

Each meeting is written under `<work_dir>/drafts/<meeting-id>/`:

- `audio.mp3`: the full audio submitted to Azure.
- `draft.txt`: the full-meeting transcript, with one diarised speaker label per utterance.
- `metadata.json`: relative source path, engine, generation date, status, segment count and confidence statistics.
- `segments/segment_0000/`, `segments/segment_0001/`, etc.: each contains `audio.mp3`, editable `audio.txt` and `metadata.json`.

Both `draft.txt` and each segment's `audio.txt` contain one utterance per line, prefixed with its diarised speaker label (for example, `Speaker 1: Hello.`). The segment folders are the final output. Move them out of the draft tree to annotate, then listen to each segment's `audio.mp3` and correct its `audio.txt`, including speaker attribution. Do not annotate in place: anything left under `segments/` is regenerable scratch and is replaced if that sample is generated again. There is no separate export command or copied output dataset. Existing export directories from earlier versions are left untouched.

## Segmentation and metadata

This flow keeps each recording as one segment (`segment_duration_seconds: null`).

Regeneration replaces a draft's `segments/` directory wholesale, including anything an interrupted or failed earlier run left behind. Annotation is done on files moved out of the draft tree, so `segments/` is regenerable scratch rather than a place to keep edits. Completed drafts are resumed untouched.

Segment metadata records the parent meeting ID, source start/end seconds, `utterance_count`, `scored_utterance_count`, `mean_utterance_confidence` and `std_utterance_confidence`. Confidence averages are unweighted and standard deviation is population standard deviation. Missing scores are excluded; aggregates are null when no scores exist. Annotation edits do not update engine confidence statistics.

Status describes generation only: `completed` or `failed`. A completed `metadata.json` is the only record that a draft is done: such a draft resumes quietly without re-transcribing, whether or not its segments are still on disk, so a sample whose segments have been moved on for annotation is never regenerated. Failed samples are retried. Any recorded generation failure gives a non-zero exit status.

Failures are contained to the sample they belong to. Whatever goes wrong for one input — a conversion error, an engine error, exhausted service retries, or a `metadata.json` that cannot be read — is logged and recorded as a failure, and the run carries on to the next sample. A generation failure is written to that draft's `metadata.json` so the sample is retried next run; a draft whose existing `metadata.json` could not be read is left exactly as it is on disk, since it may hold hand-made edits. The only whole-run failures are the config-wide ones: a missing or empty input directory, a work directory inside the input directory, and a draft recorded with a different `segment_duration_seconds`.

Sample IDs depend on the relative input path. Changed audio is not detected automatically: move its existing draft aside before regenerating. Older metadata using `pending_review` or `approved` is not a status this version recognises: such a draft is reported as a failed sample and skipped, leaving the file untouched, so change its status to `completed` to resume it.

## Smoke test

Place one short recording in `evals/dataset_generation/silver_transcripts/input/smoke/`, then run:

```bash
poetry run python -m evals.dataset_generation.silver_transcripts.src.main --config evals/dataset_generation/silver_transcripts/configs/smoke_test.yaml
```

This calls Azure and writes to `output/smoke/drafts/` under this directory.

This implementation uses `segment_duration_seconds: null` (full-recording segmenting) in the pipeline flow.
