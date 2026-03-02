import { expect, test } from '@playwright/test'
import { SettingsPage } from './pages/SettingsPage'

test.describe('Settings page', () => {
  test('shows setting page elements', async ({ page }) => {
    const settingsPage = new SettingsPage(page)
    await settingsPage.goto()
    await expect(settingsPage.heading()).toBeVisible()
    await expect(settingsPage.saveButton()).toBeVisible()
  })
  test('retention settings reflects user', async ({ page }) => {
    const settingsPage = new SettingsPage(page)
    await settingsPage.goto()

    await expect(settingsPage.dataRetentionHeading()).toBeVisible()
    for (const rententionPeriod of [
      'Keep indefinitely',
      '1 day',
      '7 days',
      '30 days',
      '90 days',
    ]) {
      await expect(settingsPage.radioOption(rententionPeriod)).toBeVisible()
    }

    await expect(settingsPage.radioOption('30 days')).toBeChecked()
  })
  test.skip('test retention submission', async ({ page }) => {
    // no UI changes so hard to test
  })
})
