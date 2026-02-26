import { expect, test } from '@playwright/test'
import { BackendApiMock } from './mocks/BackendApiMock'
import { HomePage } from './pages/HomePage'

test('home page renders hero, CTA, and mocked recent meeting', async ({
  page,
}) => {
  const backendApiMock = new BackendApiMock(page)
  await backendApiMock.mockHomePageSuccess()

  const homePage = new HomePage(page)
  await homePage.goto()

  await expect(homePage.heading()).toBeVisible()
  await expect(homePage.newMeetingCta()).toBeVisible()
  await expect(homePage.newMeetingCta()).toHaveAttribute('href', '/new')

  await expect(homePage.recentMeetingsHeading()).toBeVisible()
  await expect(homePage.retentionNotice()).toBeVisible()

  // log the html to the console
  const html = await page.content()
  console.log(html)

  await expect(
    homePage.transcriptionItemTitle('Quarterly planning meeting')
  ).toBeVisible()

  await expect(homePage.transcriptionItemLink('transcription-1')).toBeVisible()
})
