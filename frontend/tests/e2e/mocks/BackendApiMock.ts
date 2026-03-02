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

  /**
   * Mocks the /api/proxy/user-templates endpoint.
   *
   * @param templates - If `true`, returns a default fake template. If `false`, returns an empty array.
   *                   For more flexibility, consider changing this to accept an array of templates.
   *
   * Usage:
   *   await backendApiMock.mockUserTemplates(); // returns []
   *   await backendApiMock.mockUserTemplates(true); // returns one fake template
   */
  async mockUserTemplates(templates: boolean = false) {
    await this.page.route('**/api/proxy/user-templates', async (route) => {
      const { pathname } = new URL(route.request().url())

      if (pathname !== '/api/proxy/user-templates') {
        await route.fallback()
        return
      }

      if (templates) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 'a0a109ba-f87c-4cf0-b196-bfe656c16cb6',
              updated_datetime: '2026-03-02T11:16:55.620631Z',
              name: 'Form Template',
              content: 'Form Template content',
              description: 'Form template description',
              type: 'form',
              questions: null,
            },
            {
              id: '1989c365-db64-4787-8408-7f570eb61388',
              updated_datetime: '2026-03-02T11:11:27.447621Z',
              name: 'Document Template',
              content: '<p>Document Template content</p>',
              description: 'Document template description',
              type: 'document',
              questions: null,
            },
          ]),
        })
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([]),
        })
      }
    })
  }

  /**
   * Mocks the backend API endpoint for retrieving meeting minute templates.
   * 
   * Intercepts requests to `/api/proxy/templates` and returns a predefined list of template objects
   * containing template metadata such as name, description, category, and agenda usage requirements.
   * 
   * @async
   * @returns {Promise<void>}
   * 
   * @example
   * await backendApiMock.mockTemplates();
   */
  async mockTemplates() {
    await this.page.route('**/api/proxy/templates', async (route) => {
      const { pathname } = new URL(route.request().url())

      if (pathname !== '/api/proxy/templates') {
        await route.fallback()
        return
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            name: 'Cabinet',
            description: 'Formal minutes following cabinet meeting structure',
            category: 'Formal Minutes',
            agenda_usage: 'optional',
          },
          {
            name: 'Care Assessment V2',
            description:
              'Enhanced Social care assessment template based on Care Act Eligibility Criteria',
            category: 'Social Care',
            agenda_usage: 'not_used',
          },
          {
            name: 'Delivery',
            description: 'Formal minutes following the delivery style guide',
            category: 'Formal Minutes',
            agenda_usage: 'not_used',
          },
          {
            name: "Short 'n' Sweet",
            description: 'Executive summary of the meeting + action items',
            category: 'Common',
            agenda_usage: 'not_used',
          },
          {
            name: 'General',
            description:
              'Standard meeting summary with key points, decisions, and action items',
            category: 'Common',
            agenda_usage: 'optional',
          },
          {
            name: 'Planning Committee',
            description: 'Planning committee minutes template',
            category: 'Formal Minutes',
            agenda_usage: 'required',
          },
        ]),
      })
    })
  }
}
