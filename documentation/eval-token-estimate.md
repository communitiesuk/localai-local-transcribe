# Eval Pipeline Token & Cost Estimate

Order-of-magnitude LLM token *and spend* budget for a full synthetic-data eval run, as a function of:

* **N** — number of meetings generated and evaluated
* **L** — expected average transcript length in words

## Run design (fixed)

| Stage | Applies to | What happens |
|---|---|---|
| **(a)** | all N | Generate N synthetic transcripts |
| **(b)** | all N | Evaluate standard summarisation |
| **(c)** | N/10 transcripts | Sample 1/10, detect protected characteristics, generate **9** counterfactuals each |
| **(d)** | **~N variants** | Evaluate bias on the enriched set, **5 iterations** per variant |

Sampling 1/10 and producing 9 counterfactuals gives 10 variants per sampled transcript, so the
enriched set is `(N/10) × 10 = N` — **the same size as the original generation**. Bias eval therefore
does **50 runs per sampled transcript** (10 variants × 5 iterations).

For sizing a quota and a budget, not precise accounting.

---

## 1. Assumptions

### 1.1 Pricing (USD per 1M tokens)

| Tier | Model | Input | Cached input | Output |
|---|---|---:|---:|---:|
| **FAST** | GPT-5-nano | $0.05 | $0.005 | $0.40 |
| **BEST** | GPT-5.1 | $1.25 | $0.125 | $10.00 |

Cached input is **10% of input price** on both tiers. Note the **8:1 output-to-input ratio on BEST** —
a generated token costs 8× a read one, so output-heavy stages punch above their token weight.

> ⚠️ OpenAI list prices. This project calls **Azure OpenAI via APIM** (`adapters/azure_apim.py`);
> confirm Azure rates and any APIM markup before committing a budget.

### 1.2 Pipeline parameters

| Assumption | Value | Basis |
|---|---|---|
| Tokens per word | 2 | `env-impact.md` §5.1 |
| **Chars per word** | **6.0** | ✅ measured 5.80 across 5 output transcripts; rounded up for speaker labels |
| Eval summarisation template | General = SimpleTemplate + citations | ✅ `counterfactual.yaml` |
| Words per speaker turn (`r`) | **109** | ✅ measured, 5 files in `transcription_generation/output/` (91–146) |
| Distinct speaker agents (`S`) | 5 | ⚠️ assumed — affects cache fragmentation, §5.2 |
| Judge dimensions — **both** evals | **8** | ✅ `src/constants.py:19` `DIMENSIONS_LABELS` |
| **Protected characteristics** | **9** | ✅ `shared_constants.py:4` `ProtectedCharacteristic` |
| **PC detection chunking** | 1,000 chars, 400 overlap → **stride 600** | ✅ `characteristics/configs/default_config.yaml` |
| **PC detection model** | `gpt5-1` → **BEST** | ✅ same config |
| **PC detection prompt** | 423 words | ✅ `wc -w agent_base.jinja2` |
| PC detection output per call | ~40 words | ⚠️ assumed — most of the 9 axes return empty per chunk |
| Counterfactuals per sampled transcript | 9 | run design |
| **Counterfactual rewrite prompt** | 797 words | ✅ `wc -w counterfactual_rewrite.j2` |
| Evidence spans injected into rewrite prompt | ~100 words | ⚠️ assumed — `rewriter.py:143` passes detection spans through |
| Bias runs per sampled transcript | 50 = 10 variants × 5 | ✅ `iteration_runner.py:102` |
| Retries / failures | zero | `env-impact.md` convention — real runs exceed this |

> **🐛 Stale config — fix before running.** `build_metrics` reads `cfg.metrics` from the yaml
> (`src/common/metric.py:164`), and `configs/counterfactual.yaml:20` still lists the **old** 3-judge
> set (`accuracy, coverage, readability`). The current set is the 8 in `DIMENSIONS_LABELS`. A run
> today would silently evaluate 3 dimensions. **Correcting it raises bias-judge cost 2.7×.**

### 1.3 Protected-characteristic detection (stage c prerequisite)

Counterfactual rewriting requires a `CharacteristicDetection` input (`rewriter.py:39`), produced by a
separate pipeline that is **easy to miss in a cost estimate**. Its structure:

`process_chunk_parallel` (`chunker.py:274-299`) runs **one focused BEST agent per protected
characteristic, per chunk** — `asyncio.gather` over all 9 characteristics. With `stride = 600 chars`
and 6 chars/word:

```
chunks        ≈ L × 6 / 600  =  L / 100
detection calls ≈ 9 × L/100  =  0.09 · L        →  810 BEST calls at L = 9,000
```

