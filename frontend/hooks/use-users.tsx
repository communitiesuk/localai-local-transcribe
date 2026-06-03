import { useQuery } from '@tanstack/react-query'
import { listUsersUsersGetOptions } from '@/lib/client/@tanstack/react-query.gen'

export function useUsers(page: number, pageSize: number = 10) {
  return useQuery({
    ...listUsersUsersGetOptions({
      query: {
        page,
        page_size: pageSize,
      },
    }),
  })
}
