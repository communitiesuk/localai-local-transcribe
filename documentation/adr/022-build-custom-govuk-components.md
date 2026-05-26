# ADR-022: Build custom govuk-compliant React components (drop shadcn, keep Radix for exceptions)

## Status

Proposed

Date of decision: 2026-05-26

## Context and Problem Statement

Local Transcribe must comply with GDS service standards, which means adopting the GOV.UK Design System for user-facing patterns. The current frontend (generated from the i.AI cookiecutter) mixes three styling layers: `govuk-frontend` v6.1.0 (installed but used only in the layout shell and one editor warning list), 22 shadcn-style React components in `components/ui/` each wrapping a Radix primitive with Tailwind styling, and Tailwind v4 utility classes applied throughout. There is no documented convention on which layer to reach for, which puts the service at risk of failing the GDS compliance check on visual and accessibility consistency. We need a formal decision on how to bring the frontend into GOV.UK Design System compliance.

## Considered Options

* Build our own thin React wrappers around `govuk-frontend`
* Adopt an existing community React govuk-frontend library
* Continue with shadcn and custom styling
* Use GOV.UK Prototype Kit components

## Decision Outcome

Build our own thin React wrappers around `govuk-frontend`, drop the shadcn styling layer, and keep Radix primitives only in narrow cases where `govuk-frontend` has no equivalent.

Three threads make up the decision:

1. **Build our own govuk components.** Thin React wrappers around `govuk-frontend` HTML and CSS, living in `frontend/components/govuk/`, following the pattern already used in the layout shell. We control the upgrade cadence directly. The wrappers are mostly `className` composition and ARIA passthrough, so the maintenance burden is small. The evidence for rejecting community libraries lives in [`documentation/library-evaluation.md`](../library-evaluation.md) and is summarised in the Pros and Cons section below.
2. **Drop shadcn.** Its purpose was to give Radix a visual style. Once `govuk-frontend` is the source of styling, shadcn's role evaporates. The 22 components in `components/ui/` get migrated to `components/govuk/` for anything with a GOV.UK Design System equivalent, and the rest are reclassified as Radix-only.
3. **Keep Radix only for primitives where `govuk-frontend` has no equivalent.** Dialogs, popovers, tooltips, and the complex menus inside the rich-text editor have no GOV.UK Design System counterpart. Radix primitives are the most accessible unstyled primitives in the React ecosystem and remain the right tool for those gaps. The boundary is documented in the conventions doc that ships with the rewrite.

## Pros and Cons of the Options

### Build our own thin React wrappers around `govuk-frontend` (chosen)

The Design System ships as Nunjucks templates and CSS. We import the CSS in `app/govuk.scss` (already done) and write thin React wrappers around the HTML structure each component expects. The layout shell already follows this pattern.

* Good, because we control the upgrade cadence directly: when GOV.UK Design System moves, we move, not when a third-party maintainer ships a new version.
* Good, because the wrappers are genuinely thin (mostly `className` composition and ARIA passthrough), so the maintenance burden is small.
* Good, because it extends an existing pattern in the codebase rather than introducing a new approach.
* Good, because the Design System ships fully accessible HTML and the wrapper's job is to not break that. Accessibility comes for free if we wrap correctly.
* Neutral, because we own a small library of wrappers (perhaps 15 to 20 components by the time we are done).
* Bad, because in-house code is in-house code: bugs, drift, and onboarding cost are ours.

### Adopt an existing community React govuk-frontend library (rejected)

We evaluated six public candidates: `govuk-react`, `LandRegistry/govuk-react-components`, `@rottitime/govuk-design-react`, `penx/govuk-frontend-react`, `pa-digital/govuk-frontend-react`, `surevine/govuk-react-jsx`. The full matrix lives at `documentation/library-evaluation.md`. Headline reasons each was discounted:

