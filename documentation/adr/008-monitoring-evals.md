# ADR-008: Evals Monitoring

## Status

Accepted

Date of decision: 2026-05-15

Date amended: 2026-11-17

## Context and Problem Statement

Current monitoring of AI system components relies primarily on user action logging, which is reactive and imperfect. User feedback only surfaces after significant issues occur, missing gradual quality deterioration and failing to pinpoint which system component is underperforming.

Without continuous evaluation monitoring, performance changes from upstream providers (e.g., Azure AI Speech, LLM API updates) can be misattributed to new features, leading to incorrect decisions. Third-party AI services frequently update to address user-reported issues and improve aggregate performance, which can inadvertently cause regressions on specific tasks important to our use case.

How can we implement ongoing evaluation monitoring to detect quality changes, distinguish between feature-related and provider-related performance shifts, and maintain visibility into system health?

## Considered Options

* Tiered dataset based evals with continuous monitoring
* Continuous monitoring with full dataset
* Evaluation on flagged inputs
* Third-party moderation/safety APIs
* Shadow evaluation
* Random sampling of live production data
* No additional monitoring

## Decision Outcome

Continue monitoring with the full evaluation dataset.

Under the new Data Sharing Agreement (DSA) we are working towards, live user data may be used for evaluation monitoring when an authorised user or council donates the meeting. Donation must be an affirmative choice; passive collection, random sampling, and shadow evaluation of general production traffic are not currently included.

Identifiable donated audio may be retained for up to 12 months, then must be deleted or anonymised. Data must be used only for approved evaluation monitoring and handled under DSA-approved access, storage, and processing controls. Donation must be an affirmative opt-in, including during onboarding.

## Pros and Cons of the Options

### Tiered dataset based evals

A stratified approach using multiple dataset subsets: a comprehensive dataset for pre-deployment validation, a medium subset for weekly monitoring, and a minimal subset for rapid PR-level regression detection.

* Good, because cost and coverage are tunable per tier, and tiers can be added incrementally.
* Good, because it enables rapid feedback on prompt changes before full deployment.
* Bad, because it requires maintaining multiple synchronized dataset versions.
* Bad, because comparing results across tiers requires additional normalization.

### Continuous monitoring with full dataset

Run the complete evaluation dataset on a regular cadence (e.g., weekly or per release).

* Good, because it provides complete coverage and directly comparable results across runs.
* Good, because it avoids the complexity of managing multiple dataset tiers.
* Bad, because inference costs accumulate rapidly and feedback cycles are slow.
* Bad, because it lacks granularity for PR-level validation.

### Evaluation on flagged inputs

Evaluate inputs flagged as problematic via explicit feedback (e.g., thumbs down) or implicit signals (e.g., response dismissal) using LLM-as-a-judge.

* Good, because it focuses resources on actual user pain points and surfaces unknown issues.
* Bad, because it requires high implementation effort and misses issues users don't flag.
* Bad, because it creates blind spots that can mask overall performance degradation.
* Neutral, because an interaction signal alone does not constitute donation.

### Third-party moderation/safety APIs

Use external services (e.g., OpenAI moderation, Lakera Guard) to evaluate risk categories such as harmful content or PII leakage on live data.

* Good, because it leverages specialist expertise maintained externally.
* Bad, because it incurs ongoing costs, creates vendor dependency, and generic taxonomies may not fit our domain.

### Shadow evaluation

Run old prompt/model variants alongside the production version on live traffic to compare performance, using LLM-as-a-judge.

* Good, because it enables direct comparison on identical real-world inputs.
* Bad, because it doubles inference costs and requires significant infrastructure (dual execution, traffic routing).
* Bad, because general production traffic is not currently covered without donation.

### Random sampling of live production data

Periodically sample production inputs/outputs and run LLM-as-a-judge evaluations against existing criteria.

* Good, because costs are controllable via sample size and frequency.
* Bad, because results aren't comparable across periods and curated datasets already cover common cases.
* Bad, because passive sampling is not currently covered; each meeting would need to be donated.

### No additional monitoring

Rely solely on existing user logging and feedback (e.g., PostHog analytics).

* Good, because it requires no additional cost or engineering effort.
* Bad, because it cannot detect gradual degradation, distinguish feature vs. provider regressions, or provide visibility between user-reported incidents.
