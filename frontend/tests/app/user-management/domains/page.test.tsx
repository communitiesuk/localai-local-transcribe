import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import EditApprovedDomainsPage, {
  DomainsUpdateConflictError,
} from '@/app/user-management/organisations/[organisationId]/domains/page'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useOrganisation } from '@/hooks/use-organisation'
import { getOrganisationOrganisationsOrganisationIdGetQueryKey } from '@/lib/client/@tanstack/react-query.gen'
import { useBannerStore } from '@/stores/use-banner-store'

// Overrides React's `use` hook to synchronously unwrap dynamic promises during tests
vi.mock('react', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react')>()
  return {
    ...actual,
    use<T>(promise: Promise<T> & { _value?: T }): T {
      if (
        promise &&
        typeof promise.then === 'function' &&
        '_value' in promise
      ) {
        return promise._value as T
      }
      return actual.use(promise)
    },
  }
})

const mockBack = vi.fn()
const mockPush = vi.fn()
const mockParams = vi.fn(() => ({ organisationId: 'org-1' }))

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    back: mockBack,
    push: mockPush,
  }),
  useParams: () => mockParams(),
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
  let currentOrganisationId = 'org-1'

  beforeEach(() => {
    vi.clearAllMocks()
    useBannerStore.getState().clearBanner()
    currentOrganisationId = 'org-1'

    vi.mocked(useAuthorisedUser).mockImplementation(
      (options?: { organisationId?: string }) => {
        const organisationId = options?.organisationId || currentOrganisationId

        return {
          currentUser: {
            id: 'user-1',
            organisation_id: 'org-1',
            roles: ['local_authority_admin'],
          },
          isAllowed: organisationId === 'org-1',
          isLoading: false,
          isError: false,
        } as unknown as ReturnType<typeof useAuthorisedUser>
      }
    )

    vi.mocked(useOrganisation).mockImplementation(
      (param?: string | { organisationId?: string }) => {
        const organisationId =
          typeof param === 'string'
            ? param
            : param?.organisationId || currentOrganisationId

        return {
          data: {
            id: organisationId,
            name:
              organisationId === 'org-1'
                ? 'Maidstone Borough Council'
                : 'Different Council',
            allowed_domains: ['maidstone.gov.uk', 'communities.gov.uk'],
            created_datetime: '2025-01-01T00:00:00Z',
            updated_datetime: '2025-01-01T00:00:00Z',
          },
          isLoading: false,
        } as unknown as ReturnType<typeof useOrganisation>
      }
    )

    // Transparently forward mutation callbacks to hook options
    vi.mocked(useMutation).mockImplementation((options) => {
      const mutateAsync = async (variables: unknown) => {
        try {
          const data = await mockMutateAsync(variables)
          if (
            options &&
            'onSuccess' in options &&
            typeof options.onSuccess === 'function'
          ) {
            options.onSuccess(data, variables, undefined)
          }
          return data
        } catch (error) {
          if (
            options &&
            'onError' in options &&
            typeof options.onError === 'function'
          ) {
            options.onError(error as Error, variables, undefined)
          }
          throw error
        }
      }

      return {
        mutateAsync,
        isPending: false,
      } as unknown as ReturnType<typeof useMutation>
    })

    vi.mocked(useQueryClient).mockReturnValue({
      invalidateQueries: mockInvalidateQueries,
      setQueryData: mockSetQueryData,
    } as unknown as ReturnType<typeof useQueryClient>)
  })

  // Synchronous page renderer using the synchronous `use` hook override
  const renderPage = (params = { organisationId: 'org-1' }) => {
    currentOrganisationId = params.organisationId
    mockParams.mockReturnValue(params)

    const paramsPromise = Promise.resolve(params) as Promise<{
      organisationId: string
    }> & { _value?: { organisationId: string } }
    paramsPromise._value = params

    render(<EditApprovedDomainsPage params={paramsPromise} />)
  }

  it('renders a loading state while the user or organisation is loading', () => {
    vi.mocked(useOrganisation).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as unknown as ReturnType<typeof useOrganisation>)

    renderPage()
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders the heading, back link, and prepopulates the textarea with the approved domains', () => {
    renderPage()

    expect(
      screen.getByRole('heading', { name: 'Edit approved domains' })
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Back' })).toBeInTheDocument()

    const textarea = screen.getByLabelText('Approved domains', {
      exact: false,
    }) as HTMLTextAreaElement
    expect(textarea.value).toBe('maidstone.gov.uk\ncommunities.gov.uk')
  })

  it('renders the hint text and the expandable help section', () => {
    renderPage()

    expect(screen.getByText(/List any approved domains/i)).toBeInTheDocument()
    expect(screen.getByText('More about approved domains')).toBeInTheDocument()
    expect(screen.getByText(/able to be invited to a/i)).toBeInTheDocument()
  })

  it('triggers router.back on back link click', async () => {
    renderPage()
    await userEvent.click(screen.getByRole('link', { name: 'Back' }))
    expect(mockBack).toHaveBeenCalledTimes(1)
  })

  it('submits the parsed domains list, updates the query cache, and navigates back on success', async () => {
    const mockUpdatedOrganisation = {
      id: 'org-1',
      name: 'Maidstone Borough Council',
      allowed_domains: ['maidstone.gov.uk', 'communities.gov.uk'],
    }
    mockMutateAsync.mockResolvedValueOnce(mockUpdatedOrganisation)
    renderPage()

    const textarea = screen.getByLabelText('Approved domains', {
      exact: false,
    })
    await userEvent.clear(textarea)
    await userEvent.type(
      textarea,
      'maidstone.gov.uk\n\n  communities.gov.uk  \n'
    )

    await userEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(mockMutateAsync).toHaveBeenCalledWith({
      organisationId: 'org-1',
      allowedDomains: ['maidstone.gov.uk', 'communities.gov.uk'],
      updatedDatetime: '2025-01-01T00:00:00Z',
    })

    await waitFor(() => {
      expect(mockSetQueryData).toHaveBeenCalledWith(
        getOrganisationOrganisationsOrganisationIdGetQueryKey({
          path: { organisation_id: 'org-1' },
        }),
        mockUpdatedOrganisation
      )
    })

    expect(useBannerStore.getState().banner).toEqual(
      expect.objectContaining({
        variant: 'success',
        title: 'Approved domains updated',
      })
    )
    expect(mockPush).toHaveBeenCalledWith('/user-management')
  })

  it('shows a validation error and does not submit when all domains are removed', async () => {
    renderPage()

    const textarea = screen.getByLabelText('Approved domains', {
      exact: false,
    })
    await userEvent.clear(textarea)

    await userEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(
      screen.getAllByText('Enter at least one approved domain')
    ).not.toHaveLength(0)
    expect(mockMutateAsync).not.toHaveBeenCalled()
  })

  it('shows a conflict banner and refetches instead of navigating away when the domains were changed elsewhere', async () => {
    mockMutateAsync.mockRejectedValueOnce(new DomainsUpdateConflictError())
    renderPage()

    await userEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(
      await screen.findByText(/your changes were not saved/i)
    ).toBeInTheDocument()
    expect(mockInvalidateQueries).toHaveBeenCalledWith({
      queryKey: getOrganisationOrganisationsOrganisationIdGetQueryKey({
        path: { organisation_id: 'org-1' },
      }),
    })
    expect(mockPush).not.toHaveBeenCalled()
    expect(useBannerStore.getState().banner).toBeNull()
  })

  it('renders a Cancel link back to user management', () => {
    renderPage()
    expect(screen.getByRole('link', { name: 'Cancel' })).toHaveAttribute(
      'href',
      '/user-management'
    )
  })

  it('shows authorization error when LOCAL_AUTHORITY_ADMIN tries to access different organisation', () => {
    renderPage({ organisationId: 'different-org' })
    expect(
      screen.getByText(
        /You are not authorised to edit domains for this organisation/i
      )
    ).toBeInTheDocument()
  })
})
