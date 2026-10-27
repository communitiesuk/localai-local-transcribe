# ADR-032: Feature Flag Mechanism

## Status

Draft

Date of decision: {yyyy-MM-dd}

## Context and Problem Statement

To support trunk-based development (ADR-030), we require per-environment feature flags. We also expect that it
may be useful, either now or in future, to run A/B style experiments, and to be able to dynamically configure
feature flags (e.g. to roll back a buggy feature quickly). We currently have no feature flag mechanism.

What mechanism should we use to define, evaluate, and change feature flags?

## Considered Options

* Per-environment flags in the repository
* AWS AppConfig feature flags
* Database-backed flags, managed by developers
* Database-backed flags, with an admin UI
* Third-party feature flag service
* Self-hosted experimentation platform

## Decision Outcome

AWS AppConfig feature flags, because it supports even our nice-to-have use cases (fine-grained flags, runtime changes,
A/B experiments) without the need for any new product assurance or procurement.

## Pros and Cons of the Options

### Per-environment flags in the repository

Flags and their per-environment values are defined in the repository (e.g. as Terraform variables passed to ECS task
definitions as environment variables, or as a flags file keyed by environment). The backend reads them at startup and
exposes them to the frontend.

* Good, because it is simple to build, with no new infrastructure, services or suppliers.
* Good, because flag changes are version-controlled and code-reviewed, and are promoted with the commit that contains
  them, so each environment's flag state is fully described by its deployed commit.
* Good, because local development and test overrides are simple.
* Neutral, because changing a flag in an environment means promoting a commit, though trunk-based development should
  mean this is feasible.
* Bad, because flags cannot change without a deployment, making them slow as an emergency kill switch.
* Bad, because there is no targeting below the environment level.
* Bad, because product/delivery team members cannot change flags without developer help.
* Bad, because it does not support experiments.

### AWS AppConfig feature flags

Flags are defined as AWS AppConfig feature flag configuration profiles in each environment's AWS account. Flag
definitions can be managed in Terraform, with flag values either also managed in Terraform or changed at runtime via
the AWS console/CLI (with Terraform configured to ignore value changes). The backend retrieves flags via the AppConfig
Data API (with caching) or the AppConfig Agent sidecar. Multi-variant flags can return different values based on context
supplied by the backend (e.g. organisation or user ID), including percentage splits; note this requires using the Agent.

* Good, because AWS services are already assured, so no new supplier assurance or procurement is required.
* Good, because flags can change without a deployment, with built-in validation, gradual deployment and automatic
  rollback on CloudWatch alarms.
* Good, because multi-variant flags support per-organisation, per-user and percentage targeting.
* Good, because changes are audited via CloudTrail.
* Neutral, because there is a cost, but it is low (tens of dollars a month, even without caching, for private beta workloads)
* Bad, because A/B testing experiments have a cost ($0.90 per experiment-hour: ~$650 for a one month experiment)
* Bad, because product/delivery team members would need AWS console access to each environment's account (including
  production) to change flags, or a custom wrapper would need building.
* Neutral, because a local implementation for development and tests will need some thought, but the AppConfig Agent does
  provide a local development mode in which is reads from a file instead of from AWS config.

### Database-backed flags, managed by developers

Flags are stored in the application's Postgres database: flag definitions (with default values) are created via
Alembic migrations, and optional overrides can be set per organisation or user. The backend evaluates flags 
(optionally with a short-lived cache). There is no UI: developers change flag values directly in each environment's
database (e.g. via the bastion).

* Good, because flags can change without a deployment.
* Good, because per-organisation and per-user targeting are possible, either immediately or as extensions.
* Good, because it requires no new infrastructure, services or suppliers.
* Neutral, because percentage rollouts would need building (e.g. deterministic hashing of user IDs).
* Bad, because routine flag changes require developers to write directly to production databases, which is
  error-prone and increases the use of privileged production access.
* Bad, because flag changes are not code-reviewed, and are only audited if we build auditing (e.g. an audit table or
  trigger).
* Bad, because product/delivery team members cannot change flags without developer help.
* Bad, because analytics and analysis for experiments would need to be built.

### Database-backed flags, with an admin UI

As above, but with an admin UI in Local Transcribe for viewing and changing flag values and overrides, restricted to
a suitable role.

As above, but also:
* Good, because product/delivery team members can change flags without developer help.
* Bad, because it requires the most build effort of the in-house options.
* Good, because no direct database access is needed

### Third-party feature flag service

Use a hosted feature flag service, such as LaunchDarkly, ConfigCat, Flagsmith Cloud or Unleash Cloud, via its
server-side SDKs in the backend.

* Good, because it provides a mature UI, targeting (per organisation, per user, percentage), audit logs and
  permissions, with minimal build effort.
* Good, because flags can change without a deployment.
* Good, because product/delivery team members can change flags without developer help.
* Bad, because the service would need to go through cyber assurance.
* Bad, because a paid plan would need to go through procurement.
* Neutral, because whether user identifiers are sent to the supplier depends on the product: some SDKs (e.g.
  ConfigCat) evaluate targeting rules locally after downloading them, while others evaluate remotely.
* Neutral, because experiment support varies by product, and is often a separately priced add-on.

### Self-hosted experimentation platform

Self-host an open source (or source-available) platform that supports both feature flags and experiments (e.g.
GrowthBook) on our own infrastructure, such as ECS. The backend uses the platform's SDK to evaluate flags and assign
variants, and experiment exposures and outcomes are analysed by the platform.

* Good, because experiment assignment, tracking, and analysis are are all typically supported, with some integration.
* Good, because flags can change without a deployment.
* Good, because product/delivery team members can change flags without developer help.
* Good, because the core product is typically free to self-host (sometimes excluding e.g. SSO, audit).
* Neutral, because products differ in where experiment data comes from: some analyse metrics directly from our own
  database, while others ingest and store events themselves (possibly duplicating analytics data in a new store).
* Bad, because it is a new service to run, patch and secure, and may require additional data stores of its own (e.g.
  GrowthBook requires a MongoDB-compatible database, such as Amazon DocumentDB).

## More Information

* [OpenFeature](https://openfeature.dev/)
* [AWS AppConfig feature flags](https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-creating-multi-variant-feature-flags.html)
* [GrowthBook self-hosting](https://docs.growthbook.io/self-host)
* Third-party services: [LaunchDarkly](https://launchdarkly.com/), [ConfigCat](https://configcat.com/),
  [Flagsmith](https://www.flagsmith.com/), [Unleash](https://www.getunleash.io/)
