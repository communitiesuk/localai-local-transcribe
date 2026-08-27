import { SearchRecordings } from '@/components/recent-meetings/search-recordings'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  replace: vi.fn(),
  searchParams: new URLSearchParams(),
}))

vi.mock('next/navigation', () => ({
  usePathname: () => '/transcriptions',
  useRouter: () => ({
    replace: mocks.replace,
  }),
  useSearchParams: () => mocks.searchParams,
}))

describe('<SearchRecordings />', () => {
  beforeEach(() => {
    mocks.replace.mockReset()
    mocks.searchParams = new URLSearchParams('sort=oldest&page=3')
  })

  it('submits partial recording date search params while preserving sort and clearing page', async () => {
    render(<SearchRecordings />)

    await userEvent.click(screen.getByText('Show search fields'))
    await userEvent.type(screen.getAllByLabelText('Month')[0], '7')
    await userEvent.type(screen.getByLabelText('Client name'), 'Jane')
    await userEvent.click(screen.getByRole('button', { name: 'Submit' }))

    expect(mocks.replace).toHaveBeenCalledOnce()

    const [pathname, queryString] = mocks.replace.mock.calls[0][0].split('?')
    const params = new URLSearchParams(queryString)

    expect(pathname).toBe('/transcriptions')
    expect(params.get('sort')).toBe('oldest')
    expect(params.has('page')).toBe(false)
    expect(params.get('date_of_recording_month')).toBe('7')
    expect(params.has('date_of_recording')).toBe(false)
    expect(params.get('client_name')).toBe('Jane')
  })

  it('keeps DOB full-date validation for incomplete DOB searches', async () => {
    render(<SearchRecordings />)

    await userEvent.click(screen.getByText('Show search fields'))
    await userEvent.type(screen.getAllByLabelText('Month')[1], '4')
    await userEvent.click(screen.getByRole('button', { name: 'Submit' }))

    expect(
      await screen.findByText('The date of birth must include a day and year')
    ).toBeInTheDocument()
    expect(mocks.replace).not.toHaveBeenCalled()
  })

  it('resets search params while preserving unrelated params and clearing page', async () => {
    mocks.searchParams = new URLSearchParams(
      'sort=oldest&page=3&client_name=Jane&date_of_recording_month=7'
    )

    render(<SearchRecordings />)

    await userEvent.click(screen.getByText('Show search fields'))
    await userEvent.click(screen.getByRole('button', { name: 'Reset' }))

    expect(mocks.replace).toHaveBeenCalledWith('/transcriptions?sort=oldest')
  })
})
