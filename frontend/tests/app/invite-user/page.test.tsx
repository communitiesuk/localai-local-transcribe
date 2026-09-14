import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import AdminAddUserPage from '@/app/invite-user/page'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useOrganisation } from '@/hooks/use-organisation'
import { useInviteUserStore } from '@/stores/use-invite-user-store'
import { userExistsUsersUserExistsGet } from '@/lib/client'

const mockPush = vi.fn()

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))

vi.mock('@/hooks/use-authorised-user', () => ({
  useAuthorisedUser: vi.fn(),
}))

vi.mock('@/hooks/use-organisation', () => ({
  useOrganisation: vi.fn(),
}))

vi.mock('@/lib/client', () => ({
  userExistsUsersUserExistsGet: vi.fn(),
}))

const organisationId = '00000000-0000-0000-0000-000000000001'

describe('Invite new user page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useInviteUserStore.getState().clearInviteDetails()

    vi.mocked(useAuthorisedUser).mockReturnValue({
      currentUser: { organisation_id: organisationId },
      isLoading: false,
      isError: false,
    } as unknown as ReturnType<typeof useAuthorisedUser>)

    vi.mocked(useOrganisation).mockReturnValue({
      data: { id: organisationId, allowed_domains: ['example.com'] },
    } as unknown as ReturnType<typeof useOrganisation>)

    vi.mocked(userExistsUsersUserExistsGet).mockResolvedValue({
      data: { exists: false },
    } as unknown as Awaited<ReturnType<typeof userExistsUsersUserExistsGet>>)
  })

  it('asks for an evaluation ID and explains where it comes from', () => {
    render(<AdminAddUserPage />)

    expect(screen.getByLabelText('Evaluation ID')).toBeRequired()
    expect(
      screen.getByText(/evaluation ID that MHCLG provided for this person/i)
    ).toBeInTheDocument()
    expect(
      screen.getByText(/cannot be one that is already in use/i)
    ).toBeInTheDocument()
    expect(
      screen.getByText(/see it in Local Transcribe again/i)
    ).toBeInTheDocument()
  })

  it('carries the evaluation ID through to the confirmation step', async () => {
    const user = userEvent.setup()
    render(<AdminAddUserPage />)

    await user.type(screen.getByLabelText('Name'), 'Test User')
    await user.type(
      screen.getByLabelText('Email address'),
      'test.user@example.com'
    )
    await user.type(screen.getByLabelText('Evaluation ID'), ' EVAL-001 ')
    await user.click(screen.getByRole('button', { name: 'Continue' }))

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/invite-user/confirm')
    })
    expect(useInviteUserStore.getState().evaluationId).toBe('EVAL-001')
  })
})
