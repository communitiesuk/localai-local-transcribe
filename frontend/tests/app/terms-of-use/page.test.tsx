/* eslint-disable @typescript-eslint/no-explicit-any */
import TermsOfUsePage from '@/app/terms-of-use/page'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return {
    ...actual,
    useQuery: vi.fn(),
    useMutation: vi.fn(),
    useQueryClient: vi.fn(),
  }
})

describe('<TermsOfUsePage />', () => {
  const scrollIntoView = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    Element.prototype.scrollIntoView = scrollIntoView

    vi.mocked(useQuery).mockReturnValue({
      data: { id: 'user-1', accepted_tou: false },
    } as any)

    vi.mocked(useQueryClient).mockReturnValue({
      setQueryData: vi.fn(),
      invalidateQueries: vi.fn(),
    } as any)
  })

  const renderWithFailingMutation = () => {
    vi.mocked(useMutation).mockImplementation(
      ({ onError }: any) =>
        ({
          mutate: () => onError?.(new Error('failed')),
          isPending: false,
        }) as any
    )

    return render(<TermsOfUsePage />)
  }

  it('does not show an error summary before submission', () => {
    vi.mocked(useMutation).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any)

    render(<TermsOfUsePage />)

    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('moves focus to the error summary when submission fails', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const user = userEvent.setup()
    renderWithFailingMutation()

    await user.click(
      screen.getByRole('button', { name: 'Accept and continue' })
    )

    const errorSummary = await screen.findByText(
      'Accept the terms of use to continue'
    )
    const summaryContainer = errorSummary.closest('.govuk-error-summary')

    await waitFor(() => expect(summaryContainer).toHaveFocus())
    expect(scrollIntoView).toHaveBeenCalled()
  })

  it('shows a confirmation screen with review and exit options when declining', async () => {
    const user = userEvent.setup()
    vi.mocked(useMutation).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any)

    render(<TermsOfUsePage />)

    await user.click(screen.getByRole('button', { name: 'I do not accept' }))

    expect(
      screen.getByRole('heading', { name: 'Terms of Use required' })
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Review Terms of Use' })
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Exit Local Transcribe' })
    ).toHaveAttribute('href', '/api/proxy/signout')
  })

  it('returns to the terms and clears a stale submission error when reviewing again', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const user = userEvent.setup()
    renderWithFailingMutation()

    await user.click(
      screen.getByRole('button', { name: 'Accept and continue' })
    )
    await screen.findByText('Accept the terms of use to continue')

    await user.click(screen.getByRole('button', { name: 'I do not accept' }))
    await user.click(
      screen.getByRole('button', { name: 'Review Terms of Use' })
    )

    expect(
      screen.queryByText('Accept the terms of use to continue')
    ).not.toBeInTheDocument()
  })

  it('disables "I do not accept" while a submission is pending', () => {
    vi.mocked(useMutation).mockReturnValue({
      mutate: vi.fn(),
      isPending: true,
    } as any)

    render(<TermsOfUsePage />)

    expect(
      screen.getByRole('button', { name: 'I do not accept' })
    ).toBeDisabled()
  })
})

describe('<TermsOfUsePage /> bfcache handling', () => {
  const scrollIntoView = vi.fn()
  let reloadMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.clearAllMocks()
    Element.prototype.scrollIntoView = scrollIntoView

    vi.mocked(useQuery).mockReturnValue({
      data: { id: 'user-1', accepted_tou: false },
    } as any)

    vi.mocked(useQueryClient).mockReturnValue({
      setQueryData: vi.fn(),
      invalidateQueries: vi.fn(),
    } as any)

    vi.mocked(useMutation).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any)

    reloadMock = vi.fn()
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...window.location, reload: reloadMock },
    })
  })

  it('reloads the page when restored from the back/forward cache', () => {
    render(<TermsOfUsePage />)

    const event = new Event('pageshow')
    Object.defineProperty(event, 'persisted', { value: true })
    window.dispatchEvent(event)

    expect(reloadMock).toHaveBeenCalledTimes(1)
  })

  it('does not reload on a normal (non-persisted) pageshow', () => {
    render(<TermsOfUsePage />)

    const event = new Event('pageshow')
    Object.defineProperty(event, 'persisted', { value: false })
    window.dispatchEvent(event)

    expect(reloadMock).not.toHaveBeenCalled()
  })
})
