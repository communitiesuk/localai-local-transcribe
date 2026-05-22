"""
Environmental Impact Calculations for Local Transcribe.

Reproduces every calculation from documentation/env-impact.md.
All ASSUMPTIONS are at the top — edit them to explore scenarios.
Every result is derived directly; no pre-computed constant feeds into another step.

Run with: python documentation/env_assets/calculations.py
"""

# =============================================================================
# ASSUMPTIONS — source/measured values; edit these to model different scenarios
# =============================================================================

# --- Meeting / transcript ---
TRANSCRIPT_WORDS = 9_000  # X: words in transcript (1-hour baseline, ~7,500–9,000 typical)
NUM_SECTIONS = 6  # Y: sections produced by SectionTemplate
TOKENS_PER_WORD = 2  # conservative estimate for English text [B.1]

# --- Carbon intensity ---
INFERENCE_CARBON_INTENSITY_G_PER_KWH = 258  # EU-27 average [10]
TRAINING_CARBON_INTENSITY_G_PER_KWH = 386  # US average, EPA eGRID [14]

# --- ASR (transcription) — measurements from study [15], Whisper proxy ---
ASR_STUDY_TOTAL_ENERGY_KWH = 0.49  # kWh measured over the study sample
ASR_STUDY_AUDIO_HOURS = 22  # hours of audio in the study sample
ASR_STUDY_TOTAL_CO2E_G = 380  # g CO₂e measured over the study sample
# Note: the study's implied carbon intensity (~776 g/kWh) differs from EU-27.
# CO₂e for combined totals (Section 8) is recalculated using EU-27 for consistency.

# --- LLM benchmark measurements [1] Table 4, medium (1k input / 1k output) prompt ---
# These are raw measurements; per-token rates are derived below.
GPT4O_BENCHMARK_WH = 1.215  # Wh for 1k-input + 1k-output tokens, GPT-4o Mar '25
GPT4O_BENCHMARK_TOKENS = 2_000  # total tokens in that benchmark prompt
GPT4_TURBO_BENCHMARK_WH = 5.940  # Wh for 1k-input + 1k-output tokens, GPT-4 Turbo
GPT4_TURBO_BENCHMARK_TOKENS = 2_000  # total tokens in that benchmark prompt

# --- LLM training energy [11] ---
GPT4_TRAINING_MWH = 57_000  # midpoint of 52k–62k MWh range
GPT4O_TRAINING_MWH = 1_151  # Gopher (280B params) proxy for GPT-4o (~200B params)

# --- LLM user base [13] ---
LLM_USER_BASE = 800_000_000  # ChatGPT weekly active users at peak

# --- Executive Summary (executive_summary.j2) ---
EXEC_SUMMARY_SYSTEM_WORDS = 129  # counted directly from executive_summary.j2

# --- UserTemplate DOCUMENT (user_template.py document_prompt) ---
DOCUMENT_PROMPT_FIXED_WORDS = 115  # fixed words in document_prompt, excluding {template} and {date}
USER_TEMPLATE_CONTENT_WORDS = 200  # user-defined template content (assumption; varies in practice)
DOCUMENT_DATE_WORDS = 7  # formatted datetime, e.g. "Monday 22 May 2026 14:30:00"

# --- OWSM v3 training hardware [19][20][21][22] ---
OWSM_GPU_COUNT = 64  # NVIDIA A100 40GB PCIe GPUs used
OWSM_GPU_TDP_W = 250  # TDP per GPU in watts [20]
OWSM_TRAINING_DAYS = 10  # duration of training run
OWSM_SERVER_GPU_DRAW_W = 3_200  # GPU power draw for a server with 8 A100s [22]
OWSM_SERVER_NON_GPU_LOW_W = 500  # lower bound, non-GPU components [22]
OWSM_SERVER_NON_GPU_HIGH_W = 1_000  # upper bound, non-GPU components [22]
OWSM_PUE = 1.56  # industry average PUE 2024 [21]

# --- ASR user base [23] ---
ASR_USER_BASE = 300_000_000  # Microsoft Teams monthly active users


# =============================================================================
# HELPERS
# =============================================================================


def words_to_tokens(words: float) -> float:
    return words * TOKENS_PER_WORD


def _section(title: str) -> None:
    print(f"\n{'=' * 62}")
    print(f"  {title}")
    print("=" * 62)


def _row(label: str, value: str) -> None:
    print(f"  {label:<44} {value}")


# =============================================================================
# SECTION 6: TRANSCRIPTION IMPACT (1-hour meeting)
# =============================================================================


