import { useMemo } from 'react'
import { GuardrailResultResponse } from '@/lib/client'
import { VerifiedGuardrailsList } from './VerifiedGuardrailsList'
import { WarningsList } from './WarningsList'
import { LLMHallucination } from '@/lib/client'
import { HallucinationsList } from '@/app/transcriptions/[transcriptionId]/MinuteTab/components/editor/HallucinationsList'

interface GuardrailProps {
  guardrailResults: GuardrailResultResponse[]
  hallucinations?: LLMHallucination[] | null
}

export function GuardrailResponseComponent({
  guardrailResults = [],
  hallucinations = [],
}: GuardrailProps) {
  const { warnings, passes } = useMemo(() => {
    return {
      warnings: guardrailResults.filter((r) => r.passed === false),
      passes: guardrailResults.filter((r) => r.passed === true),
    }
  }, [guardrailResults])

  const hasHallucinations = (hallucinations?.length ?? 0) > 0
  const hasWarnings = warnings.length > 0

  if (!guardrailResults.length && !hasHallucinations) return null

  return (
    <div className="flex flex-col gap-6">
      {/* 1. Hallucinations (Red alert) */}
      {hasHallucinations && (
        <div className="border-l-4 border-red-500 py-2 pl-4">
          <h3 className="font-bold text-red-700">⚠️ Hallucination Warning</h3>
          <HallucinationsList hallucinations={hallucinations} />
        </div>
      )}

      {hasWarnings && (
        <div className="govuk-warning-text mb-6">
          <span className="govuk-warning-text__icon" aria-hidden="true">
            !
          </span>
          <div className="govuk-warning-text__text">
            {/* Reduced the title size and merged the intro text */}
            <h3 className="govuk-heading-s mb-2 text-gray-900">
              Accuracy Mismatch
            </h3>
            <p className="govuk-body-s mb-3">
              The automated guardrail system detected a significant discrepancy
              between the meeting transcript and the generated summary.
            </p>

            {/* Reasoning and Confidence inside the warning flow */}
            <WarningsList warnings={warnings} />
          </div>
        </div>
      )}

      {/* 3. Success: Celebrate (No reasoning shown!) */}
      {!hasWarnings && !hasHallucinations && (
        <div className="border-l-4 border-green-500 py-2 pl-4">
          <VerifiedGuardrailsList passes={passes} isVisible={true} />
        </div>
      )}
    </div>
  )
}
