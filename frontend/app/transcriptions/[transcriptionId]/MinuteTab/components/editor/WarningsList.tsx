import { AlertCircle } from 'lucide-react'
import { GuardrailResultResponse } from '@/lib/client'

export function WarningsList({
  warnings,
}: {
  warnings: GuardrailResultResponse[]
}) {
  if (warnings.length === 0) return null

  return (
    <div className="flex flex-col gap-4">
      {warnings.map((result) => (
        <div key={result.id} className="flex flex-col gap-2">
          {/* Use the reasoning as the primary message, remove the label/badge */}
          {result.reasoning && (
            <p className="text-amber-900 text-sm leading-relaxed italic border-l-2 border-amber-300 pl-3">
              {'"'}
              {result.reasoning}
              {'"'}
            </p>
          )}

          {/* Keep the confidence low-key, just as a small metadata point */}
          {result.score !== null && (
            <p className="text-xs text-amber-800/70 font-medium">
              System confidence: {(result.score * 100).toFixed(0)}%
            </p>
          )}
        </div>
      ))}
    </div>
  )
}