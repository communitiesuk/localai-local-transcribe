/* eslint-disable @typescript-eslint/no-explicit-any */
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import EditApprovedDomainsPage from '@/app/user-management/organisations/[organisationId]/domains/page'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useOrganisation } from '@/hooks/use-organisation'
import { getOrganisationOrganisationsOrganisationIdGetQueryKey } from '@/lib/client/@tanstack/react-query.gen'
import { Suspense } from 'react'

const mockBack = vi.fn()
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    back: mockBack,
    push: mockPush,
  }),
}))

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

vi.mock('@/hooks/use-authorised-user', () => ({
  useAuthorisedUser: vi.fn(),
}))

vi.mock('@/hooks/use-organisation', () => ({
  useOrganisation: vi.fn(),
}))

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return {
    ...actual,
    setQueryData: vi.fn(),
    useMutation: vi.fn(),
    useQueryClient: vi.fn(),
  }
})

describe('<EditApprovedDomainsPage />', () => {
  const mockMutateAsync = vi.fn()
  const mockInvalidateQueries = vi.fn()
  const mockSetQueryData = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(useAuthorisedUser).mockReturnValue({
      currentUser: {
        id: 'user-1',
        organisation_id: 'org-1',
        roles: ['LOCAL_AUTHORITY_ADMIN'],
      },
      isAllowed: true,
      isLoading: false,
      isError: false,
    } as any)

    vi.mocked(useOrganisation).mockReturnValue({
      data: {
        id: 'org-1',
        name: 'Maidstone Borough Council',
        allowed_domains: ['maidstone.gov.uk', 'communities.gov.uk'],
        created_datetime: '2025-01-01T00:00:00Z',
        updated_datetime: '2025-01-01T00:00:00Z',
      },
      isLoading: false,
    } as any)

    vi.mocked(useMutation).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    } as any)

    vi.mocked(useQueryClient).mockReturnValue({
      invalidateQueries: mockInvalidateQueries,
      setQueryData: mockSetQueryData,
    } as any)
  })

  const renderPage = (params = { organisationId: 'org-1' }) => {
    return render(
      <Suspense fallback={<div>Loading...</div>}>
        <EditApprovedDomainsPage params={Promise.resolve(params)} />
      </Suspense>
    )
  }
  it('renders a loading state while the user or organisation is loading', () => {
    vi.mocked(useOrganisation).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as any)

    renderPage()
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders the heading, back link, and prepopulates the textarea with the approved domains', async () => {
    renderPage()

    expect(
      await screen.findByRole('heading', { name: 'Edit approved domains' })
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Back' })).toBeInTheDocument()

    const textarea = screen.getByLabelText('Approved domains', {
      exact: false,
    }) as HTMLTextAreaElement
    expect(textarea.value).toBe('maidstone.gov.uk\ncommunities.gov.uk')
  })

  it('renders the hint text and the expandable help section', async () => {
    renderPage()

    expect(
      await screen.findByText(/Please list any approved domains/i)
    ).toBeInTheDocument()
    expect(screen.getByText('More about approved domains')).toBeInTheDocument()
    expect(screen.getByText(/able to be invited to a/i)).toBeInTheDocument()
  })

  it('triggers router.back on back link click', async () => {
    renderPage()
    await screen.findByRole('link', { name: 'Back' })
    await userEvent.click(screen.getByRole('link', { name: 'Back' }))
    expect(mockBack).toHaveBeenCalledTimes(1)
  })

  it('submits the parsed domains list, updates the query cache, and navigates back on success', async () => {
    mockMutateAsync.mockResolvedValueOnce({})
    renderPage()

    const textarea = await screen.findByLabelText('Approved domains', {
      exact: false,
    })
    await userEvent.clear(textarea)
    await userEvent.type(
      textarea,
      'maidstone.gov.uk\n\n  communities.gov.uk  \n'
    )

    await userEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(mockMutateAsync).toHaveBeenCalledWith(
      {
        path: { organisation_id: 'org-1' },
        body: { allowed_domains: ['maidstone.gov.uk', 'communities.gov.uk'] },
      },
      expect.any(Object)
    )

    const mockUpdatedOrganisation = {
      id: 'org-1',
      name: 'Maidstone Borough Council',
      allowed_domains: ['maidstone.gov.uk', 'communities.gov.uk'],
    }

    const mutationCallArgs = mockMutateAsync.mock.calls[0]
    const onSuccessCallback = mutationCallArgs[1]?.onSuccess
    onSuccessCallback?.(mockUpdatedOrganisation)

    expect(mockSetQueryData).toHaveBeenCalledWith(
      getOrganisationOrganisationsOrganisationIdGetQueryKey({
        path: { organisation_id: 'org-1' },
      }),
      mockUpdatedOrganisation
    )
    expect(mockPush).toHaveBeenCalledWith('/user-management')
  })

  it('shows a validation error and does not submit when all domains are removed', async () => {
    renderPage()

    const textarea = await screen.findByLabelText('Approved domains', {
      exact: false,
    })
    await userEvent.clear(textarea)

    await userEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(
      await screen.findAllByText('Enter at least one approved domain')
    ).not.toHaveLength(0)
    expect(mockMutateAsync).not.toHaveBeenCalled()
  })

  it('renders a Cancel link back to user management', async () => {
    renderPage()
    expect(await screen.findByRole('link', { name: 'Cancel' })).toHaveAttribute(
      'href',
      '/user-management'
    )
  })

  it('shows authorization error when LOCAL_AUTHORITY_ADMIN tries to access different organisation', async () => {
    renderPage({ organisationId: 'different-org' })
    expect(
      await screen.findByText(
        /You are not authorised to edit domains for this organisation/i
      )
    ).toBeInTheDocument()
  })
})
