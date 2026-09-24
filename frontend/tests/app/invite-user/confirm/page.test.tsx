import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useMutation } from '@tanstack/react-query'
import AdminAddUserConfirmPage, {
  getInviteErrorMessage,
} from '@/app/invite-user/confirm/page'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useOrganisation } from '@/hooks/use-organisation'
import { useInviteUserStore } from '@/stores/use-invite-user-store'
import { UserRole } from '@/lib/utils'

const mockPush = vi.fn()
const mockReplace = vi.fn()
const mockMutateAsync = vi.fn()
let searchParams = new URLSearchParams()

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  useSearchParams: () => searchParams,
}))

vi.mock('@/hooks/use-authorised-user', () => ({
  useAuthorisedUser: vi.fn(),
}))

vi.mock('@/hooks/use-organisation', () => ({
  useOrganisation: vi.fn(),
}))

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  createUserUsersPostMutation: () => ({}),
}))

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return { ...actual, useMutation: vi.fn() }
})

const GENERIC_MESSAGE = 'Could not send the invitation. Try again.'

describe('getInviteErrorMessage', () => {
  it('returns the specific detail thrown by the client', () => {
    const error = {
      detail: 'This evaluation ID is already in use.',
    }

    expect(getInviteErrorMessage(error)).toBe(
      'This evaluation ID is already in use.'
    )
  })

  it('falls back to the generic message when there is no detail', () => {
    expect(getInviteErrorMessage(new Error('network failure'))).toBe(
      GENERIC_MESSAGE
    )
  })

  it('falls back to the generic message when the detail is not a string', () => {
    expect(getInviteErrorMessage({ detail: [{ msg: 'bad' }] })).toBe(
      GENERIC_MESSAGE
    )
  })

  it('falls back to the generic message for null', () => {
    expect(getInviteErrorMessage(null)).toBe(GENERIC_MESSAGE)
  })
})

describe('<AdminAddUserConfirmPage /> as a support admin with no organisation of their own', () => {
  const selectedOrganisationId = '00000000-0000-0000-0000-000000000002'

  beforeEach(() => {
    vi.clearAllMocks()
    searchParams = new URLSearchParams(
      `organisationId=${selectedOrganisationId}`
    )
    vi.mocked(useAuthorisedUser).mockReturnValue({
      currentUser: {
        organisation_id: null,
        roles: [UserRole.MHCLG_SUPPORT_ADMIN],
      },
      isLoading: false,
      isError: false,
    } as unknown as ReturnType<typeof useAuthorisedUser>)
    vi.mocked(useOrganisation).mockImplementation(
      (organisationId: string) =>
        ({
          data:
            organisationId === selectedOrganisationId
              ? { id: selectedOrganisationId }
              : undefined,
        }) as unknown as ReturnType<typeof useOrganisation>
    )
    vi.mocked(useMutation).mockReturnValue({
      mutateAsync: mockMutateAsync,
    } as unknown as ReturnType<typeof useMutation>)
    useInviteUserStore
      .getState()
      .setInviteDetails('Test User', 'test.user@example.com', 'EVAL-001')
  })

  it('shows the confirmation rather than loading forever', () => {
    render(<AdminAddUserConfirmPage />)

    expect(screen.getByRole('button', { name: 'Invite' })).toBeInTheDocument()
  })

  it('creates the user in the organisation they selected', async () => {
    const user = userEvent.setup()
    render(<AdminAddUserConfirmPage />)

    await user.click(screen.getByRole('button', { name: 'Invite' }))

    expect(mockMutateAsync).toHaveBeenCalledWith({
      body: {
        name: 'Test User',
        email: 'test.user@example.com',
        evaluation_id: 'EVAL-001',
        organisation_id: selectedOrganisationId,
      },
    })
  })

  it('returns to user management with the invited organisation selected when the invitation succeeds', async () => {
    const user = userEvent.setup()
    render(<AdminAddUserConfirmPage />)

    await user.click(screen.getByRole('button', { name: 'Invite' }))

    expect(mockPush).toHaveBeenCalledWith(
      `/user-management?organisationId=${selectedOrganisationId}`
    )
  })

  it('links back to the invite form with the selected organisation when cancelling', () => {
    render(<AdminAddUserConfirmPage />)

    expect(screen.getByRole('link', { name: 'Cancel' })).toHaveAttribute(
      'href',
      `/invite-user?organisationId=${selectedOrganisationId}`
    )
  })

  it('redirects back to the invite form with the selected organisation when invite details are missing', async () => {
    useInviteUserStore.getState().clearInviteDetails()

    render(<AdminAddUserConfirmPage />)

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith(
        `/invite-user?organisationId=${selectedOrganisationId}`
      )
    })
  })
})

describe('<AdminAddUserConfirmPage /> for an admin who belongs to an organisation', () => {
  const ownOrganisationId = '00000000-0000-0000-0000-000000000001'
  const selectedOrganisationId = '00000000-0000-0000-0000-000000000002'

  const setup = (roles: UserRole[]) => {
    vi.clearAllMocks()
    searchParams = new URLSearchParams(
      `organisationId=${selectedOrganisationId}`
    )
    vi.mocked(useAuthorisedUser).mockReturnValue({
      currentUser: { organisation_id: ownOrganisationId, roles },
      isLoading: false,
      isError: false,
    } as unknown as ReturnType<typeof useAuthorisedUser>)
    vi.mocked(useOrganisation).mockImplementation(
      (organisationId: string) =>
        ({
          data: organisationId ? { id: organisationId } : undefined,
        }) as unknown as ReturnType<typeof useOrganisation>
    )
    vi.mocked(useMutation).mockReturnValue({
      mutateAsync: mockMutateAsync,
    } as unknown as ReturnType<typeof useMutation>)
    useInviteUserStore
      .getState()
      .setInviteDetails('Test User', 'test.user@example.com', 'EVAL-001')
  }

  it('invites into the selected organisation, not the admin own one', async () => {
    setup([UserRole.MHCLG_SUPPORT_ADMIN])
    const user = userEvent.setup()
    render(<AdminAddUserConfirmPage />)

    await user.click(screen.getByRole('button', { name: 'Invite' }))

    expect(mockMutateAsync).toHaveBeenCalledTimes(1)
    expect(mockMutateAsync).toHaveBeenCalledWith({
      body: {
        name: 'Test User',
        email: 'test.user@example.com',
        evaluation_id: 'EVAL-001',
        organisation_id: selectedOrganisationId,
      },
    })
  })

  it('creates the user only once when the admin holds both roles', async () => {
    setup([UserRole.MHCLG_SUPPORT_ADMIN, UserRole.LOCAL_AUTHORITY_ADMIN])
    const user = userEvent.setup()
    render(<AdminAddUserConfirmPage />)

    await user.click(screen.getByRole('button', { name: 'Invite' }))

    expect(mockMutateAsync).toHaveBeenCalledTimes(1)
    expect(mockMutateAsync).toHaveBeenCalledWith({
      body: {
        name: 'Test User',
        email: 'test.user@example.com',
        evaluation_id: 'EVAL-001',
        organisation_id: selectedOrganisationId,
      },
    })
  })
})