def transcription_impact() -> dict:
    # Per-hour energy from study measurement
    energy_wh = (ASR_STUDY_TOTAL_ENERGY_KWH * 1_000) / ASR_STUDY_AUDIO_HOURS

    # CO₂e as reported by the study (uses study's implied carbon intensity)
    co2e_g_study = ASR_STUDY_TOTAL_CO2E_G / ASR_STUDY_AUDIO_HOURS

    # CO₂e recalculated with EU-27 intensity for consistent combined-total percentages
    co2e_g_eu27 = (energy_wh / 1_000) * INFERENCE_CARBON_INTENSITY_G_PER_KWH

    return {
        "energy_wh": energy_wh,
        "co2e_g_study": co2e_g_study,
        "co2e_g_eu27": co2e_g_eu27,
    }


# =============================================================================
# SECTION 7: LLM TOKEN USAGE AND ENERGY (Appendix B)
# =============================================================================


def _llm_result(fast_words: float, best_words: float) -> dict:
    """Convert word counts to token counts and then to energy + CO₂e."""
    fast_tokens = words_to_tokens(fast_words)
    best_tokens = words_to_tokens(best_words)

    # Per-token energy rates derived from benchmark measurements
    fast_wh_per_token = GPT4O_BENCHMARK_WH / GPT4O_BENCHMARK_TOKENS
    best_wh_per_token = GPT4_TURBO_BENCHMARK_WH / GPT4_TURBO_BENCHMARK_TOKENS

    fast_wh = fast_tokens * fast_wh_per_token
    best_wh = best_tokens * best_wh_per_token
    total_wh = fast_wh + best_wh

    co2e_g = (total_wh / 1_000) * INFERENCE_CARBON_INTENSITY_G_PER_KWH

    return {
        "fast_tokens": fast_tokens,
        "best_tokens": best_tokens,
        "total_tokens": fast_tokens + best_tokens,
        "fast_wh": fast_wh,
        "best_wh": best_wh,
        "total_wh": total_wh,
        "co2e_g": co2e_g,
    }


def simple_template(x: float = TRANSCRIPT_WORDS) -> dict:
    """
    B.2 — SimpleTemplate: General / Executive Summary (6 invocations).

    Based on actual code (common/templates/types.py, common/templates/citations.py,
    common/prompts.py, common/prompt_templates/*.j2).

    Key implementation facts that affect token counts:
      - ChatBot.structured_chat() does NOT prepend conversation history.
        hallucination_check() calls structured_chat([17-word question]) — no context included.
      - ChatBot.chat() DOES prepend history (self.messages + new_messages).
      - extract_claims() uses a fresh chatbot and only receives the draft (0.5X), NOT the transcript.
      - cite_claims() uses a fresh chatbot and receives transcript + claims + draft.

    FAST invocations (all use structured_chat — no accumulated history):
      1. Speaker ID    (generate_speaker_predictions.py): in = 110 + X, out = ~40
           system (85w) + user_prefix (25w) + transcript (X)
      2. Title         (meeting_title.j2):                in = ~12 + X, out = ~10
           template fixed incl. XML tags (~12w) + transcript (X)
      5. extract_claims (extract_claims.j2):              in = 336 + 0.5X, out = ~0.1X
           template fixed (336w) + draft_minutes (0.5X) — transcript NOT passed
      6. cite_claims   (cite_claims.j2):                  in = 235 + 1.7X, out = ~0.5X
           template fixed (235w) + indexed_transcript (1.1X) + claims (~0.1X) + draft (0.5X)

    BEST invocations:
      3. Minutes       (general.j2 + transcript.j2):      in = 345 + X, out = 0.5X
           chat() with empty history, sends system (~340w) + user (5+X)
      4. Hallucination (hallucination_detection.j2):      in = 17, out = ~80
           structured_chat([17-word question]) — history NOT included
    """
    # FAST: speaker_id + title + extract_claims + cite_claims (input + output words)
    fast_words = (
        (110 + x)
        + 40  # speaker ID
        + (12 + x)
        + 10  # title
        + (336 + 0.5 * x)
        + 0.1 * x  # extract_claims (draft only, no transcript)
        + (235 + 1.7 * x)
        + 0.5 * x  # cite_claims (transcript + claims + draft)
    )
    # BEST: minutes + hallucination
    best_words = (
        (345 + x)
        + 0.5 * x  # minutes (general.j2 system + transcript)
        + 17
        + 80  # hallucination check (17-word question only, no history)
    )
    return _llm_result(fast_words, best_words)


