import { render, screen } from '@testing-library/react'
import type { ReactNode } from 'react'
import { AppRouterContext } from 'next/dist/shared/lib/app-router-context.shared-runtime'
import { beforeAll, describe, expect, it, vi } from 'vitest'

// outside a next build next/link is the pages router version, so load the real one
vi.mock('next/link', async () => {
  const { createRequire } = await import('node:module')
  const require = createRequire(import.meta.url)
  const Module = require('node:module')
  const resolveFilename = Module._resolveFilename
  Module._resolveFilename = function (request: string, ...rest: unknown[]) {
    const target = request.startsWith('react-server-dom-webpack/')
      ? require.resolve('../../stubs/react-server-dom-webpack-client.cjs')
      : request
    return resolveFilename.call(this, target, ...rest)
  }
  const mod = await import('next/dist/client/app-dir/link.js')
  const link = (mod as { default?: unknown }).default ?? mod
  return { default: (link as { default?: unknown }).default ?? link }
})

let GovukErrorSummary: typeof import('@/components/govuk/error-summary').GovukErrorSummary

beforeAll(async () => {
  ;({ GovukErrorSummary } = await import('@/components/govuk/error-summary'))
})

function withRouter(children: ReactNode) {
  return (
    <AppRouterContext.Provider value={{ prefetch: vi.fn() } as never}>
      {children}
    </AppRouterContext.Provider>
  )
}

function clickReturningDefaultPrevented(link: HTMLElement) {
  // the app router is never mounted in jsdom, so the dispatch that follows throws
  const swallow = (event: ErrorEvent) => event.preventDefault()
  window.addEventListener('error', swallow)
  const event = new MouseEvent('click', { bubbles: true, cancelable: true })
  try {
    link.dispatchEvent(event)
  } catch {}
  window.removeEventListener('error', swallow)
  return event.defaultPrevented
}

describe('GovukErrorSummary navigation', () => {
  it('keeps the browser on the page when an error links to another route', () => {
    render(
      withRouter(
        <GovukErrorSummary
          errorList={[
            { href: '/invite-user#invitee-evaluation-id', text: 'ID in use' },
          ]}
        />
      )
    )

    const link = screen.getByRole('link', { name: 'ID in use' })
    expect(clickReturningDefaultPrevented(link)).toBe(true)
  })

  it('leaves the browser to handle an in page error link', () => {
    render(
      withRouter(
        <GovukErrorSummary
          errorList={[{ href: '#invitee-evaluation-id', text: 'Enter an ID' }]}
        />
      )
    )

    const link = screen.getByRole('link', { name: 'Enter an ID' })
    expect(clickReturningDefaultPrevented(link)).toBe(false)
  })
})
