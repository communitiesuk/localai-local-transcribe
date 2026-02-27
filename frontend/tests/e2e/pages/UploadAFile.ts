import { Locator, Page } from '@playwright/test'

export class UploadAFile {
    constructor(private page: Page) { }

    async goto() {
        await this.page.goto('/new/upload')
    }

    backLink(): Locator {
        return this.page.getByRole('link', { name: 'Back', exact: true })
    }

    maxFileSize(): Locator {
        return this.page.getByText('Maximum file size: 5GB')
    }

    fileUploadButton(): Locator {
        return this.page.getByRole('button', { name: 'Choose a file' })
    }

    // brittle but there's no accessible label at the moment
    fileUploadInput(): Locator {
        return this.page.locator('input[type="file"]')
    }

    yourTemplatesHeading(): Locator {
        return this.page.getByRole('heading', { name: 'Your templates' })
    }

    generalStyleSelector(): Locator {
        return this.page.getByRole('radio', { name: 'General' })
    }

    async attachFile() {
        this.fileUploadInput().setInputFiles({
            name: 'test.mp3',
            mimeType: 'audio/mpeg',
            buffer: Buffer.from('test'),
        })
    }
}