def section_template(x: float = TRANSCRIPT_WORDS, y: int = NUM_SECTIONS) -> dict:
    """
    B.3 — SectionTemplate: Cabinet / PlanningCommittee (5 + 2Y invocations).

    NOTE: No concrete SectionTemplate implementation (Cabinet / PlanningCommittee)
    exists in the codebase as of this audit. The formulas below are derived from
    the protocol definition in common/templates/types.py and the doc's Appendix B.3,
    corrected for the structured_chat / chat() distinction.

    FAST invocations (structured_chat, no history):
      1. Speaker ID:         in = 110 + X, out = ~40
      2. Title:              in = ~12 + X, out = ~10
      3. Section detection   (sections_from_transcript.j2): in = 74 + X, out = ~2Y
           template (69w) + transcript_wrap (5w) + transcript (X)
      6. extract_claims:     in = 336 + 0.3X, out = ~0.06X  (draft = 0.3X for SectionTemplate)
      7. cite_claims:        in = 235 + 1.46X, out = ~0.3X
           template (235w) + indexed_transcript (1.1X) + claims (~0.06X) + draft (0.3X)

    BEST invocations (section generation uses chat() → accumulates history):
      4a. First section:  chat([], [system + section1_prompt(15w)]) → in = system_words + 15
      4b. Each extra section k (k=2..Y): chat(history, [section_k_prompt(15w)])
           history grows by 15w + 0.3X/Y (prior section output) per iteration
          Section k input (context window) = system + k*15 + (k-1)*0.3X/Y
      5.  Hallucination per section (×Y): structured_chat([17w]) — history NOT included

    Total BEST context words sent across all section calls:
      sum_{k=1}^{Y} [system_words + k*15 + (k-1)*0.3X/Y]
      = Y*system + 7.5Y(Y+1) + 0.15X(Y-1)
      where system_words ≈ 345 (general.j2 equiv)
    """
    # FAST
    fast_words = (
        (110 + x)
        + 40  # speaker ID
        + (12 + x)
        + 10  # title
        + (74 + x)
        + 2 * y  # section detection (sections_from_transcript.j2)
        + (336 + 0.3 * x)
        + 0.06 * x  # extract_claims (draft = 0.3X)
        + (235 + 1.46 * x)
        + 0.3 * x  # cite_claims
    )
    # BEST: section generation (chat, accumulates history) + hallucinations (structured_chat, 17w each)
    system_words = 345
    # Sum of context windows across all Y section calls
    section_inputs = y * system_words + 7.5 * y * (y + 1) + 0.15 * x * (y - 1)
    section_outputs = y * (0.3 * x / y)  # = 0.3X total
    hallucination_words = y * (17 + 80)  # structured_chat: 17 in, 80 out, no history
    best_words = section_inputs + section_outputs + hallucination_words
    return _llm_result(fast_words, best_words)


def delivery_template(x: float = TRANSCRIPT_WORDS) -> dict:
    """
    B.4 — Delivery Template (6 invocations).

    Based on actual code: common/templates/default/delivery.py.

    Key facts:
      - Delivery uses a single BEST chatbot for sections + hallucination + attendees.
      - structured_chat() for sections takes the FULL initial_messages list (no prior history).
      - hallucination_check() calls structured_chat([17w]) — history NOT included.
      - attendees call is structured_chat([13w]) — history NOT included.
      - Citations use fresh FAST chatbots via add_citations_to_minute().

    FAST invocations:
      1. Speaker ID:      in = 110 + X, out = ~40
      2. Title:           in = ~12 + X, out = ~10
      5. extract_claims:  in = 336 + 0.4X, out = ~0.08X  (draft = sections text = 0.4X)
      6. cite_claims:     in = 235 + 1.58X, out = ~0.4X
           template (235w) + indexed_transcript (1.1X) + claims (~0.08X) + draft (0.4X)

    BEST invocations (all independent structured_chat calls — no history passed):
      3. Sections+Actions: structured_chat([system(25w), user(5+X), sections_msg(156w)])
           in = 186 + X  [system(25) + transcript_wrap(5) + sections_msg(43) + style_guide(113)]
           out = ~0.4X
      4. Hallucination:    structured_chat([17w]) — history NOT included, in = 17, out = 80
      5. Attendees:        structured_chat([13w])  — history NOT included, in = 13, out = 30
    """
    # FAST
    fast_words = (
        (110 + x)
        + 40  # speaker ID
        + (12 + x)
        + 10  # title
        + (336 + 0.4 * x)
        + 0.08 * x  # extract_claims (draft = sections text ~0.4X)
        + (235 + 1.58 * x)
        + 0.4 * x  # cite_claims
    )
    # BEST
    best_words = (
        (186 + x)
        + 0.4 * x  # sections+actions (full message list sent directly)
        + 17
        + 80  # hallucination (structured_chat, no history)
        + 13
        + 30  # attendees    (structured_chat, no history)
    )
    return _llm_result(fast_words, best_words)


