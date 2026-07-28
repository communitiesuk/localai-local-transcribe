# Eval Pipeline Token & Cost Estimate

What a full synthetic-data eval run costs, and what to do about it.

**Assumptions, formulas, caching analysis and every code citation live in
`documentation/env_assets/eval_token_model.py`** — run it to reproduce any figure here, or change one
constant to see what moves.

---

## Bottom line

Per meeting at **L = 9,000 words** (~1 hour): **3.6M tokens, $2.92**. With no prompt caching at all it
would be $3.90.

Caching changes an input token's *price* (to 10% of list), never its count, and cached tokens still
consume TPM — so size a **quota** off tokens and a **budget** off cost.

| N meetings | Tokens | Budget | Ask for (doubled for retries) |
|---|---:|---:|---|
| 10 | 36M | $29 | ~72M / ~$58 |
| 50 | 181M | $146 | ~361M / ~$292 |
| 100 | 361M | $292 | ~723M / ~$584 |
| 500 | 1.81B | $1,460 | ~3.6B / ~$2,919 |

**BEST (GPT-5.1) is 67% of tokens but 98% of cost** ($2.88 of $2.92). FAST is free in practice — every
optimisation that matters is a BEST optimisation.

---

## Where it goes

Per meeting-of-N, i.e. the run total divided by N, so the rows sum to the per-meeting cost.

| Stage | Applies to | **FAST tok** | **BEST tok** | Total tok | Tok share | **$/M tok** | **Cost** | Cost share | No-cache cost |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **(a)** Generate synthetic transcripts | all N | 871,844 | 782,728 | 1.65M | **46%** | $0.11 | **$0.19** | 6% | $1.08 |
| **(b)** Evaluate standard summarisation | all N | 51,542 | 252,330 | 0.30M | 8% | $1.35 | **$0.41** | **14%** | $0.41 |
| **(c)** PC detection + 9 counterfactuals | N/10 transcripts | — | 136,021 | 0.14M | 4% | **$2.71** | **$0.37** | **13%** | $0.37 |
| **(d)** Evaluate bias, 5 iterations | **~N variants** | 257,710 | 1,261,650 | 1.52M | 42% | $1.29 | **$1.95** | **67%** | $2.04 |
| **a+b+c+d** | | **1,181,096** | **2,432,729** | **3.61M** | 100% | $0.81 | **$2.92** | 100% | **$3.90** |

* **(a) drives the quota, not the budget** — 46% of tokens, 6% of cost. Quadratic in L, but FAST-heavy
  and already ~96% cached ($1.08 → $0.19).
* **(d) dominates spend at 67%** on volume. It is **not** a tenth of the work: sampling 1/10 and
  generating 9 counterfactuals each gives 10 variants per sampled transcript, so the enriched set is the
  same size as the original generation.
* **(c) has the worst unit price by 2×** ($2.71/M) and is nearly immune to caching — 810 uncacheable
  detection calls plus output-bound rewriting at $10/1M.

Cutting the same total a different way:

| Work | Calls | Tokens | **Cost** |
|---|---:|---:|---:|
| **Judging** — (b) 8 dimensions + (d) 40 | 48 | 1.35M | **$1.74 (59%)** |
| **Summarising** the thing being judged — (b) 3 + (d) 5 × 3 | 18 | 0.48M | **$0.63 (21%)** |
| Generation, detection, rewriting | ~249 | 1.79M | $0.56 (19%) |

Judging dominates because each of the 48 calls re-sends the transcript **and** the summary (~27,960
input tokens) with nothing cached.

---

## Sources

* [OpenAI API pricing](https://developers.openai.com/api/docs/pricing) — FAST $0.05/$0.005/$0.40,
  BEST $1.25/$0.125/$10.00 per 1M input/cached/output
* [GPT-5-nano model page](https://developers.openai.com/api/docs/models/gpt-5-nano)
