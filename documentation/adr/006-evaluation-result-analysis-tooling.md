# ADR-006: Human Data Annotation for Minute Summaries (Rubric-Aligned)

## Status

Accepted

Date of decision: 2026-05-15

## Context and Problem Statement

Minute generates summaries from meeting transcripts, evaluated using an LLM-as-judge rubric. To trust and improve LLM-as-judge scoring and prompt optimisation, we need a human annotation process that:

* Collects human scores aligned to the same rubric dimensions.
* Enables comparison of human vs. machine scores to measure correlation and calibration.
* Produces a reusable evaluation dataset for judge prompt iteration and DSPy optimisation.
* Supports periodic review in addition to one-off dataset creation.

## Considered Options

* Ad-hoc spreadsheet / offline review
* Lightweight Jupyter Notebook with UI
* Lightweight internal web annotation tool
* Full-featured third-party labeling platform
* Human-in-the-loop review embedded into the product UI

## Decision Outcome

Lightweight Jupyter Notebook with UI, because it requires no new infrastructure, aligns with existing data inspection tooling and storage access patterns, and can be built quickly without AI coding tools. A more capable internal web annotation tool remains an option if annotation needs grow beyond what the notebook can support.

## Pros and Cons of the Options

### Ad-hoc spreadsheet / offline review

Export transcripts/summaries to a spreadsheet and ask reviewers to provide scores.

* Good, because it is fast to start with no engineering required.
* Bad, because consistency and required fields are hard to enforce, and it is not well-suited for periodic reviews or audit trails.

### Lightweight Jupyter Notebook with UI

A Jupyter Notebook with an `ipywidgets` UI for reviewing and annotating transcripts and summaries. Aligned with existing output data inspection workflows, making it trivial to deploy without additional infrastructure.

The notebook reads from and writes directly to the annotation container within the input data storage, using the same access patterns as other data inspection tooling. Reviewers can score and edit annotations in-place, with results persisted back to the container.

* Good, because it is trivial to deploy — no new infrastructure or services required.
* Good, because it is consistent with existing data inspection tooling and storage access patterns.
* Good, because it can be created quickly even without AI coding tools.
* Bad, because it lacks workflow features (assignment, adjudication, change history).
* Bad, because it is not well-suited for large-scale or multi-reviewer workflows.
* Neutral, because scope can be kept minimal and expanded if needs grow.

### Lightweight internal web annotation tool

A simple web UI where reviewers can view the transcript, candidate summary, optional reference summary, and optional LLM-as-judge output, then record rubric-aligned annotations with scores, rationales, and evidence spans.

Should support: assignment queues, double annotation for inter-annotator agreement, adjudication, embedded reviewer guidelines, change history, and structured export.

* Good, because it enforces a consistent schema and supports periodic review, sampling, and integration with eval outputs.
* Bad, because it requires significant engineering effort and ongoing maintenance.
* Bad, because this is only straightforward to build with AI coding tools, which the team does not currently have access to.
* Neutral, because scope can be kept small initially and expanded over time.

### Full-featured third-party labeling platform

Use an off-the-shelf labeling tool (e.g., Label Studio, Scale AI) with built-in workflow management, QA, and analytics.

* Good, because it provides mature workflows and can scale to larger annotation programmes.
* Bad, because it may be costly, require integration work, and be hard to customise for rubric-specific UX.
* Neutral, because it can be adopted later once requirements stabilise.

### Human-in-the-loop review embedded into the product UI

Ask end users to provide feedback on summaries within the product itself.

* Good, because it captures real user judgement on real meeting distributions continuously.
* Bad, because feedback is likely noisy and not rubric-consistent without careful UX design.
* Neutral, because it can complement a dedicated annotation workflow rather than replace it.

## More Information

### Correlation and calibration

To validate LLM-as-judge, track:

* Correlation between human and LLM scores per dimension.
* Calibration curves (where judges are systematically high/low).
* Disagreement analysis by category (e.g., numbers, attribution, negation).

### Periodic reviews

The annotation tooling should support ongoing audits: sampling recent production-like outputs periodically, running human review on a fixed budget, and tracking trends across model/prompt versions.

### Data storage and export

Annotations should be stored with stable identifiers (example_id, run_id, prompt/version), the exact transcript and summary shown to the reviewer, annotation schema version, and reviewer metadata (anonymised as needed). Exports should support eval dataset creation and DSPy optimisation splits.

Signoff, consent, and data agreements are required for use of production/user transcripts, reviewer access controls, and any third-party labeling vendor usage.
