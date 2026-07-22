import { GovukTag, type TagColour } from '@/components/govuk'
import { JobStatus } from '@/lib/client'

const STATUS_TAG: Record<JobStatus, { colour: TagColour; label: string }> = {
  awaiting_start: { colour: 'blue', label: 'Processing' },
  in_progress: { colour: 'blue', label: 'Processing' },
  completed: { colour: 'green', label: 'Completed' },
  failed: { colour: 'red', label: 'Failed' },
}

export const StatusBadge = ({
  status,
  className,
}: {
  status: JobStatus
  className?: string
}) => {
  const { colour, label } = STATUS_TAG[status]

  return (
    <GovukTag colour={colour} className={className}>
      {label}
    </GovukTag>
  )
}
