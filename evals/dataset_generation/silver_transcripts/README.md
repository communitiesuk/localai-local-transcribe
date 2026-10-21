# Silver transcript generation

Generate Azure transcripts and audio segments for human annotation. Listen to each segment and correct its transcript to create a silver reference.

The pipeline reads directories from a YAML config, defaulting to `configs/smoke_test.yaml`. Paths resolve relative to the config file. Set `input_dir` to your source audio directory and optionally set `work_dir`; its default is `output/` under this directory.

```bash
poetry run python -m evals.dataset_generation.silver_transcripts.src.main --config path/to/config.yaml
```

Generation uses Azure credentials and ffmpeg. Every source is converted to mono MP3 at 192 kbps using the same helper as transcription evaluation, then transcribed once. Supported extensions are `.wav`, `.flac`, `.ogg`, `.mp3`, `.m4a` and `.aac`, discovered recursively. Keep the work directory outside the input directory.

Each meeting is written under `<work_dir>/drafts/<meeting-id>/`:

- `audio.mp3`: the full audio submitted to Azure.
- `draft.txt`: the original full-meeting transcript.
- `metadata.json`: relative source path, engine, generation date, status, segment count and confidence statistics.
- `segments/segment_0000/`, `segments/segment_0001/`, etc.: each contains `audio.mp3`, editable `transcript.txt` and `metadata.json`.

The segment folders are the final output. Move them out of the draft tree to annotate, then listen to each segment's `audio.mp3` and correct its `transcript.txt`. Do not annotate in place: anything left under `segments/` is regenerable scratch and is replaced if that sample is generated again. There is no separate export command or copied output dataset. Existing export directories from earlier versions are left untouched.

## Segmentation and metadata

Chunks target `cutoff_seconds` (600 seconds by default) and never split an utterance. A chunk normally closes only where no speech overlaps, so crosstalk is never cut mid-exchange, and a long utterance or overlapping group may exceed the target. Continuously overlapping speech offers no such point, so a chunk is also forced shut once it would span twice the cutoff; audio either side of a forced boundary overlaps in source time, and each segment records its own interval in its metadata. Leading/trailing silence outside the selected utterances is omitted, while silence within a chunk is retained. Missing or invalid timestamps fail generation; end times must be within the audio duration with a 50 ms tolerance.

Regeneration replaces a draft's `segments/` directory wholesale, including anything an interrupted or failed earlier run left behind. Annotation is done on files moved out of the draft tree, so `segments/` is regenerable scratch rather than a place to keep edits. Completed drafts are resumed untouched.

Segment metadata records the parent meeting ID, source start/end seconds, `utterance_count`, `scored_utterance_count`, `mean_utterance_confidence` and `std_utterance_confidence`. Confidence averages are unweighted and standard deviation is population standard deviation. Missing scores are excluded; aggregates are null when no scores exist. Annotation edits do not update engine confidence statistics.

Status describes generation only: `completed` or `failed`. A completed `metadata.json` is the only record that a draft is done: such a draft resumes quietly without re-transcribing, whether or not its segments are still on disk, so a sample whose segments have been moved on for annotation is never regenerated. Failed samples are retried. Any recorded generation failure gives a non-zero exit status.

Sample IDs depend on the relative input path. Changed audio is not detected automatically: move its existing draft aside before regenerating. Older metadata using `pending_review` or `approved` must be changed to `completed` before resuming.

## Smoke test

Place one short recording in `evals/dataset_generation/silver_transcripts/input/smoke/`, then run:

```bash
poetry run python -m evals.dataset_generation.silver_transcripts.src.main --config evals/dataset_generation/silver_transcripts/configs/smoke_test.yaml
```

This calls Azure and writes to `output/smoke/drafts/` under this directory. Use a recording longer than ten minutes to exercise multiple chunks.

Set `cutoff_seconds: 300` in the YAML config for approximately five-minute segments. It must be a positive finite number; whole utterances and overlapping speech can exceed the target. When changing the cutoff, use a new `work_dir` or move existing drafts aside before regenerating.
