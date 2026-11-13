# ADR-033: Types of Performance Testing

## Status

Proposed

Date of decision: pending (drafted 2026-11-13)

## Context and Problem Statement

Local Transcribe is receiving very little usage during private beta; production tells us nothing about capacity.
Before widening the housing rollout, and before we begin supporting social work, we need evidence that the service
copes with the expected load.

The following properties of Local Transcribe shape which tests are worth running:

* Local Transcribe does not autoscale. Production runs one frontend task, one backend task and two worker tasks, each 
  transcribing one recording at a time.
* Transcription and summarisation are asynchronous, with requests queued in SQS and the browser polling for completion.
* Transcription and LLM calls go to Azure services through MHCLG's APIM. They are subject to costs and quotas we do not
  control.

Which kinds of performance test should we build and run now?

## Considered Options

* Load test at expected peak
* Breakpoint (stress) test
* Spike test
* Soak test
* Per-endpoint performance tests
* Degraded-dependency test

## Decision Outcome

Load test at expected peak and a breakpoint test, built from the same scripts. Together they answer the two questions
"do we meet our targets at the expected peak?" and "what fails first, and at what load?". The answer to the second is
particularly important because of the non-scaling nature of Local Transcribe as its infrastructure currently stands;
its capacity is fixed by task counts that have been chosen without measurement.

## Pros and Cons of the Options

### Load test at expected peak

Simulate the modelled peak number of users performing a realistic mix of activity for about an hour, against a
production-sized environment with realistic existing data, and compare the results with agreed targets.

* Good, because it directly answers whether the next rollout step is safe.
* Good, because it is repeatable and gives a baseline for later comparisons.
* Neutral, because its value depends on the load model, which is based on assumptions until we have data about
  real usage.
* Bad, because on its own it does not show how much headroom exists.

### Breakpoint (stress) test

Increase load in steps until an agreed stop condition is met (error rate, queue age or latency).

* Good, because it identifies the first bottleneck and the load at which it appears.
* Good, because it gives the sizing evidence needed for future expansions.
* Good, because it reuses the load test's scripts with a different load shape, so it costs little to add.
* Bad, because it is only affordable if AI calls are stubbed (see ADR-034).

### Spike test

Apply a sudden, large increase in load.

* Neutral, because the queues absorb bursts by design, so a spike appears as longer waiting time, not failure.
* Good, because a realistic burst is easy to include in the load profile.
* Bad, because a separate test would mostly repeat what the load and breakpoint tests show.

### Soak test

Hold typical load for several hours.

* Good, because some risks only appear over time: worker temporary storage filling, CPU credits running out on the
  burstable database instance, database IAM token renewal, long-lived worker processes.
* Bad, because each run takes several hours, so it is slower to iterate on than the peak test.
* Neutral, because it can be added later at little dev cost.

### Per-endpoint performance tests

Test each API endpoint in isolation.

* Bad, because the heavy work happens in the worker, not in individual endpoints.
* Bad, because isolated endpoint load does not reflect how polling and uploads interact.
* Neutral, because the journey-based tests already report response times per endpoint.

### Degraded-dependency test

Run normal load while the AI services throttle, slow down or fail.

* Good, because LLM calls can be retried many times and the retry behaviour might amplify load.
* Good, because it shows whether stuck jobs recover without manual action.
* Bad, because it requires a stub that can inject failures.

## More Information

* Numeric targets and the load model are defined separately.
* ADR-034 covers the environment, test identity and AI dependencies. ADR-035 covers tooling and execution.
