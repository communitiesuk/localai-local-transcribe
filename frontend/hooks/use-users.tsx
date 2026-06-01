import { useQuery } from '@tanstack/react-query'
import { listUsersInOrgOrgsOrganisationIdUsersGetOptions } from '@/lib/client/@tanstack/react-query.gen'

export function useUsers(organisationId: string) {
  const query = useQuery({
    ...listUsersInOrgOrgsOrganisationIdUsersGetOptions({
      path: { organisation_id: organisationId },
    }),
    enabled: Boolean(organisationId),
  })

  return {
    ...query,
    users: query.data ?? [],
  }
}
