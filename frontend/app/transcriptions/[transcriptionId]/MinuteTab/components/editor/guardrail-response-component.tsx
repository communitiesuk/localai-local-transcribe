import { useMemo } from 'react'
import { GuardrailResultResponse } from '@/lib/client'
import { HallucinationsList, LLMHallucination } from './HallucinationsList'
import { VerifiedGuardrailsList } from './VerifiedGuardrailsList'
import { WarningsList } from './WarningsList'
import constants from '../../../../../settings/constants.json'

interface GuardrailProps {
  guardrailResults: GuardrailResultResponse[]
  hallucinations?: LLMHallucination[] | null
}

export function GuardrailResponseComponent({
  guardrailResults = [],
  hallucinations = [],
}: GuardrailProps) {
  const { warnings, passes } = useMemo(() => {
    const isWarning = (r: GuardrailResultResponse) => {
      const isLowScore =
        r.score != null && r.score < constants.GUARDRAIL_THRESHOLD
      return r.passed === false || isLowScore
    }

    return {
      warnings: guardrailResults.filter(isWarning),
      passes: guardrailResults.filter((r) => !isWarning(r)),
    }
  }, [guardrailResults])

  const hasHallucinations = (hallucinations?.length ?? 0) > 0
  const hasWarnings = warnings.length > 0

  if (!guardrailResults.length && !hasHallucinations) return null

  return (
    <div className="flex flex-col gap-4">
      <HallucinationsList hallucinations={hallucinations} />

      <WarningsList warnings={warnings} />

      <VerifiedGuardrailsList
        passes={passes}
        isVisible={!hasWarnings && !hasHallucinations}
      />
    </div>
  )
}
