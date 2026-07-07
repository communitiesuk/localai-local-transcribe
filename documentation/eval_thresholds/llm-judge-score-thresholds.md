# LLM-as-judge score thresholds: pass, review, and fail bands

Jira ticket: AIILG-678

**All threshold values are placeholders until calibrated.**

## 1. Background

LocalTranscribe provides users with AI-generated summaries of audio transcripts. Evaluation of these summaries includes LLM-as-a-judge scoring across eight quality dimensions, each scored on a 1 to 5 scale. This document aims to provide a basis for what score should consitute a pass, review or fail outcome for each dimension.

The dimensions are defined in `[evals/summarisation/src/constants.py](../evals/summarisation/src/constants.py)` and the rubrics live in `[evals/summarisation/prompts/rubrics/](../evals/summarisation/prompts/rubrics/)`.

The summaries generated using LocalTranscribe can be edited and exported by users for downstream use. The app itself does not file output into a case management system or create a statutory record. However a user can adopt a draft into statutory documentation. An example use case is a housing officer drafting a Personal Housing Plan. Under section 189A of the Housing Act 1996 a plan must be assessed, recorded in writing, given to the applicant, and kept under review [8]. Therefore, an error that survives human review can enter a statutory record through the person who adopts the draft. 

The purpose of this documentaton is to propose thresholds based on the risks and potential consequences associated with a poor score for a given dimension. This is the method recommended for choosing thresholds for LLM evaluation metrics, i.e. start from the consequences of a poor score and the level of risk the team will accept, then pick the number [2]. 

Furthermore, LLMs are imperfect instruments that carry biases. Consequently, before putting into practice, thresholds must first be calibrated by checking LLM judge scores against human scores for summaries based on real transcripts [2][3][4]. Hence all thresholds proposed here are placeholders until calibrated.

## 2 Identified risks per dimension


| Dimension            | Worst realistic harm from a low score                                                                                                                   | Reversible?                                                                                                                        | Will a reviewer catch it unaided?                                                                                                                        | Risk level                                                                                                                             |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `accuracy`           | A hallucinated or altered fact is adopted from the minute into a statutory record (a housing plan or care assessment) and drives a wrong decision       | No. Once adopted and acted on, the wrong decision has already been made [1]                                                        | Unlikely. Hallucinations read fluently and look plausible, so a reviewer under time pressure often misses them [1]                                       | High. Irreversible harm if a fluent error is adopted into a statutory record, and the error is hard to spot                            |
| `numerical_accuracy` | A wrong date, deadline, time, or reference number causes an operational error                                                                           | No. An acted-on wrong figure causes a downstream error that is hard to undo                                                        | Unlikely. A single wrong figure looks normal on the page unless it is checked against the transcript                                                     | High. A small change could carry a large consequence and is easily missed                                                              |
| `action_clarity`     | A required action is dropped, left unowned, or fabricated, so the wrong work happens or none does                                                       | Partly. An action can be clarified if caught before the minute is adopted; once it has been acted on, the effect is harder to undo | Sometimes. A vague or missing action is fairly visible, but a plausibly worded fabricated or misattributed action can pass unnoticed                     | High. Actions are the operative content of the minute: they are what someone does next                                                 |
| `coverage`           | A safeguarding disclosure, risk, or decision is silently omitted, so a housing plan or care assessment is drafted from a minute missing key information | No. An unnoticed omission cannot be recovered; the reader acts without knowing anything is missing                                 | Unlikely. The hardest failure to spot: omissions are "much harder to identify" at the point of use because nothing on the page flags them [1]            | High. Severe harm and the least catchable failure, which is why it gets the strict pass bar                                            |
| `auditability`       | A claim cannot be traced to its source, so errors cannot be verified and a person cannot seek redress                                                   | Partly. Attribution can be re-added from the recording, but only if the gap is noticed and the source is still to hand             | Sometimes. A missing attribution is visible if checked, but verifying every citation against the recording is the slow step that rushed review skips [1] | Medium. Real accountability stakes (redress, court use, the mandatory transparency duty [5][6]); the standard setting understates this |
| `template_fit`       | A required section is missing or empty, so the document is unusable in its workflow                                                                     | Yes. A missing section can be re-generated or edited in before the document is used                                                | Likely. A missing required section is visible on the page when checked against the template                                                              | Low, rising to medium where the template carries statutory fields, which a missing section can invalidate [1]                          |
| `readability`        | Poor structure or render-breaking artefacts (stray JSON, HTML, or broken tags) make the minute hard to read or unusable until reformatted               | Yes. Structure and formatting can be rewritten, and stray markup stripped, before the minute is used                               | Likely. Formatting faults and render-breaking outputs can be noticed at a glance                                                                         | Low. Formatting problems are low harm, visible on the page, and fixable by editing                                                     |
| `professional_tone`  | Non-person-centred or editorialising language, or offensive wording reproduced without cause                                                            | Yes. Tone can be rewritten before the minute is adopted or shared                                                                  | Likely. Inappropriate or editorialising tone is visible on reading                                                                                       | Low. Mostly low harm and visible; the one high-harm case (material wording softened away) is already caught by accuracy and coverage   |


