import { Locator, Page } from '@playwright/test'

export class NewMeeting {
    constructor(private page: Page) { }

    async goto() {
        await this.page.goto('/new')
    }

    backLink(): Locator {
        return this.page.getByRole('link', { name: 'Back', exact: true })
    }

    uploadFile(): Locator {
        return this.page.getByRole('link', { name: 'Upload file' })
    }

    recordMeeting(): Locator {
        return this.page.getByRole('link', { name: 'Record a virtual meeting' })
    }

    recordAudio(): Locator {
        return this.page.getByRole('link', { name: 'Record audio' })
    }

}