# Frontend rewrite critical path analysis

**Question:** Of the workstreams in the GOV.UK Design System adoption, which ones genuinely block other work, and what is the longest unavoidable chain? Where can the team fan out and run in parallel?

**Date:** 2026-05-26.

---

## Current state of the layout shell

An earlier read assumed the layout shell already uses `govuk-frontend` and that layout-first work was unnecessary. On inspection the layout shell uses some GOV.UK class names but is not structurally canonical GOV.UK Design System:

| File | State | Evidence |
|---|---|---|
| `components/layout/header.tsx` | **Partial / mixed.** Cherry-picks `govuk-header__homepage-link`, `govuk-header__product-name`, `govuk-link--inverse`, `var(--govuk-brand-colour)` onto a raw `<header className="flex h-[64px] ... bg-[var(--govuk-brand-colour)] px-8">`. The canonical `<header class="govuk-header" data-module="govuk-header">` structure is not in use. |
| `components/layout/footer.tsx` | **Two definitions in one file.** Line 3 exports `const Footer` (Tailwind only: `bg-black px-4 py-2 text-white`). Line 21 default-exports `GovFooter` (canonical `govuk-footer`). Whichever export the consumer imports decides what renders. |
| `components/layout/alpha.tsx` (the phase banner) | **Bespoke Tailwind.** Uses `bg-blue-200`, `text-blue-600`. Not `govuk-phase-banner` with `govuk-tag`. |

**Should the layout shell land before individual form components?** Yes in practice. The layout shell is not in canonical GOV.UK Design System form. If form pages migrate to canonical GOV.UK form components but the page frame around them is bespoke Tailwind, the result will look visually inconsistent. It is not a hard technical blocker (form wrappers can be written without changing the layout files), but it is a soft visual and coherence blocker for any meaningful page migration.

---

## Workstreams

The acceptance criteria name seven minimum workstreams. Three additional workstreams are needed to cover the full scope (display-component wrappers, authenticated route gating, cross-cutting deliverables, page migrations).

Each workstream has a T-shirt size: **S** ≈ under 1 day, **M** ≈ 1-3 days, **L** ≈ 3-10 days.

### Minimum workstreams from acceptance criteria

| ID | Workstream | Size | What's in it |
|---|---|---|---|
| **WS-1** | **govuk page layout** | M | Rewrite `header.tsx` to canonical `govuk-header`. Replace footer.tsx (delete the Tailwind variant, promote `GovFooter`). Replace `alpha.tsx` with canonical `govuk-phase-banner`. Add `govuk-skip-link`. Wrap `app/layout.tsx` body in `govuk-template__body` + `govuk-width-container` + `govuk-main-wrapper`. |
| **WS-2** | **individual form components** | M | Nine thin wrappers per `approach.md` decision tree: `GovukButton`, `GovukInput`+`GovukLabel`+`GovukHint`, `GovukTextarea`, `GovukSelect`, `GovukCheckboxes`, `GovukRadios`, `GovukFieldset`+`GovukErrorMessage`, `GovukErrorSummary`, `GovukBackLink`. |
| **WS-3** | **navigation patterns** | S | Replace bespoke nav in header with `govuk-service-navigation` (or `govuk-header__navigation` if the team prefers the simpler pattern). Active-state handling per page. Mobile responsive behaviour from govuk-frontend. |
| **WS-4** | **error and loading states** | M | Patterns for error pages (404, 500, 403 unauthorised) and loading skeletons. Top-level error boundary in `app/error.tsx`. Integration with existing `<GovukErrorSummary>` for form validation. The govuk-frontend doesn't ship a loading-skeleton pattern, so this is partly bespoke with govuk-tokens. |
| **WS-5** | **accessibility audit setup** | M | Install `axe-core` + `jest-axe`. Initial axe audit of the existing app (capture baseline a11y findings). Wire a CI step to fail builds on new a11y regressions. Document findings + remediation backlog. |
| **WS-6** | **Welsh language support scaffolding** | L (**deferred 2026-05-26**) | Add an i18n library (`next-intl` or similar). Lang switcher in the layout (`/cy` route prefix). Configure govuk-frontend's bilingual string variants. **No Welsh content currently exists in the codebase** (`grep` finds no `lang="cy"`, `welsh`, `cymraeg`, `i18n` strings). Deferred for now. Stays on the diagram as a dotted "if in scope" branch so it resurfaces if product reverses the decision. |
| **WS-7** | **React framework decisions (Next.js patterns, server vs client components)** | S | Document which wrappers must carry `'use client'` (anything with event handlers, hooks, or interactive state, so `Button`, `Tabs`, `Accordion`, `Details`, `Checkboxes`/`Radios` if they manage their own state). Document server-component-safe wrappers (`Label`, `Hint`, `ErrorMessage`, `Tag`, pure-markup ones). Decision on form submission style: keep React Hook Form (client) or move to server actions (more aligned with App Router). Outcome: a section in the conventions doc. |