## 3. Per-dimension thresholds

The table below summarises proposed thresholds. The section below the table expands on the rationale behind these values. All values are placeholders pending calibration. The Setting column is either Strict (pass at 4) or Standard (pass at 3). These name the two threshold settings, not a category of dimension. Whether a dimension is hallucination-gated is a separate property, which is why `coverage` takes the strict setting without joining the hallucination gate.


| Dimension            | Setting  | Pass (score >=) | Review (score =) | Fail (score <=) |
| -------------------- | -------- | --------------- | ---------------- | --------------- |
| `accuracy`           | Strict   | 4               | 3                | 2               |
| `numerical_accuracy` | Strict   | 4               | 3                | 2               |
| `action_clarity`     | Strict   | 4               | 3                | 2               |
| `coverage`           | Strict   | 4               | 3                | 2               |
| `auditability`       | Standard | 3               | 2                | 1               |
| `template_fit`       | Standard | 3               | 2                | 1               |
| `readability`        | Standard | 3               | 2                | 1               |
| `professional_tone`  | Standard | 3               | 2                | 1               |


### 3.1 `accuracy` (Factual Accuracy)

**Current rubric:** `[accuracy.j2](../evals/summarisation/prompts/rubrics/accuracy.j2)`

**Proposed thresholds (Strict setting):** pass `>= 4`, review `= 3`, fail `<= 2`

**Justification:**

LocalTranscribe outputs draft minutes that a housing officer may adopt into a Personal Housing Plan under section 189A of the Housing Act 1996 [8]. That is the primary pathway the eval rubrics stress-test. The app also supports a separate adult social care workflow via the Care Assessment V2 template, where a social care worker may adopt a draft into a care needs assessment under the Care Act 2014 [7]. If a hallucinated fact is not identified and corrected by human review, it could end up misleading a statutory decision which may be hard to reverse once acted on.

A study published by the Ada Lovelace Institute reports such a failure mode in a similar setting, including a tool that inserted "suicidal ideation" that a client never mentioned, and warns that inaccuracies entering documentation have "far-reaching impacts" [1]. This is why a score of 2, at which at least one significant factual error could mislead the reader, should be a fail.

A score of 3 still allows some noticeable imprecision or loss of specificity. In the context of a minute that may be adopted into a Personal Housing Plan or a care needs assessment, this can mean losing specificity on important details in a way that may lead to harm. Such a subtle yet consequential change may go undetected during user review, and therefore a score of 3 should be reviewed [1]. 

To pass without review, a summary must score at least 4. At 4 all assertions are accurate and there is no material loss of specificity in owners, timings, modality, or quantities. We keep the placeholder at 4 rather than require a perfect 5 because 4 is already factually safe. Requiring a perfect 5 would send accurate but slightly loosely worded summaries to review for no gain in factual safety, which is why the pass bar is 4. And whether a judge 4 is truly safe is exactly the question calibration must answer against human scores [2][3].

---

### 3.2 `numerical_accuracy` (Numeric Fidelity)

**Current rubric:**  `[numerical_accuracy.j2](../evals/summarisation/prompts/rubrics/numerical_accuracy.j2)`

**Proposed thresholds (Strict setting):** pass `>= 4`, review `= 3`, fail `<= 2`

**Justification:** 

Numbers in LocalTranscribe are operational. They may include dates, deadlines, appointment times, and reference or case identifiers. They tell a person what to do and let a minute be matched and traced. A small inaccuracy can potentially cause substantial disruption. For example, a proof-of-address deadline moving from 12 May to 15 May, a confirmed appointment for "22 May at 14:30" becoming "the following week in the afternoon", and the reference number HB-88142 being dropped. Each of these can cause a missed deadline, a missed appointment, or a minute that cannot be traced. A score of 2, at which there is at least one significant numerical error, or several smaller ones that create ambiguity or operational risk, is therefore a fail.

