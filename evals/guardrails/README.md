# Guardrail category eval

Minimal manual eval for the guardrail category mapping added around AIILG-854/AIILG-950.

Run:

```bash
poetry run python evals/guardrails/src/run_guardrail_category_eval.py
```

Layout:

- `configs/default.json` — run configuration, including the case file path.
- `input/cases.json` — ignored input case definitions.
- `src/run_guardrail_category_eval.py` — runner.
- `output/` — ignored generated results and written conclusions.

The fixture uses summaries from the final July summarisation run and applies small deterministic edits. Controls have no edit. Each bad case has one expected failure category. The script writes per-case score, reasoning, categories and the requested `f1_*` metrics to JSON.

Before a full run, put the case file at the configured ignored input path:

```text
evals/guardrails/input/cases.json
```

Default output:

```text
evals/guardrails/output/results.json
```

If APIM auth fails, refresh the local token first (`./apim.sh`, or ask a developer to do so if interactive login is required) and rerun.

After a run, write the short conclusion in `output/CONCLUSIONS.md` and upload `input/cases.json` plus `output/results.json` to the evidence folder.
