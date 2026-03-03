import { expect, test } from '@playwright/test'
import { UploadAFile } from './pages/UploadAFile'

test.describe('Upload a file page', () => {
  test('shows main page elements', async ({ page }) => {
    const uploadAFilePage = new UploadAFile(page)

    await uploadAFilePage.goto()

    await expect(uploadAFilePage.backLink()).toBeVisible()
    await expect(uploadAFilePage.maxFileSize()).toBeVisible()
    await expect(uploadAFilePage.fileUploadButton()).toBeVisible()
    await expect(uploadAFilePage.fileUploadInput()).toBeVisible()
  })

  test('reveals minuting controls after file upload', async ({ page }) => {
    const uploadAFilePage = new UploadAFile(page)

    await uploadAFilePage.goto()

    await uploadAFilePage.attachFile()

    await expect(uploadAFilePage.generalStyleSelector()).toBeChecked()
    await expect(uploadAFilePage.yourTemplatesHeading()).toBeVisible()
  })
})