### Additional workstreams

| ID | Workstream | Size | What's in it |
|---|---|---|---|
| **WS-A** | **authenticated route gating** | M | Audit current auth/role checks across pages. Standardise on a server-component check at the top of protected layouts. Closest to App Router idioms, runs before the page renders, no client-side flash of unauthorised content. Sits on the likely critical path. |
| **WS-B** | **display-component wrappers** | M | `GovukTag`, `GovukDetails`, `GovukAccordion`, `GovukNotificationBanner`. Not in AC minimum but listed in `approach.md` as part of the in-scope migration. **Tabs decision (2026-05-26):** the transcription detail page (Chat / Minute / Transcript switching) stays on Radix as a documented exception, since `govuk-tabs` is designed for static linkable tab content, not dynamic in-app switching. Static tab use elsewhere uses `GovukTabs`. |
| **WS-C** | **cross-cutting deliverables** | M | Conventions doc, ESLint rule banning new imports from `components/ui/`, worked-example form page migration end-to-end (decision 2026-05-26: `app/settings/page.tsx` is the worked example, since it exercises the minimum 4 form wrappers without audio / TipTap complications), `govuk-frontend` v6.2 patch upgrade bundled with Sprint 1 if v6.2 is out of beta by mid-sprint, otherwise deferred. This workstream produces the "team can build the new way" gate. |
| **WS-D** | **page migrations** | L+ (cumulatively, across many pages) | All page-level migrations: `app/new/*` (5 form pages), `app/templates/*` (2), `app/settings/page.tsx`, `app/page.tsx`, `app/transcriptions/*` (2), static pages (4). Spans multiple weeks if pursued sequentially, much faster if parallelised. |

---

## Dependency map

```mermaid
graph TD
    WS7[WS-7: React framework decisions<br/>S]
    WS1[WS-1: govuk page layout<br/>M]
    WS5[WS-5: a11y audit setup<br/>M]
    WS2[WS-2: form wrappers<br/>M]
    WS3[WS-3: navigation patterns<br/>S]
    WS4[WS-4: error and loading states<br/>M]
    WSA[WS-A: authenticated route gating<br/>M]
    WSB[WS-B: display-component wrappers<br/>M]
    WSC[WS-C: cross-cutting + worked example<br/>M]
    WS6[WS-6: Welsh language scaffolding<br/>L, deferred 2026-05-26]
    WSD[WS-D: page migrations<br/>L+ across many pages]
    GATE([GATE: team can build the new way])

    WS7 --> WS2
    WS1 --> WS3
    WS1 --> WSC
    WS2 --> WSC
    WSA --> WSC
    WSC --> GATE
    GATE --> WSD

    WS5 -. parallel .-> GATE
    WS4 -. parallel .-> WSD
    WSB -. parallel .-> WSD
    WS6 -. if in scope .-> WSD

    style GATE fill:#2e7d32,color:#fff
    style WS7 fill:#fff3e0
    style WS1 fill:#fff3e0
    style WS2 fill:#fff3e0
    style WSA fill:#fff3e0
    style WSC fill:#fff3e0
```

Solid arrows are hard dependencies. Dotted arrows show parallelisable work that doesn't block the gate (or doesn't block its specific downstream). Amber fill marks the critical path. Green fill marks the "team can build the new way" gate.

---

## The critical path

The longest unavoidable chain is:

