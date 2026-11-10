# Summarisation model comparison — full pipeline, all tested setups (Nov 2026)

Raw data in Sharepoint, `model_comparison_november_2026`

![All setups, cost vs quality](cost_vs_quality_llms.png)

## All setups, cost-descending

| Setup | Cost/meeting | Mean ± SD | n | Fail share* |
|---|---:|---:|---:|---:|
| All GPT 4o | £0.46 | 4.33 ± 0.92 | 194 | 32.0% |
| All Claude Sonnet 5 | £0.37 | 4.75 ± 0.71 | 152 | 21.1% |
| Claude Sonnet 5 (citing) with Haiku 4.5 | £0.31 | 4.88 ± 0.35 | 144 | 0.0% |
| All GPT 5-1 | £0.28 | 4.71 ± 0.59 | 210 | 3.7% |
| GPT 5-1 (citing) with Nano | £0.20 | 4.74 ± 0.62 | 210 | 11.1% |
| All Claude Haiku 4.5 | £0.19 | 4.56 ± 0.96 | 152 | 47.4% |
| GPT 5-1 with Luna (citing) | £0.11 | 4.79 ± 0.53 | 160 | 10.0% |
| GPT 5-1 with Nano (citing) | £0.10 | 4.48 ± 0.93 | 226 | 13.8% |
| All GPT 6 Luna | £0.02 | 4.88 ± 0.51 | 160 | 10.0% |
| All GPT 5 Nano | £0.01 | 4.28 ± 0.97 | 226 | 24.1% |

\* Fail share: % of examples with ≥1 rubric dimension below its pass bar (strict dims ≥4, others ≥3).
