'use client'
import { useRouter } from 'next/navigation'

import { useMutation } from '@tanstack/react-query'
import { createOrganisationOrganisationsPostMutation } from '@/lib/client/@tanstack/react-query.gen'

import { GovukHeading } from '@/components/govuk'
import { EditDomainsForm } from '@/components/organisations/domains-form'
import DomainsDetails from '@/components/organisations/domains-details'
import type { EditDomainsFormData } from '@/components/organisations/domains-form'
import { parseDomains, formatCurrentDateTime } from '@/lib/utils'
import { useNewOrgStore } from '@/stores/use-new-org-store'
import { useBannerStore } from '@/stores/use-banner-store'

export default function CreateNewOrganisationDomains() {
  const router = useRouter()
  const { newOrg } = useNewOrgStore()
  const clearNewOrg = useNewOrgStore((store) => store.clearNewOrg)
  const setBanner = useBannerStore((store) => store.setBanner)

  const { mutate: createOrganisation, isPending: createOrganisationPending } =
    useMutation({
      ...createOrganisationOrganisationsPostMutation(),
      onSuccess() {
        setBanner({
          variant: 'success',
          title: 'Organisation created',
          message: `Successfully created '${newOrg!.name}' at ${formatCurrentDateTime()}`,
        })
        clearNewOrg()
        router.replace(`/user-management`)
      },
      onError() {
        router.replace('/generic-error')
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
  }

  return (
    <>
      <GovukHeading>Create organisation</GovukHeading>

      <hr className="govuk-section-break govuk-section-break--visible govuk-section-break--l" />

      <EditDomainsForm
        defaultValues={[]}
        onSubmit={onSubmit}
        isPending={createOrganisationPending}
        buttonText="Create organistaion"
        buttonPendingText="Creating organisation..."
      />

      <DomainsDetails />
    </>
  )
}