* `govuk-react` (456 stars, 2,397 weekly downloads, 23 contributors) re-implements GOV.UK styles in CSS-in-JS rather than consuming the canonical CSS, and its annual release cadence trails the official Design System.
* `LandRegistry/govuk-react-components` is pinned to `govuk-frontend` v3.1.0 and has been dormant since 2021.
* `@rottitime/govuk-design-react` is the only v6.1-compatible candidate but is pre-1.0 with three contributors and 82 weekly downloads. Depending on it would be a worse single point of failure than maintaining our own wrappers.
* `penx/govuk-frontend-react` is a self-described proof of concept pinned to `govuk-frontend` v2 with seven weekly downloads.
* `pa-digital/govuk-frontend-react` targets `govuk-frontend` v5.3.1 with zero observable adoption.
* `surevine/govuk-react-jsx` is explicitly unmaintained, frozen at `govuk-frontend` v4.0.1, but pulls 43,406 weekly downloads. Its archived-but-popular status is exactly the failure mode this ADR aims to avoid: a popular community library that stalls and traps its consumers on an obsolete major.

* Good, because it would give us components for free out of the box.
* Bad, because no candidate credibly tracks `govuk-frontend` v6 with meaningful adoption.
* Bad, because adopting any candidate couples our upgrade pace to a third-party maintainer team whose posture we do not control.
* Bad, because the surevine evidence shows the failure mode: community libraries that reach significant download volumes and then stall force their consumers onto an obsolete `govuk-frontend` major with no upgrade path.

### Continue with shadcn and custom styling (rejected)

Keep the existing mix of shadcn / Radix / Tailwind / `govuk-frontend` without convention.

* Bad, because this is the problem the ADR is solving. The current state already fails to meet GDS compliance on visual and accessibility consistency.
* Bad, because shadcn was never designed to produce GOV.UK Design System markup. Achieving compliance through shadcn would mean restyling every component to the GOV.UK token system, which is the same amount of work as building wrappers around `govuk-frontend`, but with the wrong HTML.

### Use GOV.UK Prototype Kit components (rejected)

The Prototype Kit ships Nunjucks-based components (`@x-govuk/govuk-prototype-components`) intended for rapid prototyping rather than production React applications.

* Good, because the components are an MHCLG-aligned implementation of GOV.UK patterns.
* Bad, because they are Nunjucks templates, not React components. Integrating Nunjucks into a Next.js App Router app would require a parallel rendering pipeline.
* Bad, because the Prototype Kit is explicitly positioned for prototyping. Five MHCLG repos use it for prototypes, none for production frontends.

## Trade-offs

The chosen option carries three trade-offs worth recording explicitly:

* **Time cost.** Phase 0 of the rewrite (layout shell rewrite plus the minimum four form wrappers plus the worked example) is roughly one sprint with two people running in parallel. The full rewrite spans multiple sprints depending on parallelism. The critical path analysis at `documentation/critical-path-analysis.md` gives the workstream breakdown.
* **Maintenance burden.** We own a library of roughly 15 to 20 React wrappers. Each is thin (mostly `className` composition and ARIA passthrough), so the per-wrapper burden is small, but the team is responsible for following `govuk-frontend` releases and updating the wrappers when component contracts change.
* **Drift risk against upstream `govuk-frontend`.** If a `govuk-frontend` minor or major changes the HTML structure of a component, our wrapper has to be updated to match. The mitigation is to keep wrappers thin (so the change surface is small) and to track `govuk-frontend` releases.

## More Information

The current frontend state grounding this decision is visible in the codebase:

* The layout shell at `frontend/components/layout/header.tsx`, `footer.tsx`, and `alpha.tsx` cherry-picks `govuk-frontend` class names onto Tailwind structure rather than using the canonical `govuk-header`, `govuk-footer`, and `govuk-phase-banner` patterns. The first workstream of the rewrite brings these into canonical form.
* The 22 shadcn-style React components under `frontend/components/ui/` each wrap a Radix primitive with Tailwind styling.
* `frontend/package.json` declares `govuk-frontend: ^6.1.0` as a devDependency. The wrappers consume this directly via the CSS imported in `frontend/app/govuk.scss`.
