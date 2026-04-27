import { GuardrailResultResponse } from '@/lib/client'

interface WarningsListProps {
  warnings: GuardrailResultResponse[]
}

export function WarningsList({ warnings }: WarningsListProps) {
  if (!warnings || warnings.length === 0) return null

  return (
    <div className="govuk-warning-text mb-6">
      <span className="govuk-warning-text__icon" aria-hidden="true">!</span>
      <div className="govuk-warning-text__text">
        <h3 className="govuk-heading-s mb-2 text-gray-900">Accuracy mismatch</h3>
        <p className="govuk-body-s mb-3">
          The automated guardrail system detected a discrepancy between the meeting transcript and the generated summary.
        </p>

        <ul className="mt-1 list-disc space-y-1 pl-4 text-sm text-gray-900">
          {warnings.map((w) => (
            <li key={w.id}>
              <span className="font-semibold">Guardrail: </span>
              {w.reasoning ?? 'This output did not pass this guardrail.'}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
