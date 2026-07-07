'use client'

import { useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Loader2 } from 'lucide-react'

import { GovukBackLink } from '@/components/govuk'
import { EditDomainsForm, EditDomainsFormData } from '@/components/organisations/domains-form'
import DomainsDetails from '@/components/organisations/domains-details'

import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useOrganisation } from '@/hooks/use-organisation'
import { useInviteUserStore } from '@/stores/use-invite-user-store'

import { UserRole, parseDomains } from '@/lib/utils'
import {
  getOrganisationOrganisationsOrganisationIdGetQueryKey,
  updateOrganisationOrganisationsOrganisationIdPatchMutation,
} from '@/lib/client/@tanstack/react-query.gen'

export default function EditApprovedDomainsPage() {
  const router = useRouter()
  const queryClient = useQueryClient()

  const { currentUser, isLoading: userLoading } = useAuthorisedUser([
    UserRole.MHCLG_SUPPORT_ADMIN,
  ])

  const { organisationId: selectedOrganisationId } = useInviteUserStore()

  const { data: organisation, isLoading: organisationLoading } =
    useOrganisation(selectedOrganisationId || currentUser?.organisation_id || '')

  const { mutateAsync, isPending } = useMutation({
    ...updateOrganisationOrganisationsOrganisationIdPatchMutation(),
  })

  const onSubmit = useCallback(
    async (data: EditDomainsFormData) => {
      if (!organisation) return

      await mutateAsync(
        {
          path: { organisation_id: organisation.id },
          body: { allowed_domains: parseDomains(data.domains) },
        },
        {
          onSuccess(updatedOrganisation) {
            queryClient.setQueryData(
              getOrganisationOrganisationsOrganisationIdGetQueryKey({
                path: { organisation_id: organisation.id },
              }),
              updatedOrganisation
            )
            toast.success('Approved domains updated')
            router.push('/user-management')
          },
          onError() {
            toast.error('Failed to update approved domains')
          },
        }
      )
    },
    [mutateAsync, organisation, queryClient, router]
  )

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
      <h2 className="govuk-heading-s govuk-!-margin-bottom-2">
        {organisation.name}
      </h2>
      <EditDomainsForm
        defaultValues={organisation.allowed_domains}
        onSubmit={onSubmit}
        isPending={isPending}
      />

      <hr className="govuk-section-break govuk-section-break--visible govuk-section-break--l" />

      <DomainsDetails />
    </>
  )
}
