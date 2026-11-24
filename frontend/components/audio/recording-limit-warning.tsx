import { GovukWarningText } from '@/components/govuk'
import { MAX_RECORDING_DURATION_LABEL } from '@/lib/constants'

export const RECORDING_STOPPED_AT_LIMIT_PARAM = 'stoppedAtLimit'

export function RecordingLimitWarning() {
  return (
    <GovukWarningText>
      This recording reached {MAX_RECORDING_DURATION_LABEL} and has stopped.
    </GovukWarningText>
  )
}
