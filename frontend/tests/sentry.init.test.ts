import { beforeEach, afterAll, describe, expect, it, vi } from 'vitest'

// sentry.data-collection.test.ts proves the baseline object has the right values. This file proves
// each runtime actually hands that object to Sentry.init - without it, deleting `dataCollection`
// from one of the three init calls leaves the suite green while that runtime silently falls back to
// the permissive v11 defaults.

vi.mock('@sentry/nextjs', () => ({
  init: vi.fn(),
  captureRouterTransitionStart: vi.fn(),
  captureRequestError: vi.fn(),
}))

// Every config module calls init as an import side effect, guarded by `if (SENTRY_DSN)`. So the DSN
// has to be set before the import, and the module registry reset between cases - otherwise only the
// first case executes its module body and the rest trivially pass.
const CONFIG_MODULES = [
  '@/instrumentation-client',
  '@/sentry.server.config',
  '@/sentry.edge.config',
]

const ORIGINAL_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN

beforeEach(() => {
  vi.resetModules()
  // resetModules re-executes the config module bodies but leaves the mock's call history intact, so
  // without this the init calls accumulate across cases and the no-DSN assertions see earlier ones.
  vi.clearAllMocks()
  process.env.NEXT_PUBLIC_SENTRY_DSN =
    'https://public@example.ingest.sentry.io/1'
})

afterAll(() => {
  if (ORIGINAL_DSN === undefined) {
    delete process.env.NEXT_PUBLIC_SENTRY_DSN
  } else {
    process.env.NEXT_PUBLIC_SENTRY_DSN = ORIGINAL_DSN
  }
})

describe('Sentry init wiring', () => {
  it.each(CONFIG_MODULES)(
    '%s passes the pinned dataCollection baseline',
    async (modulePath) => {
      await import(modulePath)
      const Sentry = await import('@sentry/nextjs')
      const { dataCollection } = await import('@/sentry.data-collection')

      expect(Sentry.init).toHaveBeenCalledTimes(1)
      expect(Sentry.init).toHaveBeenCalledWith(
        expect.objectContaining({ dataCollection })
      )
    }
  )

  it.each(CONFIG_MODULES)(
    '%s does not initialise without a DSN',
    async (modulePath) => {
      delete process.env.NEXT_PUBLIC_SENTRY_DSN
      await import(modulePath)
      const Sentry = await import('@sentry/nextjs')

      expect(Sentry.init).not.toHaveBeenCalled()
    }
  )
})
