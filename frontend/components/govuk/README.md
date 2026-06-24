# GOV.UK component wrappers

Thin React wrappers around [govuk-frontend](https://github.com/alphagov/govuk-frontend) v6.1 markup. Import from `@/components/govuk` (or `@/components/govuk/<component>`).

**Worked example:** [`app/settings/page.tsx`](../../app/settings/page.tsx) — data-retention form using fieldset, radios, and button wrappers with React Hook Form.

## Which styling layer to use

| Need                                                  | Reach for                                                                                                                                                         |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Buttons, links, form fields, error summary, fieldsets | `@/components/govuk/*`                                                                                                                                            |
| Page layout shell (header, footer, phase banner)      | `components/layout/*` (already uses govuk classes)                                                                                                                |
| Spacing / one-off layout tweaks                       | GOV.UK spacing overrides (`govuk-!-margin-*`, `govuk-!-padding-*`) first, or Tailwind spacing utilities on a wrapper `div` only — do not restyle govuk components |
| Dialog, popover, tooltip, toast, rich-text menus      | Radix primitives under `@/components/ui/*` — see [Radix exceptions](#radix-exceptions)                                                                            |

Do **not** add new imports from `@/components/ui/*` in new code. ESLint enforces this; existing pages are grandfathered until migrated.

## Radix exceptions

Use `@/components/ui/*` only when govuk-frontend has no equivalent:

| Component file                 | Radix / other primitive        | Used for                                           |
| ------------------------------ | ------------------------------ | -------------------------------------------------- |
| `dialog.tsx`                   | `@radix-ui/react-dialog`       | Modal dialogs                                      |
| `alert-dialog.tsx`             | `@radix-ui/react-alert-dialog` | Destructive confirmations                          |
| `popover.tsx`                  | `@radix-ui/react-popover`      | Floating panels (speaker editor, citations)        |
| `tooltip.tsx`                  | `@radix-ui/react-tooltip`      | Icon tooltips                                      |
| `accordion.tsx`                | `@radix-ui/react-accordion`    | Expandable sections (support page)                 |
| `collapsible.tsx`              | `@radix-ui/react-collapsible`  | Show/hide regions                                  |
| `sonner.tsx`                   | Sonner                         | Toast notifications (`<Toaster />` in root layout) |
| `citation-popover-wrapper.tsx` | Popover + custom               | Citation previews in editor / chat                 |
| TipTap editor menus            | Radix / ProseMirror            | Rich-text toolbar (no GDS pattern)                 |

Everything else (button, input, label, radio, checkbox, select, tabs, card, badge, alert, separator) has a GOV.UK Design System equivalent — use or add a `govuk/` wrapper instead.

## Server vs client

- **Default to server components.** Wrappers such as `GovukFieldset`, `GovukErrorSummary`, and `GovukLabel` have no `'use client'` directive.
- **Add `'use client'` only when required:** browser APIs, React state, event handlers, or hooks (`GovukButton` with `onClick`, `GovukBackLink` using routing, `GovukRadios`).
- Pages that use React Hook Form or TanStack Query remain client components (`'use client'` on the page), but can still import server-safe govuk children.

## React Hook Form

1. `useForm` with `defaultValues` from server/API data.
2. Optional: `<GovukErrorSummary errors={form.formState.errors} />` at the top of the form when validation runs (hidden when empty).
3. Wrap each field in `<GovukFormGroup hasError={!!form.formState.errors.fieldName}>`.
4. Use `<Controller>` for controlled inputs. Pass `value`, `onChange`, `disabled`, and `ref` through to the govuk wrapper.

```tsx
<Controller
  control={form.control}
  name="dataRetention"
  render={({ field: { value, onChange, ref, disabled } }) => (
    <GovukRadios
      name="dataRetention"
      value={value}
      onChange={onChange}
      disabled={disabled}
      ref={ref}
      options={[
        { label: 'Keep indefinitely', value: 'none' },
        { label: '7 days', value: '7' },
      ]}
    />
  )}
/>
```

`GovukErrorSummary` accepts `errorList={[{ href: '#field', text: '…' }]}`.

## Adding a new wrapper

1. Find the [GOV.UK Design System HTML reference](https://design-system.service.gov.uk/components/) for the component.
2. Copy the nearest existing wrapper (`button.tsx`, `radios.tsx`, …) — keep markup canonical; use `cn()` only for optional caller `className`.
3. Export from [`index.ts`](./index.ts).
4. Add a structural test in [`tests/components/govuk/`](../../tests/components/govuk/) asserting class names, ARIA, and DOM hierarchy (see `header.test.tsx` / `radios.test.tsx` for patterns). **Every wrapper ships with a structural test.**

## Available wrappers

| Export                    | GDS module                       | Client? |
| ------------------------- | -------------------------------- | ------- |
| `GovukAccordion`          | Accordion                        | No      |
| `GovukBackLink`           | Back link (href or dynamic back) | Yes     |
| `GovukButton`             | Button                           | Yes     |
| `GovukButtonLink`         | Button link                      | Yes     |
| `GovukDetails`            | Details                          | No      |
| `GovukErrorSummary`       | Error summary                    | No      |
| `GovukFieldset`           | Fieldset                         | No      |
| `GovukFormGroup`          | Form group                       | No      |
| `GovukHint`               | Hint                             | No      |
| `GovukLabel`              | Label                            | No      |
| `GovukLegend`             | Legend                           | No      |
| `GovukNotificationBanner` | Notification banner              | No      |
| `GovukRadios`             | Radios                           | Yes     |
| `GovukTag`                | Tag                              | No      |
| `GovukTextarea`           | Textarea                         | Yes     |

## Display wrappers

### GovukTag

Renders a `<strong>` pill. Pass a `colour` prop for one of the ten canonical variants:
`grey`, `green`, `turquoise`, `blue`, `light-blue`, `purple`, `pink`, `red`, `orange`, `yellow`.
Omit `colour` for the default blue.

```tsx
<GovukTag>Active</GovukTag>
<GovukTag colour="grey">Inactive</GovukTag>
```

### GovukDetails

Disclosure panel backed by govuk-frontend JS (bootstrapped via `<GovukInit />`).
Pass a `summary` prop for the visible toggle text; children go in the revealed panel.

```tsx
<GovukDetails summary="Help with this field">
  <p className="govuk-body">Explanatory text.</p>
</GovukDetails>
```

### GovukAccordion

Expandable sections backed by govuk-frontend JS (bootstrapped via `<GovukInit />`).
Requires an `id` prop (used by the JS to derive internal ARIA IDs).
Uses the `GovukAccordion.Section` compound child.
Pass `headingLevel` (2–6, default 2) on each Section to match surrounding document structure.

> **govuk-frontend JS dependency:** `GovukDetails` and `GovukAccordion` rely on `<GovukInit />` being present in the layout to bootstrap the disclosure behaviour. The static markup is rendered server-side; the JS adds toggle controls and ARIA attributes at mount time.

```tsx
<GovukAccordion id="help-accordion">
  <GovukAccordion.Section heading="Who can use this service">
    <p className="govuk-body">Anyone with a GOV.UK account.</p>
  </GovukAccordion.Section>
  <GovukAccordion.Section heading="How long data is kept">
    <p className="govuk-body">Up to 90 days.</p>
  </GovukAccordion.Section>
</GovukAccordion>
```

### GovukNotificationBanner

Renders an `important` (default) or `success` banner.

ARIA roles follow the GOV.UK pattern:
- `important` → `role="region"` with `aria-labelledby`
- `success` → `role="alert"` with `aria-labelledby`

When more than one banner appears on the same page, pass a unique `titleId` to each so `aria-labelledby` stays valid.

```tsx
<GovukNotificationBanner>
  <p className="govuk-body">There may be a delay in processing your request.</p>
</GovukNotificationBanner>

<GovukNotificationBanner variant="success" titleId="save-banner-title">
  <h3 className="govuk-notification-banner__heading">Template saved</h3>
</GovukNotificationBanner>
```
