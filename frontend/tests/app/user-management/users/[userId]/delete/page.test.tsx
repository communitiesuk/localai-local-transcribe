/* eslint-disable @typescript-eslint/no-explicit-any */
import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import UserPageDelete from '@/app/user-management/users/[userId]/delete/page'
import { useBannerStore } from '@/stores/use-banner-store'

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  getUserUsersMeGetOptions: vi.fn(() => ({
    queryKey: ['current-user'],
    queryFn: vi.fn(),
  })),
  getTargetUserUsersUserIdGetOptions: vi.fn(() => ({
    queryKey: ['target-user'],
    queryFn: vi.fn(),
  })),
  deleteUserUsersUserIdDeleteMutation: vi.fn(() => ({})),
}))

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}))

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return {
    ...actual,
    useQuery: vi.fn(),
    useMutation: vi.fn(),
  }
})

vi.mock('@/stores/use-banner-store', () => ({
  useBannerStore: vi.fn(),
}))

vi.mock('@/lib/utils', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/utils')>()
  return {
    ...actual,
    formatCurrentDateTime: vi.fn(() => '01/01/2026, 12:00'),
  }
})

const mockReplace = vi.fn()
const mockSetBanner = vi.fn()

const currentUser = {
  id: 'current-user',
}

const targetUser = {
  id: 'user-1',
  name: 'Alice Smith',
  email: 'alice@example.gov.uk',
  organisation_id: 'org-1',
}

describe('<UserPageDelete />', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(useRouter).mockReturnValue({ replace: mockReplace } as any)

    vi.mocked(useQuery).mockImplementation(
      (options: any) =>
        ({
          data:
            options.queryKey?.[0] === 'current-user' ? currentUser : targetUser,
          isLoading: false,
          isError: false,
        }) as any
    )

    vi.mocked(useMutation).mockImplementation(
      (options: any) =>
        ({
          mutate: () => options.onSuccess(),
          isPending: false,
        }) as any
    )

    vi.mocked(useBannerStore).mockImplementation((selector: any) =>
      selector({ setBanner: mockSetBanner })
    )
  })

  const renderPage = async (userId = 'user-1') => {
    await act(async () =>
      render(<UserPageDelete params={Promise.resolve({ userId })} />)
    )
  }

  it('redirects to user management with the deleted user organisation selected after deleting', async () => {
    const user = userEvent.setup()
    await renderPage()

    await user.click(screen.getByRole('button', { name: 'Delete account' }))

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith(
        '/user-management?organisationId=org-1'
      )
    })
  })
})
