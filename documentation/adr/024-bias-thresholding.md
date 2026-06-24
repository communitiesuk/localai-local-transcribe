# ADR-024: Setting Pass/Fail thresholds for bias metrics

## Status

Draft

Date of decision: 2026-06-23

## Context and Problem Statement

Model providers will tweak their models over time. This will likely introduce variance into our measured bias scores. Our intended response to bias is to improve our base template prompts, and over time we expect to keep driving bias down through this prompt-improvement work rather than treat any single level as "good enough" forever. The open question is timing: intervening too early is wasteful (we would be chasing statistical fluctuations), but we want to know if significant interventions are need. So we need both a floor that defines unacceptable bias and a signal that distinguishes a real regression from noise.

## Considered Options

1. Comparison baseline - against a naive template, another AI system, or manually annotated summaries
2. Established rule of thumb - the 4/5 rule
3. Control charts (Statistical Process Control)
4. Minimum Detectable Effect (MDE) sizing

## Decision Outcome

We will use control charts as the ongoing monitoring mechanism, anchored by the 4/5 rule.

Control charts watches for drift and regressions. On their own they can detect change relative to a baseline. The assumption is that baseline is acceptable. The 4/5 rule supplies the missing baseline, by defining the minimum acceptable level of bias.

Crucially, 4/5 is a floor, not a target. It establishes the minimum we will tolerate, but it is not where we intend to stay. As prompt improvement and optimisation work proceeds, we will actively strive to suppress bias well below what the 4/5 rule strictly necessitates. In future once our new performance becomes stable, we will baseline based on that improved performance.

## Pros and Cons of the Options

### 1. Comparison baseline - against a naive template, another AI system, or manually annotated summaries

Judge bias relative to a comparator and report the difference, rather than against an absolute number. Candidate comparators: a naive "Summarise this." template, another AI system (e.g. M365 Copilot's summarise feature), or manually annotated summaries.

* Good, because a relative comparison is easier to interpret and communicate than a raw absolute score.
* Bad, because every variant still needs a threshold on the difference, a comparison gives context but does not on its own define where Pass becomes Fail.
* Bad, because the naive template is a low bar that says nothing about absolute acceptability.
* Bad, because comparison to another AI system or a manual annotation does not reflect the current user workflow.

### 2. Established rule of thumb - the 4/5 rule

An accepted bias figure that is widely cited in AI bias research: the likelihood of a non-privileged group getting a good / acceptable outcome should be no less than 4/5 (80%) of the privileged group.

* Good, because it is an easy framework to work with and apply.
* Good, because it is used in a lot of research as a threshold.
* Good, because for the judge metric we get a acceptability definits essentially for free (they are defined for summarisation evaluation anyways)
* Bad, because it is not treated as a definite "fine" mark with respect to UK law.
* Bad, because it offers a relatively shallow framing of the bias problem.

### 3. Control charts (Statistical Process Control)

The concrete tool of Statistical Process Control (SPC). Rather than setting a fixed absolute threshold, establish a baseline period (e.g. the first N transcripts before any system changes), compute the mean and standard deviation of scores across it, and set control limits at mean ± 3 standard deviations; any later batch falling outside those limits triggers a flag. We would monitor the factual-vs-counterfactual gap rather than raw scores. A sudden widening or a reversal in direction is the signal we care about; a gap narrowing toward zero is improvement, not an alert.

* Good, because it adapts to our actual data distribution instead of imposing an arbitrary absolute number.
* Good, because monitoring the factual-vs-counterfactual gap targets exactly the bias signal we care about.
* Good, because it naturally catches drift and regressions over time, not just point-in-time failures.
* Bad, because it needs enough samples per batch for a stable mean, which may be demanding.
* Bad, because the baseline may need recomputing after large bias improvements.
* Neutral, because it detects change relative to a baseline but assumes the baseline itself is acceptable.

### 4. Minimum Detectable Effect (MDE) sizing

Rather than asking "what's the threshold for bad?", ask "what's the smallest bias difference we could reliably detect given our sample sizes?". Using the observed standard deviation from existing data plus a chosen power and significance level, a power formula gives the minimum detectable effect (for a two-sample t-test, MDE ≈ 2.8 × (SD / √N)).

* Good, because it stops us setting a threshold finer than we could ever reliably detect.
* Good, because it reuses data we already have.
* Bad, because picking a sensible power and significance level is difficult.
* Bad, because it is tough to explain to a non-technical audience beyond "no detectable bias", which is really a claim that our hyperparameter selection is good.
* Bad, because it can be noisy, especially where we see explainable, "useful" bias.

## More Information

* Metrics in scope: LLM-as-judge scores and the Regard sentiment score, computed over factual/counterfactual transcript pairs.
