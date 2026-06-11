import { useQuery } from '@tanstack/react-query'
import { getOrganisationOrganisationsOrganisationIdGetOptions } from '@/lib/client/@tanstack/react-query.gen'

export function useOrganisation(organisationId: string) {
  return useQuery({
    ...getOrganisationOrganisationsOrganisationIdGetOptions({
      path: {
        organisation_id: organisationId,
      },
    }),
    enabled: !!organisationId,
  })
}
