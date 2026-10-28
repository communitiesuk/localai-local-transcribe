import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import {
  QueryClient,
  useQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query'
import SettingsPage from '@/app/settings/page'
import { validateCustomRetention } from '@/lib/data-retention'
import type { GetUserResponse } from '@/lib/client'
import { getUserUsersMeGetQueryKey } from '@/lib/client/@tanstack/react-query.gen'

const mockBack = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({ back: mockBack }),
}))
vi.mock('@tanstack/react-query', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@tanstack/react-query')>()),
  useQuery: vi.fn(),
  useMutation: vi.fn(),
  useQueryClient: vi.fn(),
}))

const user: GetUserResponse = {
  id: 'user-1',
  email: 'user@example.com',
  name: 'Jamie Smith',
  data_retention_days: 7,
  roles: ['standard_user'],
  created_datetime: '',
  updated_datetime: '',
  last_login: '',
  accepted_tou: true,
  is_active: true,
  organisation_id: null,
}

describe('SettingsPage', () => {
  const mutateAsync = vi.fn()
  let queryClient: QueryClient
  function mutation(isPending = false) {
    const common = {
      mutateAsync,
      mutate: vi.fn(),
      reset: vi.fn(),
      error: null,
      isError: false as const,
      isSuccess: false as const,
      isPaused: false,
      data: undefined,
      failureCount: 0,
      failureReason: null,
      submittedAt: 0,
      variables: undefined,
      context: undefined,
    }
    vi.mocked(useMutation).mockReturnValue(
      isPending
        ? { ...common, isPending: true, isIdle: false, status: 'pending' }
        : { ...common, isPending: false, isIdle: true, status: 'idle' }
    )
  }
  function query(data: GetUserResponse | undefined, isError = false) {
    vi.mocked(useQuery).mockReturnValue({ data, isError } as ReturnType<
      typeof useQuery
    >)
  }

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    query(user)
    queryClient = new QueryClient()
    vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue()
    vi.mocked(useQueryClient).mockReturnValue(queryClient)
    mutation()
    mutateAsync.mockResolvedValue({ ...user, data_retention_days: 14 })
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: {
        enumerateDevices: vi.fn().mockResolvedValue([]),
        getUserMedia: vi.fn(),
      },
    })
  })

  it('shows loading and surfaces a failed user query', () => {
    query(undefined)
    const { unmount } = render(<SettingsPage />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
    unmount()
    query(undefined, true)
    expect(() => render(<SettingsPage />)).toThrow('Unable to load settings')
  })

  it('renders account details, presets, custom option, microphones and back link', async () => {
    render(<SettingsPage />)
    expect(screen.getByText('Jamie Smith')).toBeInTheDocument()
    expect(screen.getByText('Standard')).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: 'Settings' })
    ).toBeInTheDocument()
    expect(screen.getByLabelText('7 days')).toBeChecked()
    expect(screen.getByLabelText('14 days')).toBeInTheDocument()
    expect(screen.getByLabelText('30 days')).toBeInTheDocument()
    expect(screen.getByLabelText('Custom')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Save retention period' })
    ).toBeDisabled()
    expect(screen.getByLabelText('Custom period in days')).not.toBeVisible()
    expect(
      screen.getByRole('heading', { name: 'Microphone settings' })
    ).toBeInTheDocument()
    await userEvent.click(screen.getByRole('link', { name: 'Back' }))
    expect(mockBack).toHaveBeenCalled()
  })

  it.each([1, 15])('preserves existing custom value %i', async (days) => {
    query({ ...user, data_retention_days: days })
    render(<SettingsPage />)
    expect(screen.getByLabelText('Custom')).toBeChecked()
    expect(screen.getByLabelText('Custom period in days')).toHaveValue(
      String(days)
    )
    expect(
      screen.getByRole('button', { name: 'Save retention period' })
    ).toBeDisabled()
    await screen.findByRole('button', { name: 'Allow microphone access' })
  })

  it('saves a preset, updates user cache, shows success, and resets dirty state', async () => {
    render(<SettingsPage />)
    await userEvent.click(screen.getByLabelText('14 days'))
    await userEvent.click(
      screen.getByRole('button', { name: 'Save retention period' })
    )
    expect(mutateAsync).toHaveBeenCalledWith({
      body: { data_retention_days: 14 },
    })
    expect(
      await screen.findByText('Data retention period updated')
    ).toBeInTheDocument()
    expect(queryClient.getQueryData(getUserUsersMeGetQueryKey())).toEqual({
      ...user,
      data_retention_days: 14,
    })
    expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: getUserUsersMeGetQueryKey(),
    })
    expect(
      screen.getByRole('button', { name: 'Save retention period' })
    ).toBeDisabled()
  })

  it('shows blank, format, and range errors with a focusing summary link, without submitting', async () => {
    render(<SettingsPage />)
    await userEvent.click(screen.getByLabelText('Custom'))
    const input = screen.getByLabelText('Custom period in days')
    expect(
      screen.getByRole('link', { name: 'Custom period cannot be blank' })
    ).toHaveAttribute('href', '#customDays')
    await userEvent.click(
      screen.getByRole('link', { name: 'Custom period cannot be blank' })
    )
    expect(input).toHaveFocus()
    await userEvent.type(input, 'abc')
    expect(
      screen.getByRole('link', { name: 'Enter a number in the correct format' })
    ).toBeInTheDocument()
    await userEvent.clear(input)
    await userEvent.type(input, '31')
    expect(
      screen.getByRole('link', { name: 'The number must be between 1 and 30' })
    ).toBeInTheDocument()
    expect(input).toHaveAttribute('aria-invalid', 'true')
    expect(input).toHaveAttribute(
      'aria-describedby',
      'customDays-hint customDays-error'
    )
    expect(
      screen.getByRole('button', { name: 'Save retention period' })
    ).toBeDisabled()
    expect(mutateAsync).not.toHaveBeenCalled()
    await userEvent.click(screen.getByLabelText('30 days'))
    expect(screen.queryByText('There is a problem')).not.toBeInTheDocument()
  })

  it('saves valid custom days and retains draft when switching radios', async () => {
    mutateAsync.mockResolvedValueOnce({ ...user, data_retention_days: 15 })
    render(<SettingsPage />)
    await userEvent.click(screen.getByLabelText('Custom'))
    await userEvent.type(screen.getByLabelText('Custom period in days'), '15')
    await userEvent.click(screen.getByLabelText('30 days'))
    await userEvent.click(screen.getByLabelText('Custom'))
    expect(screen.getByLabelText('Custom period in days')).toHaveValue('15')
    await userEvent.click(
      screen.getByRole('button', { name: 'Save retention period' })
    )
    await screen.findByText('Data retention period updated')
    expect(mutateAsync).toHaveBeenCalledWith({
      body: { data_retention_days: 15 },
    })
    expect(screen.getByLabelText('Custom period in days')).toHaveValue('15')
  })

  it('retains input and allows retry after a failed save', async () => {
    mutateAsync.mockRejectedValueOnce(new Error('Offline'))
    render(<SettingsPage />)
    await userEvent.click(screen.getByLabelText('14 days'))
    await userEvent.click(
      screen.getByRole('button', { name: 'Save retention period' })
    )
    await screen.findByRole('link', {
      name: 'Your data retention period could not be saved. Try again.',
    })
    expect(screen.getByLabelText('14 days')).toBeChecked()
    expect(
      screen.queryByText('Data retention period updated')
    ).not.toBeInTheDocument()
    await userEvent.click(
      screen.getByRole('button', { name: 'Save retention period' })
    )
    await screen.findByText('Data retention period updated')
  })

  it('disables retention controls while saving without disabling microphone permission', async () => {
    mutation(true)
    render(<SettingsPage />)
    expect(screen.getByLabelText('7 days')).toBeDisabled()
    expect(
      screen.getByRole('button', { name: 'Saving retention period...' })
    ).toBeDisabled()
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: 'Allow microphone access' })
      ).toBeEnabled()
    )
  })

  it('saves microphones independently while retaining custom retention errors', async () => {
    vi.mocked(navigator.mediaDevices.enumerateDevices).mockResolvedValue([
      {
        deviceId: 'default',
        kind: 'audioinput',
        label: 'Default',
        groupId: '',
        toJSON: () => ({}),
      },
      {
        deviceId: 'teams',
        kind: 'audioinput',
        label: 'Teams',
        groupId: '',
        toJSON: () => ({}),
      },
    ])
    render(<SettingsPage />)
    await userEvent.click(screen.getByLabelText('Custom'))
    await userEvent.selectOptions(
      await screen.findByLabelText('Online'),
      'teams'
    )
    await userEvent.click(
      screen.getByRole('button', { name: 'Save microphones' })
    )
    expect(
      await screen.findByText('Microphone settings updated')
    ).toBeInTheDocument()
    expect(
      screen.getByRole('link', { name: 'Custom period cannot be blank' })
    ).toBeInTheDocument()
    expect(mutateAsync).not.toHaveBeenCalled()
  })
})

describe('custom retention validation', () => {
  it.each(['', ' '])('rejects blank %j', (value) =>
    expect(validateCustomRetention(value)).toBe('Custom period cannot be blank')
  )
  it.each(['abc', '1.5', '15.0', '1e1', '7x', '+7'])(
    'rejects format %j',
    (value) =>
      expect(validateCustomRetention(value)).toBe(
        'Enter a number in the correct format'
      )
  )
  it.each(['0', '-1', '31', '9999999999999999999999'])(
    'rejects range %j',
    (value) =>
      expect(validateCustomRetention(value)).toBe(
        'The number must be between 1 and 30'
      )
  )
  it.each(Array.from({ length: 30 }, (_, i) => String(i + 1)))(
    'accepts %s days',
    (value) => expect(validateCustomRetention(value)).toBeNull()
  )
})
