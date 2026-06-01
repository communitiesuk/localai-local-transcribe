import { render } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

vi.mock('@sentry/nextjs', () => ({ captureException: vi.fn() }))

describe('<GovukInit />', () => {
  it('calls initAll exactly once after mount', async () => {
    vi.doMock('govuk-frontend', () => ({ initAll: vi.fn() }))
    const { GovukInit } = await import('@/components/layout/govuk-init')
    const { initAll } = await import('govuk-frontend')
    render(<GovukInit />)
    await vi.waitFor(() => expect(initAll).toHaveBeenCalledTimes(1))
  })

  it('captures a dynamic-import failure to Sentry instead of failing silently', async () => {
    vi.resetModules()
    vi.doMock('govuk-frontend', () => {
      throw new Error('chunk load failed')
    })
    const Sentry = await import('@sentry/nextjs')
    const { GovukInit } = await import('@/components/layout/govuk-init')
    render(<GovukInit />)
    await vi.waitFor(() =>
      expect(Sentry.captureException).toHaveBeenCalledTimes(1),
    )
  })
})
