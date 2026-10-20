# ADR-031: Image Promotion Strategy

## Status

Draft

Date of decision: {yyyy-MM-dd}

## Context and Problem Statement

Local Transcribe is deployed to three environments (`development`, `staging`, `production`), each in its own AWS account.
Automated integration and developer team testing takes place in `development`. Product team testing takes place in
`staging`. Ideally, as work is promoted between environments, the differences between the builds / deployments
should be minimised, to reduce the risk of accidentally introducing defects.

How should we promote our work between environments to introduce as few changes as possible?

## Considered Options

* Rebuild per environment from `development`
* Rebuild per environment from a commit, with pinned inputs
* Rebuild per environment from an environment branch, with pinned inputs
* Build images for all environments at the same time
* Native ECR cross-account replication
* Runtime frontend configuration, copying images between registries
* Multi-bundle frontend image, copying images between registries

## Decision Outcome

Rebuild per environment from an environment branch, with pinned inputs, because it requires relatively few changes,
only stores deployed images in each environment's ECR, and makes it clear what is deployed in each environment.
Although promotion involves rebuilding images, rather than promoting the exact image, the opportunity for drift is
minimised.

## Pros and Cons of the Options

### Rebuild per environment from `development`

Merges to `development` build and deploy to the development environment. Staging and production deployments are
triggered manually against a branch (in practice `development`); the workflow rebuilds images in the target
environment from the head of that branch and applies its Terraform. This is the current approach.

* Good, because it already exists and is well understood.
* Good, because each environment's frontend is built with its own `NEXT_PUBLIC_*` values.
* Bad, because the deployed commit is "whatever is at the head of the branch", not a specific, previously-tested
  commit.
* Bad, because images are rebuilt at promotion time from unpinned inputs, so production may differ from what was
  tested even for the same commit.

### Rebuild per environment from a commit, with pinned inputs

Dockerfile base images are pinned by digest, apt-get installed packages are pinned by version
and `poetry export` is executed without `--without-hashes`. Deployments to development occur as now. Deployments
to staging and production are triggered manually by specifying a commit SHA that is reachable from `development`.

* Good, because the change is small: Dockerfile pinning plus a `commit_sha` input to the deploy workflow.
* Good, because images are built at promotion time, so any commit remains promotable regardless of development ECR
  retention.
* Neutral, because the inputs are the same but the outputs are not bit-for-bit identical (timestamps, Next.js build
  IDs), so equivalence cannot be verified by digest.
* Bad, because pinned apt versions (e.g. `ffmpeg`) are removed from Debian mirrors when superseded, so later builds
  of older commits can fail.
* Bad, because more pins need ongoing maintenance.

### Rebuild per environment from an environment branch, with pinned inputs

As above, but instead of specifying a commit SHA, create `staging` and `production` branches and automatically
deploy from those when they receive merges. No development work happens directly on these branches, only merges.

As above, plus:

* Good, because the state of each environment can be easily viewed on a named branch.
* Neutral, because changes to environments go through a PR - increasing visibility, but also increasing ceremony
  burden.

### Build images for all environments at the same time

On each merge to `development`, build images for every environment in one workflow run and push them to each
environment's ECR, tagged with the commit SHA. Backend and worker can be built once and pushed to all three registries
(identical digests); the frontend is built three times with each environment's `NEXT_PUBLIC_*` values. Promotion is
then a Terraform apply specifying the image, rather than a build step.

* Good, because all variants are built from the same source and pinned dependenceis at approximately the same moment,
  reducing build drift.
* Good, because promotion is fast and does not depend on external registries.
* Bad, because staging and production ECRs fill with images that may never be promoted, which interacts badly with
  count-based lifecycle rules (currently `image_retention_count = 10`): the image running in production, or a build
  someone wants to promote, may be expired by later development builds.
* Bad, because vulnerability scanning in staging and production would report on images that never ship, adding noise.

### Native ECR cross-account replication

Build environment-neutral images once in development and configure ECR registry replication to replicate them to the
staging and production accounts. Promotion is a Terraform apply specifying the image.

Note that converting the frontend image to be environment-neutral requires several changes: various data is baked
into the Next.js build, currently, and would need to be replaced with server-side reads of environment variables and
serving those variables to the client-side app (e.g. via a `window.__PUBLIC_CONFIG__` global variable). Pre-rendered
pages would need special handling to avoid the client-side configuration being pre-rendered.

* Good, because the same image digests run in every environment.
* Bad, because it requires environment-neutral images, so the frontend must first move to runtime configuration.
* Bad, because every development image is replicated to staging and production, with the same lifecycle-expiry and
  scanning-noise issues as building for all environments at once.
* Neutral, because replication is asynchronous, so deploy jobs must wait for images to arrive, although in practice
  promotions will usually be a relatively long time after builds.

### Runtime frontend configuration, copying images between registries

Build environment-neutral images, as above. Promote by copying them with `crane copy`, instead of replicating
every image.

* Good, because a single, digest-identical image is promoted unchanged.
* Good, because staging and production ECRs only contain promoted images.
* Bad, because it requires environment-neutral images, so the frontend must first move to runtime configuration.
* Neutral, because a development image must still be copied to staging before the development ECR lifecycle policy
  expires it, but we would typically only promote recently deployed images.

### Multi-bundle frontend image, copying images between registries

Build the Next.js frontend once per environment within a single Docker build, using separate build stages with each
environment's `NEXT_PUBLIC_*` values supplied as build secrets. Build a single runtime image containing all standalone
Next.js builds in different directories, and select the appropriate one at container start based on an environment
variable. Images are built once in development and promoted with `crane copy`, as above.

* Good, because a single, digest-identical image set is promoted unchanged.
* Good, because no application code changes are needed, and pages retain their current rendering behaviour.
* Good, because staging and production ECRs only contain promoted images.
* Neutral, because production's public configuration values (Sentry DSN, Plausible domain) are present
  in the development image; these are already exposed to browsers and are not secrets.
* Bad, because the frontend image grows by roughly two additional standalone outputs, and frontend build time
  increases (mitigated by parallel stages).
* Neutral, because a development image must still be copied to staging before the development ECR lifecycle policy
  expires it, but we would typically only promote recently deployed images.

## More Information

* [crane](https://github.com/google/go-containerregistry/blob/main/cmd/crane/README.md)
* [Amazon ECR private image replication](https://docs.aws.amazon.com/AmazonECR/latest/userguide/replication.html)