def basic_minutes(x: float = TRANSCRIPT_WORDS) -> dict:
    """
    B.5 — Basic Minutes fallback (4 FAST-only invocations).

    Based on actual code: common/services/minute_handler_service.py,
    common/prompts.py, common/prompt_templates/basic_minutes.j2.

    Key facts:
      - Speaker ID and Title use fresh chatbots (structured_chat, no history).
      - Basic summary uses chatbot.chat() — sends empty history + [system, user+transcript].
      - Hallucination uses structured_chat([17w]) — history NOT included.

    FAST invocations:
      1. Speaker ID:     in = 110 + X, out = ~40
           system (85w: generate_speaker_predictions.py) + user_prefix (25w) + transcript (X)
      2. Title:          in = ~12 + X, out = ~10
           meeting_title.j2 fixed (~12w incl. XML tags) + transcript (X)
      3. Basic summary:  in = 12 + X, out = ~0.3X
           chat([system(7w: basic_minutes.j2), user(5+X: transcript.j2)])
           — first call on fresh chatbot, so history is empty (no prepended messages)
      4. Hallucination:  in = 17, out = ~80
           structured_chat([17-word question]) — history NOT included despite prior chat()

    Note: the doc's B.5 summary says "25 + X" for inv 3 input and "43 + 1.3X" for inv 4 —
    these assume the hallucination check includes the accumulated context, which it does not.
    Actual: inv 3 fixed = 12w (7 system + 5 transcript wrapper), inv 4 = 17w.
    """
    fast_words = (
        (110 + x)
        + 40  # speaker ID
        + (12 + x)
        + 10  # title
        + (12 + x)
        + 0.3 * x  # basic summary (chat, empty history, system+transcript)
        + 17
        + 80  # hallucination (structured_chat, 17 words only)
    )
    return _llm_result(fast_words, best_words=0)


def executive_summary(x: float = TRANSCRIPT_WORDS) -> dict:
    """
    B.2a — Short 'n' Sweet / ExecutiveSummary (4 invocations, no citations).

    ExecutiveSummary (common/templates/default/executive_summary.py) is a SimpleTemplate
    subclass with citations_required=False — extract_claims and cite_claims are skipped.

    System prompt is executive_summary.j2 (EXEC_SUMMARY_SYSTEM_WORDS = 129w), NOT general.j2.
    hallucination_check() calls structured_chat([17w question]) — history NOT included.

    FAST invocations (structured_chat, no history):
      1. Speaker ID  (generate_speaker_predictions.py): in = 110 + X, out = ~40
      2. Title       (generate_meeting_title.py / meeting_title.j2): in = 12 + X, out = ~10

    BEST invocations:
      3. Minutes (executive_summary.j2 + transcript.j2):
           chat() on fresh chatbot: system (129w) + user (5+X from get_transcript_messages)
           in = 134 + X, out = ~0.3X  (short summary, not full minutes)
      4. Hallucination (hallucination_detection.j2): in = 17, out = ~80
           structured_chat([17-word question]) — history NOT included
    """
    fast_words = (110 + x) + 40 + (12 + x) + 10  # speaker ID + title
    best_words = (EXEC_SUMMARY_SYSTEM_WORDS + 5 + x) + 0.3 * x + 17 + 80  # minutes + hallucination
    return _llm_result(fast_words, best_words)


def user_template_document(x: float = TRANSCRIPT_WORDS) -> dict:
    """
    B.6.1 — UserTemplate (DOCUMENT type): 4 invocations (2 FAST + 2 BEST).

    Source: common/templates/user_template.py, generate_user_template() — DOCUMENT branch.

    System prompt = document_prompt string (lines 9-36 of user_template.py):
      - DOCUMENT_PROMPT_FIXED_WORDS (115w) fixed text, excluding {template} and {date} values
      - USER_TEMPLATE_CONTENT_WORDS (200w) user-defined template content (varies in practice)
      - DOCUMENT_DATE_WORDS (7w) for the formatted datetime string
      Total system ≈ 115 + 200 + 7 = 322w
    hallucination_check() calls structured_chat([17w question]) — history NOT included.

    FAST invocations (structured_chat, no history):
      1. Speaker ID  (generate_speaker_predictions.py): in = 110 + X, out = ~40
      2. Title       (generate_meeting_title.py / meeting_title.j2): in = 12 + X, out = ~10

    BEST invocations:
      3. Document gen (document_prompt system + transcript.j2 user):
           chat() on fresh chatbot: system (322w) + user (5+X from get_transcript_messages)
           in = 327 + X, out = ~0.5X
      4. Hallucination (hallucination_detection.j2): in = 17, out = ~80
           structured_chat([17-word question]) — history NOT included
    """
    doc_system_words = DOCUMENT_PROMPT_FIXED_WORDS + USER_TEMPLATE_CONTENT_WORDS + DOCUMENT_DATE_WORDS
    fast_words = (110 + x) + 40 + (12 + x) + 10  # speaker ID + title
    best_words = (doc_system_words + 5 + x) + 0.5 * x + 17 + 80  # doc gen + hallucination
    return _llm_result(fast_words, best_words)


# =============================================================================
# APPENDIX F.2: USAGE-WEIGHTED IMPACT
# Production usage shares (December 2024 – May 2026, Appendix F.1)
# =============================================================================

