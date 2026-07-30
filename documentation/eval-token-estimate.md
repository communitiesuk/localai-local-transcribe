# Eval Pipeline Token & Cost Estimate

What a full synthetic-data eval run costs, and what to do about it.

**Assumptions, formulas, caching analysis and every code citation live in
`documentation/env_assets/eval_token_model.py`** — run it to reproduce any figure here, or change one
constant to see what moves.

---

## Bottom line

Per meeting at **L = 9,000 words** (~1 hour): **3.6M tokens, £2.46**. With no prompt caching at all it
would be £3.28.

All figures are **GBP**, priced on **Azure OpenAI, Sweden Central, Data Zone** — the deployment this
service actually uses (`FAST_LLM_PROVIDER`/`BEST_LLM_PROVIDER` both default to `azure_apim`).

Caching changes an input token's *price* (to ~10% of list), never its count, and cached tokens still
consume TPM — so size a **quota** off tokens and a **budget** off cost.

| N meetings | Tokens | Budget | Ask for (doubled for retries) |
|---|---:|---:|---|
| 10 | 36M | £25 | ~72M / ~£49 |
| 50 | 181M | £123 | ~361M / ~£246 |
| 100 | 361M | £246 | ~723M / ~£492 |
| 500 | 1.81B | £1,229 | ~3.6B / ~£2,458 |

**BEST (GPT-5.1) is 67% of tokens but 98% of cost** (£2.41 of £2.46). FAST is free in practice — every
optimisation that matters is a BEST optimisation.

---

## Where it goes

Per meeting-of-N, i.e. the run total divided by N, so the rows sum to the per-meeting cost.

| Stage | Applies to | **FAST tok** | **BEST tok** | Total tok | Tok share | **£/M tok** | **Cost** | Cost share | No-cache cost |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **(a)** Generate synthetic transcripts | all N | 871,844 | 782,728 | 1.65M | **46%** | £0.10 | **£0.17** | 7% | £0.91 |
| **(b)** Evaluate standard summarisation | all N | 51,542 | 252,330 | 0.30M | 8% | £1.13 | **£0.34** | **14%** | £0.34 |
| **(c)** PC detection + 9 counterfactuals | N/10 transcripts | — | 136,021 | 0.14M | 4% | **£2.27** | **£0.31** | **13%** | £0.31 |
| **(d)** Evaluate bias, 5 iterations | **~N variants** | 257,710 | 1,261,650 | 1.52M | 42% | £1.08 | **£1.64** | **67%** | £1.72 |
| **a+b+c+d** | | **1,181,096** | **2,432,729** | **3.61M** | 100% | £0.68 | **£2.46** | 100% | **£3.28** |

* **(a) drives the quota, not the budget** — 46% of tokens, 7% of cost. Quadratic in L, but FAST-heavy
  and already ~96% cached (£0.91 → £0.17).
* **(d) dominates spend at 67%** on volume. It is **not** a tenth of the work: sampling 1/10 and
  generating 9 counterfactuals each gives 10 variants per sampled transcript, so the enriched set is the
  same size as the original generation.
* **(c) has the worst unit price by 2×** (£2.27/M) and is nearly immune to caching — 810 uncacheable
  detection calls plus output-bound rewriting at £8.34/1M.

Cutting the same total a different way:

| Work | Calls | Tokens | **Cost** |
|---|---:|---:|---:|
| **Judging** — (b) 8 dimensions + (d) 40 | 48 | 1.35M | **£1.46 (59%)** |
| **Summarising** the thing being judged — (b) 3 + (d) 5 × 3 | 18 | 0.48M | **£0.53 (21%)** |
| Generation, detection, rewriting | ~249 | 1.79M | £0.48 (19%) |

Judging dominates because each of the 48 calls re-sends the transcript **and** the summary (~27,960
input tokens) with nothing cached.

---

## Sources

[Azure OpenAI pricing](https://azure.microsoft.com/en-us/pricing/details/azure-openai/#pricing), read
with **Region: Sweden Central, Model type: Data Zone**, in GBP per 1M tokens:

| Tier | Model | Input | Cached input | Output |
|---|---|---:|---:|---:|
| FAST | GPT-5-nano | £0.05 | £0.01 | £0.34 |
| BEST | GPT-5.1 | £1.05 | £0.11 | £8.34 |

These are the standard Data Zone rates. The page also lists a **Priority Processing** column for
GPT-5.1 at £2.09/£0.21/£16.67 — 2× standard — which this service does not use.

---

## Appendix: efficiency

Judge, PC detection and counterfactual rewrite are all BEST (`adapter_factory.py:26`,
`default_config.yaml:3`, `rewriter.py:32`); only `extract_claims`/`cite_claims` are FAST, and they cost
£0.04. Savings are per meeting, then at N=50, each measured on its own.

* **Fix judge prefix caching — £1.07, £53, 43%. Do this first.** `metric.py:65` puts a fresh
  `secrets.token_hex(4)` and the rubric *above* the transcript, so all 48 calls pay full price for the
  same ~28k tokens. Move them below it. No behaviour change, no quality risk.
* **Settle the iteration count — £1.30, £65.** £1.64 of the £2.46 assumes 5 iterations, but
  `counterfactual.yaml:9` says `num_iterations: 1` and generation runs at `temperature=0.0`. If 1 is
  right, N=50 is £58, not £123 — the estimate's largest uncertainty.
* **`template_fit` + `auditability` → code — £0.36, £18.** Schema conformance and whether citations
  resolve to real spans are exactly checkable: cheaper *and* more reliable than judging them.
* **PC detection → FAST — £0.15, £7.** Worst unit price (£2.27/M) and uncacheable. Config-only trial, but
  gate it on recall agreement — it feeds a fairness pipeline.
* **Rewrite flagged spans, not whole transcripts — £0.11, £5.** Keep BEST; cut output volume only, as bad
  rewrites silently poison the bias eval.
* **Don't shrink the judge.** [SLMJury](https://arxiv.org/html/2606.07810),
  [Judging the Judges](https://arxiv.org/pdf/2406.12624): small judges are fine on verifiable tasks but
  correlate only 0.36–0.42 with humans on open-ended quality scoring, which is what our rubric does. Nor
  a jury of them — [panel errors are correlated](https://arxiv.org/html/2605.29800v1) (9 judges ≈ 2.2
  effective votes). If trialled, enable reasoning:
  [~+10pp for <2× FLOPs](https://arxiv.org/html/2509.13332v1).
* **All four fixes stacked: £1.38, £69, 56%** — not additive, since caching and dimension-pruning attack
  the same judge input.
