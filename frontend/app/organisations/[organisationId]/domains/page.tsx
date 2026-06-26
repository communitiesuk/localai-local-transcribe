'use client'

import { use, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'
import { GovukHeading, GovukDetails } from '@/components/govuk'
import { EditDomainsForm } from '@/components/organisations/domains-form'
import { useOrganisation } from '@/hooks/use-organisation'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { UserRole } from '@/lib/utils'

export default function EditOrganisationDomains(props: {
  params: Promise<{ organisationId: string }>
}) {
  const router = useRouter()
  const _ = useAuthorisedUser([UserRole.MHCLG_SUPPORT_ADMIN])

  const { organisationId } = use(props.params)

  const {
    data: organisation,
    isLoading: organisationLoading,
    isError: organisationError,
  } = useOrganisation(organisationId)

  useEffect(() => {
    if (organisationError) {
      router.replace('/generic-error')
    }
  }, [organisationError, router])

  if (organisationLoading) {
    return <Loader2 className="animate-spin" />
  }
  if (organisationError) return null

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
