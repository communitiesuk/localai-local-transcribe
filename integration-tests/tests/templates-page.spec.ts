import { expect, test } from '@playwright/test'
import { TemplatesPage } from './pages/TemplatesPage'

test.describe('Templates page', () => {
  test('shows templates page elements', async ({ page }) => {
    const templatesPage = new TemplatesPage(page)
    await templatesPage.goto()

    await expect(templatesPage.heading()).toBeVisible()
  })
})
