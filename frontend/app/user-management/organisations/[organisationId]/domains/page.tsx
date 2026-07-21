'use client'

import { use, useCallback, useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Loader2 } from 'lucide-react'

import { GovukBackLink, GovukNotificationBanner } from '@/components/govuk'
import {
  EditDomainsForm,
  EditDomainsFormData,
} from '@/components/organisations/domains-form'

import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useOrganisation } from '@/hooks/use-organisation'

import { UserRole, parseDomains, formatCurrentDateTime } from '@/lib/utils'
import { updateOrganisationOrganisationsOrganisationIdPatch } from '@/lib/client'
import { getOrganisationOrganisationsOrganisationIdGetQueryKey } from '@/lib/client/@tanstack/react-query.gen'
import { useBannerStore } from '@/stores/use-banner-store'

const CONFLICT_STATUS = 409

export class DomainsUpdateConflictError extends Error {}

export default function EditApprovedDomainsPage(props: {
  params: Promise<{ organisationId: string }>
}) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const setBanner = useBannerStore((store) => store.setBanner)
  const [hasConflict, setHasConflict] = useState(false)

  const { organisationId } = use(props.params)
  console.log('DIAGNOSTIC: organisationId from params:', organisationId)

  const { currentUser, isLoading: userLoading } = useAuthorisedUser([
    UserRole.MHCLG_SUPPORT_ADMIN,
    UserRole.LOCAL_AUTHORITY_ADMIN,
  ])

  const { data: organisation, isLoading: organisationLoading } =
    useOrganisation(organisationId)

  useEffect(() => {
    console.log('DIAGNOSTIC organisation changed:', organisation)
  }, [organisation])

  // 1. Destructure mutateAsync instead of mutate
  const { mutateAsync, isPending } = useMutation({
    mutationFn: async (variables: {
      organisationId: string
      allowedDomains: string[]
      updatedDatetime: string
    }) => {
      const { data, response } =
        await updateOrganisationOrganisationsOrganisationIdPatch({
          path: { organisation_id: variables.organisationId },
          body: {
            allowed_domains: variables.allowedDomains,
            updated_datetime: variables.updatedDatetime,
          },
          throwOnError: false,
        })

      if (response?.status === CONFLICT_STATUS) {
        throw new DomainsUpdateConflictError()
      }

      if (!data) {
        throw new Error('Failed to update approved domains')
      }

      return data
    },
    onSuccess: (updatedOrganisation) => {
      queryClient.setQueryData(
        getOrganisationOrganisationsOrganisationIdGetQueryKey({
          path: { organisation_id: updatedOrganisation.id },
        }),
        updatedOrganisation
      )
      setBanner({
        variant: 'success',
        title: 'Approved domains updated',
        message: `Successfully updated approved domains for '${updatedOrganisation.name}' at ${formatCurrentDateTime()}`,
      })
      router.push('/user-management')
    },
    onError: (error) => {
      if (error instanceof DomainsUpdateConflictError) {
        setHasConflict(true)
        if (organisation?.id) {
          queryClient.invalidateQueries({
            queryKey: getOrganisationOrganisationsOrganisationIdGetQueryKey({
              path: { organisation_id: organisation.id },
            }),
          })
        }
      } else {
        toast.error('Failed to update approved domains')
      }
    },
  })

  // 2. Await mutateAsync and catch errors to prevent unhandled rejection errors
  const onSubmit = useCallback(
    async (data: EditDomainsFormData) => {
      if (!organisation) return

      setHasConflict(false)

      try {
        await mutateAsync({
          organisationId: organisation.id,
          allowedDomains: parseDomains(data.domains),
          updatedDatetime: organisation.updated_datetime,
        })
      } catch {
        // Handled globally in onError above
      }
    },
    [mutateAsync, organisation]
  )

  if (userLoading || organisationLoading || !organisation) {
    return (
      <div className="govuk-body flex items-center gap-2">
        <Loader2 className="animate-spin" />
        Loading...
      </div>
    )
  }

  if (
    currentUser?.roles?.includes(UserRole.LOCAL_AUTHORITY_ADMIN) &&
    currentUser.organisation_id?.toLowerCase() !== organisationId.toLowerCase()
  ) {
    return (
      <div className="govuk-body flex items-center gap-2">
        <Loader2 className="animate-spin" />
        You are not authorised to edit domains for this organisation.
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
      {hasConflict && (
        <GovukNotificationBanner variant="important" title="Important">
          Someone else updated the approved domains for this organisation after
          this page was loaded, so your changes were not saved. The list below
          has been refreshed with the latest domains - please check it and try
          again.
        </GovukNotificationBanner>
      )}
      <EditDomainsForm
        key={organisation.updated_datetime}
        defaultValues={organisation.allowed_domains}
        onSubmit={onSubmit}
        isPending={isPending}
      />
    </>
  )
}