# (template_name, production_share, implementation)
# Shares sum to 1.0.
# Lowercase variants (general, delivery, cabinet) are the same built-in templates
# as their capitalised counterparts — combined here with their shares merged.
TEMPLATE_USAGE_SHARES: list[tuple[str, float, str]] = [
    ("General", 0.5241, "SimpleTemplate"),  # General 51.32% + general 1.09%
    ("Delivery", 0.1523, "DeliveryTemplate"),  # Delivery 14.83% + delivery 0.40%
    ("Short 'n' Sweet", 0.1234, "ExecutiveSummary (SimpleTemplate, no citations)"),
    ("User generated", 0.0960, "UserTemplate DOCUMENT"),
    ("Cabinet", 0.0589, "SectionTemplate (Y=6)"),  # Cabinet 5.58% + cabinet 0.31%
    ("Care Assessment", 0.0261, "SimpleTemplate (deprecated v1, assumed)"),
    ("Planning Committee", 0.0120, "SectionTemplate (Y=6)"),
    ("Care Assessment V2", 0.0073, "SimpleTemplate"),
]


def _template_result(name: str, x: float, y: int = NUM_SECTIONS) -> dict:
    """Map a production template name to its calculated LLM result."""
    simple = simple_template(x)
    section = section_template(x, y)
    deliv = delivery_template(x)
    exec_s = executive_summary(x)
    user_d = user_template_document(x)

    mapping: dict[str, dict] = {
        "General": simple,
        "Delivery": deliv,
        "Short 'n' Sweet": exec_s,
        "User generated": user_d,
        "Cabinet": section,
        "Care Assessment": simple,  # deprecated v1, assumed equivalent to SimpleTemplate
        "Planning Committee": section,
        "Care Assessment V2": simple,
    }
    return mapping[name]


def usage_weighted_impact(x: float = TRANSCRIPT_WORDS, y: int = NUM_SECTIONS) -> dict:
    """
    F.2.3 — Compute usage-weighted average LLM impact across all production templates.

    Applies the production usage shares from TEMPLATE_USAGE_SHARES to the
    per-template token and energy calculations.
    """
    weighted_tokens = 0.0
    weighted_wh = 0.0
    weighted_co2e = 0.0

    for name, share, _ in TEMPLATE_USAGE_SHARES:
        r = _template_result(name, x, y)
        weighted_tokens += share * r["total_tokens"]
        weighted_wh += share * r["total_wh"]
        weighted_co2e += share * r["co2e_g"]

    return {
        "total_tokens": weighted_tokens,
        "total_wh": weighted_wh,
        "co2e_g": weighted_co2e,
    }


# =============================================================================
# SECTION 8: COMBINED IMPACT (Transcription + LLM)
# =============================================================================


def combined_impact(llm: dict, asr: dict) -> dict:
    total_energy_wh = llm["total_wh"] + asr["energy_wh"]
    # Use EU-27 recalculated CO₂e for transcription so percentages are consistent
    total_co2e_g = llm["co2e_g"] + asr["co2e_g_eu27"]
    asr_pct = 100 * asr["co2e_g_eu27"] / total_co2e_g
    llm_pct = 100 * llm["co2e_g"] / total_co2e_g
    return {
        "total_energy_wh": total_energy_wh,
        "total_co2e_g": total_co2e_g,
        "asr_pct": asr_pct,
        "llm_pct": llm_pct,
    }


# =============================================================================
# SECTION 10 / APPENDIX C: LLM TRAINING IMPACT (per user)
# =============================================================================


def llm_training_impact() -> dict:
    gpt4_training_kwh = GPT4_TRAINING_MWH * 1_000
    gpt4o_training_kwh = GPT4O_TRAINING_MWH * 1_000

    # Amortise over user base
    gpt4_per_user_kwh = gpt4_training_kwh / LLM_USER_BASE
    gpt4o_per_user_kwh = gpt4o_training_kwh / LLM_USER_BASE

    gpt4_per_user_wh = gpt4_per_user_kwh * 1_000
    gpt4o_per_user_wh = gpt4o_per_user_kwh * 1_000

    gpt4_co2e_g = gpt4_per_user_kwh * TRAINING_CARBON_INTENSITY_G_PER_KWH
    gpt4o_co2e_g = gpt4o_per_user_kwh * TRAINING_CARBON_INTENSITY_G_PER_KWH

    llm_total_wh = gpt4_per_user_wh + gpt4o_per_user_wh
    llm_total_co2e = gpt4_co2e_g + gpt4o_co2e_g

    return {
        "gpt4_training_kwh": gpt4_training_kwh,
        "gpt4o_training_kwh": gpt4o_training_kwh,
        "gpt4_per_user_wh": gpt4_per_user_wh,
        "gpt4o_per_user_wh": gpt4o_per_user_wh,
        "gpt4_co2e_g": gpt4_co2e_g,
        "gpt4o_co2e_g": gpt4o_co2e_g,
        "llm_total_wh": llm_total_wh,
        "llm_total_co2e": llm_total_co2e,
    }


