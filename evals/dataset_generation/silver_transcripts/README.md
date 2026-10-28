# Silver transcript generation

Generate Azure transcripts and audio segments for human annotation. Listen to each segment and correct its transcript to create a silver reference.

The pipeline reads directories from a YAML config, defaulting to `configs/smoke_test.yaml`. Paths resolve relative to the config file. Set `input_dir` to your source audio directory and optionally set `work_dir`; its default is `output/` under this directory.

```bash
poetry run python -m evals.dataset_generation.silver_transcripts.src.main --config path/to/config.yaml
```

Generation uses Azure credentials and ffmpeg. Every source is converted to mono MP3 at 192 kbps using the same helper as transcription evaluation. Sources up to two hours use synchronous Azure transcription. Sources over two hours and up to four hours use the existing Azure batch adapter: the MP3 is uploaded to the configured storage service, submitted for asynchronous transcription, then deleted after a result is retrieved. Polling allows at least 30 minutes and scales to twice the recording duration. If a submitted job does not complete, its uploaded audio is retained so the running job can still access it. This requires S3 or Azure Blob storage so Azure can fetch the uploaded audio; `STORAGE_SERVICE_NAME=local` is not supported for batch transcription. Recordings over four hours fail with a recorded error. Supported extensions are `.wav`, `.flac`, `.ogg`, `.mp3`, `.m4a` and `.aac`, discovered recursively. Keep the work directory outside the input directory.

Each meeting is written under `<work_dir>/drafts/<meeting-id>/`:

- `audio.mp3`: the full audio submitted to Azure.
- `draft.txt`: the full-meeting transcript, with one diarised speaker label per utterance.
- `metadata.json`: relative source path, engine, generation date, status, segment count and confidence statistics.
- `segments/segment_0000/`, `segments/segment_0001/`, etc.: each contains `audio.mp3`, editable `audio.txt` and `metadata.json`.

Both `draft.txt` and each segment's `audio.txt` contain one utterance per line, prefixed with its diarised speaker label (for example, `Speaker 1: Hello.`). The segment folders are the final output. Move them out of the draft tree to annotate, then listen to each segment's `audio.mp3` and correct its `audio.txt`, including speaker attribution. Do not annotate in place: anything left under `segments/` is regenerable scratch and is replaced if that sample is generated again. There is no separate export command or copied output dataset. Existing export directories from earlier versions are left untouched.

## Segmentation and metadata

Chunks target `cutoff_seconds` (600 seconds by default) and never split an utterance. A chunk normally closes only where no speech overlaps, so crosstalk is never cut mid-exchange, and a long utterance or overlapping group may exceed the target. Continuously overlapping speech offers no such point, so a chunk is also forced shut once it would span twice the cutoff; audio either side of a forced boundary overlaps in source time, and each segment records its own interval in its metadata. As a result, a clip may contain speech whose utterance is assigned to the neighboring segment and is absent from this clip's `audio.txt`. Annotators should use each clip's audio as the source of truth and add or correct any audible speech and speaker attribution in that clip's transcript. Leading/trailing silence outside the selected utterances is omitted, while silence within a chunk is retained. Missing or invalid timestamps fail generation; end times must be within the audio duration with a 50 ms tolerance.

Regeneration replaces a draft's `segments/` directory wholesale, including anything an interrupted or failed earlier run left behind. Annotation is done on files moved out of the draft tree, so `segments/` is regenerable scratch rather than a place to keep edits. Completed drafts are resumed untouched.

Segment metadata records the parent meeting ID, source start/end seconds, `utterance_count`, `scored_utterance_count`, `mean_utterance_confidence` and `std_utterance_confidence`. Confidence averages are unweighted and standard deviation is population standard deviation. Missing scores are excluded; aggregates are null when no scores exist. Annotation edits do not update engine confidence statistics.

Status describes generation only: `completed` or `failed`. A completed `metadata.json` is the only record that a draft is done: such a draft resumes quietly without re-transcribing, whether or not its segments are still on disk, so a sample whose segments have been moved on for annotation is never regenerated. Failed samples are retried. Any recorded generation failure gives a non-zero exit status.

Failures are contained to the sample they belong to. Whatever goes wrong for one input — a conversion error, an engine error, exhausted service retries, or a `metadata.json` that cannot be read — is logged and recorded as a failure, and the run carries on to the next sample. A generation failure is written to that draft's `metadata.json` so the sample is retried next run; a draft whose existing `metadata.json` could not be read is left exactly as it is on disk, since it may hold hand-made edits. The only whole-run failures are the config-wide ones: a missing or empty input directory, a work directory inside the input directory, an invalid `cutoff_seconds`, and a draft recorded with a different `cutoff_seconds`.

Sample IDs depend on the relative input path. Changed audio is not detected automatically: move its existing draft aside before regenerating. Older metadata using `pending_review` or `approved` is not a status this version recognises: such a draft is reported as a failed sample and skipped, leaving the file untouched, so change its status to `completed` to resume it.

## Smoke test

Place one short recording in `evals/dataset_generation/silver_transcripts/input/smoke/`, then run:

```bash
poetry run python -m evals.dataset_generation.silver_transcripts.src.main --config evals/dataset_generation/silver_transcripts/configs/smoke_test.yaml
```

This calls Azure and writes to `output/smoke/drafts/` under this directory. The code default is a 10-minute cutoff, but `smoke_test.yaml` overrides it to 60 seconds, so a recording longer than two minutes should exercise multiple chunks (continuous overlap can extend a chunk to twice the cutoff).

Set `cutoff_seconds: 300` in the YAML config for approximately five-minute segments. It must be a positive finite number; whole utterances and overlapping speech can exceed the target. When changing the cutoff, use a new `work_dir` or move existing drafts aside before regenerating.

## Azure DevOps

The manual `evals-silver-transcripts.yml` pipeline downloads recordings from the restricted input container (default prefix `transcription/`), runs the same generator and publishes drafts and segments to `debug/silver-transcripts/<Azure DevOps build ID>/` in the restricted storage account and as an Azure DevOps artifact. Both uploads are attempted after generation failures when the output directory exists. Its default cutoff is 60 seconds and can be changed when starting the run. The output contains audio and transcripts: use appropriate access controls and retention for the input data.
