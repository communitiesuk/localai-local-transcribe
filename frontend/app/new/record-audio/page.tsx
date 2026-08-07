import { MicRecorderForm } from '@/components/audio/mic-recorder'
import { GovukBackLink } from '@/components/govuk'

export default function RecordAudio() {
  return (
    <div>
      <GovukBackLink href="/" />
      <h1 className="govuk-heading-xl">Record a meeting</h1>
      <MicRecorderForm />
    </div>
  )
}
