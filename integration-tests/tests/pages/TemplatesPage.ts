import { Locator, Page } from '@playwright/test'

export interface Template {
  name: string
  description: string
  content: string
}

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

  async createDocumentTemplate(template: Template) {
    await this.page
      .getByRole('link', { name: 'Create a new template' })
      .first()
      .click()

    await this.page
      .getByRole('textbox', { name: 'Name your template' })
      .fill(template.name)
    await this.page
      .getByRole('textbox', { name: 'A description to help' })
      .fill(template.description)

    // TODO: change this when the accessibility issue on the rich text editor is resolved
    await this.page.getByRole('textbox').nth(2).click()
    await this.page.keyboard.type(template.content)

    await this.page.getByRole('button', { name: 'Save' }).click()
  }

  async deleteDocumentTemplate() {
    // Click Delete twice - once on template card, then on modal confirmation
    // Brittle selector - assumes you want to delete the first template
    await this.page.getByRole('button', { name: 'Delete' }).first().click()
    await this.page.getByRole('button', { name: 'Delete' }).click()
  }

  documentTemplateItem(title: string): Locator {
    return this.page.getByText(title, { exact: true })
  }

  formTemplateItem(title: string): Locator {
    return this.page.getByText(title, { exact: true })
  }
}
