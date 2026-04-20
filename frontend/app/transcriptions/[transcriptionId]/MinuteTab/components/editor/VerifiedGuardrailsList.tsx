import { CheckCircle } from 'lucide-react'
import { StatusSection } from './statussection'
import { formatLabel } from '@/lib/utils'
import { GuardrailResultResponse } from '@/lib/client'

interface VerifiedGuardrailsListProps {
  passes: GuardrailResultResponse[]
  isVisible: boolean
}

export function VerifiedGuardrailsList({
  passes,
  isVisible,
}: VerifiedGuardrailsListProps) {
  if (!isVisible || passes.length === 0) return null

  return (
    <StatusSection title="AI Verified" icon={CheckCircle} variant="success">
      <div className="flex flex-col gap-1 pl-7">
        {passes.map((result) => (
          <div
            key={result.id}
            className="flex items-center gap-2 text-xs opacity-90"
          >
            <span className="capitalize">
              {formatLabel(result.guardrail_type)}
            </span>
            <span className="opacity-50">•</span>
            <span>Pass</span>
          </div>
        ))}
      </div>
    </StatusSection>
  )
}
