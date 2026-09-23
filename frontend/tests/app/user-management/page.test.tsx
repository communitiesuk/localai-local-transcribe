import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useQuery } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import UserManagementPage from '@/app/user-management/page'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useGetOrganisations, useOrganisation } from '@/hooks/use-organisation'
import { UserRole } from '@/lib/utils'

const mockPush = vi.fn()
const mockReplace = vi.fn()
let searchParams = new URLSearchParams()

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
  }),
  useSearchParams: () => searchParams,
}))

vi.mock('@/hooks/use-authorised-user', () => ({
  useAuthorisedUser: vi.fn(),
}))

vi.mock('@/hooks/use-organisation', () => ({
  useOrganisation: vi.fn(),
  useGetOrganisations: vi.fn(),
}))

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return {
    ...actual,
    useQuery: vi.fn(),
  }
})

const organisations = [
  {
    id: 'org-1',
    name: 'Maidstone Borough Council',
  },
  {
    id: 'org-2',
    name: 'Different Council',
  },
]

describe('<UserManagementPage />', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    searchParams = new URLSearchParams()

    vi.mocked(useAuthorisedUser).mockReturnValue({
      currentUser: {
        organisation_id: null,
        roles: [UserRole.MHCLG_SUPPORT_ADMIN],
      },
      isLoading: false,
      isError: false,
    } as unknown as ReturnType<typeof useAuthorisedUser>)

    vi.mocked(useOrganisation).mockReturnValue({
      data: undefined,
    } as unknown as ReturnType<typeof useOrganisation>)

    vi.mocked(useGetOrganisations).mockReturnValue({
      data: organisations,
    } as unknown as ReturnType<typeof useGetOrganisations>)

    vi.mocked(useQuery).mockImplementation(
      (options) =>
        ({
          data:
            options.enabled !== false
              ? {
                  items: [
                    {
                      id: 'user-1',
                      name: 'Org Two User',
                      email: 'org.two.user@example.com',
                      roles: [],
                      is_active: true,
                    },
                  ],
                  total_pages: 1,
                  total_count: 1,
                }
              : undefined,
          isLoading: false,
          error: null,
        }) as unknown as ReturnType<typeof useQuery>
    )
  })

  it('selects the organisation from the organisationId query parameter', () => {
    searchParams = new URLSearchParams('organisationId=org-2')

    render(<UserManagementPage />)

    expect(screen.getByLabelText('Selected council:')).toHaveValue('org-2')
    expect(screen.getByText('Org Two User')).toBeInTheDocument()
  })

  it('updates the organisationId query parameter when a system admin selects an organisation', async () => {
    const user = userEvent.setup()
    searchParams = new URLSearchParams('page=3')

    render(<UserManagementPage />)

    await user.selectOptions(
      screen.getByLabelText('Selected council:'),
      'org-1'
    )

    const target = mockReplace.mock.calls[0]?.[0] ?? ''
    expect(target).toContain('organisationId=org-1')
    expect(target).toContain('page=1')
  })

  it('starts the invite user journey with the selected organisation in the URL', async () => {
    const user = userEvent.setup()
    searchParams = new URLSearchParams('organisationId=org-2')

    render(<UserManagementPage />)

    await user.click(screen.getByRole('button', { name: 'Invite new user' }))

    expect(mockPush).toHaveBeenCalledWith('/invite-user?organisationId=org-2')
  })
})
