'use client'

import { use } from 'react'
import { GovukHeading } from '@/components/govuk'
import { EditDomainsForm } from '@/components/organisations/domains-form'
import { useOrganisation } from '@/hooks/use-organisation'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { UserRole } from '@/lib/utils'

export default function EditOrganisationDomains(props: {
  params: Promise<{ organisationId: string }>
}) {
  const { organisationId } = use(props.params)

  const {
    data: organisation,
    isLoading: organisationLoading,
    isError: organisationError,
  } = useOrganisation(organisationId)

  return (
    <>
      <GovukHeading>Edit approved domains</GovukHeading>
      <h1>Org Page</h1>
      <p>{organisation?.id}</p>

      {organisation && <EditDomainsForm organisation={organisation} />}
    </>
  )
}