# =============================================================================
# APPENDIX D: ASR (OWSM v3) TRAINING IMPACT
# =============================================================================


def asr_training_impact() -> dict:
    # Tier 1: GPU energy only
    gpu_energy_kwh = OWSM_GPU_COUNT * OWSM_GPU_TDP_W * 24 * OWSM_TRAINING_DAYS / 1_000

    # Tier 2: Add system overhead (CPU, memory, networking, storage)
    non_gpu_midpoint_w = (OWSM_SERVER_NON_GPU_LOW_W + OWSM_SERVER_NON_GPU_HIGH_W) / 2
    system_overhead_fraction = non_gpu_midpoint_w / OWSM_SERVER_GPU_DRAW_W
    system_energy_kwh = gpu_energy_kwh * (1 + system_overhead_fraction)

    # Tier 3: Apply PUE (cooling, power distribution, lighting)
    total_energy_kwh = system_energy_kwh * OWSM_PUE

    # Amortise over ASR user base
    per_user_kwh = total_energy_kwh / ASR_USER_BASE
    per_user_wh = per_user_kwh * 1_000
    co2e_g = per_user_kwh * TRAINING_CARBON_INTENSITY_G_PER_KWH

    return {
        "gpu_energy_kwh": gpu_energy_kwh,
        "non_gpu_midpoint_w": non_gpu_midpoint_w,
        "system_overhead_fraction": system_overhead_fraction,
        "system_energy_kwh": system_energy_kwh,
        "total_energy_kwh": total_energy_kwh,
        "per_user_wh": per_user_wh,
        "co2e_g": co2e_g,
    }


# =============================================================================
# REPORTING
# =============================================================================


