import { GovukDetails } from '@/components/govuk'

export default function DomainsDetails() {
  return (
    <GovukDetails summary="More about approved domains">
      <p className="govuk-body">
        These are the email address domains that are able to be invited to a
        given organisation using Internal Access authentication.
      </p>
      <p className="govuk-body">
        Email addresses without an associated approved domain will not be able
        to be invited.
      </p>
    </GovukDetails>
  )
}
