import { expect, test } from '@playwright/test'
import { TemplatesPage } from './pages/TemplatesPage'
import { BackendApiMock } from './mocks/BackendApiMock'

test.describe('Templates page', () => {
  test('shows templates page elements', async ({ page }) => {
    const backendMock = new BackendApiMock(page)
    await backendMock.mockCurrentUser()
    await backendMock.mockUserTemplates()

    const templatesPage = new TemplatesPage(page)
    await templatesPage.goto()

    await expect(templatesPage.heading()).toBeVisible()
  })
  test('shows template exists', async ({ page }) => {
    const backendMock = new BackendApiMock(page)
    await backendMock.mockCurrentUser()
    await backendMock.mockUserTemplates(true)

    const templatesPage = new TemplatesPage(page)
    await templatesPage.goto()

    await expect(templatesPage.documentTemplateItem()).toBeVisible()
    await expect(templatesPage.formTemplateItem()).toBeVisible()
  })
})
