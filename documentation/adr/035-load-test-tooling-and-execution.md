# ADR-035: Load Test Tooling and Execution

## Status

Proposed

Date of decision: pending (drafted 2026-11-13)

## Context and Problem Statement

ADR-033 and ADR-034 decide what we test and where; we also need to choose the tool that generates load and the place
it runs from.

Constraints from the current infrastructure and application:

* CloudFront only admits requests from Great Britain (`terraform/modules/frontdoor/cloudfront.tf`).
* The CloudFront WAF blocks any IP address that sends more than 2,000 requests in five minutes, and non-production
  environments have IP allow-lists.
* Recordings are uploaded directly to S3 using a presigned URL, so the load generator needs good bandwidth to S3.
* The browser polls for results every one to two seconds. A realistic test must reproduce this.
* The durations that matter most (upload to transcript ready; summary requested to summary ready) span many requests
  and a queue, so the tool must record custom timings.
* The backend, worker and evaluation code are Python, managed with Poetry. The frontend is TypeScript.
* All CI runs on GitHub-hosted runners.

Which tool should we use, and where should it run?

## Considered Options

Tool:

* Locust
* k6
* Playwright (browser-driven)
* Artillery
* AWS Distributed Load Testing

Execution:

* GitHub-hosted runner generates the load
* ECS Fargate task in the `perf` account generates the load, orchestrated by GitHub Actions
* Developer laptop

## Decision Outcome

**Locust**, because it fits our Python stack, supports the custom load shapes and custom timings we need, and the
load involved is small enough that raw generator efficiency does not matter.

**An ECS Fargate task in the `perf` account, orchestrated by manually triggered GitHub Actions workflows**, because
the load generator must be in the UK, come from known IP addresses and have fast access to S3. GitHub-hosted runners
meet none of these.

Test code lives in a top-level `perf/` package with its own Poetry dependency group and container image, so nothing
test-related is shipped in the application images.

## Pros and Cons of the Options

### Locust

* Good, because tests are Python and can reuse the application's types and the Poetry tooling used by the project.
* Good, because custom load shapes cover the ramp, hold, burst and breakpoint profiles.
* Good, because custom events can report end-to-end durations alongside request statistics.
* Good, because it runs headless and produces CSV and HTML reports.
* Bad, because one process uses one CPU core, so very high loads need distributed mode.

### k6

* Good, because it is efficient and has built-in pass/fail thresholds.
* Good, because tests are written in JavaScript, which our developers know.
* Bad, because it cannot reuse Python types or helpers, and adds a second toolchain for test code.
* Bad, because its efficiency advantage is irrelevant at our load.

### Playwright (browser-driven)

* Good, because it reproduces browser behaviour exactly, including polling, with no emulation to maintain.
* Good, because `integration-tests/` already uses it.
* Bad, because each virtual user needs a real browser, which is expensive at hundreds of users.
* Bad, because the load we care about is server-side, so browser fidelity adds little.

### Artillery

* Neutral, because it is capable, with YAML scenarios and JavaScript hooks.
* Bad, because multi-step journeys with polling and custom timings are awkward to express in YAML.
* Bad, because nobody on the team uses it.

### AWS Distributed Load Testing

* Good, because it provides managed Fargate execution and dashboards.
* Bad, because it deploys a complicated solution stack that we would need to own in Terraform.
* Neutral, because scenarios are still written for another tool, so it does not remove that choice.

### GitHub-hosted runner generates the load

* Good, because it needs no extra infrastructure.
* Bad, because runners are outside Great Britain and are blocked by the geo restriction.
* Bad, because runner IP addresses are unpredictable, so they cannot be allow-listed or exempted from the rate limit.
* Bad, because shared runners give variable network and CPU performance, which adds noise to results.

### ECS Fargate task in the `perf` account, orchestrated by GitHub Actions

* Good, because traffic originates in `eu-west-2` from the environment's fixed NAT gateway addresses.
* Good, because requests still enter through the public hostname, so the full path is tested.
* Good, because uploads to S3 are fast and consistent.
* Good, because the team triggers runs from the familiar GitHub Actions interface.
* Bad, because it needs a task definition and image repository in the `perf` account.

### Developer laptop

* Good, because it is ideal for developing and debugging scripts against `docker compose`.
* Bad, because results depend on the developer's network and are not repeatable.
* Bad, because office IP addresses would hit the rate limit.
