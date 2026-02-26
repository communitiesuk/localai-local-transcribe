import { Locator, Page } from '@playwright/test'

export class HomePage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/')
  }

  heading(): Locator {
    return this.page.getByRole('heading', {
      name: 'AI transcription and drafting service',
    })
  }

  newMeetingCta(): Locator {
    return this.page.getByRole('link', { name: 'New meeting' })
  }

  recentMeetingsHeading(): Locator {
    return this.page.getByRole('heading', { name: 'Recent meetings:' })
  }

  retentionNotice(): Locator {
    return this.page.getByText('Your data retention period is set to')
  }

  transcriptionItemLink(id: string): Locator {
    return this.page.locator(`a[href="/transcriptions/${id}"]`)
  }

  transcriptionItemTitle(title: string): Locator {
    return this.page.getByText(title)
  }
}