```
WS-7 (framework decisions, S)
   ↓
WS-1 (page layout, M)  ──┐  } in parallel: A and B can both run after WS-7
WS-2 (form wrappers, M) ─┤
WS-A (auth gating, M)  ──┘
   ↓
WS-C (worked-example form page end-to-end + conventions doc + ESLint, M)
   ↓
GATE: team can build the new way
```

**Estimated critical-path length:**

| Stage | T-shirt | Notes |
|---|---|---|
| WS-7 | S | Decisions, not implementation. Can be settled in a single sitting. |
| WS-1 + WS-2 + WS-A in parallel | M | Three workstreams, each M. If three people take one each, the longest pole is whichever finishes last (≈ M). If one person sequences them, ≈ 3×M = up to a sprint. |
| WS-C | M | Worked example + conventions doc + ESLint. Can be partly overlapped with the tail of WS-1/2/A. |

**Realistic critical-path window: ≈ 1 sprint with two people running in parallel, ≈ 2 sprints solo.**

---

## Parallelism off the critical path

These workstreams do not block the gate. They run independently once their own prerequisites are met:

- **WS-3 (navigation patterns)**: blocked only on WS-1. Can land alongside WS-2 or just after WS-1.
- **WS-4 (error and loading states)**: independent. Can start any time.
- **WS-5 (accessibility audit setup)**: independent. Can start any time. Useful to run early to catch issues in the new wrappers as they land.
- **WS-B (display-component wrappers)**: independent of the critical path. Blocked on Open Question O3 for `Tabs` specifically.
- **WS-6 (Welsh language scaffolding)**: deferred (decision 2026-05-26). Stays in the diagram on the dotted "if in scope" branch so the option resurfaces if product reverses.
- **WS-D (page migrations)**: gated by the GATE, not on the critical path. Cumulatively the largest work but trivially parallelisable across team members once the gate opens.

---

## Recommended execution order

**Sprint 1 (this week):**

1. WS-7 (React framework decisions): half-day discussion plus writeup.
2. WS-1 (page layout) + WS-2 (form wrappers) + WS-A (auth gating): parallel streams. WS-1 and WS-A in particular shape WS-2's implementation, so a brief sync between owners mid-sprint is worth it.
3. WS-5 (a11y audit setup): start in parallel. Bench the baseline before the rewrite changes anything.
4. WS-C (worked-example end-to-end): runs in the tail of Sprint 1 once WS-2 has at least the minimum 4 form wrappers (`Button`, `Input`/`Label`/`Hint`, `Fieldset`/`ErrorMessage`, `ErrorSummary`).
5. **Hit the GATE by end of Sprint 1.**

**Sprint 2 onwards (parallel streams):**

- Stream A: complete WS-2 (remaining form wrappers) + WS-B (display wrappers, resolve Tabs question).
- Stream B: WS-3 (navigation) + WS-4 (error and loading states).
- Stream C: WS-D, page migrations, prioritise by user traffic (home, transcriptions list, new transcription flow).
- Out-of-band: govuk-frontend v6.2 patch upgrade, ESLint rule landing.

---

## Settled execution-order questions

1. **Welsh language support (WS-6): deferred.** No Welsh content in the codebase today, the decision belongs to product rather than engineering. WS-6 stays in the diagram on the dotted "if in scope" branch so the option resurfaces if product reverses.
2. **Worked-example page for WS-C: `app/settings/page.tsx`.** Small form, no audio / TipTap complications, exercises the minimum 4 form wrappers (`Button`, `Input`+`Label`+`Hint`, `Fieldset`+`ErrorMessage`, `ErrorSummary`).
3. **Authenticated route gating (WS-A): server-component check at the top of protected layouts.** Closest to App Router idioms, runs before the page renders, no client-side flash of unauthorised content. Drops the Next.js middleware and client-side guard alternatives.
4. **Tabs (WS-B): Radix exception for the transcription detail page only.** `govuk-tabs` is designed for static linkable tab content, not for app-style dynamic switching with state. Documented as a Radix exception in the conventions doc. Static tab use elsewhere uses `GovukTabs`.
5. **`govuk-frontend` v6.2 upgrade timing: conditional bundle.** Bundle with Sprint 1 (alongside WS-1 layout rewrite) if v6.2 is out of beta by mid-sprint, otherwise defer to a separate PR after the rewrite lands. No reason to ship a beta dep just to save a future PR.
