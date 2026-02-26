import { Page } from '@playwright/test'

export class BackendApiMock {
  constructor(private page: Page) {}

  async mockHomePageSuccess() {
    await this.abortPosthog()
    await this.mockCurrentUser()
    await this.mockTranscriptions()
  }

  private async mockCurrentUser() {
    await this.page.route('**/api/proxy/users/me', async (route) => {
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

  private async mockTranscriptions() {
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

  private async abortPosthog() {
    await this.page.route('https://eu.i.posthog.com/**', async (route) => {
      await route.abort()
    })
    await this.page.route('https://*.posthog.com/**', async (route) => {
      await route.abort()
    })
  }
}
