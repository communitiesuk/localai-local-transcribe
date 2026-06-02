import { useQuery } from '@tanstack/react-query'
import {
  listUsersInOrgOrgsOrganisationIdUsersGetOptions,
  listUsersUsersGetOptions,
} from '@/lib/client/@tanstack/react-query.gen'

export function useOrgUsers(organisationId: string) {
  const query = useQuery({
    ...listUsersInOrgOrgsOrganisationIdUsersGetOptions({
      path: { organisation_id: organisationId },
    }),
    enabled: Boolean(organisationId),
  })

  return {
    ...query,
    users: query.data ?? undefined,
  }
}

export function useSystemUsers(enabled: boolean | undefined) {
  const query = useQuery({
    ...listUsersUsersGetOptions(),
    enabled: Boolean(enabled),
  })
  return {
    ...query,
    users: query.data ?? undefined,
  }
}
