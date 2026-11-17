# ADR-033: Types of Performance Testing

## Status

Proposed

Date of decision: pending (drafted 2026-11-13)

## Context and Problem Statement

Local Transcribe is receiving very little usage during private beta; production tells us nothing about capacity.
Before widening the housing rollout, and before we begin supporting social work, we need evidence that the service
copes with the expected load.

The following properties of Local Transcribe shape which tests are worth running:

* Local Transcribe does not currently autoscale. Production runs one frontend task, one backend task and two worker
  tasks. Adding ECS autoscaling would be a small change, but nothing has been measured to tell us which metric to scale
  on, at what threshold, or up to how many tasks.
* Some limits are shared by every task and would not move with autoscaling: the single database instance and its
  connection limit, and the APIM quotas.
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
"do we meet our targets at the expected peak?" and "what fails first, and at what load?".

The breakpoint test is run in two stages:

1. Against fixed task counts, to measure what one task of each service can handle. This figure is what an autoscaling 
   policy would be built from.
2. If autoscaling is then added, again with scaling enabled, to check that it reacts quickly enough and to find the
   limit at the maximum task count, where the shared limits become the bottleneck.

## Pros and Cons of the Options

### Load test at expected peak

Simulate the modelled peak number of users performing a realistic mix of activity, against a production-sized
environment with realistic existing data, and compare the results with agreed targets.

Peak load is held until queue length and waiting time are either stable or clearly growing continually, and for at 
least as long as several complete user journeys (record, wait for the transcript, create a document). A run of about 15
minutes should be sufficient.

* Good, because it directly answers whether the next rollout step is safe.
* Good, because a short run is cheap to repeat.
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

* Good, because the queues only protect the workers, so a sudden burst could overload the backend and frontend tasks.
* Neutral, because we do not expect sharply spiking traffic in the live service.
* Good, because a realistic burst is easy to include in the load profile.
* Bad, because a separate test of a larger, unrealistic spike would mostly repeat what the breakpoint test shows.

### Soak test

Hold typical load for several hours.

* Good, because some risks only appear over time: worker temporary storage filling, CPU credits running out on the
  burstable database instance, database IAM token renewal, long-lived worker processes.
* Bad, because each run takes several hours, so it is slower to iterate on than the peak test.
* Neutral, because it can be added later at little dev cost.

### Per-endpoint performance tests

Test each API endpoint in isolation.

* Good, because they are cheap, simple and quick to run, so they can run often.
* Good, because they show how each endpoint's response time changes from release to release under low load.
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
* Per-endpoint tests answer a different question (has a release made an endpoint slower?) from the one this ADR
  addresses (can we support the expected load?). They are not chosen here, but could be added later as a regression
  check.
* ADR-034 covers the environment, test identity and AI dependencies. ADR-035 covers tooling and execution.
