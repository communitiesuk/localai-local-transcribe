# ADR-034: Load Test Environment, Test Identity and AI Dependencies

## Status

Proposed

Date of decision: pending (drafted 2026-11-13)

## Context and Problem Statement

ADR-033 proposes peak load and breakpoint testing. Three questions must be answered before any of it can be built.

**Where do tests run?** Currently we have `development`, `staging` and `production`, each in its own AWS environment 
(ADR-031). Staging is much smaller than production (backend 256 CPU units against 4096; one worker against two), it is
the release promotion path, and it shares the APIM test endpoint with development.

**How do virtual users sign in?** The load balancer authenticates users against GDS Internal Access (ADR-026), which
emails a one-time code. The backend accepts only the load balancer's signed `x-amzn-oidc-data` token, and checks its
signer, issuer and audience and requires `email` and `sub` claims (`common/auth.py`). The only bypass is
`ENVIRONMENT=local`. There is no way for a script to sign in.

**Do tests call the real AI services?** Every transcription and summary goes through MHCLG's Azure APIM to Azure
Speech and Azure OpenAI, with costs and quotas we do not control.

## Considered Options

Environment:

* Dedicated `perf` environment in its own AWS account
* Staging, in a booked window, temporarily resized
* Production, out of hours

Test identity:

* Cognito user pool as the load balancer's identity provider, with an adapter
* Self-built mock identity provider
* Test-only trusted signing key in application code
* Disable load balancer authentication

AI dependencies:

* Always call real APIM
* Always stub
* Stub by default, with one calibration run against real APIM

## Decision Outcome

**Dedicated `perf` environment**, because it is the only option that is production-sized, does not block releases, and
can have its identity provider replaced without affecting anyone. It is sized like production while a test runs and
scaled to zero tasks otherwise.

**Cognito user pool with an adapter, in `perf` only**, because the whole production request path is exercised
(CloudFront, WAF, load balancer authentication, frontend, backend) and no authentication bypass is added to
application code. GDS Internal Access itself is not tested.

**Stub by default, with one calibration run**, because stubbing makes runs free, repeatable and able to go beyond
real quotas, while one measured run against APIM checks quota at the target peak.

Safeguards: the Cognito pool, adapter and stub are created only by `terraform/perf`; the production Terraform root
does not expose the variables that select them; real-AI runs happen only in a window and volume agreed with the APIM
team.

## Pros and Cons of the Options

### Dedicated `perf` environment

* Good, because task sizes and counts can match production exactly.
* Good, because tests never block or pollute the release path.
* Good, because test-only infrastructure is isolated in one account.
* Bad, because it needs a new AWS account and DNS changes.
* Bad, because it has fixed costs when idle (NAT gateway, load balancer, database storage).
* Bad, because it is a fourth environment to keep deployable.

### Staging, in a booked window, temporarily resized

* Good, because it exists today and needs no new account or DNS.
* Bad, because releases are blocked during tests and test data must be cleaned out afterwards.
* Bad, because replacing its identity provider would break real sign-in testing on staging.
* Bad, because resizing up and down for each run is error-prone.

### Production, out of hours

* Good, because it is exactly the system we care about.
* Bad, because it holds real users' recordings and case data.
* Bad, because test accounts and synthetic data would have to be created in the live service.
* Bad, because a failed test becomes a production incident.

### Cognito user pool with an adapter

* Good, because application authentication code is unchanged and fully exercised.
* Good, because passwords and sessions are handled by a managed service.
* Good, because Cognito's hosted domain needs no DNS request.
* Neutral, because virtual users must script the hosted sign-in form once per run.
* Bad, because the adapter is an extra component, and Cognito's sign-in rate limits constrain how fast users start.
* Bad, because it is unproven until built.

### Self-built mock identity provider

* Good, because claims are fully under our control and sign-in is trivial to script.
* Good, because there are no third-party rate limits.
* Bad, because we would be writing our own identity provider instead of using an existing one.
* Bad, because it must be publicly reachable over HTTPS with a publicly trusted certificate.

### Test-only trusted signing key in application code

* Good, because it is the simplest to build and to script against.
* Bad, because it adds an authentication bypass to production code, relying on configuration never being wrong.
* Bad, because tests would skip the load balancer's authentication step.
* Bad, because it would need security review and would be raised by penetration testers.

### Disable load balancer authentication

* Bad, because the backend still requires a signed token, so this achieves nothing without the previous option.

### Always call real APIM

* Good, because results include real service behaviour.
* Bad, because every run costs money in proportion to audio hours, which rules out breakpoint testing.
* Bad, because the APIM test instance's quotas may differ from production's, so results may not transfer anyway.
* Bad, because heavy runs may affect other APIM tenants.

### Always stub

* Good, because runs are free and repeatable.
* Good, because failures and throttling can be injected deliberately.
* Bad, because invented response times could make the results untrustworthy.
* Bad, because real quota limits would never be discovered.

### Stub by default, with one calibration run

* Good, because it keeps the benefits of stubbing.
* Good, because the calibration run checks for throttling at the target peak.
* Bad, because the stub must be built.
* Neutral, because the calibration run needs agreement from the APIM team.

## More Information

* If the adapter approach fails when built, fall back to the self-built mock identity provider.
* Fixed monthly cost of an idle `perf` environment can to be estimated from the development account's bill.
