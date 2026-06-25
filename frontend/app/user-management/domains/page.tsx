'use client'

import { GovukBackLink } from '@/components/govuk'
import { EditDomainsForm } from '@/components/organisations/domains-form'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useOrganisation } from '@/hooks/use-organisation'
import { UserRole } from '@/lib/utils'
import { Loader2 } from 'lucide-react'

export default function EditApprovedDomainsPage() {
  const { currentUser, isLoading: userLoading } = useAuthorisedUser([
    UserRole.MHCLG_SUPPORT_ADMIN,
  ])

  const { data: organisation, isLoading: organisationLoading } =
    useOrganisation(currentUser?.organisation_id ?? '')

  if (userLoading || organisationLoading || !organisation) {
    return (
      <div className="govuk-body flex items-center gap-2">
        <Loader2 className="animate-spin" />
        Loading...
      </div>
    )
  }

  return (
    <>
      <GovukBackLink />
      <h1 className="govuk-heading-l">Edit approved domains</h1>
      <EditDomainsForm organisation={organisation} />
    </>
  )
}
