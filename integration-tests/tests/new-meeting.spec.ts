import { expect, test } from '@playwright/test'
import { NewMeeting } from './pages/NewMeeting'

test.describe('New meeting page', () => {
  test('shows new meeting page elements', async ({ page }) => {
    const newMeetingPage = new NewMeeting(page)

    await newMeetingPage.goto()

    await expect(newMeetingPage.backLink()).toBeVisible()
    await expect(newMeetingPage.uploadFile()).toBeVisible()
    await expect(newMeetingPage.recordMeeting()).toBeVisible()
    await expect(newMeetingPage.recordAudio()).toBeVisible()
  })
})