Each call carries the 423-word prompt plus a ~167-word chunk (~1,180 tokens in, ~80 out). Because the
40% chunk overlap re-processes every character ~1.67×, and each chunk is scanned 9 separate times,
**detection costs more in tokens than the counterfactual rewriting it feeds** — see §7 lever 2.

---

## 2. Headline figures (L = 9,000)

**~3.7M tokens per meeting-of-N.** Cost depends on caching, so always state which basis:

| Basis | Cost / meeting | Use it for |
|---|---:|---|
| **Raw** (list price, no cache credit) | **$3.89** | worst-case ceiling |
| **Today** (caching as the code actually behaves) | **$2.94** | ✅ **budgeting a run today** |
| **Fixed** (after the §5.1 judge-prefix fix) | **$1.56** | budgeting if that fix lands first |

Token counts are identical across all three — caching changes price, not volume.

### Tier split (today's basis)

| Tier | Tokens | Tok share | Cost (today) | **Cost share** |
|---|---:|---:|---:|---:|
| FAST (GPT-5-nano) | 1.29M | 35% | $0.05 | **2%** |
| BEST (GPT-5.1) | 2.41M | 65% | $2.89 | **98%** |
| **Total** | **3.70M** | 100% | **$2.94** | 100% |

**FAST is free, in practice.** Every optimisation that matters is a BEST optimisation.

---

## 3. Per-run formulas

With the 1/10 sampling rate baked in, both terms collapse into a single function of N and L:

```
FAST  ≈ N · (L²/109 +  59.6·L +  8,900)
BEST  ≈ N · (L²/109 + 177.2·L + 76,800)
─────────────────────────────────────────
TOTAL ≈ N · (0.018·L² + 237·L + 86,000)
```

To flex the sampling rate, the pre-collapse form is
`N·(L²/109 + 11.6L + 1,486) + B·N·(480L + 74,300)` for FAST and
`N·(L²/109 + 27.3L + 14,744) + B·N·(1,499L + 620,300)` for BEST, with `B = 0.1` here.

### Scaling with L

| L (words) | Chunks (PC) | FAST tok | BEST tok | Total tok | **Cost (today)** | Cost (raw) |
|---|---:|---:|---:|---:|---:|---:|
| 2,000 | 20 | 0.16M | 0.47M | 0.63M | **$0.77** | $0.85 |
| 5,000 | 50 | 0.54M | 1.19M | 1.73M | **$1.68** | $1.90 |
| 9,000 (1 hr) | 90 | 1.29M | 2.41M | 3.70M | **$2.94** | $3.89 |

### Totals by N (L = 9,000)

| N | Tokens | Cost (today) | Cost (fixed) |
|---|---:|---:|---:|
| 10 | 37M | $29 | $16 |
| 50 | 185M | $147 | $78 |
| 100 | 370M | $294 | $156 |
| 500 | 1.85B | $1,471 | $782 |

---

## 4. Cost separation by stage (L = 9,000)

All figures are **per meeting-of-N**, i.e. the run total divided by N, so the four rows sum to the
per-meeting cost. Multiply any row by N for the whole run.

Watch the scoping on (c) and (d) — they differ:

* **(c)** touches only the **N/10 sampled transcripts**. Its per-sampled-transcript cost is amortised
  over all N here, so the row shows 1/10 of it.
* **(d)** touches the **whole enriched set of `(N/10) × 10 = ~N` variants**, each run 5×. That is
  **5N bias runs** for the whole job, or **5 production summarisations + 40 judge calls** per
  meeting-of-N. Stage (d) is *not* a tenth of the work — the 1/10 sampling is exactly cancelled by the
  10 variants each sampled transcript produces.

### 4.1 Summary

| Stage | Applies to | **FAST tok** | **BEST tok** | Total tok | Tok share | **Cost (today)** | Cost share | Cost (raw) | Cost (fixed) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **(a)** Generate synthetic transcripts | all N | 761,119 | 748,103 | 1.51M | **41%** | **$0.16** | 6% | $1.01 | $0.16 |
| **(b)** Evaluate standard summarisation | all N | 87,886 | 255,244 | 0.34M | 9% | **$0.42** | **14%** | $0.42 | $0.21 |
| **(c)** PC detection + 9 counterfactuals | N/10 transcripts | — | 136,080 | 0.14M | 4% | **$0.37** | **12%** | $0.37 | $0.35 |
| **(d)** Evaluate bias, 5 iterations | **~N variants** | 439,430 | 1,276,220 | 1.72M | 46% | **$1.99** | **68%** | $2.09 | $0.85 |
| **a+b+c+d** | | **1,288,435** | **2,415,647** | **3.70M** | 100% | **$2.94** | 100% | **$3.89** | **$1.56** |

### 4.2 Stage (c) split — detection vs rewriting

