'use client'

import { updateOrganisationOrganisationsOrganisationIdPatchMutation } from '@/lib/client/@tanstack/react-query.gen'
import { EditDomainsForm } from '@/components/organisations/domains-form'
import DomainsDetails from '@/components/organisations/domains-details'
import { parseDomains } from '@/lib/utils'
import type { EditDomainsFormData } from '@/components/organisations/domains-form'
import { useRouter } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { GovukBackLink } from '@/components/govuk'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useOrganisation } from '@/hooks/use-organisation'
import { UserRole } from '@/lib/utils'
import { Loader2 } from 'lucide-react'

export default function EditApprovedDomainsPage() {
  const router = useRouter()

  const { currentUser, isLoading: userLoading } = useAuthorisedUser([
    UserRole.MHCLG_SUPPORT_ADMIN,
  ])

  // BUG: replace with id from dropdown once implemented
  const { data: organisation, isLoading: organisationLoading } =
    useOrganisation(currentUser?.organisation_id ?? '')

  const { mutate: editOrganisationDomains } = useMutation({
    ...updateOrganisationOrganisationsOrganisationIdPatchMutation(),
    onSuccess() {
      router.replace(`/user-management`)
    },
  })

  // non-null assertion - onSubmit only called once organisation has loaded
  const onSubmit = (data: EditDomainsFormData) => {
    editOrganisationDomains({
      path: { organisation_id: organisation!.id },
      body: { allowed_domains: parseDomains(data.domains) },
    })
  }

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
      <EditDomainsForm
        defaultValues={organisation.allowed_domains}
        onSubmit={onSubmit}
      />

      <hr className="govuk-section-break govuk-section-break--visible govuk-section-break--l" />

      <DomainsDetails />
    </>
  )
}
