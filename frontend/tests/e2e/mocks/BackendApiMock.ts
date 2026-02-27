import { Page } from '@playwright/test'

export class BackendApiMock {
  constructor(private page: Page) {}

  async mockCurrentUser() {
    await this.page.route('**/api/proxy/users/me', async (route) => {
      console.log('Mocking current user API response')
      const { pathname } = new URL(route.request().url())

      if (pathname !== '/api/proxy/users/me') {
        await route.fallback()
        return
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'user-1',
          created_datetime: '2025-01-01T00:00:00Z',
          updated_datetime: '2025-01-01T00:00:00Z',
          email: 'test@test.com',
          data_retention_days: 30,
        }),
      })
    })
  }

  async mockTranscriptions() {
    await this.page.route('**/api/proxy/transcriptions*', async (route) => {
      const { pathname } = new URL(route.request().url())

      if (pathname !== '/api/proxy/transcriptions') {
        await route.fallback()
        return
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'transcription-1',
              created_datetime: '2025-01-01T12:30:00Z',
              title: 'Quarterly planning meeting',
              text: 'Draft notes',
              status: 'completed',
            },
          ],
          total_count: 1,
          page: 1,
          page_size: 10,
          total_pages: 1,
        }),
      })
    })
  }

  async abortPosthog() {
    await this.page.route('https://*.posthog.com/**', async (route) => {
      await route.abort()
    })
  }
}
