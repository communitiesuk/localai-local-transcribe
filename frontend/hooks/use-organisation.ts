import { useQuery } from '@tanstack/react-query'
import {
  getOrganisationOrganisationsOrganisationIdGetOptions,
  listOrganisationsOrganisationsGetOptions,
} from '@/lib/client/@tanstack/react-query.gen'

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

export function useGetOrganisations(isEnabled: boolean) {
  return useQuery({
    ...listOrganisationsOrganisationsGetOptions(),
    enabled: isEnabled,
    placeholderData: (previousData) => previousData,
  })
}
