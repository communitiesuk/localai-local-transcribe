# ADR-023: Approach to Transcription Bias Evaluation

## Status

Accepted

Date of decision: 2026-05-22

## Context and Problem Statement

Transcription services are susceptible to two interrelated sources of bias. First, the linguists who annotate training data may hold implicit views about how certain speech patterns, dialects, or accents should be normalised, introducing annotation bias into the model's foundations. Second, certain demographic groups - particularly those with non-standard accents, regional dialects, or linguistic features less common in formal recorded speech - may be underrepresented in a provider's training dataset, leading to systematically higher error rates for those speakers.

Given that Local Transcribe processes council meetings, which may involve speakers from linguistically diverse communities, we need to decide how much dedicated effort to invest in evaluating transcription bias, and what form that evaluation should take.

## Considered Options

* Linguist-curated dataset
* Targeted real-data collection
* Bias-lens interpretation of existing data

## Decision Outcome

Bias-lens interpretation of existing data, because dedicated collection is expensive, coverage of disadvantaged groups is inherently incomplete, the transcription provider is expected to evaluate against these biases themselves, and the higher-impact bias risks in Local Transcribe lie in the summarisation stage where our mitigation options are stronger. Residual risk is managed by prioritising councils from areas of extraordinary linguistic diversity or notable regional variation in English in our evaluation set.

## Pros and Cons of the Options

### Linguist-curated dataset

Commission or acquire (audio, transcript) pairs assembled with linguist input, designed to reflect the dialects, accents, and speech patterns likely to appear in council meetings.

* Good, because it directly addresses annotation bias through specialist oversight.
* Good, because it enables targeted measurement of error rate disparities across demographic groups.
* Bad, because linguist-validated datasets are expensive and slow to produce.

### Targeted real-data collection

Collect real council recordings that over-represent speakers from groups known to have higher transcription error rates and use these to stress-test the pipeline.

* Good, because it grounds evaluation in authentic speech.
* Good, because it can surface failure modes that affect real users.
* Bad, because acquiring sufficient volume from any single underrepresented group is difficult, and many such groups exist.
* Bad, because the space of potentially disadvantaged groups is large, leaving blind spots likely.
* Bad, because reference transcripts produced by annotators may embed the same annotation bias we are trying to alleviate.

### Bias-lens interpretation of existing data

Use the transcription evaluation data already collected for general quality assessment (per ADR-007), but apply a bias-aware lens during analysis, noting whether error rates vary systematically across councils or speaker demographics.

* Good, because it has near-zero additional cost.
* Good, because it remains sensitive to bias signals that emerge from the real distribution of Local Transcribe users.
* Bad, because without targeted over-sampling, the dataset may not surface disparities with statistical confidence.
* Bad, because it cannot distinguish annotation bias from model bias.

## More Information

The transcription provider is an established service with its own incentives to evaluate for demographic bias, so the problem is not wholly unattended. Bias in the summarisation stage presents higher impact risks and better avenues for mitigation (see ADR-002), making it the more appropriate focus for dedicated effort. Prioritising councils from areas of extraordinary linguistic diversity and notable regional variation in English in our evaluation set is the most practical way to keep blind spots narrow.
