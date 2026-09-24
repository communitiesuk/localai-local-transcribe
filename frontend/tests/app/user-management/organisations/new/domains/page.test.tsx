import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import CreateNewOrganisationDomains from '@/app/user-management/organisations/new/domains/page'
import { useNewOrgStore } from '@/stores/use-new-org-store'

const mockReplace = vi.fn()
const mockMutate = vi.fn()
const mockInvalidateQueries = vi.fn()

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    replace: mockReplace,
  }),
}))

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  createOrganisationOrganisationsPostMutation: () => ({}),
  listOrganisationsOrganisationsGetQueryKey: () => ['organisations'],
}))

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return {
    ...actual,
    useMutation: vi.fn(),
    useQueryClient: vi.fn(),
  }
})

describe('<CreateNewOrganisationDomains />', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useNewOrgStore.getState().setNewOrg({
      name: 'New Council',
      allowedDomains: [],
    })

    vi.mocked(useQueryClient).mockReturnValue({
      invalidateQueries: mockInvalidateQueries,
    } as unknown as ReturnType<typeof useQueryClient>)

    vi.mocked(useMutation).mockImplementation((options) => {
      mockMutate.mockImplementation((variables) => {
        options.onSuccess?.(
          {
            id: 'new-org-id',
            name: 'New Council',
            allowed_domains: variables.body.allowed_domains,
          },
          variables,
          undefined,
          {} as never
        )
      })

      return {
        mutate: mockMutate,
        isPending: false,
      } as unknown as ReturnType<typeof useMutation>
    })
  })

  it('returns to user management with the new organisation selected when creation succeeds', async () => {
    const user = userEvent.setup()
    render(<CreateNewOrganisationDomains />)

    await user.type(screen.getByLabelText('Approved domains'), 'new.gov.uk')
    await user.click(
      screen.getByRole('button', { name: 'Create organistaion' })
    )

    expect(mockReplace).toHaveBeenCalledWith(
      '/user-management?organisationId=new-org-id'
    )
  })
})
