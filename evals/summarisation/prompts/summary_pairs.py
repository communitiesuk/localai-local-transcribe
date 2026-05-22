"""
evals/summarisation/fixtures/summary_pairs.py
=============================================
Reference fixtures for manual and automated judge testing.

Each entry contains a transcript excerpt, a GOOD summary (expected ≥ 4 on
the primary dimension) and a BAD summary (expected ≤ 2), along with expected
score bounds used by the live test suite.

All scenarios are grounded in realistic Local Authority housing / social care
contexts and mirror the worked examples in AIILG-457 HLD sections 3.1.a-h.
"""

from __future__ import annotations

from typing import TypedDict


class SummaryFixture(TypedDict):
    description: str
    transcript: str
    good_summary: str
    bad_summary: str
    primary_dimension: str
    good_expected_min_score: int
    bad_expected_max_score: int


FIXTURES: dict[str, SummaryFixture] = {
    # ── D1: ACCURACY ─────────────────────────────────────────────────────────
    "accuracy_nhs_referral": {
        "description": (
            "Good summary correctly attributes the NHS Maudsley referral and "
            "condition. Bad summary fabricates a dental appointment."
        ),
        "transcript": (
            "Housing Officer (00:34:12): Right, so we agreed that Mr Okafor "
            "would be referred to NHS Maudsley Hospital for a further assessment "
            "of his bipolar condition. That referral will be arranged by the "
            "Haringey Local Authority caseworker before the next meeting, which "
            "is scheduled for 21 July.\n"
            "Customer (00:34:45): Yes, that's correct. I understand."
        ),
        "good_summary": (
            "Personal Housing Plan — Emmanuel Okafor\n"
            "Reference: HAR-2026-00412\n\n"
            "The customer agreed to a further assessment of his bipolar condition "
            "by the NHS Maudsley Hospital, to be arranged by the Haringey Local "
            "Authority caseworker before the next meeting on 21 July."
        ),
        "bad_summary": (
            "Personal Housing Plan — Emmanuel Okafor\n"
            "Reference: HAR-2026-00412\n\n"
            "The customer consented to a dental health check-up following his "
            "decision to quit his job and retrain as a dental technician. A "
            "referral to a community clinic was discussed."
        ),
        "primary_dimension": "accuracy",
        "good_expected_min_score": 4,
        "bad_expected_max_score": 2,
    },
    # ── D2: NUMERICAL ACCURACY ────────────────────────────────────────────────
    "numerical_accuracy_deadlines": {
        "description": (
            "Good summary reproduces the exact date (12 May 2026), time (14:30), "
            "and reference number (HB-88142). Bad summary shifts the deadline "
            "and vagues up the appointment time."
        ),
        "transcript": (
            "Housing Officer (00:15:22): So you need to bring proof of address — "
            "deadline of 12 May 2026. And the follow-up appointment is booked for "
            "22 May at 14:30, reference number HB-88142.\n"
            "Customer (00:15:40): Got it, 12 May for the documents, and I'll be "
            "there at half two on the 22nd."
        ),
        "good_summary": (
            "Actions\n"
            "1. Customer to provide proof of address by 12 May 2026.\n"
            "2. Follow-up appointment confirmed for 22 May 2026 at 14:30 "
            "(ref: HB-88142)."
        ),
        "bad_summary": (
            "Actions\n"
            "1. Customer to provide proof of address by 15 May.\n"
            "2. A follow-up appointment was booked for the following week "
            "in the afternoon."
        ),
        "primary_dimension": "numerical_accuracy",
        "good_expected_min_score": 4,
        "bad_expected_max_score": 2,
    },
    # ── D3: TEMPLATE FIT ──────────────────────────────────────────────────────
    "template_fit_php": {
        "description": (
            "Personal Housing Plan template requires reference, DOB, background, "
            "incident, and actions sections. Good fills all; bad is a free-form "
            "fragment missing required fields."
        ),
        "transcript": (
            "Housing Officer (00:02:10): Let's go through Mr Martins's Personal "
            "Housing Plan. Reference 6655321b, date of birth 14 February 1989.\n"
            "Housing Officer (00:04:30): On 2 April the police were called by the "
            "neighbour after items were thrown over the fence and discriminatory "
            "abuse was shouted.\n"
            "Housing Officer (00:10:00): Actions: customer to attend anger "
            "management assessment by 5 May; Housing Officer to review tenancy "
            "conditions by 19 May."
        ),
        "good_summary": (
            "4. Personal Housing Plan — Jeff Martins\n"
            "4.1 Reference: 6655321b\n"
            "4.2 Customer DOB: 14 February 1989\n\n"
            "Background\n"
            "The customer's PHP was reviewed at the meeting.\n\n"
            "Incident (2 April 2026)\n"
            "On 2 April, police were called by the next-door neighbour after the "
            "customer was observed throwing items over the fence and shouting "
            "discriminatory abuse.\n\n"
            "Actions\n"
            "1. Customer to attend anger management assessment by 5 May 2026.\n"
            "2. Housing Officer to review tenancy conditions by 19 May 2026."
        ),
        "bad_summary": (
            "PHP for customer 6655321 Martins J DOB 14/2/89. Stuff happened with "
            "the neighbour, police called. Actions assigned to various parties."
        ),
        "primary_dimension": "template_fit",
        "good_expected_min_score": 4,
        "bad_expected_max_score": 2,
    },
    # ── D4: COVERAGE ──────────────────────────────────────────────────────────
    "coverage_machete_incident": {
        "description": (
            "Material facts — 999 call, machete, bus, arrest, bail — must all "
            "appear. Bad summary reduces a serious incident to vague 'tension'."
        ),
        "transcript": (
            "Social Worker (00:08:15): The meeting covered the incident on 2 "
            "April. A woman on a bus called 999 after the customer was reported "
            "to be ripping up seats with a machete. Police attended and the "
            "customer was arrested and bailed pending further investigation.\n"
            "Customer (00:09:00): I wasn't doing anything wrong.\n"
            "Social Worker (00:09:10): That's noted and it's been recorded."
        ),
        "good_summary": (
            "The meeting confirmed that on 2 April police were called following a "
            "999 call by a woman on a bus who alleged that the customer had been "
            "ripping up the seats with a machete. The customer was arrested and "
            "bailed to await further investigation."
        ),
        "bad_summary": (
            "The meeting was a general catch-up about the customer's wellbeing. "
            "He said he had been a bit tense of late and the team discussed "
            "supporting him going forward."
        ),
        "primary_dimension": "coverage",
        "good_expected_min_score": 4,
        "bad_expected_max_score": 2,
    },
    # ── D5: ACTION CLARITY ────────────────────────────────────────────────────
    "action_clarity_three_actions": {
        "description": (
            "Three actions with explicit owners and deadlines. " "Bad summary is vague with no owners or dates."
        ),
        "transcript": (
            "Housing Officer (00:22:10): So three actions from today. First, the "
            "customer to report to me on CBT progress by 12 May. Second, "
            "Occupational Health to complete the risk assessment to confirm "
            "eligibility. Third, we'll book a second meeting for 22 May. Agreed?\n"
            "Customer (00:22:35): Agreed."
        ),
        "good_summary": (
            "Actions\n"
            "1. Customer to report to Housing Officer on CBT progress by 12 May "
            "2026.\n"
            "2. Occupational Health to complete risk assessment to confirm "
            "customer eligibility (deadline to be confirmed by Occupational "
            "Health).\n"
            "3. Second meeting to be booked for 22 May 2026."
        ),
        "bad_summary": (
            "The meeting discussed the customer's substance use. Some actions "
            "were assigned to various team members. Further steps will be "
            "taken as needed."
        ),
        "primary_dimension": "action_clarity",
        "good_expected_min_score": 4,
        "bad_expected_max_score": 2,
    },
    # ── D6a: PROFESSIONAL TONE (neutral paraphrase) ───────────────────────────
    "professional_tone_paraphrase": {
        "description": (
            "Casual aggression should be paraphrased neutrally. "
            "Bad summary reproduces slang verbatim where paraphrase is better."
        ),
        "transcript": (
            "Housing Officer (00:45:00): The customer became agitated when the "
            "tenancy review was mentioned.\n"
            "Customer (00:45:10): Yow, yuh a chat seh mi foolish? Watch yuhself.\n"
            "Housing Officer (00:45:20): I've noted that and recorded it for "
            "the file."
        ),
        "good_summary": (
            "The customer became agitated when the tenancy review was raised and "
            "made a dismissive remark directed at the Housing Officer. The comment "
            "was noted and recorded on file."
        ),
        "bad_summary": (
            'The customer said "Yow, yuh a chat seh mi foolish? Watch yuhself" '
            "when the tenancy review was mentioned. He seemed quite annoyed "
            "and rude."
        ),
        "primary_dimension": "professional_tone",
        "good_expected_min_score": 4,
        "bad_expected_max_score": 2,
    },
    # ── D6b: PROFESSIONAL TONE (material quote retention) ─────────────────────
    "professional_tone_direct_threat": {
        "description": (
            "A direct threat is materially relevant to safeguarding and must be "
            "quoted exactly. Bad summary paraphrases in a way that loses severity."
        ),
        "transcript": (
            "Customer (00:51:30): Shut up about that or I'll break both your legs.\n"
            "Housing Officer (00:51:35): That's a direct threat and I'm escalating."
        ),
        "good_summary": (
            "The customer stated, \"shut up about that or I'll break both your "
            'legs", which was recorded as a direct threat and escalated due to '
            "safeguarding concerns."
        ),
        "bad_summary": (
            "The customer became upset and used aggressive language, which was "
            "escalated accordingly. The Housing Officer noted the customer's "
            "frustration."
        ),
        "primary_dimension": "professional_tone",
        "good_expected_min_score": 4,
        "bad_expected_max_score": 2,
    },
    # ── D7: READABILITY ───────────────────────────────────────────────────────
    "readability_render_safe": {
        "description": (
            "Output must be render-safe plain text following the template. "
            "Bad summary contains raw JSON and broken HTML artefacts."
        ),
        "transcript": (
            "Housing Officer (00:03:00): Reference 6655321b. Date of birth "
            "14 February 1989.\n"
            "Housing Officer (00:03:30): Two actions: Housing Officer to share "
            "application guidance with the customer; customer to send proof of "
            "address by 12 May."
        ),
        "good_summary": (
            "4. Personal Housing Plan — Jeff Martins\n"
            "4.1 Reference: 6655321b\n"
            "4.2 Customer DOB: 14 February 1989\n\n"
            "Actions\n"
            "1. Housing Officer to share application guidance with the customer.\n"
            "2. Customer to send proof of address by 12 May 2026."
        ),
        "bad_summary": (
            '{"ref":"6655321b","dob":"14/2/89","actions":["share guidance",'
            '"proof of address by 12 May"]} '
            "See .cust3627b.docx paragraphs 6 & 7. "
            "<br/><b>TODO: fill in background section</b>"
        ),
        "primary_dimension": "readability",
        "good_expected_min_score": 4,
        "bad_expected_max_score": 2,
    },
    # ── D8: AUDITABILITY (CITATION ACCURACY / COHERENCE) ──────────────────────────────────────────────────────
    "auditability_timestamps": {
        "description": (
            "Claims must be attributed to speakers with accurate timestamps. "
            "Bad summary uses inaccurate attributions and omits all attribution."
        ),
        "transcript": (
            "Housing Officer (00:34:12): I can confirm the customer's application "
            "has been signed off by the assessor on 3 April 2026.\n"
            "Customer (00:34:50): That's a relief, thank you."
        ),
        "good_summary": (
            "The Housing Officer (00:34:12) confirmed that the customer's "
            "application had been signed off by the assessor on 3 April 2026. "
            "The customer acknowledged the update."
        ),
        "bad_summary": (
            "The Housing Officer said his application was going okay and "
            "things were moving in the right direction. There were no "
            "issues flagged at this stage."
        ),
        "primary_dimension": "auditability",
        "good_expected_min_score": 4,
        "bad_expected_max_score": 2,
    },
}