A score of 3 should be reviewed rather than passed. At 3 there is still noticeable imprecision, normalisation drift, or loss of specificity, and in this domain a shifted deadline or a dropped case number can cause a missed appointment or misfiling even when the prose does not read as misleading. A single wrong figure also looks normal on the page unless it is checked against the transcript. Numeric hallucination whereby uncertain figures are converted into confident exact values is also a risk that should be penalised because inventing precision is arguably as harmful as fabricating a figure. A pass should require a score of 4.

---

### 3.3 `action_clarity` (Actionability)

**Current rubric:** `[action_clarity.j2](../evals/summarisation/prompts/rubrics/action_clarity.j2)`

**Proposed thresholds (Strict setting):** pass `>= 4`, review `= 3`, fail `<= 2`

**Justification:** 

Actions ensure that meetings have real consequences. They define what someone must do next, by when, and on whose authority. A well-formed action is concrete and owned, for example "Customer to report to Housing Officer on CBT progress by 12 May 2026". A vague one such as "Some actions were assigned to various team members. Further steps will be taken as needed" has no owner, deadline or deliverable and cannot be implemented or tracked. In the context of LocalTranscribe that can mean an eligibility assessment or follow-up meeting does not take place. A score of 2, where actions are missing two or more of owner, deadline, and deliverable, cannot be reliably carried out, is a fail.

A score of 3 must be reviewed. At 3 an action is identifiable but typically missing one element, such as a deadline that is implied rather than stated, and an implied deadline is not actionable. To pass without review, a summary must score at least 4. A 5 requires every action to state its owner, deadline, and deliverable explicitly, with no inference. A 4 is reached when the actions are clear and any remaining gap is minor and can be filled from context or the template. A summary should be scored at 4 rather than 5 when, for example, one action leaves its deadline to be confirmed and another does not restate its owner, yet each action can still be carried out. The gap between 4 and 5 is how comprehensively each detail is spelled out, not whether the action is operable, so the pass score is 4.

---

### 3.4 `coverage` (Transcript Factual Completeness)

**Current rubric:** `[coverage.j2](../evals/summarisation/prompts/rubrics/coverage.j2)`

**Proposed thresholds (Strict setting):** pass `>= 4`, review `= 3`, fail `<= 2`

**Justification:** 

Omitted information can have serious consequences in this domain. If a safeguarding disclosure, a risk, or a decision is left out, the reader forms a confident but incomplete picture and may act on it. If that minute is used to draft a Personal Housing Plan or, in the separate social care pathway, a care needs assessment, the statutory document is then built on an incomplete picture [8][7]. The Ada Lovelace study on transcription tools gives specific examples, including AI summaries that downplayed the needs of women in records, and warns that missing details distort the account even when nothing false is added [1].

The risk is amplified by the fact that omissions are difficult to identify. The study states that "more subtle changes in the way documentation is presented, including omissions in the transcripts, are likely to be much harder for social workers to identify at the point of use" [1]. An end user reading an otherwise fluent summary has nothing that flags the missing piece of information. To find it they would have to compare the summary against the full transcript, which end users may not do thoroughly enough or at all under time pressure [1]. Because the end user who reviews the draft is unlikely to identify the omission, the safer approach is to set a higher pass bar in the eval.

A score of 3 allows some non-trivial omissions. For safeguarding content, a non-trivial omission is not an acceptable pass. Giving coverage the strict setting, so that a score of 3 falls into the eval review band and 2 or below fails, is commensurate with the harm. 

---

### 3.5 `auditability` (Citation Quality)

**Current rubric:** `[auditability.j2](../evals/summarisation/prompts/rubrics/auditability.j2)` 

**Proposed thresholds (Standard setting):** pass `>= 3`, review `= 2`, fail `<= 1`

**Justification:** 

Traceability is what allows a record to be checked, challenged, and used. The Ada Lovelace study ties it directly to accountability. Records allow people to "understand significant events in their lives and seek redress when things go wrong", and social workers must be able to "stand up in court and read this out". The study's first recommendation is mandatory transparency recording and "watermarking" of AI output [1]. UK public-sector rules reinforce this. The Algorithmic Transparency Recording Standard is mandatory for central government tools that influence decisions about people, including in housing and social care, and it exists precisely so that algorithmic outputs can be traced and scrutinised [6]. Data protection law gives a person the right to an explanation of, and the right to contest, an automated decision, which is impossible if claims cannot be traced to their source [5].

As such, there is an argument that auditability should have a pass bar of 4. Attribution in this context is ensuring transparency and accountability control and a pass bar of 3 accepts a summary where minor speakers or contextual comments may be unattributed, which may be defensible for an internal note but less so for a minute that may later be disclosed or used in proceedings.

