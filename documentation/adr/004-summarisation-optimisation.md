# ADR-004: Optimisation Strategy for Local Transcribe Summarisation and Evaluation Prompts

## Status

Accepted

Date of decision: 2026-01-15

## Context and Problem Statement

Local Transcribe generates summaries from meeting transcripts, and we also maintain an LLM-as-judge evaluation pipeline to score summaries (e.g., faithfulness, coverage, conciseness, coherence).

We need an optimisation approach that can:

* Improve the quality and consistency of Local Transcribe’s summarisation prompts.
* Improve the quality and consistency of the judge prompt and scoring behavior.
* Be reproducible, versioned, and measurable, with clear validation to avoid overfitting.

Manual prompt iteration is slow, difficult to reproduce, and tends to drift without systematic evaluation. We can use DSPy optimizers (notably MiPROv2) to systematically search over instructions and demonstrations for both the product prompts and the judge prompt.

## Considered Options

* Manual prompt engineering with ad-hoc evaluation
* Prompt optimisation using DSPy optimizers (MiPROv2) (preferred)
* Fine-tuning (or instruction-tuning) models
* Ensemble / multi-judge strategies without optimisation

## Decision Outcome

Prompt optimisation using DSPy optimizers, because it is an automated and systematic approach. Other options are more expensive, or time consuming. We think the manual approach is unlikely to achieve the same results.

### Implementation deferred to a later project stage

While DSPy is the agreed optimisation strategy, implementing prompt optimisation has been pushed to a later stage of the project. Two factors drive this:

* User feedback so far has not exposed any significant issues with the templated prompts currently in use, so there is no pressing quality problem to solve.
* Our evaluation is not yet fully in place, so we cannot reliably identify prompt inefficiencies ourselves.

Running DSPy optimisation now — before we can measure what it improves — would be somewhat wasteful. We will revisit this once the evaluation pipeline is mature enough to detect inefficiencies and once user feedback (or our own evaluation) surfaces a concrete need.

## Pros and Cons of the Options

### Manual prompt engineering with ad-hoc evaluation

This approach iterates on prompts by hand and validates changes via informal spot-checks or basic automated metrics.

* Good, because it is easy to start and has low tooling overhead.
* Good, because it allows rapid exploration early in a project.
* Bad, because it is not systematic and hard to reproduce.
* Bad, because it tends to overfit to whatever examples the author happens to review.
* Bad, because it becomes unmanageable as the number of prompts/modules increases.

### Prompt optimisation using DSPy optimizers (MiPROv2) (preferred)

This approach models both the summarisation pipeline and the judge as DSPy programs with explicit modules (predictors). We then apply DSPy optimizers to automatically improve natural-language instructions and select few-shot demonstrations.

Per DSPy documentation, MiPROv2 works at a high level by:

* Creating both few-shot examples and new instructions for each predictor.
* Searching over combinations of instructions and demonstrations using Bayesian Optimization to find the best combination under a metric.

This enables optimising:

* The summariser prompt(s) used by Local Transcribe.
* The judge prompt used to score outputs.

Key requirements for this approach:

* A clearly defined metric and a train/validation split.
* A held-out evaluation set to measure generalisation.
* Versioning of optimized artifacts (instructions + demos) and the metric definition.

* Good, because it is systematic and reproducible.
* Good, because it jointly optimises instructions and demonstrations, which can significantly improve prompt quality.
* Good, because it can scale to multiple prompts/modules and be rerun as data changes.
* Bad, because it requires careful metric design and data splits to avoid overfitting, and can amplify any LLM-judge biases.
* Bad, because it increases compute/cost during optimisation.
* Neutral, because it benefits from periodic human review and calibration.
* Neutral, because it can be bootstrapped to optimise a different model at fraction of the cost.

### Fine-tuning (or instruction-tuning) models

This approach collects a dataset and fine-tunes a model for summarisation, judging, or both.

* Good, because it can yield strong improvements and reduce prompt sensitivity.
* Bad, because it requires larger datasets, training infrastructure, and governance.
* Bad, because it can be difficult to debug and to rollback small behavioral changes.
* Neutral, because it can complement DSPy optimisation (e.g., after finding stable instructions and datasets).

### Ensemble / multi-judge strategies without optimisation

This approach uses multiple judge models and aggregates their decisions to improve robustness.

* Good, because it can reduce variance from a single judge model.
* Bad, because it increases inference cost.
* Bad, because it does not directly improve the underlying prompts.
* Neutral, because it can be combined with DSPy optimisation (e.g., optimising against an ensemble metric).
* Neutral, because it can be implemented later to enhance single LLM-judge metric.

## More Information

Things to consider:

* Adding optimisation runs that significantly increase LLM usage/cost
* Switching judge models/providers requires consideration (cost, data handling, security)
