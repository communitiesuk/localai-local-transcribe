'use client'

import { use } from 'react'
import { GovukHeading, GovukDetails } from '@/components/govuk'
import { EditDomainsForm } from '@/components/organisations/domains-form'
import { useOrganisation } from '@/hooks/use-organisation'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { UserRole } from '@/lib/utils'

export default function EditOrganisationDomains(props: {
  params: Promise<{ organisationId: string }>
}) {
  const _ = useAuthorisedUser([UserRole.MHCLG_SUPPORT_ADMIN])

  const { organisationId } = use(props.params)

  const {
    data: organisation,
    isLoading: organisationLoading,
    isError: organisationError,
  } = useOrganisation(organisationId)

  return (
    <>
      <GovukHeading>Edit approved domains</GovukHeading>

      {organisation && <EditDomainsForm organisation={organisation} />}

      <hr className="govuk-section-break govuk-section-break--visible govuk-section-break--l" />

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
    </>
  )
}