On the other hand, the potential consequences of poor auditability are arguably not as great as those of factual inaccuracy. A weak or missing attribution makes a claim harder to trace and challenge, but the claim itself can still be verified against the recording and the source is usually recoverable. A factual or numerical error instead places something false in the minute that a reader may act on directly, and once adopted that may be difficult to reverse. Poor auditability reduces the ability to scrutinise the record whereas a factual error changes the content of the record itself. On that basis auditability is kept at the standard setting for now.

---

### 3.6 `template_fit` (Template Adherence and Completeness)

**Current rubric:** `[template_fit.j2](../evals/summarisation/prompts/rubrics/template_fit.j2)`

**Proposed thresholds (Standard setting):** pass `>= 3`, review `= 2`, fail `<= 1`

**Justification:** 

Statutory templates such as a Personal Housing Plan or a care needs assessment have required sections set by policy or law, and the Ada Lovelace study notes that such assessments carry strict formatting and content requirements [1]. In such cases, missing sections are not only a presentation issue but may make the document invalid for its purposes. Therefore the harm in this case depends on whether a template carries statutory fields.

At score 3, "all required template sections are present; minor omissions within sections remain, but the template intent is met.". In this case, a score 3 is more recoverable through review and editing than a fabrication or a non-trivial omission. That supports the standard setting of pass at score 3 or higher.

---

### 3.7 `readability` (Structure and Readability)

**Current rubric:** `[readability.j2](../evals/summarisation/prompts/rubrics/readability.j2)`

**Proposed thresholds (Standard setting):** pass `>= 3`, review `= 2`, fail `<= 1`

**Justification:** 

This dimension mostly concerns formatting, structure and rendering, and whether the summary is logically organised with sensible headings. A score of 3 follows the template broadly with only minor ordering or heading issues, or an occasional raw URL, that do not prevent comprehension.

Quality degradation for this domain will for the most part be a relatively low-risk issue. A formatting issue is reasonably easily noticable on the page and can be corrected by editing before the minute is used hence we allow a pass at a score of 3 or higher.

---

### 3.8 `professional_tone` (Tone)

**Current rubric:** `[professional_tone.j2](../evals/summarisation/prompts/rubrics/professional_tone.j2)`

**Proposed thresholds (Standard setting):** pass `>= 3`, review `= 2`, fail `<= 1`

**Justification:** 

Tone is mostly lower harm and an unsatisfactory tone is usually easy to notice and correct on reading. While not as potentially harmful as fabrication or missing key information, it can have real negative impacts on readers and users. For example, the Ada Lovelace study on AI transcription services suggests that records must be "readable and relatable", citing one one social worker who described academic language being used in a child's record as "horrific" [1].

Tone could potentially have a higher harm if a material threat or safeguarding statement is softened into vague paraphrase rather than being quoted accurately. However, the rubric handles this directly. That specific failure is for the most part an accuracy and coverage problem (the meaning is changed or lost), so it is already addressed by those dimensions, and tone does not need a strict pass bar to cover it. That is why tone stays standard while the safeguarding risk is still gated elsewhere.

## 5. Citations

1. Ada Lovelace Institute. "Scribe and prejudice? Exploring the use of AI transcription tools in social care." February 2026.
2. B. Sarmah, M. Li, J. Lyu, S. Frank, N. Castellanos, S. Pasquali, D. Mehta. "How to Choose a Threshold for an Evaluation Metric for Large Language Models." arXiv:2412.12148, 2024.
3. K. Schroeder, Z. Wood-Doughty. "Can You Trust LLM Judgments? Reliability of LLM-as-a-Judge." arXiv:2412.12509, 2024.
4. R. Lee et al. "How to Correctly Report LLM-as-a-Judge Evaluations." 2025.
5. Information Commissioner's Office. "Rights related to automated decision-making including profiling" (UK GDPR Article 22 guidance) and guidance on meaningful human review.
6. Department for Science, Innovation and Technology and Central Digital and Data Office. "Algorithmic Transparency Recording Standard: guidance for public sector bodies" and "ATRS mandatory scope and exemptions policy." Mandatory for central government from February 2024.
7. Care Act 2014, section 9 (duty to assess an adult's needs for care and support).
8. Housing Act 1996, section 189A (assessments and personalised plan), inserted by the Homelessness Reduction Act 2017, section 3; and Homelessness Code of Guidance for Local Authorities, Chapter 11 (Assessments and personalised plans).

