/* eslint-disable @typescript-eslint/no-explicit-any */
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import SettingsPage from '@/app/settings/page'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

// Mock next/navigation
const mockBack = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    back: mockBack,
  }),
}))

// Mock react-query
vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return {
    ...actual,
    useQuery: vi.fn(),
    useMutation: vi.fn(),
    useQueryClient: vi.fn(),
  }
})

describe('<SettingsPage />', () => {
  const mockMutateAsync = vi.fn()
  const mockInvalidateQueries = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(useQuery).mockReturnValue({
      data: {
        id: 'user-1',
        email: 'user@example.com',
        data_retention_days: 7,
      },
    } as any)

    vi.mocked(useMutation).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    } as any)

    vi.mocked(useQueryClient).mockReturnValue({
      invalidateQueries: mockInvalidateQueries,
    } as any)
  })

  it('renders loading state when user is loading/undefined', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
    } as any)

    render(<SettingsPage />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders page layout, back link, form components, and sets initial default value from user data', () => {
    render(<SettingsPage />)

    // Check heading and back link
    expect(
      screen.getByRole('heading', { name: 'Settings' })
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Back' })).toBeInTheDocument()

    // Check hint text
    expect(
      screen.getByText(/After this period the transcriptions/i)
    ).toBeInTheDocument()

    // Check radio buttons (Yes/No options or retention options)
    const oneDay = screen.getByLabelText('1 day') as HTMLInputElement
    const sevenDays = screen.getByLabelText('7 days') as HTMLInputElement
    const thirtyDays = screen.getByLabelText('30 days') as HTMLInputElement

    expect(oneDay).toBeInTheDocument()
    expect(sevenDays).toBeInTheDocument()
    expect(thirtyDays).toBeInTheDocument()

    // Since initial data_retention_days is 7, the "7 days" option should be checked
    expect(sevenDays.checked).toBe(true)
  })

  it('triggers router.back on back link click', async () => {
    render(<SettingsPage />)

    const backLink = screen.getByRole('link', { name: 'Back' })
    await userEvent.click(backLink)

    expect(mockBack).toHaveBeenCalledTimes(1)
  })

  it('submits selected values and invalidates queries on success', async () => {
    mockMutateAsync.mockResolvedValueOnce({})
    render(<SettingsPage />)

    // Select "1 day"
    const oneDay = screen.getByLabelText('1 day')
    await userEvent.click(oneDay)

    // Submit
    const saveButton = screen.getByRole('button', { name: 'Save' })
    await userEvent.click(saveButton)

    // Verify update mutation was called with retention days = 1
    expect(mockMutateAsync).toHaveBeenCalledWith(
      {
        body: {
          data_retention_days: 1,
        },
      },
      expect.any(Object)
    )

    // Manually trigger onSuccess to verify query invalidation
    const mutationCallArgs = mockMutateAsync.mock.calls[0]
    const onSuccessCallback = mutationCallArgs[1]?.onSuccess
    if (onSuccessCallback) {
      onSuccessCallback()
    }

    expect(mockInvalidateQueries).toHaveBeenCalled()
  })
})
