"""Token/cost model for a full synthetic-data eval run. Conclusions: ../eval-token-estimate.md

Run it to reproduce that doc's tables; edit a constant to see what moves.

Each stage (a)-(d) is a list of Calls groups: N identical calls with per-call input/output words and
a cached-prefix fraction. cost = in_tok*((1-cached)*p_in + cached*p_cached) + out_tok*p_out. Token
counts are the same either way -- caching changes an input token's price, not its count. Two bases:
`today` (caching as the code behaves) and `raw` (no cache credit, for comparison).

Assumptions -- ✅ verified in repo, ⚠️ assumed:
  ✅ 2 tokens/word                 env-impact.md 5.1
  ✅ 6.0 chars/word                measured 5.81 over transcription_generation/output/
  ✅ r = 109 words/turn            measured, range 91-146
  ✅ S = 2 speakers                config.py:10
  ✅ actors FAST, facilitator BEST participant.py:11, transcript_generator.py:77
  ✅ FAST gpt-5-nano, BEST gpt5-1  settings.py:114,124
  ✅ 3 calls per summarisation     types.py:92-108 + citations.py:25,34. Not 6: env-impact B.2 also
                                   counts speaker-ID/title/hallucination, none on this path.
  ⚠️ summary = 0.5*L words         env-impact B.2. Weakest input; at 0.25*L the bill is $2.37 not $2.92
  ✅ 8 judge dimensions            constants.py:19, optimisation/runner.py:206. But the bias eval
                                   reads cfg.metrics and counterfactual.yaml:20 still lists 3.
  ✅ judge output ~60 words        measured `reason` fields, median 45-47
  ✅ judge rubric ~420 words       measured, 372-460 across rubrics
  ✅ 9 characteristics             shared_constants.py:4
  ✅ chunk 1000/400 -> stride 600  default_config.yaml, chunker.py:206
  ✅ 9 BEST agents per chunk       chunker.py:274-299
  ✅ PC prompt 423 w               wc -w agent_base.jinja2
  ⚠️ PC output ~40 w/call          most axes return empty per chunk
  ✅ rewrite prompt 797 w          wc -w counterfactual_rewrite.j2
  ⚠️ + 100 w evidence spans        rewriter.py:143
  ⚠️ 50 bias runs / sampled        10 variants x 5. counterfactual.yaml:9 says num_iterations: 1.
                                   10 not 18: record_builder.py:91 baseline_cache reuses originals.
  ⚠️ zero retries                  azure_apim.py:30 allows 6
  ✅ sentiment/REGARD local        bias/constants.py:3, regard_scorer.py:51 -- no tokens
  ✅ hallucination addon off       common/config.py:77

Caching as it stands -- ~1,024-token minimum, exact prefix match from token 0:
  (a)  actors ~96%, facilitator ~98%. Actors fragment S ways (own persona first), so uncached is
       2*L*S for the pool and 2*L for the single facilitator chain. Reminders append after history
       (client.py:50) so they are suffixes and preserve the prefix.
  (b)  0%. Judges regenerate marker_hash per call (metric.py:65) above the transcript, and the
       per-dimension rubric (system_prompt.j2:28) precedes it too. Summarisation calls are one-offs.
  (c)  0%. Detection's shared block is ~846 tok, under the minimum; rewrites are one per axis.
  (d)  summarisation ~80% (5 identical prompts per variant); judges 0%, as (b).
Not modelled: cache TTL, and APIM routing (prefix caches are per-deployment).
"""

from dataclasses import dataclass, field

TPW = 2  # tokens per word (env-impact.md 5.1)
CPW = 6.0  # chars per word (measured 5.81, rounded up)
R = 109.0  # words per speaker turn (measured)
S = 2  # speaker agents (config.py:10 default)
B = 0.1  # sampling rate for stage (c)
VARIANTS = 10  # 1 original + 9 counterfactuals
ITERATIONS = 5  # run-design choice
DIMS = 8  # DIMENSIONS_LABELS
NCHAR = 9  # ProtectedCharacteristic
CHUNK_CHARS = 1000
STRIDE_CHARS = 600

