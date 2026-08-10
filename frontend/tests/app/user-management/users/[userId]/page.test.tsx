/* eslint-disable @typescript-eslint/no-explicit-any */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import UserPage from '@/app/user-management/users/[userId]/page'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { useBannerStore } from '@/stores/use-banner-store'

// Mock the generated client (requires a running backend to generate)
vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  getTargetUserUsersUserIdGetOptions: vi.fn(() => ({
    queryKey: ['user'],
    queryFn: vi.fn(),
  })),
  getTargetUserUsersUserIdGetQueryKey: vi.fn(() => ['user']),
  updateUserRolesUsersUserIdRolesPatchMutation: vi.fn(() => ({})),
}))

vi.mock('@/lib/client', () => ({
  UserRole: {
    STANDARD_USER: 'standard_user',
    LOCAL_AUTHORITY_ADMIN: 'local_authority_admin',
    MHCLG_SUPPORT_ADMIN: 'mhclg_support_admin',
  },
}))

// Synchronously unwrap Promise params (mirrors the domains page.test.tsx pattern)
vi.mock('react', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react')>()
  return {
    ...actual,
    use: (promise: any) => {
      if (
        promise &&
        typeof promise.then === 'function' &&
        '_value' in promise
      ) {
        return promise._value
      }
      return actual.use(promise)
    },
  }
})

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}))

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return {
    ...actual,
    useQuery: vi.fn(),
    useMutation: vi.fn(),
    useQueryClient: vi.fn(),
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
const mockMutateAsync = vi.fn()
const mockInvalidateQueries = vi.fn()
const mockSetBanner = vi.fn()

const baseUser = {
  id: 'user-1',
  name: 'Alice Smith',
  email: 'alice@example.gov.uk',
  roles: ['standard_user'],
  is_active: true,
  organisation_id: 'org-1',
  accepted_tou: true,
  data_retention_days: 90,
  last_login: '2026-01-01T00:00:00Z',
}

describe('<UserPage />', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(useRouter).mockReturnValue({ replace: mockReplace } as any)

    vi.mocked(useQuery).mockReturnValue({
      data: baseUser,
      isLoading: false,
      isError: false,
    } as any)

    vi.mocked(useMutation).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    } as any)

    vi.mocked(useQueryClient).mockReturnValue({
      invalidateQueries: mockInvalidateQueries,
    } as any)

    vi.mocked(useBannerStore).mockImplementation((selector: any) =>
      selector({ setBanner: mockSetBanner })
    )
  })

  const renderPage = (userId = 'user-1') => {
    const paramsPromise = Promise.resolve({ userId }) as any
    paramsPromise._value = { userId }
    render(<UserPage params={paramsPromise} />)
  }

  it('renders exactly two role options: "Standard user" and "Organisation admin"', () => {
    renderPage()

    const radios = screen.getAllByRole('radio')
    expect(radios).toHaveLength(2)
    expect(screen.getByLabelText('Standard user')).toBeInTheDocument()
    expect(screen.getByLabelText('Organisation admin')).toBeInTheDocument()
  })

  it('never renders an "Admin" option or exposes mhclg_support_admin as a selectable value', () => {
    renderPage()

    expect(screen.queryByLabelText('Admin')).not.toBeInTheDocument()

    const radios = screen.getAllByRole('radio') as HTMLInputElement[]
    const values = radios.map((r) => r.value)
    expect(values).not.toContain('mhclg_support_admin')
  })

  it('submits roles: ["local_authority_admin"] when "Organisation admin" is selected and saved', async () => {
    mockMutateAsync.mockResolvedValueOnce({})
    renderPage()

    await userEvent.click(screen.getByLabelText('Organisation admin'))
    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }))

    expect(mockMutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        body: { roles: ['local_authority_admin'] },
        path: { user_id: 'user-1' },
      })
    )
  })

  it('redirects to user management and shows a success banner after saving', async () => {
    mockMutateAsync.mockResolvedValueOnce({})
    renderPage()

    await userEvent.click(screen.getByLabelText('Organisation admin'))
    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }))

    await waitFor(() => {
      expect(mockSetBanner).toHaveBeenCalledWith({
        variant: 'success',
        title: 'Success',
        message: 'Permissions for Alice Smith saved at 01/01/2026, 12:00',
      })
    })
    expect(mockReplace).toHaveBeenCalledWith('/user-management')
  })

  it('shows an error banner and does not redirect when role update fails', async () => {
    mockMutateAsync.mockRejectedValueOnce({
      error: { detail: 'Only a system admin can perform this action' },
    })
    renderPage()

    await userEvent.click(screen.getByLabelText('Organisation admin'))
    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }))

    expect(
      await screen.findByText('Only a system admin can perform this action')
    ).toBeInTheDocument()
    expect(mockReplace).not.toHaveBeenCalled()
  })

  it('defaults to "Organisation admin" when user has both standard and admin roles', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: {
        ...baseUser,
        roles: ['standard_user', 'local_authority_admin'],
      },
      isLoading: false,
      isError: false,
    } as any)

    renderPage()

    const organisationAdmin = screen.getByLabelText(
      'Organisation admin'
    ) as HTMLInputElement
    expect(organisationAdmin.checked).toBe(true)
  })
})
