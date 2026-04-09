import { v4 as uuid } from 'uuid'
import { expect, test } from '@playwright/test'
import { TemplatesPage } from './pages/TemplatesPage'
import type { Template } from './pages/TemplatesPage'

test.describe('Templates page', () => {
  test('shows templates page elements', async ({ page }) => {
    const templatesPage = new TemplatesPage(page)
    await templatesPage.goto()

    await expect(templatesPage.heading()).toBeVisible()
  })
  test('adds and deletes a template', async ({ page }) => {
    const template: Template = {
      name: `Test User Template ${uuid()}`,
      description: 'Test User Template Description',
      content: 'Test User Template Content',
    }

    const templatesPage = new TemplatesPage(page)
    await templatesPage.goto()

    await templatesPage.createDocumentTemplate(template)
    await expect(
      templatesPage.documentTemplateItem(template.name)
    ).toBeVisible()

    await templatesPage.deleteDocumentTemplate()
    await expect(templatesPage.documentTemplateItem(template.name)).toHaveCount(
      0
    )
  })
})
