import { useQuery } from '@tanstack/react-query'
import { getOrganisationOrganisationsOrganisationIdGetOptions } from '@/lib/client/@tanstack/react-query.gen'

type PendingOrganisationId = string | null | undefined

export function useOrganisation(organisationId?: PendingOrganisationId) {
  return useQuery({
    ...getOrganisationOrganisationsOrganisationIdGetOptions({
      path: {
        organisation_id: organisationId!, // wont be undefined due to enabled
      },
    }),
    enabled: !!organisationId,
  })
}
