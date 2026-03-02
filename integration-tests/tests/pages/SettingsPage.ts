import { Locator, Page } from '@playwright/test'

export class SettingsPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/settings')
  }

  heading(): Locator {
    return this.page.getByRole('heading', {
      name: 'Settings',
    })
  }

  dataRetentionHeading(): Locator {
    return this.page.getByText('Data Retention Period')
  }

  radioOption(label: string): Locator {
    return this.page.getByRole('radio', { name: label })
  }

  saveButton(): Locator {
    return this.page.getByRole('button', { name: 'Save' })
  }
}
