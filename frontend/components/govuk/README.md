# GOV.UK component wrappers

Thin React wrappers around [govuk-frontend](https://github.com/alphagov/govuk-frontend) v6.1 markup. Import from `@/components/govuk` (or `@/components/govuk/<component>`).

**Worked example:** [`app/settings/page.tsx`](../../app/settings/page.tsx) — data-retention form using fieldset, radios, and button wrappers with React Hook Form.

## Which styling layer to use

| Need                                                  | Reach for                                                                              |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Buttons, links, form fields, error summary, fieldsets | `@/components/govuk/*`                                                                 |
| Page layout shell (header, footer, phase banner)      | `components/layout/*` (already uses govuk classes)                                     |
| Spacing / one-off layout tweaks                       | Tailwind utilities on a wrapper `div` only — do not restyle govuk components           |
| Dialog, popover, tooltip, toast, rich-text menus      | Radix primitives under `@/components/ui/*` — see [Radix exceptions](#radix-exceptions) |

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

- **Default to server components.** Wrappers such as `GovukBackLink`, `GovukFieldset`, `GovukErrorSummary`, and `GovukLabel` have no `'use client'` directive.
- **Add `'use client'` only when required:** browser APIs, React state, event handlers, or hooks (`GovukButton` with `onClick`, `GovukBackLinkClient`, `GovukRadios`).
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
    >
      <GovukRadios.Item value="none">Keep indefinitely</GovukRadios.Item>
      <GovukRadios.Item value="7">7 days</GovukRadios.Item>
    </GovukRadios>
  )}
/>
```

`GovukErrorSummary` accepts either `errorList={[{ href: '#field', text: '…' }]}` or `errors={form.formState.errors}` (uses each field's `message`).

## Adding a new wrapper

1. Find the [GOV.UK Design System HTML reference](https://design-system.service.gov.uk/components/) for the component.
2. Copy the nearest existing wrapper (`button.tsx`, `radios.tsx`, …) — keep markup canonical; use `cn()` only for optional caller `className`.
3. Export from [`index.ts`](./index.ts).
4. Add a structural test in [`tests/components/govuk/`](../../tests/components/govuk/) asserting class names, ARIA, and DOM hierarchy (see `header.test.tsx` / `radios.test.tsx` for patterns). **Every wrapper ships with a structural test.**

## Available wrappers

| Export                             | GDS module                            | Client? |
| ---------------------------------- | ------------------------------------- | ------- |
| `GovukBackLink`                    | Back link (href)                      | No      |
| `GovukBackLinkClient`              | Back link (`onClick` / `router.back`) | Yes     |
| `GovukButton`                      | Button                                | Yes     |
| `GovukErrorSummary`                | Error summary                         | No      |
| `GovukFieldset`                    | Fieldset                              | No      |
| `GovukFormGroup`                   | Form group                            | No      |
| `GovukHint`                        | Hint                                  | No      |
| `GovukLabel`                       | Label                                 | No      |
| `GovukLegend`                      | Legend                                | No      |
| `GovukRadios` / `GovukRadios.Item` | Radios                                | Yes     |

## Loading states

When data is fetching, use a visually hidden message or a `govuk-!-display-none` toggle. Do not use spinners or animated loaders.

**Preferred pattern:**

```tax
{isLoading && <p className="govuk-visually-hidden”>Loading users</p>}
{users && <GovukTable>…</GovukTable>}
```
