import { XCircle } from 'lucide-react'
import { StatusSection } from './statussection' 
import { formatLabel } from '@/lib/utils' 
export type LLMHallucination = {
  hallucination_type: string
  hallucination_text: string
  hallucination_reason: string
}

interface HallucinationsListProps {
  hallucinations?: LLMHallucination[] | null
}

export function HallucinationsList({
  hallucinations,
}: HallucinationsListProps) {
  // Guard clause: If there are no hallucinations, don't render anything
  if (!hallucinations || hallucinations.length === 0) return null

  return (
    <StatusSection
      title="Hallucinations Detected"
      icon={XCircle}
      variant="error"
    >
      {hallucinations.map((h, i) => (
        <div
          key={i}
          className="flex flex-col gap-1 rounded border border-red-100 bg-white/50 p-2 text-sm"
        >
          <span className="font-medium capitalize">
            {formatLabel(h.hallucination_type)}:
          </span>
          {h.hallucination_text && (
            <p className="text-red-900 italic">
              {'"'}
              {h.hallucination_text}
              {'"'}
            </p>
          )}
          {h.hallucination_reason && (
            <p className="text-xs text-red-700">
              Reason: {h.hallucination_reason}
            </p>
          )}
        </div>
      ))}
    </StatusSection>
  )
}
