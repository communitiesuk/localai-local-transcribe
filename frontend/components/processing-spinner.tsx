export function ProcessingSpinner({
  label,
  message,
}: {
  label: string
  message?: string
}) {
  return (
    <div className="flex h-72 flex-col items-center justify-center gap-4">
      <div
        aria-label={label}
        aria-live="polite"
        role="status"
        className="h-28 w-28 animate-spin rounded-full border-[12px] border-gray-400 border-t-sky-700"
      />
      {message && <p className="govuk-body">{message}</p>}
    </div>
  )
}
