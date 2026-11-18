# ADR-009: Prompt Optimization Data Collection

## Status

Accepted

Date of decision: 2026-05-15

Date amended: 2026-11-17

## Context and Problem Statement

Prompt optimization requires high-quality data reflecting real-world usage and failure modes. Without systematic collection, improvements rely on anecdotal evidence and ad-hoc reports, making optimization reactive and inconsistent.

Collection approaches face trade-offs between data quality, cost, user experience, and the risk of biasing the system toward specific user segments or predefined problem categories.

How should we collect data to support prompt optimization while balancing resource constraints and data quality requirements?

## Considered Options

* Automated collection via user-flagged inputs
* Prompted user feedback collection
* Automated collection via system-flagged inputs
* Manual annotation of production samples
* Explicit meeting donation by councils or professionals
* No systematic data collection

## Decision Outcome

Under the new Data Sharing Agreement (DSA) we are working towards, meetings donated by councils or professionals may be used for prompt optimisation. Donation must be an affirmative choice; passive collection is not currently included.

Only anonymised data may be used. Identifiable audio must be deleted or anonymised within 12 months and handled under DSA controls.

## Pros and Cons of the Options

### Automated collection via user-flagged inputs

Automatically collect problematic inputs flagged via explicit feedback (thumbs down, corrections) and implicit signals (immediate dismissal, repeated queries).

* Good, because user corrections provide direct examples of desired outputs and scale automatically with usage.
* Bad, because it requires significant infrastructure and depends on users recognising and reporting issues.
* Bad, because feedback or implicit behaviour alone does not constitute donation.
* Neutral, because it can build on the infrastructure described in ADR-008.

### Prompted user feedback collection

Actively prompt users for structured feedback after specific interactions, and use LLMs to extract patterns from responses (e.g. via axial coding).

* Good, because it yields richer feedback than binary flags and can capture nuanced user expectations.
* Bad, because it adds friction, risks low response rates, and can give disproportionate influence to highly engaged users.
* Bad, because it requires careful UX design and adds LLM inference costs for processing.
* Neutral, because a prompt can provide the required donation choice.

### Automated collection via system-flagged inputs

Use automated detection (hallucination checks, third-party safety APIs) to flag problematic outputs without user intervention.

* Good, because it is consistent, proactive, and scales without user engagement.
* Bad, because it only catches anticipated failure modes, may produce false positives, and lacks user corrections showing desired outputs.
* Bad, because system flagging cannot authorise collection.

### Manual annotation of production samples

Sample production inputs and have human annotators label them with quality scores or corrections.

* Good, because trained annotators provide high-quality, nuanced judgements.
* Bad, because it is resource-intensive, slow, hard to scale, and annotator biases can reinforce existing system issues.
* Bad, because sampling production data is implicit collection without an affirmative donation decision.

### Explicit meeting donation by councils or professionals

Councils or professionals choose which meetings to donate.

* Good, because collection is explicit and provides real usage data.
* Bad, because asking for consent will bias donations towards non-problematic meetings.

### No systematic data collection

Rely on ad-hoc issue reports and informal feedback without structured data collection.

* Good, because it requires no implementation effort and avoids data handling complexity.
* Bad, because optimization becomes reactive, inconsistent, and unable to support automated prompt engineering.

## Links

* Related to ADR-008: Evals Monitoring (data collection infrastructure)