def print_results() -> None:
    asr = transcription_impact()
    st = simple_template()
    sec = section_template()
    dv = delivery_template()
    bm = basic_minutes()
    es = executive_summary()
    utd = user_template_document()
    llm_t = llm_training_impact()
    asr_t = asr_training_impact()
    wt = usage_weighted_impact()

    print("\nENVIRONMENTAL IMPACT ASSESSMENT — Local Transcribe")
    print(
        f"Assumptions: X={TRANSCRIPT_WORDS:,} words  |  Y={NUM_SECTIONS} sections  |  " f"{TOKENS_PER_WORD} tokens/word"
    )
    print(
        f"Carbon intensity: inference={INFERENCE_CARBON_INTENSITY_G_PER_KWH} g/kWh  |  "
        f"training={TRAINING_CARBON_INTENSITY_G_PER_KWH} g/kWh"
    )

    # ── Section 6: Transcription ──────────────────────────────────────────────
    _section("Section 6: Transcription (1-hour meeting)")
    _row("Source: total energy over study", f"{ASR_STUDY_TOTAL_ENERGY_KWH} kWh / {ASR_STUDY_AUDIO_HOURS} hours")
    _row(
        "Energy per hour",
        f"{ASR_STUDY_TOTAL_ENERGY_KWH * 1000} Wh / {ASR_STUDY_AUDIO_HOURS} h"
        f"  = {asr['energy_wh']:.2f} Wh  ({asr['energy_wh'] / 1000:.4f} kWh)",
    )
    _row(
        "CO₂e (study carbon intensity)",
        f"{ASR_STUDY_TOTAL_CO2E_G} g / {ASR_STUDY_AUDIO_HOURS} h" f"  = {asr['co2e_g_study']:.2f} g",
    )
    _row(
        "CO₂e (EU-27, used in combined totals)",
        f"{asr['energy_wh']:.2f} Wh × {INFERENCE_CARBON_INTENSITY_G_PER_KWH} g/kWh / 1000"
        f"  = {asr['co2e_g_eu27']:.2f} g",
    )

    # ── Section 7: LLM per template ──────────────────────────────────────────
    fast_wh_per_tok = GPT4O_BENCHMARK_WH / GPT4O_BENCHMARK_TOKENS
    best_wh_per_tok = GPT4_TURBO_BENCHMARK_WH / GPT4_TURBO_BENCHMARK_TOKENS

    templates = [
        ("Section 7.1: SimpleTemplate", st, "6"),
        (f"Section 7.2: SectionTemplate Y={NUM_SECTIONS}", sec, f"5+2×{NUM_SECTIONS}={5+2*NUM_SECTIONS}"),
        ("Section 7.3: Delivery Template", dv, "6"),
        ("Section 7.4: Basic Minutes (fallback)", bm, "4"),
    ]

    for title, r, inv in templates:
        _section(f"{title}  [{inv} invocations]")
        _row("FAST (GPT-4o) tokens", f"{r['fast_tokens']:,.0f}")
        _row("BEST (GPT-4 Turbo) tokens", f"{r['best_tokens']:,.0f}")
        _row("Total tokens", f"{r['total_tokens']:,.0f}")
        _row("FAST energy", f"{r['fast_tokens']:,.0f} × {fast_wh_per_tok:.6f} Wh/token" f"  = {r['fast_wh']:.2f} Wh")
        _row("BEST energy", f"{r['best_tokens']:,.0f} × {best_wh_per_tok:.6f} Wh/token" f"  = {r['best_wh']:.2f} Wh")
        _row(
            "Total LLM energy",
            f"{r['fast_wh']:.2f} + {r['best_wh']:.2f}" f"  = {r['total_wh']:.2f} Wh  ({r['total_wh'] / 1000:.4f} kWh)",
        )
        _row(
            "CO₂e",
            f"{r['total_wh']:.2f} Wh / 1000 × {INFERENCE_CARBON_INTENSITY_G_PER_KWH} g/kWh" f"  = {r['co2e_g']:.1f} g",
        )

    # ── Section 7.6: Template comparison ─────────────────────────────────────
    _section("Section 7.6: Template Comparison Summary")
    print(f"  {'Template':<34} {'Invocations':>11} {'Tokens':>10} {'Energy':>12} {'CO₂e':>8}")
    print(f"  {'-'*34} {'-'*11} {'-'*10} {'-'*12} {'-'*8}")
    rows = [
        ("Basic Minutes", "4", bm),
        ("Short 'n' Sweet (no citations)", "4", es),
        ("UserTemplate DOCUMENT", "4", utd),
        ("Delivery", "6", dv),
        ("SimpleTemplate", "6", st),
        (f"SectionTemplate Y={NUM_SECTIONS}", f"5+2×{NUM_SECTIONS}={5+2*NUM_SECTIONS}", sec),
    ]
    for name, inv, r in rows:
        print(f"  {name:<34} {inv:>11} {r['total_tokens']:>10,.0f}" f" {r['total_wh']:>9.1f} Wh {r['co2e_g']:>6.1f} g")

    # ── Section 8: Combined impact ────────────────────────────────────────────
    _section("Section 8: Combined Impact per 1-Hour Meeting")
    print("  (Transcription CO₂e recalculated at EU-27 intensity for consistent percentages)\n")
    print(f"  {'Template':<30} {'Energy':>12} {'CO₂e':>8} {'ASR%':>6} {'LLM%':>6}")
    print(f"  {'-'*30} {'-'*12} {'-'*8} {'-'*6} {'-'*6}")
    for name, _, r in rows:
        c = combined_impact(r, asr)
        print(
            f"  {name:<30} {c['total_energy_wh']:>9.1f} Wh {c['total_co2e_g']:>6.1f} g"
            f" {c['asr_pct']:>5.1f}% {c['llm_pct']:>5.1f}%"
        )

    # ── Appendix F.2: Usage-weighted impact ──────────────────────────────────
    _section("Appendix F.2: Usage-Weighted Impact (production shares, Dec 2024–May 2026)")
    print(f"  {'Template':<28} {'Share':>6} {'Impl.':<38} {'LLM Wh':>8} {'CO₂e':>7}")
    print(f"  {'-'*28} {'-'*6} {'-'*38} {'-'*8} {'-'*7}")
    for tname, share, impl in TEMPLATE_USAGE_SHARES:
        r = _template_result(tname, TRANSCRIPT_WORDS)
        print(f"  {tname:<28} {share:>5.1%} {impl:<38} {r['total_wh']:>8.1f} {r['co2e_g']:>6.1f}g")
    print()
    wt_combined = combined_impact(wt, asr)
    _row("Usage-weighted LLM energy", f"{wt['total_wh']:.1f} Wh  ({wt['total_wh'] / 1000:.4f} kWh)")
    _row("Usage-weighted LLM CO₂e", f"{wt['co2e_g']:.1f} g")
    _row("+ Transcription (EU-27)", f"{asr['energy_wh']:.1f} Wh  /  {asr['co2e_g_eu27']:.1f} g")
    _row(
        "Usage-weighted TOTAL energy",
        f"{wt_combined['total_energy_wh']:.1f} Wh  ({wt_combined['total_energy_wh'] / 1000:.4f} kWh)",
    )
    _row("Usage-weighted TOTAL CO₂e", f"{wt_combined['total_co2e_g']:.1f} g")

    # ── Appendix C: LLM training ──────────────────────────────────────────────
    _section("Appendix C: LLM Training Impact (per user, amortised)")
    _row("GPT-4 training total", f"{GPT4_TRAINING_MWH:,} MWh = {llm_t['gpt4_training_kwh']:,.0f} kWh")
    _row(
        "GPT-4 per-user energy",
        f"{llm_t['gpt4_training_kwh']:,.0f} kWh / {LLM_USER_BASE:,}" f"  = {llm_t['gpt4_per_user_wh']:.2f} Wh",
    )
    _row(
        "GPT-4 per-user CO₂e",
        f"{llm_t['gpt4_per_user_wh']:.2f} Wh / 1000 × {TRAINING_CARBON_INTENSITY_G_PER_KWH} g/kWh"
        f"  = {llm_t['gpt4_co2e_g']:.2f} g",
    )
    print()
    _row("GPT-4o training total", f"{GPT4O_TRAINING_MWH:,} MWh = {llm_t['gpt4o_training_kwh']:,.0f} kWh")
    _row(
        "GPT-4o per-user energy",
        f"{llm_t['gpt4o_training_kwh']:,.0f} kWh / {LLM_USER_BASE:,}" f"  = {llm_t['gpt4o_per_user_wh']:.4f} Wh",
    )
    _row(
        "GPT-4o per-user CO₂e",
        f"{llm_t['gpt4o_per_user_wh']:.4f} Wh / 1000 × {TRAINING_CARBON_INTENSITY_G_PER_KWH} g/kWh"
        f"  = {llm_t['gpt4o_co2e_g']:.4f} g",
    )
    print()
    _row(
        "LLM combined per-user energy",
        f"{llm_t['gpt4_per_user_wh']:.2f} + {llm_t['gpt4o_per_user_wh']:.4f}" f"  = {llm_t['llm_total_wh']:.2f} Wh",
    )
    _row(
        "LLM combined per-user CO₂e",
        f"{llm_t['gpt4_co2e_g']:.2f} + {llm_t['gpt4o_co2e_g']:.4f}" f"  = {llm_t['llm_total_co2e']:.2f} g",
    )

    # ── Appendix D: OWSM ASR training ─────────────────────────────────────────
    _section("Appendix D: ASR Training Impact — OWSM v3 proxy (per user)")
    _row(
        "Tier 1 — GPU energy",
        f"{OWSM_GPU_COUNT} GPUs × {OWSM_GPU_TDP_W}W × 24h × {OWSM_TRAINING_DAYS}d / 1000"
        f"  = {asr_t['gpu_energy_kwh']:,.0f} kWh",
    )
    _row(
        "Non-GPU overhead (midpoint)",
        f"({OWSM_SERVER_NON_GPU_LOW_W}+{OWSM_SERVER_NON_GPU_HIGH_W}) / 2"
        f"  = {asr_t['non_gpu_midpoint_w']:.0f} W"
        f"  →  fraction = {asr_t['non_gpu_midpoint_w']:.0f} / {OWSM_SERVER_GPU_DRAW_W}"
        f"  = {asr_t['system_overhead_fraction']:.4f}",
    )
    _row(
        "Tier 2 — + system overhead",
        f"{asr_t['gpu_energy_kwh']:,.0f} × (1 + {asr_t['system_overhead_fraction']:.4f})"
        f"  = {asr_t['system_energy_kwh']:,.0f} kWh",
    )
    _row(
        "Tier 3 — + PUE", f"{asr_t['system_energy_kwh']:,.0f} × {OWSM_PUE}" f"  = {asr_t['total_energy_kwh']:,.0f} kWh"
    )
    _row(
        "Per-user energy",
        f"{asr_t['total_energy_kwh']:,.0f} kWh / {ASR_USER_BASE:,} × 1000" f"  = {asr_t['per_user_wh']:.4f} Wh",
    )
    _row(
        "Per-user CO₂e",
        f"{asr_t['per_user_wh']:.4f} Wh / 1000 × {TRAINING_CARBON_INTENSITY_G_PER_KWH} g/kWh"
        f"  = {asr_t['co2e_g']:.4f} g",
    )

    # ── Section 10.2: Training vs inference ──────────────────────────────────
    system_training_wh = llm_t["llm_total_wh"] + asr_t["per_user_wh"]
    system_training_co2e = llm_t["llm_total_co2e"] + asr_t["co2e_g"]
    simple_combined = combined_impact(st, asr)
    ratio = simple_combined["total_energy_wh"] / system_training_wh

    _section("Section 10.2: Training vs Inference (SimpleTemplate baseline)")
    _row(
        "System training total per user",
        f"{llm_t['llm_total_wh']:.2f} + {asr_t['per_user_wh']:.4f}"
        f"  = {system_training_wh:.2f} Wh  /  {system_training_co2e:.2f} g CO₂e",
    )
    _row(
        "1-hour SimpleTemplate meeting",
        f"{simple_combined['total_energy_wh']:.2f} Wh  /  {simple_combined['total_co2e_g']:.2f} g CO₂e",
    )
    _row(
        "Inference / training ratio",
        f"{simple_combined['total_energy_wh']:.2f} / {system_training_wh:.2f}" f"  = {ratio:.1f}×",
    )
    print()


if __name__ == "__main__":
    print_results()
