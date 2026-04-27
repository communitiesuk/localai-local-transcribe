import { GuardrailResultResponse } from '@/lib/client'
import { WarningsList } from './WarningsList'
import { VerifiedGuardrailsList } from './VerifiedGuardrailsList'

interface GuardrailProps {
  guardrailResults: GuardrailResultResponse[]
}

export function GuardrailResponseComponent({ guardrailResults = [] }: GuardrailProps) {
  if (guardrailResults.length === 0) return null

  const warnings = guardrailResults.filter((r) => !r.passed)
  const passes = guardrailResults.filter((r) => r.passed)

  const hasWarnings = warnings.length > 0
  const showVerified = !hasWarnings && passes.length > 0

  return (
    <div className="flex flex-col gap-6">
      <WarningsList warnings={warnings} />
      {showVerified && <VerifiedGuardrailsList passes={passes} />}
    </div>
  )
}
