import { Locator, Page } from '@playwright/test'

export class TemplatesPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/templates')
  }

  heading(): Locator {
    return this.page.getByRole('heading', {
      name: 'Your templates',
    })
  }

  documentTemplateItem(): Locator {
    return this.page.getByText('Document Template', { exact: true })
  }

  formTemplateItem(): Locator {
    return this.page.getByText('Form Template', { exact: true })
  }
}
