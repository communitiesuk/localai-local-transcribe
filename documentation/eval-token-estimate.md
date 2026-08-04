# Eval Pipeline Token & Cost Estimate

What a full synthetic-data eval run costs, and what to do about it.

**Assumptions, formulas, caching analysis and every code citation live in
`documentation/env_assets/eval_token_model.py`** — run it to reproduce any figure here, including the
appendix's savings, or change one constant to see what moves. Judge prompt segment sizes are measured by
`env_assets/measure_judge_prompt_sizes.py`.

---

## Bottom line

Per meeting at **L = 9,000 words** (~1 hour): **3.7M tokens, £1.33**. With no prompt caching at all it
would be £3.32. Judge prefix caching (AIILG-791) is in and priced in: it took this from £2.50, **−47%**.

All figures are **GBP**, priced on **Azure OpenAI, Sweden Central, Data Zone** — the deployment this
service actually uses (`FAST_LLM_PROVIDER`/`BEST_LLM_PROVIDER` both default to `azure_apim`).

Caching changes an input token's *price* (to ~10% of list), never its count, and cached tokens still
consume TPM — so size a **quota** off tokens and a **budget** off cost. Tokens are in fact slightly *up*
on the pre-caching estimate (3.61M): the judge prompt is now measured, not approximated.

| N meetings | Tokens | Budget | Ask for (doubled for retries) |
|---|---:|---:|---|
| 10 | 37M | £13 | ~73M / ~£27 |
| 50 | 183M | £67 | ~366M / ~£133 |
| 100 | 366M | £133 | ~731M / ~£267 |
| 500 | 1.83B | £667 | ~3.7B / ~£1,334 |

**BEST (GPT-5.1) is 68% of tokens but 97% of cost** (£1.29 of £1.33). FAST is free in practice — every
optimisation that matters is a BEST optimisation.

---

## Where it goes

Per meeting-of-N, i.e. the run total divided by N, so the rows sum to the per-meeting cost.

| Stage | Applies to | **FAST tok** | **BEST tok** | Total tok | Tok share | **£/M tok** | **Cost** | Cost share | No-cache cost |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **(a)** Generate synthetic transcripts | all N | 871,844 | 782,728 | 1.65M | **45%** | £0.10 | **£0.17** | 13% | £0.91 |
| **(b)** Evaluate standard summarisation | all N | 51,542 | 259,338 | 0.31M | 9% | £0.54 | **£0.17** | 13% | £0.35 |
| **(c)** PC detection + 9 counterfactuals | N/10 transcripts | — | 136,021 | 0.14M | 4% | **£2.27** | **£0.31** | **23%** | £0.31 |
| **(d)** Evaluate bias, 5 iterations | **~N variants** | 257,710 | 1,296,690 | 1.55M | 43% | £0.44 | **£0.69** | **52%** | £1.75 |
| **a+b+c+d** | | **1,181,096** | **2,474,777** | **3.66M** | 100% | £0.36 | **£1.33** | 100% | **£3.32** |

* **(a) drives the quota, not the budget** — 45% of tokens, 13% of cost. Quadratic in L, but FAST-heavy
  and already ~96% cached (£0.91 → £0.17).
* **(d) still dominates spend at 52%** on volume. It is **not** a tenth of the work: sampling 1/10 and
  generating 9 counterfactuals each gives 10 variants per sampled transcript, so the enriched set is the
  same size as the original generation. Its 40 judge calls went £1.25 → £0.27, the largest win from
  caching, and it is still the biggest line — what remains is summarisation, not judging.
* **(c) now has the worst unit price by 5×** (£2.27/M) and is the one stage caching left untouched — 810
  uncacheable detection calls plus output-bound rewriting at £8.34/1M. 13% → 23% of the bill without
  changing at all.

Cutting the same total a different way:

| Work | Calls | Tokens | **Cost** |
|---|---:|---:|---:|
| **Judging** — (b) 8 dimensions + (d) 40 | 48 | 1.39M | **£0.33 (25%)** |
| **Summarising** the thing being judged — (b) 3 + (d) 5 × 3 | 18 | 0.48M | **£0.53 (39%)** |
| Generation, detection, rewriting | ~248 | 1.79M | £0.48 (36%) |

**Judging is no longer the largest line** — 38% of tokens, 25% of cost. Only 2 of the 48 calls are cold:
the rubric is the sole per-dimension difference and sits last (513 of 14,418 words), so the rest serve
~96% of their ~28,800 input tokens from cache, or ~65% for bias iterations, which re-hit the transcript
sitting above the summary. Summarising the material now costs more than judging it.

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
£0.04. Savings are per meeting, then at N=50, each measured on its own — reproduce with `savings()`.

**Done: judge prefix caching — £1.17, £58, 47%** (AIILG-791), which also reordered what is left.

* **Settle the iteration count — £0.52, £26, 39%. Now the top lever.** £0.69 of the £1.33 assumes 5
  iterations, but `counterfactual.yaml:9` says `num_iterations: 1` and generation runs at
  `temperature=0.0`. If 1 is right, N=50 is £41, not £67 — the estimate's largest uncertainty.
* **PC detection → FAST — £0.15, £7, 11%.** Worst unit price (£2.27/M) and the only stage caching missed.
  Config-only trial, but gate it on recall agreement — it feeds a fairness pipeline.
* **Rewrite flagged spans, not whole transcripts — £0.11, £5, 8%.** Keep BEST; cut output volume only, as
  bad rewrites silently poison the bias eval.
* **`template_fit` + `auditability` → code — £0.07, £3, 5%.** Was £0.36 before caching: pruning
  dimensions now only removes already-warm calls. Do it for reliability, not cost — schema conformance
  and whether citations resolve to real spans are exactly checkable.
* **Don't shrink the judge** — less reason to now its input is mostly cached.
  [SLMJury](https://arxiv.org/html/2606.07810),
  [Judging the Judges](https://arxiv.org/pdf/2406.12624): small judges are fine on verifiable tasks but
  correlate only 0.36–0.42 with humans on open-ended quality scoring, which is what our rubric does. Nor
  a jury of them — [panel errors are correlated](https://arxiv.org/html/2605.29800v1) (9 judges ≈ 2.2
  effective votes). If trialled, enable reasoning:
  [~+10pp for <2× FLOPs](https://arxiv.org/html/2509.13332v1).
* **All four stacked: £0.80, £40, 60%** — roughly additive now, unlike caching and dimension-pruning,
  which overlapped. N=50 would be ~£27.
