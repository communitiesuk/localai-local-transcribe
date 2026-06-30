'use client'
import { useRouter } from 'next/navigation'

import { useMutation } from '@tanstack/react-query'
import { createOrganisationOrganisationsPostMutation } from '@/lib/client/@tanstack/react-query.gen'

import { GovukHeading, GovukDetails } from '@/components/govuk'
import { EditDomainsForm } from '@/components/organisations/domains-form'
import DomainsDetails from '@/components/organisations/domains-details'
import type { EditDomainsFormData } from '@/components/organisations/domains-form'
import { parseDomains, UserRole } from '@/lib/utils'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useNewOrgStore } from '@/stores/use-new-org-store'

export default function CreateNewOrganisationDomains() {
  const router = useRouter()
  const { newOrg } = useNewOrgStore()
  const clearNewOrg = useNewOrgStore((store) => store.clearNewOrg)
  const _ = useAuthorisedUser([UserRole.MHCLG_SUPPORT_ADMIN])

  const { mutate: createOrganisation } = useMutation({
    ...createOrganisationOrganisationsPostMutation(),
    onSuccess() {
      router.replace(`/user-management`)
    },
  })

  const onSubmit = (data: EditDomainsFormData) => {
    createOrganisation({
      // non-null assertion - wont make it to this page without there being an org name
      body: {
        name: newOrg!.name,
        allowed_domains: parseDomains(data.domains),
      },
    })
    clearNewOrg()
  }

  return (
    <>
      <GovukHeading>Create organisation</GovukHeading>

      <hr className="govuk-section-break govuk-section-break--visible govuk-section-break--l" />

      <EditDomainsForm defaultValues={[]} onSubmit={onSubmit} />

      <DomainsDetails />
    </>
  )
}
