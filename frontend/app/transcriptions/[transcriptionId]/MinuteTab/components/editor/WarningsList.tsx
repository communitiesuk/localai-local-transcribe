import { AlertTriangle, XCircle } from 'lucide-react'
import { StatusSection } from './statussection'
import { formatLabel } from '@/lib/utils'
import { GuardrailResultResponse } from '@/lib/client'

export function WarningsList({
  warnings,
}: {
  warnings: GuardrailResultResponse[]
}) {
  if (warnings.length === 0) return null

  return (
    <StatusSection
      title="Guardrail Warnings"
      icon={AlertTriangle}
      variant="warning"
    >
      {warnings.map((result) => (
        <div
          key={result.id}
          className={`flex flex-col gap-1 rounded border p-2 text-sm ${
            result.passed
              ? 'border-yellow-100 bg-white/50'
              : 'border-red-100 bg-red-50'
          }`}
        >
          <div className="flex items-center gap-2">
            {result.passed ? (
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
            ) : (
              <XCircle className="h-4 w-4 text-red-600" />
            )}
            <span
              className={`font-medium capitalize ${result.passed ? 'text-yellow-800' : 'text-red-800'}`}
            >
              {formatLabel('Accuracy Audit')}:
            </span>
            <span
              className={`rounded border px-1 text-xs font-bold uppercase ${
                result.passed
                  ? 'border-yellow-600 bg-yellow-100 text-yellow-800'
                  : 'border-red-600 bg-red-100 text-red-700'
              }`}
            >
              {result.passed ? 'WARNING' : 'FAILED'}
            </span>
          </div>
          {result.reasoning && (
            <p className="italic opacity-90">
              {'"'}
              {result.reasoning}
              {'"'}
            </p>
          )}

          {result.score !== null && (
            <p className="ml-6 text-xs opacity-75">
              Confidence: {(result.score * 100).toFixed(0)}%
            </p>
          )}
        </div>
      ))}
    </StatusSection>
  )
}
