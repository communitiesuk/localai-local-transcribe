import { useQuery } from '@tanstack/react-query'
import { listUsersUsersGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import { USERS_PER_PAGE } from '@/lib/constants'

export function useUsers(page: number, pageSize: number = USERS_PER_PAGE) {
  return useQuery({
    ...listUsersUsersGetOptions({
      query: {
        page,
        page_size: pageSize,
      },
    }),
    placeholderData: (previousData) => previousData,
  })
}
