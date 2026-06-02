import { useQuery } from '@tanstack/react-query'
import { listUsersUsersGetOptions } from '@/lib/client/@tanstack/react-query.gen'

export function useSystemUsers() {
  const query = useQuery({
    ...listUsersUsersGetOptions(),
  })
  return query
}