| Sub-stage | Calls / sampled transcript | BEST tok (per meeting-of-N) | Cost (today) |
|---|---|---:|---:|
| (c1) PC detection — 9 agents × 90 chunks | **810** | 102,060 | **$0.18** |
| (c2) Counterfactual rewriting — 9 variants | 9 | 34,020 | $0.18 |
| **(c) total** | **819** | **136,080** | **$0.37** |

**(c2) breakdown per sampled transcript:** 9 calls × (897 words prompt + L words transcript) in =
178,200 tokens; 9 × L words out = 162,000 tokens. The **output side is 91% of c2's tokens** — each
counterfactual is a complete rewritten transcript, which is why c2 costs the same as 810 detection
calls despite being only 9 requests. Note (c1) feeds (c2): detection's evidence spans are injected
into the rewrite prompt (`rewriter.py:143`).

**Detection is half of stage (c) and 3× the rewriting in tokens** despite producing no transcript
text — 810 separate BEST calls to scan one transcript. See §7 lever 2.

### 4.3 Cost detail (today's basis)

| Stage | FAST cost | BEST cost | **Stage total** |
|---|---:|---:|---:|
| (a) | $0.015 | $0.150 | **$0.16** |
| (b) | $0.008 | $0.410 | **$0.42** |
| (c) | — | $0.368 | **$0.37** |
| (d) | $0.027 | $1.964 | **$1.99** |
| **a+b+c+d** | **$0.05** | **$2.89** | **$2.94** |

### 4.4 What the separation shows

* **(a) is the token hog (41%) but only 6% of cost.** It runs on all N and is quadratic in L, yet it
  is FAST-heavy and caches well ($1.01 raw → $0.16 today — the one stage caching already rescues). It
  drives the *quota*, not the *budget*.
* **(b) is 14% of cost and the worst cost-per-token of the four.** It also runs on all N, so its 8
  BEST judge calls never disappear behind the bias term. Per token it is ~4× stage (a).
* **(c) is only 4% of tokens but 12% of cost, and nearly immune to caching.** Both halves are
  all-BEST: detection is 810 uncacheable small calls, rewriting is output-bound at $10/1M.
* **(d) still dominates at 68%**, and holds nearly all the caching headroom: $2.09 raw → $0.85 fixed.

---

## 5. Caching: prefix structure, and what it's worth

Azure OpenAI caches automatically above ~1k tokens, but only on an **exact prefix match from token
0**. Three things decide the hit rate: **chain count** (fragmentation), **ordering** (invariant bulk
must precede varying text), and **repetition**.

### 5.1 🐛 Judge calls: currently 0% cacheable, for two independent reasons

`metric.py:61-77` builds each judge call as `[system: rubric_for_dim, user: transcript + summary]`:

* **`marker_hash = secrets.token_hex(4)` is regenerated per call** (`metric.py:65`) and injected into
  *both* messages *above* the transcript. A fresh random token near the prompt head **guarantees a
  prefix miss on every call.**
* **The per-dimension rubric sits in the system message** — first — so even with a stable hash, all 8
  dimensions diverge before reaching the shared transcript.

Across stages (b) and (d) this is **480 judge calls per 10 meetings**, each re-sending a full
transcript uncached — **$1.74 of the $2.94, or 59% of total spend**, at zero cache benefit.

The hash is a genuine prompt-injection defence (distinguishing real BEGIN/END markers from injected
lookalikes, `metric.py:63-64`), so it cannot simply be constant. But it only needs to be unguessable
**by whoever authored the transcript**, not unique per call. Deriving it **once per transcript**
preserves that property while letting all 40 judge calls for a variant share one prefix.
⚠️ Worth a security review before adopting — not a free win.

### 5.2 Stage (a): one conversation, but one chain *per agent*

Actors all receive the same accumulated conversation, but each is prefixed by its own persona
(`actor_system.j2`), so the prefix diverges at token 0 and **the shared history is not shared in
cache terms** — it fragments `S` ways. Within one actor's chain, turn *k* and *k+S* still share a
prefix, so caching works; it just misses the `S·r` words added since that actor last spoke.

| Agent | Chains | Uncached input | Hit rate (S=5) |
|---|---|---|---|
| Actors (FAST) | S = 5 | ≈ 2·L·S tokens | ~88% |
| Facilitator (BEST) | 1 | ≈ 2·L tokens | ~98% |

Reminders append *after* history (`client.py:50` sends `self.messages + messages`), so they are
suffixes and preserve the prefix. Actors and facilitator are **different models** and can never share
a cache regardless of ordering. Unifying personas to a trailing position would merge the actor pool
into one chain (~88% → ~98%) — a FAST-tier saving worth **<$0.01/meeting. Not worth the
instruction-following risk.**

### 5.3 PC detection: structurally uncacheable

