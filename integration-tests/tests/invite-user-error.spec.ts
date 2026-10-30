import { expect, test, type Page } from '@playwright/test'
import { InviteUserPage } from './pages/InviteUserPage'

const ORGANISATION_ID = '11111111-1111-1111-1111-111111111111'
const TIMESTAMP = '2026-01-01T00:00:00Z'

const INVITEE = {
  name: 'Test Invitee',
  email: 'test.invitee@test.co.uk',
  evaluationId: 'EVAL-1177',
}

const EVALUATION_ID_IN_USE = 'Evaluation ID is already in use'

async function stubInviteJourney(page: Page) {
  await page.route('**/api/proxy/users/me', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: '22222222-2222-2222-2222-222222222222',
        created_datetime: TIMESTAMP,
        updated_datetime: TIMESTAMP,
        accepted_tou: true,
        last_login: TIMESTAMP,
        is_active: true,
        name: 'Test Admin',
        email: 'test@test.co.uk',
        data_retention_days: 30,
        roles: ['local_authority_admin'],
        organisation_id: ORGANISATION_ID,
      }),
    })
  )

  await page.route(`**/api/proxy/organisations/${ORGANISATION_ID}`, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: ORGANISATION_ID,
        name: 'Test Council',
        allowed_domains: ['test.co.uk'],
        created_datetime: TIMESTAMP,
        updated_datetime: TIMESTAMP,
      }),
    })
  )

  await page.route('**/api/proxy/users/user/exists*', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ exists: false }),
    })
  )

  await page.route('**/api/proxy/users', (route) => {
    if (route.request().method() !== 'POST') {
      return route.fallback()
    }

    return route.fulfill({
      status: 400,
      contentType: 'application/json',
      body: JSON.stringify({ detail: EVALUATION_ID_IN_USE }),
    })
  })
}

test.describe('Invite user error summary', () => {
  test('keeps the entered details when returning from an error', async ({
    page,
  }) => {
    await stubInviteJourney(page)

    const inviteUserPage = new InviteUserPage(page)
    await inviteUserPage.goto()
    await inviteUserPage.fillDetails(INVITEE)

    // a full page load gives a fresh window, which is the bug the fix prevents
    await page.evaluate(() => {
      Object.assign(window, { inviteUserDocument: true })
    })

    await inviteUserPage.continueButton().click()
    await expect(page).toHaveURL(/\/invite-user\/confirm$/)

    await inviteUserPage.inviteButton().click()

    const errorLink = inviteUserPage.errorSummaryLink(EVALUATION_ID_IN_USE)
    await expect(errorLink).toBeVisible()
    await errorLink.click()

    await expect(page).toHaveURL(/\/invite-user#invitee-evaluation-id$/)
    await expect(
      page.evaluate(
        () =>
          (window as unknown as { inviteUserDocument?: boolean })
            .inviteUserDocument
      )
    ).resolves.toBe(true)

    await expect(inviteUserPage.nameInput()).toHaveValue(INVITEE.name)
    await expect(inviteUserPage.emailInput()).toHaveValue(INVITEE.email)
    await expect(inviteUserPage.evaluationIdInput()).toHaveValue(
      INVITEE.evaluationId
    )
  })
})
