import { expect, test } from '@playwright/test'

test('GET /health returns status ok', async ({ request }) => {
  const response = await request.get('/health')
  const body = await response.json()

  expect(response.status()).toBe(200)
  expect(body).toEqual({ status: 'ok' })
})

test('/support page renders support content', async ({ page }) => {
  await page.goto('/support')

  await expect(
    page.getByRole('heading', { name: 'Support Center' })
  ).toBeVisible()
  await expect(
    page.locator('a[href="mailto:minute-support@cabinetoffice.gov.uk"]')
  ).toBeVisible()
})

test('/privacy page renders heading', async ({ page }) => {
  await page.goto('/privacy')

  await expect(
    page.getByRole('heading', { name: 'Privacy Notice' })
  ).toBeVisible()
})