The 9 per-characteristic agents share a chunk but each prompt embeds its own characteristic, and
chunks differ from one another. The shared instruction block is ~423 words (~846 tokens) — **below the
~1,024-token cache minimum** — so even reordering would not qualify it. Treat detection as 0%
cacheable and attack its *call count* instead (§7 lever 2).

### 5.4 Headroom and what it's worth

| Stage | Hit now | Hit if fixed | Blocker |
|---|---|---|---|
| (a) generation | ~93% | ~98% | persona fragmentation — *not worth fixing, FAST-tier* |
| (b) production summarisation | ~0% | ~0% | 6 one-off distinct prompts, no repetition |
| (b) + (d) judges | **0%** | **~90%** | per-call `marker_hash`; rubric-first ordering |
| (c1) PC detection | ~0% | ~0% | prompt below cache minimum (§5.3) |
| (c2) counterfactuals | ~0% | ~90% | ⚠️ ordering unverified — 9 calls share one transcript |
| (d) summarisation | ~80% | ~80% | already good: 5 identical iterations per variant |

The decisive number is the **BEST input hit rate**:

| Scenario | FAST hit | **BEST hit** | Cost / meeting | vs. today |
|---|---:|---:|---:|---:|
| No caching at all | 0% | 0% | $3.89 | — |
| **As the code stands today** | 80% | **35%** | **$2.94** | — |
| With hash + ordering fixed | 86% | **87%** | **$1.56** | **−47%** |

**Fixing the judge prefix nearly halves the bill** — ~$1.38/meeting, ~$69 on a 50-meeting run — with
no change to eval semantics; prompt caching does not affect sampling, so the 5 iterations stay
statistically valid.

**After that fix, output is 59% of cost.** The lever then stops being caching and becomes *generating
less*: fewer iterations, fewer counterfactuals.

> **⚠️ Caching cuts spend, not rate limits.** Cached input generally still counts toward TPM. Size a
> *rate-limit* ask on the raw §3 token figures; use cost figures only for budget.

---

## 6. What to ask for

Both doubled for retries and headroom, at L = 9,000:

| N | Token quota | Budget (today) |
|---|---:|---:|
| 10 | ~74M | ~$59 |
| 50 | ~370M | ~$294 |
| 100 | ~740M | ~$588 |
| 500 | ~3.7B | ~$2,941 |

Split roughly **35% FAST / 65% BEST** by volume. Halve the budget column if the §5.1 judge fix lands
first.

---

## 7. Levers, ranked by money saved

1. **Fix the judge `marker_hash` + ordering** (§5.1) — ~47% of spend, no semantic change. Top lever.
2. **Raise the PC-detection chunk size.** 1,000 chars with 400 overlap means 90 chunks × 9 agents =
   810 BEST calls to scan one transcript, re-reading every character ~1.67×. GPT-5.1's context makes
   this far smaller than necessary: at 8,000 chars/chunk it drops to ~8 chunks and **72 calls, an ~11×
   reduction** — detection cost $0.18 → $0.04/meeting. ⚠️ Larger chunks may reduce detection recall;
   validate against the existing labelled set before adopting.
3. **Bias eval internals** — stage (d) is 68% of cost; iterations 5→3 or dimensions 8→5 each cut
   roughly a third of it.
4. **Standard-eval judge count** — stage (b) is 14% of cost and runs on *all* N, so trimming its 8
   dimensions scales 10× harder than trimming bias eval's.
5. **Counterfactual count** — 9→5 cuts stage (c2); output-bound, so immune to caching.
6. ~~FAST-tier optimisation~~ — 2% of cost. Ignore.

---

## 8. Caveats

* **⚠️ Verify the generator reaches your target L.** Sampled outputs are only 549–636 words (4–6
  turns), far short of 9,000. Either `word_target` was low or generation stops early — confirm before
  sizing on L = 9,000. Stage (a) is 41% of tokens, so this drives the quota more than the budget.
* **PC detection output size assumed** (~40 words/call). It is 810 calls, so if detections are richer
  than assumed this line grows; the input side is measured and dominates.
* **Zero-retry assumption.** Production retry allows 6 attempts with backoff. Note `pipeline.py:51`
  also sleeps 2s between chunks — at 90 chunks that is ~3 min/transcript of pure wall-clock.
* **Azure vs OpenAI pricing** unconfirmed (§1.1).
* **`r` and `S`** — affect stage (a): 41% of tokens, 6% of cost.
* **Stage (c2) prompt ordering unverified** — its cache headroom is inferred from the judge path.
* Sentiment (`cardiffnlp/twitter-roberta-base`) and REGARD (`sasha/regardv3`) run **locally — zero
  token cost**.

---

## Sources

* [OpenAI API pricing](https://developers.openai.com/api/docs/pricing)
* [GPT-5-nano model page](https://developers.openai.com/api/docs/models/gpt-5-nano)
