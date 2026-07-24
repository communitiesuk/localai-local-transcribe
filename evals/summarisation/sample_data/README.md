# Summarisation eval sample data (safe proxy data)

Synthetic, non-sensitive input for developing the blob-storage summarisation flow. **No real or
sensitive data.** These files mirror the layout expected inside the `input` container under the
`summarisation/` prefix, so uploading this folder's contents reproduces the blob structure the
standard summarisation eval reads.

| Path                       | Eval     | Notes                                                            |
| -------------------------- | -------- | --------------------------------------------------------------- |
| `standard/dialogues.jsonl` | standard | JSONL of `{id, dialogue, summary}` synthetic meeting dialogues. |

The hallucination eval takes no disk input — it runs as an addon to the standard eval.

## Upload to the input container

The eval containers authenticate with Entra ID (no account keys). Sign in first (`az login`), then
upload with your account name and `--auth-mode login`:

```bash
az storage blob upload-batch \
  --account-name "<evals-storage-account-name>" \
  --auth-mode login \
  --destination input \
  --destination-path summarisation \
  --source evals/summarisation/sample_data
```

This produces `input/summarisation/standard/dialogues.jsonl`, which the
`configs/blob-smoke-test.yaml` config reads via `dataset.blob_path`.