# prompt sizes, measured with wc -w / build_system_prompt
ACTOR_PERSONA_W = 725
FACILITATOR_SYS_W = 247
ACTOR_GEN_W = 1133
PC_PROMPT_W = 423
PC_OUT_W = 40  # ASSUMED
CF_PROMPT_W = 797 + 100  # rewrite template + evidence spans (ASSUMED 100)
JUDGE_SYS_W = 420  # measured 372-460 across rubrics
JUDGE_WRAPPER_W = 60
JUDGE_OUT_W = 60  # measured rationale 45-47 words + JSON envelope
SUMMARY_RATIO = 0.5  # minute output = 0.5*L words (env-impact B.2)

PRICE = {  # $ per token: (input, cached input, output)
    "FAST": (0.05e-6, 0.005e-6, 0.40e-6),
    "BEST": (1.25e-6, 0.125e-6, 10.00e-6),
}


@dataclass
class Calls:
    """A group of identical-shape LLM calls."""

    tier: str
    n: float
    in_w: float  # input words per call
    out_w: float  # output words per call
    cached: float = 0.0  # fraction of input words hitting a warm prefix

    @property
    def in_tok(self):
        return self.n * self.in_w * TPW

    @property
    def out_tok(self):
        return self.n * self.out_w * TPW

    @property
    def tok(self):
        return self.in_tok + self.out_tok

    def cost(self, no_cache=False):
        pin, pcached, pout = PRICE[self.tier]
        frac = 0.0 if no_cache else self.cached
        return self.in_tok * ((1 - frac) * pin + frac * pcached) + self.out_tok * pout


@dataclass
class Stage:
    key: str
    label: str
    scope: str
    calls: list[Calls] = field(default_factory=list)

    def tok(self, tier=None):
        return sum(c.tok for c in self.calls if tier is None or c.tier == tier)

    def cost(self, no_cache=False, tier=None):
        return sum(c.cost(no_cache) for c in self.calls if tier is None or c.tier == tier)


def summarisation_calls(n, cached, L):
    """General via generate_summary: 1 BEST minute + extract_claims + cite_claims (both FAST)."""
    return [
        Calls("BEST", n, 345 + L, SUMMARY_RATIO * L, cached),
        Calls("FAST", n, 336 + SUMMARY_RATIO * L, 0.1 * L, cached),
        Calls("FAST", n, 235 + 1.7 * L, SUMMARY_RATIO * L, cached),
    ]


def judge_call(n, L):
    """One BEST call per dimension, carrying transcript + summary + rubric. Never cached."""
    return Calls("BEST", n, JUDGE_SYS_W + JUDGE_WRAPPER_W + L + SUMMARY_RATIO * L, JUDGE_OUT_W)


def build(L=9000.0):
    turns = L / R
    history_w = L * (turns - 1) / 2  # conversation history summed over all turns

    # (a) generation, per meeting
    actor_in_w = turns * ACTOR_PERSONA_W + history_w
    fac_in_w = turns * FACILITATOR_SYS_W + history_w
    a = Stage("a", "Generate synthetic transcripts", "all N")
    a.calls += [
        Calls("FAST", 1, actor_in_w, L, 1 - turns * S * R / actor_in_w),
        Calls("BEST", 1, fac_in_w, turns * 30, 1 - turns * R / fac_in_w),
        Calls("BEST", 1, ACTOR_GEN_W, S * 150),
    ]

    # (b) standard summarisation eval, per meeting
    b = Stage("b", "Evaluate standard summarisation", "all N")
    b.calls += summarisation_calls(1, 0.0, L)
    b.calls.append(judge_call(DIMS, L))

    # (c) PC detection + counterfactual rewriting, per sampled transcript
    chunks = L * CPW / STRIDE_CHARS
    c = Stage("c", "PC detection + 9 counterfactuals", "N/10 transcripts")
    c.calls += [
        Calls("BEST", B * chunks * NCHAR, PC_PROMPT_W + CHUNK_CHARS / CPW, PC_OUT_W),
        Calls("BEST", B * 9, CF_PROMPT_W + L, L),
    ]

    # (d) bias eval, per sampled transcript
    runs = B * VARIANTS * ITERATIONS
    d = Stage("d", "Evaluate bias, 5 iterations", "~N variants")
    d.calls += summarisation_calls(runs, 1 - 1 / ITERATIONS, L)
    d.calls.append(judge_call(DIMS * runs, L))

    return [a, b, c, d]


