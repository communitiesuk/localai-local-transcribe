import { AudioUploadForm } from '@/components/audio/AudioUploadForm'
import { GovukBackLink } from '@/components/govuk'

export default function Upload() {
  return (
    <div>
      <GovukBackLink href="/" />
      <h1 className="govuk-heading-xl">Upload a file</h1>
      <AudioUploadForm />
    </div>
  )
}
