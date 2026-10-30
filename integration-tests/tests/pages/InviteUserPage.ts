import { Locator, Page } from '@playwright/test'

export class InviteUserPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/invite-user')
  }

  nameInput(): Locator {
    return this.page.getByLabel('Name', { exact: true })
  }

  emailInput(): Locator {
    return this.page.getByLabel('Email address')
  }

  evaluationIdInput(): Locator {
    return this.page.getByLabel('Evaluation ID')
  }

  continueButton(): Locator {
    return this.page.getByRole('button', { name: 'Continue' })
  }

  inviteButton(): Locator {
    return this.page.getByRole('button', { name: 'Invite' })
  }

  errorSummaryLink(text: string): Locator {
    return this.page.getByRole('link', { name: text })
  }

  async fillDetails(details: {
    name: string
    email: string
    evaluationId: string
  }) {
    await this.nameInput().fill(details.name)
    await this.emailInput().fill(details.email)
    await this.evaluationIdInput().fill(details.evaluationId)
  }
}
