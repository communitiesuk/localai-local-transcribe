# ADR-030: Branching Strategy

## Status

Draft

Date of decision: {yyyy-MM-dd}

## Context and Problem Statement

Currently, features branches are merged into `development` by PRs. Each merge causes a build and deployment
into the `development` AWS environment. Deployments to `staging` and `production` are triggered manually,
with each deploying the head of the `development` branch. It is difficult to avoid releasing incomplete,
untested, or otherwise unreleasable work as a result. Such work blocks releases (including urgent fixes)
until it is completed or reverted.

What branching strategy should we use so that commits can be integrated frequently and in-progress work
can be managed without blocking releases?

## Considered Options

* Merge to `development` without feature flags
* Trunk-based development, feature flags, and hotfix exceptions
* Release branches

## Decision Outcome

Trunk-based development, feature flags, and hotfix exceptions, because it aims to make every commit on `development`
releasable (so any commit can be promoted to staging), while keeping branches short-lived and the process simple.

## Pros and Cons of the Options

### Merge to `development` without feature flags

Feature branches are merged into `development` when complete. Staging and production are deployed from the head of
`development`. This is the current approach.

* Good, because it already exists and needs no new tooling.
* Bad, because promoting a commit promotes everything merged before it, so one unready change blocks all releases.
* Bad, because there is no defined path for urgent fixes when `development` is not releasable.

### Trunk-based development, feature flags, and hotfix exceptions

All changes are merged into `development` frequently via short-lived branches. Incomplete work is hidden behind
feature flags, so every commit on `development` is, in theory, releasable. Fixing forward is preferred, but where
not possible, hotfix branches (from the currently deployed commit) can be created used to deploy from (and merged
back to `development`).

* Good, because unfinished features need not prevent other changes from being released.
* Good, because short-lived branches reduce merge conflicts and keep integration continuous.
* Good, because release (enabling a feature) is decoupled from deployment (shipping code), so features can be
  enabled per environment, and disabled without a rollback.
* Good, because hotfixes use the same build-and-promote workflow as normal releases.
* Neutral, because it depends on a feature flag mechanism; exactly what is left for another ADR.
* Bad, because flags add code paths and testing combinations, and need discipline to remove once a feature is fully
  released.
* Bad, because it relies on the trunk always being releasable, which requires team discipline.

### Release branches

A `release/*` branch is cut from `development` when a release is planned, stabilised (e.g. reverting in-progress work),
and promoted to staging and production from that branch.

* Good, because unready work on `development` does not block a release, without needing feature flags.
* Good, because it provides a natural place for hotfixes to an in-flight or recent release.
* Bad, because fixes must be applied to both the release branch and `development`, which is error-prone.
* Bad, because release branch commits are either never deployed to development, or require complex deployment management.
* Bad, because it adds process and ceremony that is disproportionate for a small team releasing frequently.

## More Information

* [Trunk-based development](https://trunkbaseddevelopment.com/)
* [Branch by abstraction](https://trunkbaseddevelopment.com/branch-by-abstraction/)
