import { expect, test } from '@playwright/test'
import { HomePage } from './pages/HomePage'

test.describe('Home page', () => {
  test('shows main page elements', async ({ page }) => {
    const homePage = new HomePage(page)

    await homePage.goto()

    await expect(homePage.templatesLink()).toBeVisible()
    await expect(homePage.settingsLink()).toHaveCount(1)
    await expect(homePage.heading()).toBeVisible()
    await expect(homePage.newMeetingCta()).toBeVisible()
    await expect(homePage.newMeetingCta()).toHaveAttribute('href', '/new')
  })
})
