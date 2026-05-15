# ADR-009: Prompt Optimization Data Collection

## Status

Accepted

Date of decision: 2026-05-15

## Context and Problem Statement

Prompt optimization requires high-quality data reflecting real-world usage and failure modes. Without systematic collection, improvements rely on anecdotal evidence and ad-hoc reports, making optimization reactive and inconsistent.

Collection approaches face trade-offs between data quality, cost, user experience, and the risk of biasing the system toward specific user segments or predefined problem categories.

How should we collect data to support prompt optimization while balancing resource constraints and data quality requirements?

## Considered Options

* Automated collection via user-flagged inputs
* Prompted user feedback collection
* Automated collection via system-flagged inputs
* Manual annotation of production samples
* No systematic data collection

## Decision Outcome

No systematic data collection, pending a clearer understanding of the Data Protection landscape and approval for limited collection. This decision is subject to change once those constraints are resolved.

## Pros and Cons of the Options

### Automated collection via user-flagged inputs

Automatically collect problematic inputs flagged via explicit feedback (thumbs down, corrections) and implicit signals (immediate dismissal, repeated queries).

* Good, because user corrections provide direct examples of desired outputs and scale automatically with usage.
* Bad, because it requires significant infrastructure and depends on users recognising and reporting issues.
* Neutral, because it builds on monitoring infrastructure described in ADR-008.

### Prompted user feedback collection

Actively prompt users for structured feedback after specific interactions, and use LLMs to extract patterns from responses (e.g. via axial coding).

* Good, because it yields richer feedback than binary flags and can capture nuanced user expectations.
* Bad, because it adds friction, risks low response rates, and can give disproportionate influence to highly engaged users.
* Bad, because it requires careful UX design and adds LLM inference costs for processing.

### Automated collection via system-flagged inputs

Use automated detection (hallucination checks, third-party safety APIs) to flag problematic outputs without user intervention.

* Good, because it is consistent, proactive, and scales without user engagement.
* Bad, because it only catches anticipated failure modes, may produce false positives, and lacks user corrections showing desired outputs.

### Manual annotation of production samples

Sample production inputs and have human annotators label them with quality scores or corrections.

* Good, because trained annotators provide high-quality, nuanced judgements.
* Bad, because it is resource-intensive, slow, hard to scale, and annotator biases can reinforce existing system issues.

### No systematic data collection

Rely on ad-hoc issue reports and informal feedback without structured data collection.

* Good, because it requires no implementation effort and avoids data handling complexity.
* Bad, because optimization becomes reactive, inconsistent, and unable to support automated prompt engineering.

## Links

* Related to ADR-008: Evals Monitoring (data collection infrastructure)
