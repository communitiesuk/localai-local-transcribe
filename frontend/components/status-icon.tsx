import { GovukTag } from '@/components/govuk'
import { JobStatus } from '@/lib/client'

// Status to GovukTag colour mapping (canonical GOV.UK tag colours):
//   Processing (awaiting_start, in_progress) -> blue
//   Completed                                -> green
//   Failed                                   -> red
export const StatusBadge = ({
  status,
  className,
}: {
  status: JobStatus
  className?: string
}) => {
  if (['awaiting_start', 'in_progress'].includes(status)) {
    return (
      <GovukTag colour="blue" className={className}>
        Processing
      </GovukTag>
    )
  }

  if (status === 'completed') {
    return (
      <GovukTag colour="green" className={className}>
        Completed
      </GovukTag>
    )
  }

  if (status === 'failed') {
    return (
      <GovukTag colour="red" className={className}>
        Failed
      </GovukTag>
    )
  }
}
