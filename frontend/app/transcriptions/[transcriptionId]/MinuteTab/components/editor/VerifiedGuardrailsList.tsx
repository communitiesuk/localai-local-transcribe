import { GuardrailResultResponse } from '@/lib/client'

interface VerifiedGuardrailsListProps {
  passes: GuardrailResultResponse[]
}

export function VerifiedGuardrailsList({
  passes,
}: VerifiedGuardrailsListProps) {
  if (!passes || passes.length === 0) return null

  return (
    <div className="border-l-4 border-green-500 py-2 pl-4">
      <h3 className="font-bold text-green-700">Summary verified</h3>
      <p className="mt-1 text-sm text-gray-900">
        The generated summary passed the configured accuracy and safety checks.
      </p>

      <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-gray-900">
        {passes.map((p) => (
          <li key={p.id}>
            <span className="font-semibold">
              {p.passed ? 'Passed' : 'Failed'}:
            </span>{' '}
            {p.reasoning ?? p.error ?? 'No additional details provided.'}
          </li>
        ))}
      </ul>
    </div>
  )
}