def report(L=9000.0):
    st = build(L)
    tok = sum(s.tok() for s in st)
    cost = sum(s.cost() for s in st)
    raw = sum(s.cost(no_cache=True) for s in st)

    print(f"\n{'=' * 104}\nL = {L:,.0f} words   S = {S}   iterations = {ITERATIONS}   dims = {DIMS}\n{'=' * 104}")
    print(
        f"\n{'Stage':<40}{'FAST tok':>11}{'BEST tok':>11}{'Total':>11}{'tok%':>7}{'$/M':>8}{'Cost':>8}{'%':>6}{'No cache':>10}"
    )
    for s in st:
        print(
            f"({s.key}) {s.label:<35}{s.tok('FAST'):>11,.0f}{s.tok('BEST'):>11,.0f}{s.tok():>11,.0f}"
            f"{s.tok() / tok * 100:>6.0f}%{s.cost() / s.tok() * 1e6:>8.2f}{s.cost():>8.2f}"
            f"{s.cost() / cost * 100:>5.0f}%{s.cost(no_cache=True):>10.2f}"
        )
    print(
        f"{'a+b+c+d':<40}{sum(s.tok('FAST') for s in st):>11,.0f}{sum(s.tok('BEST') for s in st):>11,.0f}"
        f"{tok:>11,.0f}{'100%':>7}{cost / tok * 1e6:>8.2f}{cost:>8.2f}{'100%':>6}{raw:>10.2f}"
    )

    print("\nTier split")
    for tier in ("FAST", "BEST"):
        t = sum(s.tok(tier) for s in st)
        cc = sum(s.cost(tier=tier) for s in st)
        print(f"  {tier:<5}{t:>11,.0f} tok ({t / tok * 100:.0f}%)   ${cc:.2f} ({cc / cost * 100:.0f}% of cost)")

    print("\nSummarising vs judging")
    judges = [c for s in st for c in s.calls if c.tier == "BEST" and c.out_w == JUDGE_OUT_W]
    summ = [c for s in st if s.key in "bd" for c in s.calls if c not in judges]
    other = [c for s in st if s.key in "ac" for c in s.calls]
    turns = L / R
    for name, group, n in [
        ("Judging", judges, sum(c.n for c in judges)),
        ("Summarising", summ, sum(c.n for c in summ)),
        ("Generation, detection, rewriting", other, 2 * turns + 1 + sum(c.n for c in st[2].calls)),
    ]:
        t = sum(c.tok for c in group)
        cc = sum(c.cost() for c in group)
        print(f"  {name:<34}{n:>6.0f} calls{t:>11,.0f} tok   ${cc:.2f} ({cc / cost * 100:.0f}%)")

    print("\nTotals by N")
    for n in (10, 50, 100, 500):
        t = tok * n
        unit = f"{t / 1e6:.0f}M" if t < 1e9 else f"{t / 1e9:.2f}B"
        print(f"  N={n:<5}{unit:>8}   ${cost * n:>8,.0f}   ask for ~{t * 2 / 1e6:,.0f}M / ~${cost * n * 2:,.0f}")


if __name__ == "__main__":
    for length in (2000.0, 5000.0, 9000.0):
        report(length)
