# Frontend library evaluation matrix

**Baseline:** Local Transcribe currently pins `govuk-frontend: ^6.1.0` (npm devDependency in `frontend/package.json`) and pulls in `@radix-ui/*` primitives for non-GOV.UK UI. There is no React component-library wrapper installed; the GOV.UK styles come straight from the upstream package and components are written by hand in `frontend/components/`.

**Evaluation date:** 2026-05-26.

---

## Methodology

**What was searched.** Public GitHub and npm for React component libraries claiming GOV.UK Design System compatibility. Query terms:

- `"React govuk-frontend wrapper library v6 npm 2025"`
- `"HM Land Registry HMLR React govuk-frontend component library GitHub"`
- `"govuk-frontend React peer dependency"`
- Direct inspection of libraries surfaced in team review (specifically the HMLR React govuk-frontend repository), plus any library surfaced by a GOV.UK service team blog post or repo cross-reference.

**Sources consulted.** GitHub repository pages (commits, branches, package.json, README, ACCESSIBILITY.md where present); npm public download API (`api.npmjs.org/downloads/point/last-week/*`); bundlephobia.com (for packages on npm); GitHub contributors API.

**Selection criteria.** For each candidate: declared `govuk-frontend` peer dependency, last meaningful commit and release, React compatibility, component coverage, license, observable adoption (stars, weekly downloads, contributor count, public consumers), accessibility-test posture, bundle size.

**Disqualification rule.** A candidate is discounted if any of: explicitly marked unmaintained or archived; pinned to `govuk-frontend` v4 or earlier with no upgrade path to v6; pre-1.0 single-maintainer with no production consumers; "proof of concept" status; not actually a React component library (e.g. Nunjucks-based prototype components).

---

## Matrix

