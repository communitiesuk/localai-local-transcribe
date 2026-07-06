type LoadingSkeletonProps = {
  /** Number of body placeholder lines to render. */
  rows?: number
}

/**
 * Shared loading placeholder used by the route-level `loading.tsx` files.
 * Renders a heading bar and a set of content lines inside the canonical
 * GOV.UK grid so the skeleton matches the layout shell and there is no
 * visual jump when the real content resolves.
 *
 * The visible blocks are hidden from assistive tech; a single visually
 * hidden "Loading" message is announced via `role="status"`.
 */
export function LoadingSkeleton({ rows = 4 }: LoadingSkeletonProps) {
  return (
    <div className="govuk-grid-row" role="status" aria-live="polite">
      <div className="govuk-grid-column-two-thirds">
        <span className="govuk-visually-hidden">Loading</span>
        <div
          aria-hidden="true"
          className="govuk-!-margin-bottom-6 h-9 w-2/3 animate-pulse rounded bg-[#f3f2f1]"
        />
        <div aria-hidden="true" className="flex flex-col gap-4">
          {Array.from({ length: rows }).map((_, index) => (
            <div
              key={index}
              className="h-5 w-full animate-pulse rounded bg-[#f3f2f1]"
            />
          ))}
        </div>
      </div>
    </div>
  )
}
