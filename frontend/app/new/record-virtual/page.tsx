import { TabRecorderForm } from '@/components/audio/tab-recorder/tab-recorder'
import { GovukBackLink } from '@/components/govuk'

export default function RecordVirtual() {
  return (
    <div>
      <GovukBackLink href="/" />
      <h1 className="govuk-heading-xl">Record a meeting</h1>
      <TabRecorderForm />
    </div>
  )
}