| Library | Current ver | govuk-frontend | React | Adoption (stars / contributors / npm weekly DLs) | Component coverage | A11y test posture | Bundle (min / gzip) | License | Discounted because |
|---|---|---|---|---|---|---|---|---|---|
| **[govuk-react](https://github.com/govuk-react/govuk-react)** | v0.10.7 (May 2024) | Not declared as peer dep. Uses styled-components, re-implements GOV.UK styles in CSS-in-JS rather than consuming `govuk-frontend` CSS. | React ≥16.8.0 (peer) | 456 / **23** / 2,397 | Full set via `@govuk-react/*` sub-packages (Button, Input, Date Input, Checkbox, Radio, Tabs, Header, Footer, Phase Banner, Error Summary, ~30+ components) | Separate `ACCESSIBILITY.md` exists in repo, no automated a11y test suite claim in README | 185.5 kB / 54 kB | MIT | Re-implements GOV.UK styles in CSS-in-JS rather than consuming the canonical govuk-frontend CSS, so any Design System change has to wait on a coordinated upstream PR before we can use it. Annual release cadence trails the official Design System. Adopting it would couple our upgrade pace to a small volunteer maintainer team rather than to govuk-frontend itself. |
| **[LandRegistry/govuk-react-components](https://github.com/LandRegistry/govuk-react-components)** | v3.1.0-3 (untagged) | **govuk-frontend 3.1.0** (peer dep, master `package.json`), pinned to v3 | React 16 (regular dep) | 3 / **4** / not on npm | JSX ports of Nunjucks macros, lightweight (assumes consumer brings the CSS) | No a11y test claims | Not on npm | MIT | Pinned to govuk-frontend v3 from 2021, three majors behind. Last meaningful commit was 2021-07-13 (a Dependabot ssri bump), so the repo has been dormant for nearly five years. No SSR / Next.js support claimed. Was initially evaluated as a possible v6-compatible option, but on inspection predates v5. |
| **[@rottitime/govuk-design-react](https://github.com/rottitime/govuk-design-react)** | v0.14.4 (Apr 2026) | **^6.1.0** peer dep (matches our baseline) | React ≥16.8.0 (peer) | 3 / **3** / 82 | TypeScript, Storybook at rottitime.github.io/govuk-design-react. Component coverage in progress, library pre-1.0 | README claims "designed to meet the highest accessibility standards" but no specific tooling / WCAG test suite declared | Not on bundlephobia | MIT | The only v6.1-compatible option in the public ecosystem, but adoption is effectively zero (82 weekly downloads, 3 stars, 3 contributors, no production users surfaced) and the library is pre-1.0. Depending on a single-maintainer pre-1.0 library would be a worse single point of failure than maintaining our own wrappers. |
| **[penx/govuk-frontend-react](https://github.com/penx/govuk-frontend-react)** | v0.0.12 | `govuk-frontend: ^2.4.0` (pinned to v2, four majors behind) | React peer `>=15` | 4 / **1** / 7 | Partial: Button, Header, Input, Date Input, Radios, Tables, Error Summary (several marked TODO) | No a11y test claims | Not on bundlephobia | ISC | Self-described proof of concept, pinned to govuk-frontend v2 (four majors behind), component coverage incomplete with several components still marked TODO. Single maintainer, 7 weekly downloads. Not suitable for production use. |
| **[pa-digital/govuk-frontend-react](https://github.com/pa-digital/govuk-frontend-react)** | Released v1.0.11 (May 2024). `main` branch package.json shows v3.7.5 with `govuk-frontend: ^5.8.0` (unreleased work). | Released: v5.3.1. Main branch: ^5.8.0. Either way, not v6. | React 18 (devDep only, no formal peer) | 0 / **1** / not on npm | Component list not exposed on repo page | No a11y test claims | Not on npm | MIT | Latest release (v1.0.11, May 2024) targets govuk-frontend v5.3.1, with unreleased work on main moving to v5.8.0. Neither reaches v6. Zero observable adoption: 0 stars, 0 forks, 1 contributor, not published to npm under a discoverable name. No signal of production use. |
| **[surevine/govuk-react-jsx](https://github.com/surevine/govuk-react-jsx)** | v7.1.0 (Jul 2022) | **govuk-frontend: 4.0.1** (frozen) | React ^18.1.0 (regular dep) | 4 / **3** / **43,406** (most-downloaded React govuk wrapper, despite archived status) | Panel, Input, Select, Radios, Checkboxes, Date Input, Error Summary, Table, Header, Footer, etc. (broad) | Test suite validates output against reference govuk-frontend markup; no automated WCAG test claims | 61.7 kB / 12 kB | MIT | Explicitly unmaintained since 2022, frozen at govuk-frontend v4.0.1 (two majors behind). The 43k weekly downloads despite the archival warning is exactly the failure mode this ADR aims to avoid: a popular community library that stalls and traps its consumers on an obsolete major. The maintainers' own recommendation is to copy components into your own project, which is what this ADR proposes. |

---

## Out of scope / not React component libraries (noted for completeness)

- **[@x-govuk/govuk-prototype-components](https://x-govuk.github.io/)**: Nunjucks-based components for the GOV.UK Prototype Kit. Used by five MHCLG repos *for prototyping only*, never as a production React library. Not a candidate for this evaluation, but appears as a separate considered-option in the ADR.
- **[@hmlr/frontend](https://github.com/LandRegistry/hmlr-frontend)**: HMLR's own design-system Sass/JS package. Not React. Distinct from the React-components repo evaluated above.

---

## Summary of facts

- **No published React component library currently targets `govuk-frontend` v6 with meaningful adoption.** The only v6.1-compatible option (`@rottitime/govuk-design-react`) is pre-1.0, three contributors, 82 weekly downloads.
- **The "larger" React libraries are on older majors.** `govuk-react` does not declare a `govuk-frontend` peer dep at all (it re-implements via CSS-in-JS). `pa-digital/govuk-frontend-react` is on v5.3.1/v5.8.0. `surevine/govuk-react-jsx` is explicitly stuck at v4.0.1.
- **The HMLR React component repository is dormant.** `LandRegistry/govuk-react-components` last had any commit in July 2021 and pins `govuk-frontend: 3.1.0`. There is no v6 branch.
- **All candidates are MIT-licensed except penx (ISC).** Licensing is not a discounting axis.
- **The most-adopted candidate (`govuk-react`, 456 stars, 2.4k weekly downloads, 23 contributors) lags the upstream Design System.** Its CSS-in-JS approach means a Design System change requires a coordinated upstream PR before our codebase can pick it up, the opposite of what we want.
- **The most-downloaded React govuk wrapper is one the maintainers told everyone to stop using.** `surevine/govuk-react-jsx` pulls 43k weekly downloads despite being archived since 2024 and pinned to v4.0.1. That is the failure mode this ADR is trying to design out: services adopt a community library, the maintainer steps back, the consumers are stuck on an obsolete `govuk-frontend` major with no upgrade path. Choosing to maintain our own thin wrappers is the choice not to repeat that pattern.
- **No a11y test posture differentiates the candidates.** None ship a declared automated WCAG / axe / jest-axe test suite. The strongest claim is govuk-react's separate `ACCESSIBILITY.md` documentation, and surevine's snapshot-test parity with govuk-frontend's accessible markup. Both are weak evidence relative to what an in-house wrapper around current govuk-frontend would give (the accessibility comes from govuk-frontend's HTML structure, which our wrappers don't break).

